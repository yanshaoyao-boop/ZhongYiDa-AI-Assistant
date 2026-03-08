import json
import urllib.request
import urllib.parse
from datetime import datetime

def get_realtime_exchange_rate(pair="USDCNH=X"):
    """
    Get real-time exchange rate using a reliable REST API.
    """
    try:
        # Use a more stable endpoint for demo/free access
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
            rate = data['rates'].get('CNY', 0) # Close enough for CNH in general context
            return f"实时汇率参考: 1 USD ≈ {rate:.4f} CNY/CNH"
    except Exception as e:
        return f"无法获取实时汇率 ({str(e)})"

from bs4 import BeautifulSoup
import traceback

def get_realtime_news(query, max_results=5):
    """
    Get news using Bing Search HTML parsing (fallback for when duckduckgo fails)
    """
    try:
        # First try DDGS
        from ddgs import DDGS
        ddgs = DDGS()
        results = ddgs.text(query + f" {datetime.now().year}", max_results=max_results)
        if results:
            news_text = ""
            for i, r in enumerate(results):
                news_text += f"{i+1}. {r.get('title', '未知标题')}\n摘要：{r.get('body', '无内容')}\n\n"
            return news_text
    except Exception:
        pass

    try:
        # Fallback: Bing Search HTML
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded_query}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})
        html = urllib.request.urlopen(req, timeout=10).read()
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
