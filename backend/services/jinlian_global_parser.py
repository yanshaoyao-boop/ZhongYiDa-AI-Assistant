import re
import openpyxl

JINLIAN_WAREHOUSE_KEYWORDS = ["义乌", "深圳", "东莞", "广州", "厦门", "泉州", "上海", "宁波", "合肥", "杭州", "中山"]
JINLIAN_BLACKLIST = ["偏远", "目录", "联系人", "船期", "条款", "收费标准", "规则", "附加费", "查询"]

def _is_valid_sheet(name: str) -> bool:
    for b in JINLIAN_BLACKLIST:
        if b in name:
            return False
    return True

def _safe_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None

def _extract_warehouse_codes(code_str: str) -> list:
    codes = []
    splits = re.split(r'[/,，\n ]+', code_str)
    for wh in splits:
        wh = wh.strip()
        if not wh: 
            continue
        
        # 剥离括号内的附加说明
        wh = re.sub(r'\(.*?\)|（.*?）', '', wh).strip()
        
        # 解析 YYZ1-YYZ9 的连串表示方法
        m = re.match(r'^([A-Z]{3,4})(\d+)-([A-Z]{3,4})(\d+)$', wh.upper())
        if m and m.group(1) == m.group(3):
            prefix = m.group(1)
            try:
                start = int(m.group(2))
                end = int(m.group(4))
                for n in range(start, end + 1):
                    codes.append(f"{prefix}{n}")
                continue
            except:
                pass
        
        wh = wh.upper()
        if re.match(r'^[A-Z]{2,4}\d+[A-Z]?$', wh):
            codes.append(wh)
            
    return codes

def _detect_warehouse_groups(header_row: list, ref_row: list, start_col: int):
    """
    动态侦测表头中的仓库分组及下方的价格档位
    header_row: 类似 ["交货仓", "", "义乌/上海", "", "", "深圳/广州", "", ""]
    ref_row: 类似 ["区域", "仓库代码", "21KG+", "71KG+", "100KG+", "21KG+", "71KG+", "100KG+"]
    """
    groups = []
    current_group = None
    for col_idx in range(start_col, min(start_col + 30, len(header_row))):
        h_val = str(header_row[col_idx]).strip() if col_idx < len(header_row) and header_row[col_idx] is not None else ""
        r_val = str(ref_row[col_idx]).strip() if col_idx < len(ref_row) and ref_row[col_idx] is not None else ""
        
        # 命中仓库关键字（如“义乌/上海”）则开启一个新分组
        if any(kw in h_val for kw in JINLIAN_WAREHOUSE_KEYWORDS) and h_val:
            first_city = h_val.split("/")[0].strip()
            current_group = {
                "name": f"{first_city}仓", 
                "start_col": col_idx, 
                "headers": []
            }
            groups.append(current_group)
            
        # 如果当前属于某个分组，且下方有疑似价格档位（数字或KG/CBM）
        if current_group and r_val:
            if any(char.isdigit() for char in r_val) or "KG" in r_val.upper() or "CBM" in r_val.upper() or "方" in r_val:
                current_group["headers"].append((col_idx, r_val))
                
    return groups

def parse_jinlian_global_excel(file_path: str) -> list:
    """
    专门为锦联的 欧线/加线/英线/墨线 这种一页多产品、有CBM/KG混杂的“巨兽”定制的解析器
    """
    all_quotes = []
    source_name = file_path.split("\\")[-1].split("/")[-1]

    all_quotes = []
    wb = None
    source_name = file_path.split("\\")[-1].split("/")[-1]

    try:
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        # ... (rest of logic)
        for sheet_name in wb.sheetnames:
            if not _is_valid_sheet(sheet_name):
                continue
                
            ws = wb[sheet_name]
            all_rows = [list(row) for row in ws.iter_rows(values_only=True)]
            
            i = 0
            current_product = sheet_name.replace("（新）", "").strip()
            
            while i < len(all_rows):
                row = all_rows[i]
                
                # 寻找产品名称的变更，比如："下单产品名称：JLHP-加拿大直航多伦多-卡派"
                for cell in row:
                    s = str(cell).strip() if cell is not None else ""
                    if "下单产品" in s or "JLHP-" in s or "JLKP-" in s:
                        parts = s.split("：")
                        if len(parts) > 1:
                            s = parts[-1].strip()
                        current_product = s.split("下单")[0].strip()
                        break
                        
                # 寻找核心锚点：交货仓
                anchor_col = -1
                for col_idx, val in enumerate(row):
                    s = str(val).strip() if val is not None else ""
                    if "交货仓" in s or ("义乌" in s and anchor_col == -1):
                        anchor_col = col_idx
                        break
                
                if anchor_col == -1 or i + 1 >= len(all_rows):
                    i += 1
                    continue
                    
                # 锁定接下来的两行为表头进行结构侦测
                header_row = row
                price_header_row = all_rows[i+1]
                
                region_col = -1
                wh_code_col = -1
                
                for col_idx, val in enumerate(price_header_row):
                     s = str(val).strip() if val is not None else ""
                     if "区域" in s or "城市" in s or "国家" in s or "分区" in s:
                         region_col = col_idx
                     if "仓库代码" in s or "邮编" in s:
                         wh_code_col = col_idx
                         
                # 找不到就进行兜底：第一列区域，第二列代码
                if region_col == -1 and wh_code_col == -1:
                     region_col = 1
                     wh_code_col = 2
                     
                warehouse_groups = _detect_warehouse_groups(header_row, price_header_row, anchor_col)
                if not warehouse_groups:
                    i += 1
                    continue
                
                # 找时效列所在位置
                time_col = -1
                for col_idx, val in enumerate(header_row):
                     s = str(val).strip() if val is not None else ""
                     if "时效" in s or "提取" in s:
                         time_col = col_idx
                if time_col == -1:
                    for col_idx, val in enumerate(price_header_row):
                         s = str(val).strip() if val is not None else ""
                         if "时效" in s or "提取" in s or "POD" in s:
                             time_col = col_idx

                # 开始遍历该子表的数据行
                i += 2
                while i < len(all_rows):
                    data_row = all_rows[i]
                    
                    # 遇到全空行或到达下一个副标题则跳出当前子表
                    if not any(c for c in data_row[:6] if c is not None):
                         break
                    
                    row_str = "".join([str(c) for c in data_row if c is not None])
                    if "下单产品" in row_str or "交货仓" in row_str or "附加费" in row_str or "特别说明" in row_str:
                         break
                         
                    # 提取区域与代码
                    region_val = str(data_row[region_col]).strip() if region_col != -1 and region_col < len(data_row) and data_row[region_col] is not None else ""
                    wh_code_val = str(data_row[wh_code_col]).strip() if wh_code_col != -1 and wh_code_col < len(data_row) and data_row[wh_code_col] is not None else ""
                    
                    # 双重兜底
                    if not region_val and not wh_code_val:
                         region_val = str(data_row[1]).strip() if len(data_row)>1 and data_row[1] is not None else ""
                         wh_code_val = str(data_row[2]).strip() if len(data_row)>2 and data_row[2] is not None else ""
                         if not region_val and not wh_code_val:
                             i += 1
                             continue
                             
                    # 清洗不需要的括号内容，比如把 “多伦多(邮编L开头)” 变成 “多伦多”
                    region_clean = re.sub(r'[\(\（].*?[\)\）]', '', region_val).strip()
                    
                    code_list = _extract_warehouse_codes(wh_code_val)
                    if not code_list:
                         code_list = [region_clean]
                         if not code_list[0] and wh_code_val:
                             code_list = [wh_code_val]
                             
                    # 时效
                    time_val = ""
                    if time_col != -1 and time_col < len(data_row) and data_row[time_col]:
                        time_str = str(data_row[time_col]).strip()
                        if "时效" not in time_str: # 如果包含时效可能抓到了表头
                             time_val = time_str.split("\n")[0]
                    
                    # 生成实体记录
                    for group in warehouse_groups:
                        prices = {}
                        for c, h in group["headers"]:
                            v = _safe_float(data_row[c]) if c < len(data_row) else None
                            if v and v > 0:
                                prices[h] = v
                        
                        if prices:
                            for code in code_list:
                                if not code: 
                                    continue
                                all_quotes.append({
                                    "渠道": f"{current_product}({group['name']})",
                                    "目的地区": region_clean,
                                    "仓库代码": code,
                                    "时效和赔偿约定": "",
                                    "价格体系": prices,
                                    "起收重量": "",
                                    "宣称时效": time_val,
                                    "附加备注": f"{region_val} {wh_code_val}".replace("\n", "").strip()[:80],
                                    "_source": source_name,
                                    "_type": "jinlian_global"
                                })
                    i += 1
                    
        # 处理可能的遗留问题
        return all_quotes

    except Exception as e:
        import traceback
        print(f"Error parse_jinlian_global_excel {file_path}: {e}")
        traceback.print_exc()
    finally:
        if wb:
            wb.close()

    return all_quotes
