import re
import openpyxl

# 锦联表里的仓库组关键词（不含"仓"字，需要单独识别）
JINLIAN_WAREHOUSE_KEYWORDS = [
    "义乌", "深圳", "东莞", "广州", "厦门", "泉州",
    "上海", "宁波", "合肥", "杭州", "中山"
]

# 锦联表里代表"邮编区"的行关键词（这些用来代替仓库代码）
JINLIAN_REGION_PATTERNS = [
    r"美东", r"美中", r"美西",
    r"美东南", r"美东北",
]

# 跳过的 Sheet 黑名单
JINLIAN_BLACKLIST = [
    "目录", "各公司联系人", "船期表", "理赔条款", "偏远邮编",
    "偏仓卡派", "海外仓", "承运规则", "发票模版", "偏远地区",
    "定时达", "反倾销"
]

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

def _is_region_row(text: str) -> bool:
    """判断某个单元格值是否是"美东/美中/美西"这样的区域行标识"""
    for p in JINLIAN_REGION_PATTERNS:
        if re.search(p, text):
            return True
    return False

def _detect_warehouse_groups(header_row: list, ref_row: list, start_col: int):
    """
    识别多仓库组的列范围。
    header_row: 仓库组标题行（如"义乌/上海/宁波/合肥/杭州 | 深圳/东莞/广州 | ..."）
    ref_row: 价格档位行（如"21-99KG | 100KG+ | ..."）
    """
    groups = []
    current_group = None
    for col_idx in range(start_col, min(start_col + 20, len(header_row))):
        h_val = str(header_row[col_idx]).strip() if header_row[col_idx] is not None else ""
        r_val = str(ref_row[col_idx]).strip() if col_idx < len(ref_row) and ref_row[col_idx] is not None else ""

        # 识别新仓库组标题（含有一个或多个锦联仓库关键词）
        if any(kw in h_val for kw in JINLIAN_WAREHOUSE_KEYWORDS) and h_val:
            current_group = {"name": h_val.split("/")[0].strip() + "仓", "start_col": col_idx, "headers": []}
            groups.append(current_group)

        # 识别价格档位（KG+, CBM+...），归入当前仓库组
        if current_group and r_val and ("kg" in r_val.lower() or "cbm" in r_val.lower() or "KG" in r_val):
            current_group["headers"].append((col_idx, r_val))

    return groups

def parse_jinlian_excel(file_path: str) -> list:
    """
    解析锦联系列报价表（美线）。
    结构特点：以"交货仓"/"分区"为锚点，以"美东/美中/美西"为数据行，
    价格按多仓库组横向展开。
    """
    all_quotes = []
    source_name = file_path.split("\\")[-1].split("/")[-1]

    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)

        for sheet_name in wb.sheetnames:
            if not _is_valid_sheet(sheet_name):
                continue

            ws = wb[sheet_name]
            all_rows = [list(row) for row in ws.iter_rows(values_only=True)]

            current_channel = sheet_name
            i = 0

            while i < len(all_rows):
                row = all_rows[i]

                # 识别子渠道标题行（如"美森锦优达快递派（CLX）..."）
                first_val = str(row[0] or row[1] or "").strip()
                for c in row[:4]:
                    if c and len(str(c).strip()) > 5:
                        first_val = str(c).strip()
                        break

                # 检测锚点行：含有"交货仓"或"分区"关键词
                anchor_col = -1
                region_col = -1  # "分区"/"美东"这一列的索引
                for col_idx, val in enumerate(row):
                    s = str(val).strip() if val is not None else ""
                    if "交货仓" in s or "分区" in s:
                        anchor_col = col_idx
                    if "分区" in s or "区域" in s:
                        region_col = col_idx

                if anchor_col == -1:
                    # 未发现锚点，检查是否是渠道标题行
                    non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
                    if (len(non_empty) == 1 and len(non_empty[0]) > 8 and
                            any(kw in non_empty[0] for kw in ["快递派", "卡派", "普船", "快船", "派", "限时达"])):
                        current_channel = non_empty[0].split("下单")[0].strip()
                    i += 1
                    continue

                # ------- 找到锚点行，处理价格块 -------
                # 下一行是价格档位行
                if i + 1 >= len(all_rows):
                    i += 1
                    continue

                price_header_row = all_rows[i + 1]

                # 识别仓库组（从 anchor_col+1 开始扫描）
                warehouse_groups = _detect_warehouse_groups(row, price_header_row, anchor_col + 1)

                if not warehouse_groups:
                    i += 1
                    continue

                # 找时效列
                delivery_time_col = -1
                for col_idx, val in enumerate(row):
                    s = str(val).strip() if val is not None else ""
                    if "时效" in s or "开始计算" in s:
                        delivery_time_col = col_idx
                        break

                # region_col: 数据行里"美东/美中/美西"所在列
                if region_col == -1:
                    region_col = anchor_col + 1  # 默认在锚点右边第一个

                # 从第 i+2 行开始读取数据行
                i += 2
                while i < len(all_rows):
                    data_row = all_rows[i]

                    # 读取区域标识（美东/美中/美西）
                    region_val = ""
                    for check_col in range(max(0, region_col - 1), min(region_col + 3, len(data_row))):
                        v = str(data_row[check_col]).strip() if data_row[check_col] is not None else ""
                        if _is_region_row(v):
                            region_val = v
                            region_col = check_col
                            break

                    # 非区域数据行则结束当前块
                    if not region_val:
                        # 检测是否碰到新的锚点、说明行或完全空行
                        any_val = [c for c in data_row if c is not None]
                        if not any_val:
                            i += 1
                            continue
                        # 遇到中断关键字退出
                        row_text = " ".join(str(c) for c in data_row if c)
                        if any(kw in row_text for kw in ["赔偿", "注意事项", "重货优惠", "下单产品"]):
                            break
                        i += 1
                        continue

                    # 清理区域名（去掉括号内的邮编说明）
                    region_clean = re.sub(r'[（(].*?[）)]', '', region_val).strip()

                    # 对每个仓库组提取价格
                    for group in warehouse_groups:
                        prices = {}
                        has_price = False
                        for col_idx, head in group["headers"]:
                            val = data_row[col_idx] if col_idx < len(data_row) else None
                            fval = _safe_float(val)
                            if fval is not None and fval > 0:
                                prices[head] = fval
                                has_price = True

                        if not has_price:
                            continue

                        delivery_time = ""
                        if delivery_time_col != -1 and delivery_time_col < len(data_row):
                            delivery_time = str(data_row[delivery_time_col] or "").strip()

                        all_quotes.append({
                            "渠道": f"{current_channel}({group['name']})",
                            "目的地区": region_clean,          # 锦联用"目的地区"，而非"仓库代码"
                            "仓库代码": region_clean,          # 兼容搜索逻辑，同时写入仓库代码字段
                            "时效和赔偿约定": "",
                            "价格体系": prices,
                            "起收重量": "",
                            "宣称时效": delivery_time,
                            "附加备注": f"目的地区: {region_val}",
                            "_source": source_name,
                            "_type": "region_based"        # 标记这条数据是"邮编区"类型而非"仓库代码"类型
                        })
                    i += 1

    except Exception as e:
        import traceback
        print(f"Error parse_jinlian_excel {file_path}: {e}")
        traceback.print_exc()

    return all_quotes
