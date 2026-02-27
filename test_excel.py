import pandas as pd
import json

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\价格表\深圳-明日之星-美线VIP同行价格表-执行时间2026.1.27.xlsx'
try:
    excel = pd.ExcelFile(file_path)
    output = {"sheet_names": excel.sheet_names, "sheets_head": {}}
    for sheet in excel.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
        output["sheets_head"][sheet] = df.fillna("").to_dict(orient="records")
    with open('test_excel.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
except Exception as e:
    print("Error:", e)
