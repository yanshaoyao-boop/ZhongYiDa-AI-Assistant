import pandas as pd
import re

def parse_complex_excel(file_path: str) -> list:
    """解析复杂的代理商分块报价表"""
    blacklist = ["目录", "价格查询表", "船期", "赔偿说明", "明细归类", "偏远", "无服务", "美国亚马逊仓库", "发票模版", "全渠道"]

    def is_valid_sheet(name):
        for b in blacklist:
            if b in name:
                return False
        return True

    all_quotes = []
    try:
        excel = pd.ExcelFile(file_path)

        for sheet in excel.sheet_names:
            if not is_valid_sheet(sheet):
                continue
                
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)
            
            i = 0
            while i < len(df):
                rowval = df.iloc[i].fillna("").values
                
                # Find the column containing '仓库代码'
                wh_col_idx = -1
                for idx, v in enumerate(rowval):
                    if "仓库代码" in str(v).strip() or "仓库名称" in str(v).strip():
                        wh_col_idx = idx
                        break
                
                if wh_col_idx != -1:
                    block_type = ""
                    for val in rowval:
                        if "赔偿" in str(val) or "时效" in str(val) or "开始计算" in str(val):
                            block_type += str(val) + " "
                            
                    if i + 1 < len(df):
                        row2 = df.iloc[i+1].fillna("").values
                        price_headers = []
                        # Scan next row(s) for price headers (like '12KG+', '50KG+')
                        # We start scanning after the warehouse column to be safe
                        for col_idx in range(wh_col_idx + 1, min(14, len(row2))):
                            if str(rowval[col_idx]).strip() == "起收重量":
                                break
                            if str(row2[col_idx]).strip():
                                price_headers.append((col_idx, str(row2[col_idx]).strip()))
                                
                        i += 2
                        while i < len(df):
                            data_row = df.iloc[i].fillna("").values
                            wh_codes = str(data_row[wh_col_idx]).strip() if wh_col_idx < len(data_row) else ""
                            
                            # Handle merged cell empty values by looking left if needed, but usually wh_codes are present
                            
                            if "赔偿" in wh_codes or "查验" in wh_codes or "备注" in wh_codes or "延误" in wh_codes:
                                break
                                
                            has_price = False
                            prices = {}
                            for col_idx, head in price_headers:
                                if col_idx < len(data_row):
                                    val = data_row[col_idx]
                                    if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace(".", "", 1).isdigit()):
                                        prices[head] = float(val) if isinstance(val, str) and val.replace(".", "", 1).isdigit() else val
                                        has_price = True
                            
                            if not has_price or not wh_codes:
                                if "代码" in str(data_row): 
                                    i -= 1
                                    break
                                i += 1
                                continue

                            min_weight_col, delivery_time_col, notes_col = -1, -1, -1
                            for idx, v in enumerate(rowval):
                                if "起收重量" in str(v): min_weight_col = idx
                                if "时效" in str(v) or "开始计算" in str(v): delivery_time_col = idx
                                if "备注" in str(v): notes_col = idx
                            
                            min_weight = str(data_row[min_weight_col]).strip() if min_weight_col != -1 and min_weight_col < len(data_row) else ""
                            delivery_time = str(data_row[delivery_time_col]).strip() if delivery_time_col != -1 and delivery_time_col < len(data_row) else ""
                            notes = str(data_row[notes_col]).strip() if notes_col != -1 and notes_col < len(data_row) else ""

                            import re
                            wh_codes_split = re.split(r'[/,，\n ]+', wh_codes)
                            for wh in wh_codes_split:
                                wh = wh.strip().upper()
                                if not wh or len(wh) < 3: continue
                                all_quotes.append({
                                    "渠道": sheet,
                                    "仓库代码": wh,
                                    "时效和赔偿约定": block_type.strip(),
                                    "价格体系": prices,
                                    "起收重量": min_weight,
                                    "宣称时效": delivery_time,
                                    "附加备注": notes
                                })
                            i += 1
                        continue
                i += 1
                
    except Exception as e:
        print(f"Error parse_complex_excel {file_path}: {e}")
        
    return all_quotes
