import base64
import importlib.util
import json
import sys
import tempfile
from datetime import datetime
from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response


router = APIRouter(prefix="/tools", tags=["tools"])

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_SOURCE_ROOT = REPO_ROOT / "智能工具源代码"
TOOLS_RUNTIME_ROOT = REPO_ROOT / "backend" / "data" / "tools"

FIST_TOOL_DIR = TOOLS_SOURCE_ROOT / "行政工具" / "客服转单工具（Fist专用）"
FIST_TEMPLATE_PATH = FIST_TOOL_DIR / "templates" / "index.html"
FIST_STATIC_DIR = FIST_TOOL_DIR / "static"
FIST_GENERATED_DIR = FIST_TOOL_DIR / "generated"


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _get_fist_mapper():
    mapper_path = FIST_TOOL_DIR / "excel_mapper.py"
    if not mapper_path.exists():
        raise HTTPException(
            status_code=503,
            detail="客服转单工具核心代码尚未就绪，请先上传资源并配置路径。",
        )
    return _load_module("xiaoyi_fist_excel_mapper", mapper_path)


TOOL_GROUPS = [
    {
        "key": "business",
        "title": "业务工具",
        "tools": [
            {
                "slug": "hepiao",
                "title": "合票工具",
                "summary": "保留原始 UI 的 FBA 合票工具。",
                "runtime_path": "/api/tools/runtime/business/hepiao/",
                "kind": "html_file",
                "source": TOOLS_SOURCE_ROOT / "业务工具" / "合票工具" / "dist" / "index.html",
            },
            {
                "slug": "self-order-form",
                "title": "自助下单表工具",
                "summary": "保留原始 UI 的自助下单表工具。",
                "runtime_path": "/api/tools/runtime/business/self-order-form/",
                "kind": "directory",
                "source": TOOLS_SOURCE_ROOT / "业务工具" / "自助下单表工具" / "fba-tool-pro" / "dist",
            },
            {
                "slug": "reconciliation",
                "title": "自助对账工具（应收）",
                "summary": "保留原始 UI 的自助对账工具。",
                "runtime_path": "/api/tools/runtime/business/reconciliation/",
                "kind": "html_file",
                "source": TOOLS_SOURCE_ROOT / "业务工具" / "自助对账工具（应收）" / "ReconciliationPro" / "dist" / "index.html",
            },
        ],
    },
    {
        "key": "admin",
        "title": "行政工具",
        "tools": [
            {
                "slug": "order-sheet-transform",
                "title": "下单表转换工具（客服专用）",
                "summary": "保留原始 UI 的客服下单表转换工具。",
                "runtime_path": "/api/tools/runtime/admin/order-sheet-transform/",
                "kind": "directory",
                "source": TOOLS_SOURCE_ROOT / "行政工具" / "下单表转换工具（客服专用）" / "excel-transformer" / "dist",
            },
            {
                "slug": "fist-transfer",
                "title": "客服转单工具（Fist专用）",
                "summary": "保留原始 UI 的客服转单工具。",
                "runtime_path": "/api/tools/runtime/admin/fist-transfer/",
                "kind": "html_file",
                "source": FIST_TOOL_DIR / "客服转单工具_Fist专用.html",
            },
        ],
    },
]

TOOL_INDEX = {
    (group["key"], tool["slug"]): tool
    for group in TOOL_GROUPS
    for tool in group["tools"]
}


def _resolve_tool(group: str, slug: str):
    tool = TOOL_INDEX.get((group, slug))
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    return tool


def _safe_join(base_dir: Path, relative_path: str) -> Path:
    candidate = (base_dir / relative_path).resolve()
    base_dir = base_dir.resolve()
    if candidate != base_dir and base_dir not in candidate.parents:
        raise HTTPException(status_code=400, detail="invalid path")
    return candidate


def _file_response(path: Path, media_type: str | None = None):
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="工具或静态资源文件未找到，请检查上传路径。")
    return FileResponse(path, media_type=media_type)


def _render_fist_html() -> HTMLResponse:
    if not FIST_TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Fist 模板文件未找到。")
    html = FIST_TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace('href="/static/styles.css"', 'href="./static/styles.css"')
    html = html.replace('src="/static/app.js"', 'src="./static/app.js"')
    return HTMLResponse(html)


def _render_fist_js() -> Response:
    js_path = FIST_STATIC_DIR / "app.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="Fist JS 资源未找到。")
    js = js_path.read_text(encoding="utf-8")
    js = js.replace('fetch("/api/inspect"', 'fetch("./api/inspect"')
    js = js.replace('fetch("/api/generate"', 'fetch("./api/generate"')
    return Response(content=js, media_type="application/javascript")


def _write_upload(directory: Path, file_name: str, content: str) -> Path:
    safe_name = Path(file_name).name or "upload.xlsx"
    file_path = directory / safe_name
    if "," in content:
        content = content.split(",", 1)[1]
    file_path.write_bytes(base64.b64decode(content))
    return file_path


@router.get("/")
def list_tools():
    return {
        "groups": [
            {
                "key": group["key"],
                "title": group["title"],
                "tools": [
                    {
                        "slug": tool["slug"],
                        "title": tool["title"],
                        "summary": tool["summary"],
                        "runtime_path": tool["runtime_path"],
                    }
                    for tool in group["tools"]
                ],
            }
            for group in TOOL_GROUPS
        ]
    }


@router.get("/runtime/{group}/{slug}/")
def serve_tool_root(group: str, slug: str):
    tool = _resolve_tool(group, slug)

    if tool["kind"] == "html_file":
        return _file_response(tool["source"], media_type="text/html")

    if tool["kind"] == "directory":
        return _file_response(tool["source"] / "index.html", media_type="text/html")

    if tool["kind"] == "fist_tool":
        return _render_fist_html()

    raise HTTPException(status_code=404, detail="tool runtime not found")


@router.get("/runtime/{group}/{slug}/{asset_path:path}")
def serve_tool_asset(group: str, slug: str, asset_path: str):
    tool = _resolve_tool(group, slug)

    if tool["kind"] == "directory":
        target_path = _safe_join(tool["source"], asset_path)
        return _file_response(target_path)

    if tool["kind"] == "fist_tool":
        if asset_path == "static/app.js":
            return _render_fist_js()
        if asset_path.startswith("static/"):
            target_path = _safe_join(FIST_STATIC_DIR, asset_path.removeprefix("static/"))
            return _file_response(target_path)
        if asset_path.startswith("generated/"):
            target_path = _safe_join(FIST_GENERATED_DIR, asset_path.removeprefix("generated/"))
            return _file_response(target_path)
        raise HTTPException(status_code=404, detail="asset not found")

    raise HTTPException(status_code=404, detail="asset not found")


@router.post("/runtime/admin/fist-transfer/api/inspect")
def inspect_fist_files(payload: dict):
    try:
        mapper = _get_fist_mapper()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            a_path = _write_upload(tmp_path, payload["aFileName"], payload["aFileContent"])
            b_path = _write_upload(tmp_path, payload["bFileName"], payload["bFileContent"])
            headers = mapper.load_a_headers(a_path)
            targets = mapper.extract_template_targets(b_path)
        return {"headers": headers, "targets": targets}
    except Exception as exc:
        return JSONResponse(
            {"error": f"解析文件失败: {exc}"},
            status_code=HTTPStatus.BAD_REQUEST,
        )


@router.post("/runtime/admin/fist-transfer/api/generate")
def generate_fist_files(payload: dict):
    try:
        mapper = _get_fist_mapper()
        mappings = payload.get("mappings", [])
        if len(mappings) > 30:
            raise ValueError("最多只允许 30 条映射")

        run_name = datetime.now().strftime("run-%Y%m%d-%H%M%S")
        run_dir = FIST_GENERATED_DIR / run_name
        upload_dir = run_dir / "_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        a_path = _write_upload(upload_dir, payload["aFileName"], payload["aFileContent"])
        b_path = _write_upload(upload_dir, payload["bFileName"], payload["bFileContent"])
        output_dir = run_dir / "excel"

        result = mapper.generate_workbooks(
            a_path=a_path,
            b_path=b_path,
            mappings=mappings,
            output_dir=output_dir,
        )
        zip_path = Path(result["zip_path"])

        return {
            "count": result["count"],
            "files": [Path(file_path).name for file_path in result["files"]],
            "outputDir": str(output_dir),
            "zipUrl": f"/api/tools/runtime/admin/fist-transfer/generated/{zip_path.relative_to(FIST_GENERATED_DIR).as_posix()}",
            "fixedMappings": [
                {"source": "收货件数", "target": "B16"},
                {"source": "额外服务", "target": "F6"},
                {"source": "客户单号+U000001-+收货件数", "target": "A18"},
            ],
        }
    except Exception as exc:
        return JSONResponse(
            {"error": f"生成失败: {exc}"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
