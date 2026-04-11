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
TOOLS_CONFIG_PATH = REPO_ROOT / "backend" / "config" / "tools_catalog.json"

def _resolve_tools_asset(*parts: str) -> Path:
    source_path = TOOLS_SOURCE_ROOT.joinpath(*parts)
    if source_path.exists():
        return source_path
    return TOOLS_RUNTIME_ROOT.joinpath(*parts)

def _resolve_self_order_form_dist() -> Path:
    for base_dir in (TOOLS_SOURCE_ROOT, TOOLS_RUNTIME_ROOT):
        for candidate in base_dir.rglob("fba-tool-pro"):
            dist_dir = candidate / "dist"
            if (dist_dir / "index.html").exists():
                return dist_dir
    return TOOLS_RUNTIME_ROOT / "missing-self-order-form-dist"


SELF_ORDER_FORM_DIST_DIR = _resolve_self_order_form_dist()


FIST_TOOL_DIR = _resolve_tools_asset("行政工具", "客服转单工具（Fist专用）")
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


def _load_tools_config() -> dict:
    if not TOOLS_CONFIG_PATH.exists():
        raise RuntimeError(f"Tools config file not found: {TOOLS_CONFIG_PATH}")
    try:
        return json.loads(TOOLS_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid tools config JSON: {exc}") from exc


def _resolve_configured_source(source_config: dict | None) -> Path:
    if not isinstance(source_config, dict):
        raise RuntimeError("Each tool source must be an object")

    resolver = source_config.get("resolver")
    if resolver == "asset":
        parts = source_config.get("parts")
        if not isinstance(parts, list) or not all(isinstance(part, str) and part for part in parts):
            raise RuntimeError("asset resolver requires non-empty string array field `parts`")
        return _resolve_tools_asset(*parts)

    if resolver == "self_order_form_dist":
        return SELF_ORDER_FORM_DIST_DIR

    raise RuntimeError(f"Unsupported tool source resolver: {resolver}")


def _build_tool_groups() -> list[dict]:
    raw_config = _load_tools_config()
    raw_groups = raw_config.get("groups")
    if not isinstance(raw_groups, list):
        raise RuntimeError("tools config must include an array field `groups`")

    groups: list[dict] = []
    for group in raw_groups:
        if not isinstance(group, dict):
            raise RuntimeError("Each group must be an object")
        key = group.get("key")
        title = group.get("title")
        raw_tools = group.get("tools")
        if not isinstance(key, str) or not key:
            raise RuntimeError("Group `key` must be a non-empty string")
        if not isinstance(title, str) or not title:
            raise RuntimeError("Group `title` must be a non-empty string")
        if not isinstance(raw_tools, list):
            raise RuntimeError(f"Group `{key}` must include an array field `tools`")

        tools: list[dict] = []
        for tool in raw_tools:
            if not isinstance(tool, dict):
                raise RuntimeError("Each tool must be an object")

            kind = tool.get("kind")
            built_tool = {
                "slug": tool.get("slug"),
                "title": tool.get("title"),
                "summary": tool.get("summary"),
                "runtime_path": tool.get("runtime_path"),
                "kind": kind,
                "version": tool.get("version"),
                "updated_at": tool.get("updated_at"),
                "changelog": tool.get("changelog"),
                "is_new": bool(tool.get("is_new", False)),
            }

            required_fields = ("slug", "title", "summary", "runtime_path", "kind")
            for field in required_fields:
                value = built_tool[field]
                if not isinstance(value, str) or not value:
                    raise RuntimeError(f"Tool field `{field}` must be a non-empty string")

            if kind in {"html_file", "directory"}:
                built_tool["source"] = _resolve_configured_source(tool.get("source"))
            elif kind != "fist_tool":
                raise RuntimeError(f"Unsupported tool kind: {kind}")

            tools.append(built_tool)

        groups.append({"key": key, "title": title, "tools": tools})

    return groups


TOOL_GROUPS = _build_tool_groups()

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
                        "version": tool.get("version"),
                        "updated_at": tool.get("updated_at"),
                        "changelog": tool.get("changelog"),
                        "is_new": tool.get("is_new", False),
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

