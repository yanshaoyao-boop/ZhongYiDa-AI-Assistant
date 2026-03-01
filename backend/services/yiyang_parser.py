import openpyxl
import re

def _safe_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None

def parse_yiyang_excel(file_path: str) -> list:
    """
    专门解析亿阳国际的报价表。
    主要提取两个最核心也是最标准的部分：
    1. 卡派价格汇总表 (包含所有美线海卡的Flat Data结构)
    2. YY海派渠道汇总 (按美东/美中/美西分区的海派)
    """
    all_quotes = []
    source_name = file_path.split("\\")[-1].split("/")[-1]

    wb = None
    sheets_data = {}
    try:
        if file_path.lower().endswith('.xls'):
            import xlrd
            wb = xlrd.open_workbook(file_path)
            for sheet_name in wb.sheet_names():
                sheet = wb.sheet_by_name(sheet_name)
                rows = []
                for rx in range(sheet.nrows):
                    rows.append(sheet.row_values(rx))
                sheets_data[sheet_name] = rows
            # xlrd doesn't need explicit close if no file locking, but release resources
            wb.release_resources()
            wb = None # so finally block doesn't crash on xlrd
        else:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                sheets_data[sheet_name] = [list(r) for r in sheet.iter_rows(values_only=True)]

        # ... (rest of the logic)
        # 1. 降维打击：直接提取《卡派价格汇总表》
        if "卡派价格汇总表" in sheets_data:
            all_rows = sheets_data["卡派价格汇总表"]
            for i, row in enumerate(all_rows):
                if i == 0: 
                    continue # 跳过表头
                
                channel = str(row[0]).strip() if row[0] is not None else ""
                wh = str(row[1]).strip().upper() if len(row) > 1 and row[1] is not None else ""
                
                if not channel or not wh or "对应渠道" in channel:
                    continue
                
                time_val = str(row[8]).strip() if len(row) > 8 and row[8] is not None else ""
                
                # 提取义乌仓价格(列 2,3,4)
                prices_yw = {}
                v1 = _safe_float(row[2]) if len(row) > 2 else None
                v2 = _safe_float(row[3]) if len(row) > 3 else None
                v3 = _safe_float(row[4]) if len(row) > 4 else None
                if v1: prices_yw["12KG+"] = v1
                if v2: prices_yw["51KG+"] = v2
                if v3: prices_yw["按方包税1CBM+"] = v3
                
                if prices_yw:
                    all_quotes.append({
                        "渠道": f"{channel}(义乌仓)",
                        "仓库代码": wh,
                        "时效和赔偿约定": "",
                        "价格体系": prices_yw,
                        "起收重量": "12KG+",
                        "宣称时效": time_val,
                        "附加备注": "",
                        "_source": source_name,
                        "_type": "yiyang_flat"
                    })

                # 提取深圳/广州仓价格(列 5,6,7)
                prices_sg = {}
                v4 = _safe_float(row[5]) if len(row) > 5 else None
                v5 = _safe_float(row[6]) if len(row) > 6 else None
                v6 = _safe_float(row[7]) if len(row) > 7 else None
                if v4: prices_sg["12KG+"] = v4
                if v5: prices_sg["51KG+"] = v5
                if v6: prices_sg["按方包税1CBM+"] = v6
                
                if prices_sg:
                    all_quotes.append({
                        "渠道": f"{channel}(深圳/广州仓)",
                        "仓库代码": wh,
                        "时效和赔偿约定": "",
                        "价格体系": prices_sg,
                        "起收重量": "12KG+",
                        "宣称时效": time_val,
                        "附加备注": "",
                        "_source": source_name,
                        "_type": "yiyang_flat"
                    })

        # 2. 深度扫描：解析所有包含 "渠道汇总" 关键词的 Sheet
        summary_sheets = [name for name in sheets_data.keys() if "渠道汇总" in name]
        for sheet_name in summary_sheets:
            all_rows = sheets_data[sheet_name]
            
            anchor_idx = -1
            for i, r in enumerate(all_rows):
                if any(c and "分区" in str(c) for c in r):
                    anchor_idx = i
                    break
            
            if anchor_idx != -1 and anchor_idx + 1 < len(all_rows):
                header = all_rows[anchor_idx]
                sub_header = all_rows[anchor_idx + 1]
                
                col_channel = -1
                col_region = -1
                col_time = -1
                for j, v in enumerate(header):
                    s = str(v).strip() if v else ""
                    if "下单渠道" in s or "渠道名称" in s: col_channel = j
                    if "分区" in s or "仓库代码" in s: col_region = j
                    if "时效" in s: col_time = j
                
                # 如果没找到这些关键列，跳过
                if col_region == -1: continue

                # 定义价格列组（通常是 义乌/深圳 两种仓）
                # 亿阳表的规律：分区列之后紧跟 3 列为一个仓的价格梯度
                groups = [
                    {"name": "义乌仓", "col_start": col_region + 1, "col_end": col_region + 3},
                    {"name": "深圳/广州/华南仓", "col_start": col_region + 4, "col_end": col_region + 6}
                ]
                
                for g in groups:
                    g["headers"] = []
                    for c in range(g["col_start"], g["col_end"] + 1):
                        if c < len(sub_header) and sub_header[c]:
                            g["headers"].append((c, str(sub_header[c]).strip()))
                
                current_channel = ""
                for i in range(anchor_idx + 2, len(all_rows)):
                    row = all_rows[i]
                    if not any(c for c in row): continue
                    
                    ch_val = str(row[col_channel]).strip() if col_channel != -1 and col_channel < len(row) and row[col_channel] is not None else ""
                    if ch_val: 
                        current_channel = ch_val.split("\n")[0].strip()
                    
                    if not current_channel: continue
                    
                    reg_val = str(row[col_region]).strip() if col_region < len(row) and row[col_region] is not None else ""
                    if not reg_val or "分区" in reg_val: continue
                    
                    # 清理区域名，提取仓库代码
                    raw_codes = [c.strip().upper() for c in re.split(r'[/,，\n ]+', reg_val) if c.strip()]
                    time_val = str(row[col_time]).strip() if col_time != -1 and col_time < len(row) and row[col_time] is not None else ""
                    
                    for g in groups:
                        prices = {}
                        has_price = False
                        for c, h in g["headers"]:
                            v = _safe_float(row[c]) if c < len(row) else None
                            if v and v > 0:
                                prices[h] = v
                                has_price = True
                        
                        if has_price:
                            # 如果是一串仓库代码，则每个人都加一遍
                            for code in raw_codes:
                                all_quotes.append({
                                    "渠道": f"{current_channel}({g['name']})",
                                    "目的地区": reg_val if len(reg_val) < 10 else "多目的地",
                                    "仓库代码": code,
                                    "价格体系": prices,
                                    "宣称时效": time_val.split("\n")[0] if time_val else "",
                                    "附加备注": f"Sheet: {sheet_name}",
                                    "_source": source_name,
                                    "_type": "yiyang_region"
                                })

    except Exception as e:
        import traceback
        print(f"Error parse_yiyang_excel {file_path}: {e}")
        traceback.print_exc()
    finally:
        if wb:
            wb.close()

    return all_quotes
