import pandas as pd

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\价格表\深圳-明日之星-美线VIP同行价格表-执行时间2026.1.27.xlsx'
excel = pd.ExcelFile(file_path)
for sheet in excel.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet, header=None)
    for row_idx, row in df.iterrows():
        for col_idx, val in enumerate(row):
            if "PHX5" in str(val).upper():
                print(f"Found in sheet: {sheet}, row: {row_idx}, col: {col_idx}, value: {val}")
