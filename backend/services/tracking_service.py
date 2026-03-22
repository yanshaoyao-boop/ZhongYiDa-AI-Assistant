import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, async_playwright
from playwright_stealth import Stealth
import re

TRACKING_URL = "http://mrzx.rtb56.com/track_query.aspx"
RESULT_SELECTOR = ".layui-table-body, .order-list, .empty-cont-hint, #labMessage"

# 全局浏览器实例（复用）
_browser = None
_playwright_instance = None
_browser_lock = asyncio.Lock()

async def _get_browser():
    global _browser, _playwright_instance
    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            _playwright_instance = await async_playwright().start()
            _browser = await _playwright_instance.chromium.launch(headless=True)
    return _browser

async def close_browser():
    """应用关闭时调用"""
    global _browser, _playwright_instance
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None


async def wait_for_tracking_results(page, timeout: int = 15000, timeout_error=PlaywrightTimeoutError) -> bool:
    try:
        await page.wait_for_selector(RESULT_SELECTOR, timeout=timeout)
    except timeout_error:
        return False
    return True

async def fetch_tracking_info(track_number: str) -> dict:
    """
    使用 Playwright 模拟真人行为爬取轨迹，绕过简单的验证码拦截。
    """
    browser = await _get_browser()
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 800}
    )
        
    page = await context.new_page()
    # 使用 stealth_async 专门为异步 Playwright 设计的隐藏接口
    await Stealth().apply_stealth_async(page)
    
    try:
        print(f">> 正在打开查询页面: {TRACKING_URL}")
        # 缩短等待时间，加速响应
        await page.goto(TRACKING_URL, wait_until="domcontentloaded", timeout=30000)
        
        # 使用更宽泛的选择器寻找单号输入框
        print(f">> 填充单号: {track_number}")
        # 找到那个有规律的文本域，使用原生 JS 强制赋值（绕过可见性检查）
        textarea = await page.wait_for_selector("textarea, #track_number", timeout=10000, state="attached")
        await textarea.evaluate("(el, val) => el.value = val", track_number)
        
        print(">> 点击查询按钮...")
        # 使用 evaluate 强制点击，防止按钮被遮挡或不可见
        await page.evaluate("document.querySelector('#btnSearch').click()")
        
        # 强制等待一会儿，让数据飞一会儿
        await asyncio.sleep(5)
        
        # 等待结果或验证码 (速递管家通常会弹出一个 layui 的层或者 order-list)
        await wait_for_tracking_results(page)
        
        # 检查验证码 (如果有 layer-content 通常是弹窗拦截)
        if await page.is_visible("#divVerify") or await page.is_visible(".layui-layer-content"):
            # 如果有具体的错误文本，抓下来
            err_msg = await page.get_by_text("验证码").is_visible()
            if err_msg:
                return {"status": "error", "message": "被验证码拦截了。建议由于单号敏感建议您先在网页端查核。"}
            return {"status": "error", "message": "被系统安全机制拦截。"}

        # 深度爬取：layui 表格提取 (这种系统常用的框架)
        layui_tables = await page.query_selector_all(".layui-table")
        track_data = []
        for table in layui_tables:
            rows = await table.query_selector_all("tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                row_data = [re.sub(r'\s+', ' ', (await c.inner_text()).strip()) for c in cells]
                if row_data:
                    track_data.append(" | ".join(row_data))
        
        if track_data:
            return {"status": "success", "data": "\n".join(track_data)}

        # 提取数据：传统 order-list
        content_element = await page.query_selector(".order-list")
        if content_element:
            text = await content_element.inner_text()
            clean_text = re.sub(r'\n\s*\n', '\n', text).strip()
            if clean_text and "请输入单号" not in clean_text:
                return {"status": "success", "data": clean_text}

        # 最后的保底，提取整个页面文本
        body_text = await page.inner_text("body")
        if "未查询到" in body_text:
            return {"status": "success", "data": "暂未查询到轨迹信息，请确认单号是否有误。"}
        
        # 如果文字里包含明显的物流关键词和日期，尝试返回
        if "状态" in body_text and re.search(r'\d{4}-\d{2}-\d{2}', body_text):
            return {"status": "success", "data": "查到了部分轨迹，但格式不规整，建议您核实单号。"}
            
        return {"status": "error", "message": "未能识别查询结果展示区域。"}

    except Exception as e:
        return {"status": "error", "message": f"自动化链路异常: {str(e)}"}
    finally:
        await context.close()

if __name__ == "__main__":
    res = asyncio.run(fetch_tracking_info("FBA1967S283C"))
    print(res)
