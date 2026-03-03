import os
import sys
import asyncio
import json
import uuid

# 添加后端路径以导入模块
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.doc_parser import parse_document
from services.llm_client import analyze_coach_case

COACH_CASES_FILE = r'd:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\backend\data\coach_cases.json'
CASES_DIR = r'd:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\教练案例'

async def process_file(filename):
    file_path = os.path.join(CASES_DIR, filename)
    print(f">> Processing: {filename}...")
    
    text = await parse_document(file_path)
    if not text.strip():
        return []
        
    import re
    case_blocks = re.split(r'(?=案例\s*\d+\s*[:：]|\={5,})', text)
    case_texts = [b.strip() for b in case_blocks if len(b.strip()) > 50]
    
    # 获取已有的 source 列表，避免过度重复
    existing_sources = []
    if os.path.exists(COACH_CASES_FILE):
        with open(COACH_CASES_FILE, "r", encoding="utf-8") as f:
            cases = json.load(f)
            existing_sources = [c.get("source") for c in cases]
    
    # 如果这个文件已经彻底处理过了，跳过（简单判断）
    if filename in existing_sources and "100例" not in filename:
        print(f">> {filename} already processed, skipping.")
        return []

    new_results = []
    # 针对 50例 和 100例 这种大文件，我们额外再刷 10 条
    limit = 10
    count = 0
    for t in case_texts:
        if count >= limit: break
        try:
            print(f"   -- Analyzing case {count+1}/{limit}...")
            case_data = await analyze_coach_case(t)
            case_data["id"] = uuid.uuid4().hex[:8]
            case_data["source"] = filename
            new_results.append(case_data)
            count += 1
        except Exception as e:
            print(f"   !! Error: {e}")
            continue
            
    return new_results

async def main():
    files = [
        "亚马逊美线FBA业务演练案例50例.txt",
        "跨境电商FBA询价聊天记录1.txt",
        "货代业务对练案例100例（1）.txt"
    ]
    
    all_new_cases = []
    for f in files:
        new_cases = await process_file(f)
        all_new_cases.extend(new_cases)
        
    if all_new_cases:
        with open(COACH_CASES_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        
        combined = all_new_cases + existing
        with open(COACH_CASES_FILE, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        print(f">> Done! Added {len(all_new_cases)} new cases.")

if __name__ == "__main__":
    asyncio.run(main())
