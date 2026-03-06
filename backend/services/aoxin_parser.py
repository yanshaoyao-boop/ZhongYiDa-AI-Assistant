import openpyxl
import os
import re

def parse_aoxin_excel(file_path: str) -> list:
    """
    专门为“澳鑫”设计的报价解析补丁。
    特点：
    1. 识别澳大利亚各子Sheet（私人地址、电商卡派等）
    2. 提取运费和派送费
    3. 完善仓库代码识别逻辑（处理合并列或多处代码）
    """
    all_quotes = []
    wb = None
    source_name = os.path.basename(file_path)

    try:
        # 强制 data_only=True 获取计算后的数值
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        for sheet_name in wb.sheetnames:
            # 过滤非报价Sheet
            if any(kw in sheet_name for kw in ["目录", "服务", "赔付", "公告", "须知", "地址", "分区", "交接单", "标准", "发票", "模板"]):
                continue

            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows: continue

            # 寻找表头行 (通常是 L1)
            header_row_idx = -1
            for idx, row in enumerate(rows[:10]):
                row_str = " ".join([str(c) for c in row if c is not None])
                if "目的港" in row_str and any(kw in row_str for kw in ["运费", "CBM", "KG", "代码"]):
                    header_row_idx = idx
                    break
            
            if header_row_idx == -1: continue

            headers = rows[header_row_idx]
            # 确定关键列索引
            dest_col = 0 # 目的港
            wh_code_cols = [] # 可能包含仓库代码或交货代码的列
            price_cols = [] # 各种阶梯价格
            delivery_fee_col = -1 # 派送费
            time_col = -1 # 时效
            
            for col_idx, h in enumerate(headers):
                h_str = str(h).strip() if h else ""
                if not h_str and col_idx < 5:
                    # 空白标题列也可能是存放代码的列（合并单元格残留）
                    wh_code_cols.append(col_idx)
                if any(kw in h_str for kw in ["代码", "邮编", "区域", "站点"]):
                    wh_code_cols.append(col_idx)
                if any(kw in h_str for kw in ["1CBM", "3CBM", "5CBM", "10CBM", "20CBM", "运费", "KG"]):
                    price_cols.append((col_idx, h_str))
                if "派送费" in h_str:
                    delivery_fee_col = col_idx
                if any(kw in h_str for kw in ["预计时效", "实效", "船期"]):
                    time_col = col_idx

            # 提取备注
            notes = ""
            for row in rows[header_row_idx:]:
                first_val = str(row[0]).strip() if row[0] is not None else ""
                if any(kw in first_val for kw in ["计费标准", "偏远", "注意", "说明", "包装", "规定", "备注"]):
                    row_content = " | ".join([str(c).strip() for c in row if c is not None])
                    notes += row_content + "; "

            # 提取数据行
            # 这里的逻辑是：只要有价格，且第一列或第二列有内容，就尝试解析
            curr_dest = ""
            for r_idx in range(header_row_idx + 1, len(rows)):
                row = rows[r_idx]
                
                # 检查是否进入了底部的备注区
                first_cell = str(row[0]).strip() if row[0] is not None else ""
                if any(kw in first_cell for kw in ["计费标准", "偏远", "注意", "包装"]):
                    break
                
                # 尝试提取价格
                prices = {}
                for c_idx, h_name in price_cols:
                    val = row[c_idx] if c_idx < len(row) else None
                    try:
                        fval = float(val) if val is not None else None
                        if fval is not None and fval > 0:
                            prices[h_name] = fval
                    except: pass
                
                # 如果这行没价格，也没目的港，基本是垃圾行
                if not prices and not row[0]:
                    continue

                dest = str(row[dest_col]).strip() if row[dest_col] else curr_dest
                if dest: curr_dest = dest
                
                # 汇总这一行所有的代码类片段
                raw_codes = []
                for c_idx in wh_code_cols:
                    if c_idx < len(row) and row[c_idx]:
                        raw_codes.append(str(row[c_idx]).strip())
                
                combined_code_str = "/".join(raw_codes)
                if not combined_code_str and not prices: continue

                # 拆分代码
                # 澳鑫的代码格式：BWU1/BWU2 或 AU2（邮编2000-2999）
                parts = re.split(r'[/,，\s\n]+', combined_code_str)
                cleaned_whs = []
                for p in parts:
                    p = p.strip()
                    # 剥离括号说明
                    p = re.sub(r'[\(（].*?[\)）]', '', p).strip()
                    if p: cleaned_whs.append(p)
                
                if not cleaned_whs: cleaned_whs = ["N/A"]

                delivery_fee = str(row[delivery_fee_col]).strip() if delivery_fee_col != -1 and delivery_fee_col < len(row) and row[delivery_fee_col] else ""
                time = str(row[time_col]).strip() if time_col != -1 and time_col < len(row) and row[time_col] else ""

                for wh in cleaned_whs:
                    all_quotes.append({
                        "渠道": f"澳鑫-{sheet_name}",
                        "目的地区": dest,
                        "仓库代码": wh,
                        "价格体系": prices if prices else "见详情",
                        "派送费": delivery_fee,
                        "宣称时效": time,
                        "附加备注": notes.strip(),
                        "_source": source_name
                    })

    except Exception as e:
        print(f"Error parse_aoxin_excel: {e}")
    finally:
        if wb: wb.close()

    return all_quotes
