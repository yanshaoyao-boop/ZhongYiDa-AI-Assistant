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
                if any(x in filename for x in ["欧", "加", "英", "墨"]):
                    from services.jinlian_global_parser import parse_jinlian_global_excel
                    return parse_jinlian_global_excel(file_path)
                else:
                    from services.jinlian_parser import parse_jinlian_excel
                    return parse_jinlian_excel(file_path)
            elif "亿阳" in filename:
                from services.yiyang_parser import parse_yiyang_excel
                return parse_yiyang_excel(file_path)
            elif "星夜" in filename:
                from services.xingye_parser import parse_xingye_excel
                return parse_xingye_excel(file_path)
            elif "腾信" in filename:
                from services.tengxin_parser import parse_tengxin_excel
                return parse_tengxin_excel(file_path)
            elif "商壹" in filename:
                from services.shangyi_parser import parse_shangyi_excel
                return parse_shangyi_excel(file_path)
            elif "澳鑫" in filename:
                from services.aoxin_parser import parse_aoxin_excel
                return parse_aoxin_excel(file_path)
            elif "商壹" in filename:
                from services.shangyi_parser import parse_shangyi_excel
                return parse_shangyi_excel(file_path)
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

def search_best_quotes(query: str, limit: int = 60) -> List[Dict]:
    """Search for relevant quotes based on warehouse codes or channel names in the query."""
    if not QUOTES_CACHE:
        load_all_quotes()
    
    import re
    wh_pattern = re.compile(r'[A-Z]{3,4}\d+[A-Z]?')
    found_whs = wh_pattern.findall(query.upper())
    
    # 建立仓库到区域的隐式映射
    wh_to_region = {
        "ONT8": "美西", "LGB8": "美西", "LAX9": "美西", "PHX5": "美西", "SBD1": "美西",
        "SMF3": "美西", "LAS1": "美西", "OAK3": "美西", "SCK4": "美西", "FAT1": "美西",
        "GEG1": "美西", "FTW1": "美中", "IND9": "美中", "MDW2": "美中", "MEM1": "美中",
        "MQJ1": "美中", "OKL2": "美中", "TPA2": "美中", "SDF8": "美中", "TEB9": "美东",
        "ABE2": "美东", "PHL7": "美东", "CLT2": "美东", "SAV3": "美东", "BWI2": "美东",
        "EWR4": "美东", "LGA9": "美东"
    }
    
    extra_regions = []
    for wh in found_whs:
        if wh in wh_to_region:
            extra_regions.append(wh_to_region[wh])

    region_map = {"美东": "美东", "美中": "美中", "美西": "美西",
                  "东部": "美东", "中部": "美中", "西部": "美西",
                  "新加坡": "新加坡", "马来西亚": "马来西亚", "马代": "马来西亚", "西马": "西马", "东马": "东马",
                  "泰国": "泰国", "菲律宾": "菲律宾", "越南": "越南", "印尼": "印尼", "澳洲": "澳洲", "澳大利亚": "澳洲"}
    found_regions_from_query = [v for k, v in region_map.items() if k in query]
    all_found_regions = list(set(found_regions_from_query + extra_regions))

    priority_results = []
    other_results = []
    
    # 识别查询中是否指名道姓要某一家
    explicit_agents = []
    for agent in ["锦联", "亿阳", "星夜", "腾信", "明日之星", "商壹", "澳鑫"]:
        if agent in query:
            explicit_agents.append(agent)

    def is_priority(filename: str) -> bool:
        if explicit_agents:
            return any(a in filename for a in explicit_agents)
        return "明日之星" in filename

    def is_duplicate(r: Dict, results_list: List[Dict]) -> bool:
        return any(res["渠道"] == r["渠道"] and res.get("仓库代码") == r.get("仓库代码") and res.get("目的地区") == r.get("目的地区") for res in results_list)

    def passes_geography_filter(r: Dict) -> bool:
        # 如果用户没有限制地理位置，直接放行
        if not found_whs and not all_found_regions:
            return True
        
        wh_code = r.get("仓库代码", "").upper()
        region = r.get("目的地区", "")
        
        # 精确仓库匹配
        if any(wh in wh_code for wh in found_whs):
            return True
        # 区域匹配（锦联等区域报价）
        if any(rg in region for rg in all_found_regions):
            return True
            
        return False

    # 使用集合进行去重，通过 (渠道, 仓库代码, 目的地区) 组合作为唯一键，提速 O(n^2) -> O(n)
    seen_keys = set()
    
    # 遍历所有数据并根据匹配度分级
    for filename, records in QUOTES_CACHE.items():
        is_prio_file = is_priority(filename)
        for r in records:
            if not passes_geography_filter(r):
                continue
            
            # 生成去重唯一键
            unique_key = (r.get("渠道", ""), r.get("仓库代码", ""), r.get("目的地区", ""))
            if unique_key in seen_keys:
                continue
            
            # 只有通过了地理位置过滤，才进行关键词匹配
            search_keywords = ["海派", "海运", "空派", "空运", "美森", "限时达", "普货", "带电", "卡派"]
            found_keywords = [k for k in search_keywords if k in query]
            matches_agent = any(a.lower() in filename.lower() or a.lower() in r.get("渠道", "").lower() for a in explicit_agents)
            matches_keyword = any(k.lower() in r.get("渠道", "").lower() for k in found_keywords)
            
            # 如果是指定仓库查询，默认任何包含该仓库的都是匹配的
            matches_wh = any(wh in r.get("仓库代码", "").upper() for wh in found_whs) if found_whs else False
            
            if matches_wh or matches_agent or matches_keyword or all_found_regions:
                seen_keys.add(unique_key)
                r_copy = r.copy()
                r_copy["_source"] = filename
                if is_prio_file:
                    priority_results.append(r_copy)
                else:
                    other_results.append(r_copy)

    final_results = priority_results + other_results
    return final_results[:limit]

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

