import base64
import json
import os
import tempfile
import webbrowser
from datetime import datetime
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from excel_mapper import extract_template_targets, generate_workbooks, load_a_headers


BASE_DIR = Path(__file__).resolve().parent


class MapperRequestHandler(BaseHTTPRequestHandler):
    server_version = "ExcelMapperHTTP/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            return self._serve_file(self.server.asset_dir / "templates" / "index.html", "text/html; charset=utf-8")
        if path.startswith("/static/"):
            file_path = self.server.asset_dir / path.lstrip("/")
            return self._serve_file(file_path, self._guess_content_type(file_path))
        if path.startswith("/generated/"):
            file_path = (self.server.base_dir / path.lstrip("/")).resolve()
            generated_root = (self.server.base_dir / "generated").resolve()
            if generated_root not in file_path.parents and file_path != generated_root:
                return self._send_json({"error": "无效的下载路径"}, HTTPStatus.BAD_REQUEST)
            return self._serve_file(file_path, self._guess_content_type(file_path))
        if path == "/api/health":
            return self._send_json({"ok": True, "message": "server-ready"})
        return self._send_json({"error": "未找到请求资源"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/inspect":
            return self._handle_inspect()
        if parsed.path == "/api/generate":
            return self._handle_generate()
        return self._send_json({"error": "未找到请求资源"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        return

    def _handle_inspect(self):
        try:
            payload = self._read_json()
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                a_path = self._write_upload(tmp_path, payload["aFileName"], payload["aFileContent"])
                b_path = self._write_upload(tmp_path, payload["bFileName"], payload["bFileContent"])
                headers = load_a_headers(a_path)
                targets = extract_template_targets(b_path)
            return self._send_json({"headers": headers, "targets": targets})
        except Exception as exc:
            return self._send_json({"error": f"解析文件失败: {exc}"}, HTTPStatus.BAD_REQUEST)

    def _handle_generate(self):
        try:
            payload = self._read_json()
            mappings = payload.get("mappings", [])
            if len(mappings) > 10:
                raise ValueError("最多只能配置 10 条映射")

            run_name = datetime.now().strftime("run-%Y%m%d-%H%M%S")
            run_dir = self.server.base_dir / "generated" / run_name
            upload_dir = run_dir / "_uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)

            a_path = self._write_upload(upload_dir, payload["aFileName"], payload["aFileContent"])
            b_path = self._write_upload(upload_dir, payload["bFileName"], payload["bFileContent"])
            output_dir = run_dir / "excel"

            result = generate_workbooks(
                a_path=a_path,
                b_path=b_path,
                mappings=mappings,
                output_dir=output_dir,
            )
            zip_path = Path(result["zip_path"])
            response = {
                "count": result["count"],
                "files": [Path(file_path).name for file_path in result["files"]],
                "outputDir": str(output_dir),
                "zipUrl": "/" + zip_path.relative_to(self.server.base_dir).as_posix(),
                "fixedMappings": [
                    {"source": "收货件数", "target": "B16"},
                    {"source": "额外服务", "target": "F6"},
                    {"source": "客户单号+U000001-+收货件数", "target": "A18"},
                ],
            }
            return self._send_json(response)
        except Exception as exc:
            return self._send_json({"error": f"生成失败: {exc}"}, HTTPStatus.BAD_REQUEST)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def _write_upload(self, directory: Path, file_name: str, content: str) -> Path:
        safe_name = Path(file_name).name or "upload.xlsx"
        file_path = directory / safe_name
        if "," in content:
            content = content.split(",", 1)[1]
        file_path.write_bytes(base64.b64decode(content))
        return file_path

    def _serve_file(self, file_path: Path, content_type: str):
        if not file_path.exists() or not file_path.is_file():
            return self._send_json({"error": "文件不存在"}, HTTPStatus.NOT_FOUND)
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guess_content_type(self, file_path: Path):
        suffix = file_path.suffix.lower()
        if suffix == ".html":
            return "text/html; charset=utf-8"
        if suffix == ".css":
            return "text/css; charset=utf-8"
        if suffix == ".js":
            return "application/javascript; charset=utf-8"
        if suffix == ".zip":
            return "application/zip"
        if suffix == ".xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return "application/octet-stream"


def create_server(host="127.0.0.1", port=8000, base_dir=None):
    target_dir = Path(base_dir or BASE_DIR).resolve()
    handler = MapperRequestHandler
    server = ThreadingHTTPServer((host, port), handler)
    server.base_dir = target_dir
    server.asset_dir = BASE_DIR
    return server


def main():
    host = os.environ.get("EXCEL_MAPPER_HOST", "127.0.0.1")
    port = int(os.environ.get("EXCEL_MAPPER_PORT", "8000"))
    server = create_server(host, port, BASE_DIR)
    url = f"http://{host}:{port}/"
    print(f"Excel 映射工具运行中: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
