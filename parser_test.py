import pandas as pd
import json
import re

file_path = r'd:\Antigravity-work\Projects\Dev-Forge\仲易达智能助手\价格表\深圳-明日之星-美线VIP同行价格表-执行时间2026.1.27.xlsx'

blacklist = ["目录", "价格查询表", "船期", "赔偿说明", "明细归类", "偏远", "无服务", "美国亚马逊仓库", "发票模版", "全渠道"]

def is_valid_sheet(name):
    for b in blacklist:
        if b in name:
            return False
    return True

try:
    excel = pd.ExcelFile(file_path)
    all_quotes = []

    for sheet in excel.sheet_names:
        if not is_valid_sheet(sheet):
            continue
            
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        
        i = 0
        while i < len(df):
            rowval = df.iloc[i].fillna("").values
            col1_text = str(rowval[1]).strip() if len(rowval) > 1 else ""
            
            if "仓库代码" in col1_text:
                block_type = ""
                for val in rowval:
                    if "赔偿" in str(val) or "时效" in str(val) or "开始计算" in str(val):
                        block_type += str(val) + " "
                        
                if i + 1 < len(df):
                    row2 = df.iloc[i+1].fillna("").values
                    price_headers = []
                    # Column 2,3,4 usually prices. Look up to column 10 to be safe.
                    for col_idx in range(2, min(10, len(row2))):
                        # if the next cell is "起收重量", we've passed prices
                        if str(rowval[col_idx]).strip() == "起收重量":
                            break
                        if str(row2[col_idx]).strip():
                            price_headers.append((col_idx, str(row2[col_idx]).strip()))
                            
                    i += 2
                    while i < len(df):
                        data_row = df.iloc[i].fillna("").values
                        wh_codes = str(data_row[1]).strip() if len(data_row) > 1 else ""
                        
                        # Stop conditions for block
                        if "赔偿" in wh_codes or "查验" in wh_codes or "备注" in wh_codes or "延误" in wh_codes:
                            break
                            
                        # If row doesn't have prices or codes
                        has_price = False
                        prices = {}
                        for col_idx, head in price_headers:
                            if col_idx < len(data_row):
                                val = data_row[col_idx]
                                if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace(".", "", 1).isdigit()):
                                    prices[head] = float(val) if isinstance(val, str) and val.replace(".", "", 1).isdigit() else val
                                    has_price = True
                        
                        if not has_price or not wh_codes:
                            if "代码" in wh_codes: # possibly next block
                                i -= 1
                                break
                            i += 1
                            continue

                        # Determine columns for min_weight, delivery_time, notes based on rowval
                        min_weight_col, delivery_time_col, notes_col = -1, -1, -1
                        for idx, v in enumerate(rowval):
                            if "起收重量" in str(v): min_weight_col = idx
                            if "时效" in str(v) or "开始计算" in str(v): delivery_time_col = idx
                            if "备注" in str(v): notes_col = idx
                        
                        min_weight = str(data_row[min_weight_col]).strip() if min_weight_col != -1 and min_weight_col < len(data_row) else ""
                        delivery_time = str(data_row[delivery_time_col]).strip() if delivery_time_col != -1 and delivery_time_col < len(data_row) else ""
                        notes = str(data_row[notes_col]).strip() if notes_col != -1 and notes_col < len(data_row) else ""

                        # split warehouse codes
                        # Sometimes commas or newlines are used instead of /
                        wh_codes_split = re.split(r'[/,，\n ]+', wh_codes)
                        for wh in wh_codes_split:
                            wh = wh.strip().upper()
                            if not wh or len(wh) < 3: continue
                            all_quotes.append({
                                "channel": sheet,
                                "warehouse": wh,
                                "block_type": block_type.strip(),
                                "prices": prices,
                                "min_weight": min_weight,
                                "delivery_time": delivery_time,
                                "notes": notes
                            })
                        i += 1
                    continue
            i += 1
            
    print(f"Total quotes parsed: {len(all_quotes)}")
    
    # Save a sample to check structure
    with open('parsed_quotes.json', 'w', encoding='utf-8') as f:
        json.dump(all_quotes, f, ensure_ascii=False, indent=2)

except Exception as e:
    import traceback
    traceback.print_exc()
