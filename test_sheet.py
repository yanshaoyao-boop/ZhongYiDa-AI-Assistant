import pandas as pd
import json

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\价格表\深圳-明日之星-美线VIP同行价格表-执行时间2026.1.27.xlsx'
try:
    df = pd.read_excel(file_path, sheet_name='华南明星达14T卡派', nrows=20)
    output = df.fillna("").to_dict(orient="records")
    with open('inspect_sheet.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
except Exception as e:
    print("Error:", e)
