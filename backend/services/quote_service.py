import pandas as pd
import os
import json
from typing import Dict, Any, List

# If you prefer to store flat text/dicts for the LLM
QUOTES_CACHE: Dict[str, List[Dict]] = {}
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quotes")

def init_quote_directory():
    os.makedirs(DATA_DIR, exist_ok=True)

def parse_quote_file(file_path: str) -> List[Dict]:
    """Parse an Excel or CSV quote file into a list of structured dictionaries."""
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    try:
        if ext in [".xlsx", ".xls"]:
            # 文件名路由：锦联系列用专属解析器，其他用通用解析器
            if "锦联" in filename:
                from services.jinlian_parser import parse_jinlian_excel
                return parse_jinlian_excel(file_path)
            elif "亿阳" in filename:
                from services.yiyang_parser import parse_yiyang_excel
                return parse_yiyang_excel(file_path)
            else:
                from services.excel_parser import parse_complex_excel
                return parse_complex_excel(file_path)
        elif ext == ".csv":
            df = pd.read_csv(file_path)
            return df.fillna("").to_dict(orient="records")
        else:
            raise ValueError(f"Unsupported quote format: {ext}")
            
    except Exception as e:
        print(f"Error parsing quote file {file_path}: {e}")
        return []

def load_all_quotes():
    """Load all quote files from the data directory into cache."""
    init_quote_directory()
    QUOTES_CACHE.clear()
    
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.isfile(file_path):
            records = parse_quote_file(file_path)
            if records:
                QUOTES_CACHE[filename] = records
    return list(QUOTES_CACHE.keys())

def search_best_quotes(query: str, limit: int = 15) -> List[Dict]:
    """Search for relevant quotes based on warehouse codes or channel names in the query."""
    if not QUOTES_CACHE:
        load_all_quotes()
    
    import re
    wh_pattern = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
    found_whs = wh_pattern.findall(query.upper())
    
    results = []
    
    # 优先级1：仓库代码精确匹配（美线/加线标准代码，如 ONT8, YYZ1）
    if found_whs:
        for wh in found_whs:
            for filename, records in QUOTES_CACHE.items():
                for r in records:
                    if wh in r.get("仓库代码", "").upper():
                        r_copy = r.copy()
                        r_copy["_source"] = filename
                        results.append(r_copy)
    
    # 优先级2：渠道关键词匹配（普船、快船、卡派、快递派 等）
    keywords = ["14T", "16T", "18T", "20T", "OA", "普船", "快船", "海派", "卡派",
                "快递派", "美转加", "直航", "亚马逊", "限时达", "锦联", "空派", "空运"]
    found_keywords = [k for k in keywords if k.lower() in query.lower()]
    
    if len(results) < limit:
        for filename, records in QUOTES_CACHE.items():
            for r in records:
                if any(k.lower() in r.get("渠道", "").lower() for k in found_keywords):
                    if r not in results:
                        r_copy = r.copy()
                        r_copy["_source"] = filename
                        results.append(r_copy)
            if len(results) >= limit:
                break

    # 优先级3：锦联区域匹配（美东/美中/美西），专门给快递派/空派等锦联产品用
    region_map = {"美东": "美东", "美中": "美中", "美西": "美西",
                  "东部": "美东", "中部": "美中", "西部": "美西"}
    found_regions = [v for k, v in region_map.items() if k in query]
    if found_regions and len(results) < limit:
        for filename, records in QUOTES_CACHE.items():
            for r in records:
                if r.get("_type") == "region_based" and r.get("目的地区") in found_regions:
                    if r not in results:
                        r_copy = r.copy()
                        r_copy["_source"] = filename
                        results.append(r_copy)
            if len(results) >= limit:
                break
    
    return results[:limit]

def get_quote_data_as_string(query: str = None) -> str:
    """Return quote data as formatted structured JSON text for the LLM to read."""
    if not QUOTES_CACHE:
        load_all_quotes()
        
    result = ""
    # If a query is provided, we search for specific relevant records instead of just showing the first 50
    if query:
        relevant_records = search_best_quotes(query)
        if relevant_records:
            result += f"--- 已为您精准锁定与“{query}”最匹配的报价数据 ({len(relevant_records)} 条) ---\n"
            result += "注意：以下价格均为【单价】（元/KG 或 元/CBM），绝非整票货的总价。\n"
            result += json.dumps(relevant_records, ensure_ascii=False, indent=2)
            return result
        else:
            result += "--- 未在最新报价表中找到与您搜索条件直接相关的仓库。以下展示几个常见渠道供参考： ---\n"

    # Default fallback
    for name, records in QUOTES_CACHE.items():
        result += f"--- 报价表预览: {name} (共 {len(records)} 条) ---\n"
        sample = records[:40]
        result += json.dumps(sample, ensure_ascii=False, indent=2)
        if len(records) > 40:
            result += f"\n*... (还有 {len(records) - 40} 条未展示) ...*\n"
        result += "\n\n"
            
    return result


# Initialize on module import
init_quote_directory()
try:
    load_all_quotes()
except Exception:
    pass

