import json
import urllib.request
import urllib.parse
from datetime import datetime

async def get_realtime_exchange_rate(pair="USDCNH=X"):
    """
    Get real-time exchange rate using a reliable REST API (Async).
    """
    try:
        from services.llm_client import get_client
        client = get_client()
        # Use a more stable endpoint for demo/free access
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        rate = data['rates'].get('CNY', 0) # Close enough for CNH in general context
        return f"实时汇率参考: 1 USD ≈ {rate:.4f} CNY/CNH"
    except Exception as e:
        return f"无法获取实时汇率 ({str(e)})"

from bs4 import BeautifulSoup
import traceback

async def get_realtime_news(query, max_results=5):
    """
    Get news using Bing Search HTML parsing (Async fallback)
    """
    try:
        # First try DDGS (Async)
        from ddgs import DDGS
        async with DDGS() as ddgs:
            results = await asyncio.to_thread(lambda: list(ddgs.text(query + f" {datetime.now().year}", max_results=max_results)))
            if results:
                news_text = ""
                for i, r in enumerate(results):
                    news_text += f"{i+1}. {r.get('title', '未知标题')}\n摘要：{r.get('body', '无内容')}\n\n"
                return news_text
    except Exception:
        pass

    try:
        # Fallback: Bing Search HTML (Async)
        from services.llm_client import get_client
        client = get_client()
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded_query}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        response = await client.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        snippets = soup.find_all('li', class_='b_algo')
        news_text = ""
        for i, snippet in enumerate(snippets[:max_results]):
            title_el = snippet.find('h2')
            title = title_el.text if title_el else "未知标题"
            
            p_el = snippet.find('p')
            body = p_el.text if p_el else ""
            
            if body:
                news_text += f"{i+1}. {title}\n摘要：{body}\n\n"
                
        if news_text:
            return news_text
        return "当前未检索到相关新闻。"
    except Exception as e:
        return f"搜索网页时遇到错误 ({str(e)})"

if __name__ == "__main__":
    print(get_realtime_exchange_rate())
    print(get_realtime_news("伊朗今天的新闻"))
