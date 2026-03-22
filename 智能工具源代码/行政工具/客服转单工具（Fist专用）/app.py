import base64
import json
import logging
import os
import re
import shutil
import sys
import threading
import uuid
import webbrowser
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from excel_mapper import extract_template_targets, generate_workbooks, load_a_headers

# ─── 处理打包后的目录结构 (PyInstaller) ───────────────────────────────────
if getattr(sys, "frozen", False):
    # 打包运行环境
    BASE_DIR = Path(sys._MEIPASS)
    # 生成目录在用户实际打开程序的路径下（而不是临时解压路径）
    WORKING_DIR = Path(os.getcwd())
else:
    # 直接运行环境
    BASE_DIR = Path(__file__).resolve().parent
    WORKING_DIR = BASE_DIR

# HTML 文件的实际存储位置（打包时会放进根目录）
HTML_FILE_NAME = "客服转单工具_Fist专用.html"
HTML_PATH = BASE_DIR / HTML_FILE_NAME

# 生成目录
_DATADIR = WORKING_DIR / "generated"
_DATADIR.mkdir(exist_ok=True)

try:
    import win32com.client as win32
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class MapperRequestHandler(BaseHTTPRequestHandler):
    server_version = "ExcelMapperHTTP/1.0"

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # 根目录：向用户展示主 HTML
        if path == "/":
            if HTML_PATH.exists():
                 return self._serve_file(HTML_PATH, "text/html; charset=utf-8")
            else:
                 # 兜底查找 templates 目录
                 alt_path = BASE_DIR / "templates" / "index.html"
                 if alt_path.exists():
                     return self._serve_file(alt_path, "text/html; charset=utf-8")
                 return self._send_json({"error": "找不到前端模板文件"}, HTTPStatus.NOT_FOUND)

        # 静态文件（主要是生成的 Excel 和 ZIP）
        if path.startswith("/generated/"):
            file_path = (WORKING_DIR / path.lstrip("/")).resolve()
            if _DATADIR not in file_path.parents and file_path != _DATADIR:
                return self._send_json({"error": "非法路径访问"}, HTTPStatus.FORBIDDEN)
            return self._serve_file(file_path, self._guess_content_type(file_path))

        if path == "/api/health":
            return self._send_json({"ok": True, "message": "server-ready"})
            
        return self._send_json({"error": "未找到资源"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if self.path == "/api/inspect":
            return self._handle_inspect()
        if self.path == "/api/generate":
            return self._handle_generate()
        return self._send_json({"error": "接口不存在"}, HTTPStatus.NOT_FOUND)

    def _handle_inspect(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            
            a_path = _DATADIR / f"temp_a_{uuid.uuid4().hex}.xlsx"
            b_path = _DATADIR / f"temp_b_{uuid.uuid4().hex}.xlsx"
            
            a_path.write_bytes(base64.b64decode(data["aFileContent"]))
            b_path.write_bytes(base64.b64decode(data["bFileContent"]))
            
            headers = load_a_headers(a_path)
            targets = extract_template_targets(b_path)
            
            a_path.unlink(missing_ok=True)
            b_path.unlink(missing_ok=True)
            
            return self._send_json({"headers": headers, "targets": targets})
        except Exception as e:
            logging.exception("解析失败")
            return self._send_json({"error": f"解析文件失败: {str(e)}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_generate(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            
            run_id = uuid.uuid4().hex[:8]
            run_dir = _DATADIR / f"run-{run_id}"
            run_dir.mkdir(exist_ok=True)
            
            a_path = run_dir / "data_a.xlsx"
            b_path = run_dir / "template_b.xlsx"
            a_path.write_bytes(base64.b64decode(data["aFileContent"]))
            b_path.write_bytes(base64.b64decode(data["bFileContent"]))
            
            image_config = None
            if data.get("imageConfig"):
                img_path = run_dir / f"img_{data['imageConfig']['imageName']}"
                img_path.write_bytes(base64.b64decode(data["imageConfig"]["imageContent"]))
                image_config = {
                    "path": str(img_path),
                    "target_cell": data["imageConfig"]["targetCell"]
                }
            
            result = generate_workbooks(
                a_path, b_path, data["mappings"], run_dir, image_config
            )
            
            # 处理 .xls 格式转换
            if data.get("outputFormat") == "xls" and HAS_WIN32:
                xlsx_files = [Path(p) for p in result["files"]]
                xls_files = self._convert_xlsx_to_xls_batch(xlsx_files)
                # 重新打包 ZIP
                zip_path = run_dir / "excel_output.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as arc:
                    for f in xls_files:
                        arc.write(f, arcname=f.name)
                result["zip_path"] = str(zip_path)
                result["files"] = [str(f) for f in xls_files]

            base_rel = run_dir.relative_to(WORKING_DIR).as_posix()
            zip_rel = Path(result["zip_path"]).relative_to(WORKING_DIR).as_posix()
            
            return self._send_json({
                "count": result["count"],
                "outputDir": str(run_dir),
                "zipUrl": f"/{zip_rel}",
                "files": [Path(f).name for f in result["files"]]
            })
        except Exception as e:
            logging.exception("生成失败")
            return self._send_json({"error": f"生成任务失败: {str(e)}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _convert_xlsx_to_xls_batch(self, file_paths):
        xls_files = []
        try:
            excel = win32.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            for fp in file_paths:
                try:
                    wb = excel.Workbooks.Open(str(fp.resolve()))
                    new_path = fp.with_suffix(".xls")
                    # 56 是 xlExcel8 (xls 格式)
                    wb.SaveAs(str(new_path.resolve()), FileFormat=56)
                    wb.Close()
                    xls_files.append(new_path)
                    fp.unlink() # 转换后删除原 xlsx
                except Exception as e:
                    print(f"转换单个文件失败: {e}")
            excel.Quit()
        except Exception as e:
            print(f"打开 Excel 转换器失败: {e}")
        return xls_files or file_paths

    def _serve_file(self, file_path: Path, content_type: str):
        if not file_path.exists() or not file_path.is_file():
            return self._send_json({"error": "文件不存在"}, HTTPStatus.NOT_FOUND)
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._set_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guess_content_type(self, path: Path):
        suffix = path.suffix.lower()
        if suffix in (".html", ".htm"): return "text/html; charset=utf-8"
        if suffix == ".json": return "application/json; charset=utf-8"
        if suffix == ".zip": return "application/zip"
        if suffix == ".xls": return "application/vnd.ms-excel"
        if suffix == ".xlsx": return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return "application/octet-stream"

def run_server(port=8000):
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, MapperRequestHandler)
    print(f"\n" + "═"*50)
    print(f"🚀 Fist 客服转单工具 (本地服务) 启动成功!")
    print(f"🔗 地址：http://127.0.0.1:{port}/")
    print(f"提示：程序运行时请勿关闭此黑色窗口")
    print("═"*50 + "\n")
    
    def open_browser():
        webbrowser.open(f"http://127.0.0.1:{port}/")
    
    threading.Timer(1.2, open_browser).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
