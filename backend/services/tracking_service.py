import httpx
from bs4 import BeautifulSoup
import re
import asyncio

TRACKING_URL = "http://mrzx.rtb56.com/track_query.aspx"

async def fetch_tracking_info(track_number: str) -> dict:
    """
    爬取 mrzx.rtb56.com 的单号轨迹
    返回一个包含轨迹列表或错误信息的字典
    """
    # 使用独立的 client ，因为这个站点可能是 http
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. 发送 GET 请求，获取验证凭据 __VIEWSTATE 和 __EVENTVALIDATION
            response = await client.get(TRACKING_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if response.status_code != 200:
                return {"status": "error", "message": f"无法访问查询网站，状态码: {response.status_code}"}
            
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            
            viewstate_input = soup.find("input", {"id": "__VIEWSTATE"})
            eventvalidation_input = soup.find("input", {"id": "__EVENTVALIDATION"})
            viewstategenerator_input = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
            
            if not viewstate_input or not eventvalidation_input:
                return {"status": "error", "message": "无法从查询页面解析必要的验证凭据。"}
                
            viewstate = viewstate_input.get("value", "")
            eventvalidation = eventvalidation_input.get("value", "")
            viewstategenerator = viewstategenerator_input.get("value", "") if viewstategenerator_input else ""

            # 2. 构造 POST 请求提单
            payload = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "track_number": track_number,
                "btnSearch": "查 询"
            }
            
            # 使用获取到的 cookies 继续发 POST
            response_post = await client.post(
                TRACKING_URL,
                data=payload,
                cookies=response.cookies,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": TRACKING_URL
                }
            )
            
            if response_post.status_code != 200:
                return {"status": "error", "message": f"提交查询失败，状态码: {response_post.status_code}"}
                
            result_html = response_post.text
            result_soup = BeautifulSoup(result_html, "html.parser")
            
            # 由于不知道对方具体的 DOM 结构，先尝试找带有 tracking 字样的或 table
            # 首先检查是否有错误提示
            error_hint = result_soup.find("div", {"class": "empty-cont-hint"})
            if error_hint and "未查询到" in error_hint.text:
                return {"status": "success", "data": "暂未查询到该单号的轨迹信息，请确认单号是否正确。"}
            
            # 假设轨迹是个 table 或者 ul，我们需要抽取所有的文字。由于速递管家的常见结构是 class="track-list" 或者类似的表格
            track_table = result_soup.find("table", {"class": "table"}) or result_soup.find("div", {"class": "track-list"})
            
            if track_table:
                # 简单清洗 HTML 转换为纯文本
                import re
                text_content = re.sub(r'\s+', ' ', track_table.get_text()).strip()
                return {"status": "success", "data": text_content, "raw_html": str(track_table)}
            else:
                # 没有找到典型的表格结构，返回整体 body 中间的关键部分或给大模型清洗
                body_content = result_soup.find("body")
                if body_content:
                    # 摘取内容较长或包含日期的块
                    text = body_content.get_text(separator="\n").strip()
                    # 做一些简单的压缩
                    lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 5]
                    return {"status": "success", "data": "提取到的页面信息：\n" + "\n".join(lines[:30])} # 截取前 30 行防爆炸
                
                return {"status": "success", "data": "页面成功返回，但未找到预设的轨迹结构，请人工核查页面。"}
                
        except Exception as e:
            return {"status": "error", "message": f"爬虫解析异常: {str(e)}"}

# 用于本地直接运行测试
if __name__ == "__main__":
    result = asyncio.run(fetch_tracking_info("FBA1967S283C"))
    print(result)
