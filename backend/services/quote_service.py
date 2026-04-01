import pandas as pd
import os
import json
import re
import math
from typing import Dict, Any, List

from services.parser_utils import (
    SEARCHABLE_WAREHOUSE_CODE_QUERY_PATTERN,
    extract_searchable_warehouse_codes,
)

# If you prefer to store flat text/dicts for the LLM
QUOTES_CACHE: Dict[str, List[Dict]] = {}
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quotes")
WH_CODE_PATTERN = SEARCHABLE_WAREHOUSE_CODE_QUERY_PATTERN
WEIGHT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:KG|公斤|千克)", re.IGNORECASE)
VOLUME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:CBM|立方)", re.IGNORECASE)
KG_TIER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*KG\+", re.IGNORECASE)
CBM_TIER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*CBM\+", re.IGNORECASE)

CITY_COORDINATES: dict[str, tuple[float, float]] = {
    "义乌": (29.3069, 120.0750),
    "金华": (29.0781, 119.6474),
    "泉州": (24.8741, 118.6757),
    "厦门": (24.4798, 118.0894),
    "深圳": (22.5431, 114.0579),
    "东莞": (23.0207, 113.7518),
    "广州": (23.1291, 113.2644),
    "福州": (26.0745, 119.2965),
    "福清": (25.7202, 119.3789),
    "莆田": (25.4540, 119.0078),
    "宁德": (26.6657, 119.5479),
    "南平": (26.6436, 118.1785),
    "三明": (26.2639, 117.6387),
    "龙岩": (25.0751, 117.0173),
    "漳州": (24.5133, 117.6471),
    "温州": (27.9949, 120.6994),
    "台州": (28.6564, 121.4208),
    "宁波": (29.8683, 121.5440),
    "杭州": (30.2741, 120.1551),
    "上海": (31.2304, 121.4737),
    "苏州": (31.2989, 120.5853),
    "无锡": (31.4912, 120.3119),
    "常州": (31.8112, 119.9741),
    "南京": (32.0603, 118.7969),
    "衢州": (28.9359, 118.8742),
    "上饶": (28.4548, 117.9436),
    "南昌": (28.6829, 115.8582),
    "佛山": (23.0215, 113.1214),
    "惠州": (23.1115, 114.4168),
    "中山": (22.5176, 113.3928),
    "珠海": (22.2710, 113.5767),
    "江门": (22.5787, 113.0815),
    "清远": (23.6817, 113.0560),
    "肇庆": (23.0472, 112.4651),
    "汕头": (23.3541, 116.6819),
    "潮州": (23.6567, 116.6226),
    "揭阳": (23.5498, 116.3728),
    "梅州": (24.2991, 116.1226),
    "汕尾": (22.7862, 115.3753),
}

ORIGIN_CITY_ALIASES = {
    "福永": "深圳",
}

ORIGIN_HUB_CITIES = ("义乌", "金华", "泉州", "厦门", "深圳", "东莞", "广州", "福永")
SUPPORTED_ORIGIN_CITIES = tuple(
    sorted(set(CITY_COORDINATES.keys()) | set(ORIGIN_CITY_ALIASES.keys()), key=len, reverse=True)
)

def init_quote_directory():
    os.makedirs(DATA_DIR, exist_ok=True)

def parse_quote_file(file_path: str) -> List[Dict]:
    """Parse an Excel or CSV quote file into a list of structured dictionaries."""
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    try:
        if ext in [".xlsx", ".xls"]:
            # 文件名路由：锦联系列用专属解析器，其他用通用解析器
            if "锦联" in filename:
                if any(x in filename for x in ["欧", "加", "英", "墨"]):
                    from services.jinlian_global_parser import parse_jinlian_global_excel
                    return parse_jinlian_global_excel(file_path)
                else:
                    from services.jinlian_parser import parse_jinlian_excel
                    return parse_jinlian_excel(file_path)
            elif "亿阳" in filename:
                from services.yiyang_parser import parse_yiyang_excel
                return parse_yiyang_excel(file_path)
            elif "星夜" in filename:
                from services.xingye_parser import parse_xingye_excel
                return parse_xingye_excel(file_path)
            elif "腾信" in filename:
                from services.tengxin_parser import parse_tengxin_excel
                return parse_tengxin_excel(file_path)
            elif "商壹" in filename:
                from services.shangyi_parser import parse_shangyi_excel
                return parse_shangyi_excel(file_path)
            elif "澳鑫" in filename:
                from services.aoxin_parser import parse_aoxin_excel
                return parse_aoxin_excel(file_path)
            elif "天航" in filename:
                from services.tianhang_parser import parse_tianhang_excel
                return parse_tianhang_excel(file_path)
            else:
                from services.excel_parser import parse_complex_excel
                return parse_complex_excel(file_path)
        elif ext == ".csv":
            df = pd.read_csv(file_path)
            return df.fillna("").to_dict(orient="records")
        else:
            raise ValueError(f"Unsupported quote format: {ext}")
            
    except Exception as e:
        print(f"Error parsing quote file {file_path}: {e}")
        return []

def load_all_quotes():
    """Load all quote files from the data directory into cache."""
    init_quote_directory()
    QUOTES_CACHE.clear()
    
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.isfile(file_path):
            records = parse_quote_file(file_path)
            if records:
                QUOTES_CACHE[filename] = records
    return list(QUOTES_CACHE.keys())


def extract_quote_request_details(message: str) -> Dict[str, Any]:
    normalized_message = str(message or "")
    warehouse_codes = list(dict.fromkeys(WH_CODE_PATTERN.findall(normalized_message.upper())))
    weight_match = WEIGHT_PATTERN.search(normalized_message)
    volume_match = VOLUME_PATTERN.search(normalized_message)
    return {
        "warehouse_codes": warehouse_codes,
        "weight_kg": float(weight_match.group(1)) if weight_match else None,
        "volume_cbm": float(volume_match.group(1)) if volume_match else None,
        "origin_city": _extract_origin_city(normalized_message),
    }


def _safe_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _format_price(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def pick_weight_price_tier(price_system: Dict[str, Any], weight_kg: float | None) -> tuple[str | None, float | None]:
    if not isinstance(price_system, dict) or weight_kg is None:
        return None, None

    eligible_tiers: list[tuple[float, str, float]] = []
    for raw_label, raw_price in price_system.items():
        label = str(raw_label or "")
        match = KG_TIER_PATTERN.search(label)
        price = _safe_float(raw_price)
        if not match or price is None:
            continue

        threshold = float(match.group(1))
        if weight_kg >= threshold:
            eligible_tiers.append((threshold, label, price))

    if not eligible_tiers:
        return None, None

    _, best_label, best_price = max(eligible_tiers, key=lambda item: item[0])
    return best_label, best_price


def pick_volume_price_tier(price_system: Dict[str, Any], volume_cbm: float | None) -> tuple[str | None, float | None]:
    if not isinstance(price_system, dict) or volume_cbm is None:
        return None, None

    eligible_tiers: list[tuple[float, str, float]] = []
    for raw_label, raw_price in price_system.items():
        label = str(raw_label or "")
        match = CBM_TIER_PATTERN.search(label)
        price = _safe_float(raw_price)
        if not match or price is None:
            continue

        threshold = float(match.group(1))
        if volume_cbm >= threshold:
            eligible_tiers.append((threshold, label, price))

    if not eligible_tiers:
        return None, None

    _, best_label, best_price = max(eligible_tiers, key=lambda item: item[0])
    return best_label, best_price


def _detect_origin_bucket(channel: str, source: str) -> str:
    reference_text = f"{channel} {source}".lower()
    east_markers = ["华东", "义乌", "泉州", "厦门", "金华", "福州", "福清", "莆田", "宁德", "浙江", "福建", "江苏", "上海"]
    south_markers = ["华南", "深圳", "东莞", "福永", "广州", "中山", "珠海", "佛山", "江门", "广东"]

    if any(marker.lower() in reference_text for marker in east_markers):
        return "华东"
    if any(marker.lower() in reference_text for marker in south_markers):
        return "华南"
    return "其他"


def _extract_origin_city(message: str) -> str | None:
    normalized_message = str(message or "")
    for city in SUPPORTED_ORIGIN_CITIES:
        if city in normalized_message:
            return ORIGIN_CITY_ALIASES.get(city, city)
    return None


def _detect_origin_hub_cities(channel: str, source: str) -> list[str]:
    reference_text = f"{channel} {source}"
    hubs: list[str] = []
    for hub in ORIGIN_HUB_CITIES:
        if hub in reference_text:
            canonical_hub = ORIGIN_CITY_ALIASES.get(hub, hub)
            if canonical_hub not in hubs:
                hubs.append(canonical_hub)
    return hubs


def _format_origin_hub_label(hub_cities: list[str], fallback_bucket: str) -> str:
    if hub_cities:
        return f"{'/'.join(hub_cities)}仓"
    if fallback_bucket and fallback_bucket != "其他":
        return f"{fallback_bucket}仓"
    return "当前命中"


def _calculate_distance_km(origin_city: str | None, target_city: str | None) -> float | None:
    if not origin_city or not target_city:
        return None

    origin_coords = CITY_COORDINATES.get(origin_city)
    target_coords = CITY_COORDINATES.get(target_city)
    if not origin_coords or not target_coords:
        return None

    origin_lat, origin_lng = origin_coords
    target_lat, target_lng = target_coords
    lat1 = math.radians(origin_lat)
    lat2 = math.radians(target_lat)
    delta_lat = math.radians(target_lat - origin_lat)
    delta_lng = math.radians(target_lng - origin_lng)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


def _resolve_nearest_origin_hub(origin_city: str | None, hub_cities: list[str]) -> tuple[str | None, float | None]:
    best_city = None
    best_distance = None
    for hub_city in hub_cities:
        distance = _calculate_distance_km(origin_city, hub_city)
        if distance is None:
            continue
        if best_distance is None or distance < best_distance:
            best_city = hub_city
            best_distance = distance
    return best_city, best_distance


def _collect_weight_tiers(price_system: Dict[str, Any]) -> list[tuple[float, str, float]]:
    tiers: list[tuple[float, str, float]] = []
    for raw_label, raw_price in (price_system or {}).items():
        label = str(raw_label or "")
        match = KG_TIER_PATTERN.search(label)
        price = _safe_float(raw_price)
        if not match or price is None:
            continue
        tiers.append((float(match.group(1)), label, price))
    return sorted(tiers, key=lambda item: item[0])


def _format_weight_tiers(
    price_system: Dict[str, Any],
    highlight_label: str | None,
    separator: str = " | ",
) -> str:
    rendered = []
    for _, label, price in _collect_weight_tiers(price_system):
        text = f"{label} ¥{_format_price(price)}/KG"
        if label == highlight_label:
            text = f"**{text}**"
        rendered.append(text)
    return separator.join(rendered)


def _collect_volume_tiers(price_system: Dict[str, Any]) -> list[tuple[float, str, float]]:
    tiers: list[tuple[float, str, float]] = []
    if not isinstance(price_system, dict):
        return tiers

    for raw_label, raw_price in price_system.items():
        label = str(raw_label or "")
        match = CBM_TIER_PATTERN.search(label)
        price = _safe_float(raw_price)
        if not match or price is None:
            continue
        tiers.append((float(match.group(1)), label, price))
    return sorted(tiers, key=lambda item: item[0])


def _format_full_tier_rows(price_system: Dict[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for _, label, price in _collect_weight_tiers(price_system):
        rows.append((label, f"{_format_price(price)}/KG"))
    for _, label, price in _collect_volume_tiers(price_system):
        rows.append((label, f"{_format_price(price)}/方"))
    return rows


def _has_origin_hint(message: str) -> bool:
    return any(
        keyword in message
        for keyword in ("义乌", "泉州", "厦门", "深圳", "东莞", "福永", "华东", "华南", "华中", "华北")
    )


def _is_mingrizhixing_candidate(item: Dict[str, Any]) -> bool:
    reference_text = f"{item.get('channel', '')} {item.get('source', '')}"
    reference_text_upper = reference_text.upper()
    return "明日之星" in reference_text or "MRZX" in reference_text_upper


def _pick_best_candidate(items: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not items:
        return None
    return min(items, key=lambda item: (item["total_price"], item["unit_price"], item["channel"]))


def _select_display_candidates(
    candidates: List[Dict[str, Any]],
    *,
    has_origin_hint: bool,
    origin_city: str | None,
    limit: int,
) -> List[Dict[str, Any]]:
    # 策略：如果用户指定了起运倾向，优先提取并展示该倾向区域的报价
    target_bucket_preference = None
    if origin_city:
        target_bucket_preference = _detect_origin_bucket(origin_city, "")
    
    # 手动排序权重：起运倾向匹配度 > 价格
    def candidate_priority_score(item: Dict[str, Any]) -> tuple:
        # 是否符合用户明确提到的城市/倾向
        origin_match = 0
        if origin_city and item.get("nearest_origin_hub") == origin_city:
            origin_match = 2
        elif target_bucket_preference and item.get("origin_bucket") == target_bucket_preference:
            origin_match = 1
            
        return (
            -origin_match, # 越高越好
            item["total_price"],
            item["unit_price"],
            item["channel"]
        )

    sorted_candidates = sorted(candidates, key=candidate_priority_score)

    if has_origin_hint or origin_city:
        return sorted_candidates[: max(limit, 1)]

    # 如果没有任何倾向提示，平衡展示华东和华南
    selected: List[Dict[str, Any]] = []
    for bucket in ("华东", "华南"):
        bucket_candidates = [item for item in sorted_candidates if item["origin_bucket"] == bucket]
        if not bucket_candidates:
            continue

        mingrizhixing_candidates = [item for item in bucket_candidates if _is_mingrizhixing_candidate(item)]
        chosen = _pick_best_candidate(mingrizhixing_candidates or bucket_candidates)
        if chosen:
            selected.append(chosen)

    if selected:
        return selected

    return sorted_candidates[: max(limit, 1)]


def _pick_recommended_candidate(
    display_candidates: List[Dict[str, Any]],
    *,
    has_origin_hint: bool,
    origin_city: str | None,
) -> tuple[Dict[str, Any], bool]:
    if not display_candidates:
        return {}, False

    if origin_city:
        best = min(
            display_candidates,
            key=lambda item: (
                item["origin_distance_km"] if item["origin_distance_km"] is not None else float("inf"),
                item["total_price"],
                item["unit_price"],
                item["channel"],
            ),
        )
        return best, _is_mingrizhixing_candidate(best)

    if not has_origin_hint:
        mingrizhixing_candidates = [item for item in display_candidates if _is_mingrizhixing_candidate(item)]
        if mingrizhixing_candidates:
            best = _pick_best_candidate(mingrizhixing_candidates)
            if best:
                return best, True

    best = _pick_best_candidate(display_candidates)
    return (best or display_candidates[0]), False


def _select_full_tier_display_candidates(
    candidates: List[Dict[str, Any]],
    *,
    message: str,
    has_origin_hint: bool,
    origin_city: str | None,
    limit: int,
) -> List[Dict[str, Any]]:
    if not candidates:
        return []

    target_bucket_preference = None
    if origin_city:
        target_bucket_preference = _detect_origin_bucket(origin_city, "")
    elif has_origin_hint:
        inferred_bucket = _detect_origin_bucket(message, "")
        if inferred_bucket != "其他":
            target_bucket_preference = inferred_bucket

    def candidate_priority(item: Dict[str, Any]) -> tuple:
        origin_match = 0
        if origin_city and item.get("nearest_origin_hub") == origin_city:
            origin_match = 2
        elif target_bucket_preference and item.get("origin_bucket") == target_bucket_preference:
            origin_match = 1
        return (
            -origin_match,
            0 if _is_mingrizhixing_candidate(item) else 1,
            item.get("origin_distance_km") if item.get("origin_distance_km") is not None else float("inf"),
            item.get("channel", ""),
        )

    sorted_candidates = sorted(candidates, key=candidate_priority)

    if target_bucket_preference:
        matching_candidates = [item for item in sorted_candidates if item.get("origin_bucket") == target_bucket_preference]
        if matching_candidates:
            return matching_candidates[: max(limit, 1)]

    if has_origin_hint or origin_city:
        return sorted_candidates[: max(limit, 1)]

    selected: list[Dict[str, Any]] = []
    for bucket in ("华东", "华南"):
        bucket_candidates = [item for item in sorted_candidates if item.get("origin_bucket") == bucket]
        if not bucket_candidates:
            continue
        mingrizhixing_candidates = [item for item in bucket_candidates if _is_mingrizhixing_candidate(item)]
        chosen = (mingrizhixing_candidates or bucket_candidates)[0]
        selected.append(chosen)

    if selected:
        return selected

    return sorted_candidates[: max(limit, 1)]


def _build_quote_table_rows(
    candidates: List[Dict[str, Any]],
    has_origin_hint: bool,
    origin_city: str | None,
) -> List[Dict[str, str]]:
    rows: list[dict[str, str]] = []
    if origin_city:
        for item in candidates:
            rows.append(
                {
                    "bucket_label": item["origin_label"],
                    "channel": item["channel"],
                    "transit_time": item["transit_time"] or "待确认",
                    "tier_label": f"**{item['tier_label']}**",
                    "unit_price": f"**¥{_format_price(item['unit_price'])}/KG**",
                    "total_price": f"**¥{_format_price(item['total_price'])}**",
                    "weight_tiers": _format_weight_tiers(item["price_system"], item["tier_label"], separator="<br>"),
                    "note": item["note"] or "-",
                }
            )
        return rows

    if not has_origin_hint:
        for bucket in ("华东", "华南"):
            bucket_candidates = [item for item in candidates if item["origin_bucket"] == bucket]
            if not bucket_candidates:
                continue
            item = bucket_candidates[0]
            rows.append(
                {
                    "bucket_label": f"{bucket}仓",
                    "channel": item["channel"],
                    "transit_time": item["transit_time"] or "待确认",
                    "tier_label": f"**{item['tier_label']}**",
                    "unit_price": f"**¥{_format_price(item['unit_price'])}/KG**",
                    "total_price": f"**¥{_format_price(item['total_price'])}**",
                    "weight_tiers": _format_weight_tiers(item["price_system"], item["tier_label"], separator="<br>"),
                    "note": item["note"] or "-",
                }
            )
        return rows

    for item in candidates:
        rows.append(
            {
                "bucket_label": item["origin_bucket"] if item["origin_bucket"] != "其他" else "当前命中",
                "channel": item["channel"],
                "transit_time": item["transit_time"] or "待确认",
                "tier_label": f"**{item['tier_label']}**",
                "unit_price": f"**¥{_format_price(item['unit_price'])}/KG**",
                "total_price": f"**¥{_format_price(item['total_price'])}**",
                "weight_tiers": _format_weight_tiers(item["price_system"], item["tier_label"], separator="<br>"),
                "note": item["note"] or "-",
            }
        )
    return rows


def _extract_remote_level(address_probe_context: str) -> str | None:
    if not address_probe_context:
        return None
    for level in ("UPS极偏远", "超偏远", "极偏远", "偏远"):
        if level in address_probe_context:
            return level
    return None


def _build_old_bird_tip(
    rows: List[Dict[str, str]],
    has_origin_hint: bool,
    weight_kg: float,
    volume_cbm: float | None,
    address_probe_context: str,
) -> str:
    tip_parts: list[str] = []
    remote_level = _extract_remote_level(address_probe_context)

    east_row = next((row for row in rows if row["bucket_label"] == "华东仓"), None)
    south_row = next((row for row in rows if row["bucket_label"] == "华南仓"), None)
    if not has_origin_hint and east_row and south_row:
        east_price = _safe_float(east_row["unit_price"].replace("**", "").replace("¥", "").replace("/KG", ""))
        south_price = _safe_float(south_row["unit_price"].replace("**", "").replace("¥", "").replace("/KG", ""))
        if east_price is not None and south_price is not None and south_price > east_price:
            spread = south_price - east_price
            spread_total = spread * weight_kg
            tip_parts.append(
                f"这票如果能锁到华东起运，比华南每KG便宜 ¥{_format_price(spread)}，"
                f"按 {_format_price(weight_kg)}KG 算差价约 ¥{_format_price(spread_total)}，这是眼下最直接的利润空间。"
            )

    if remote_level:
        tip_parts.append(f"地址这边已经带 {remote_level}，对客时别把偏远等级说轻，不然附加费很容易漏收。")

    if volume_cbm is None:
        tip_parts.append("你这票还没锁箱规和CBM，现阶段只能按实重先报；如果是泡货，体积重一上来，前面的利润会被吃得很快。")

    sensitive_note = next((row["note"] for row in rows if "普货" in row["note"]), "")
    if sensitive_note:
        tip_parts.append("当前命中渠道备注偏向普货口径，如果货里带电、敏感品或超长件，记得先复核渠道属性，不然容易报低。")

    if not tip_parts:
        tip_parts.append("这票先按当前命中阶梯拿去试探客户没问题，但正式拍板前还是把箱规、品类和起运仓锁死，别让后面反算把利润吃回去。")

    return "老鸟提示：" + " ".join(tip_parts[:2])


def _extract_record_warehouse_codes(record: Dict[str, Any]) -> list[str]:
    return extract_searchable_warehouse_codes(record.get("仓库代码", ""))


def _record_matches_requested_warehouses(record: Dict[str, Any], warehouse_codes: list[str]) -> bool:
    if not warehouse_codes:
        return False
    requested_codes = {code.upper() for code in warehouse_codes}
    return any(code in requested_codes for code in _extract_record_warehouse_codes(record))


def _build_reference_only_quote_response(
    warehouse_codes: list[str],
    weight_kg: float,
    candidates: List[Dict[str, Any]],
    *,
    address_probe_context: str,
    limit: int,
) -> str:
    warehouse_label = "、".join(warehouse_codes)
    reference_candidates = sorted(
        candidates,
        key=lambda item: (item["total_price"], item["unit_price"], item["channel"]),
    )[: max(limit, 1)]

    lines = [
        f"结论：当前报价表未收录 **{warehouse_label}** 的精确仓库报价，不能直接按仓库价秒报。",
        "",
        "同区域参考：",
        "| 参考类型 | 渠道 | 时效 | 对应阶梯 | 单价 | 预估总价 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in reference_candidates:
        region_label = str(item.get("destination_region") or "同区域参考").strip() or "同区域参考"
        lines.append(
            f"| {region_label} | {item['channel']} | {item['transit_time'] or '待确认'} | "
            f"**{item['tier_label']}** | **¥{_format_price(item['unit_price'])}/KG** | "
            f"**¥{_format_price(item['total_price'])}** | {item['note'] or '-'} |"
        )

    if address_probe_context:
        lines.extend(["", "地址提醒：", address_probe_context])

    lines.extend(
        [
            "",
            "补充提醒：",
            f"- 当前只命中了 **{warehouse_label}** 所在区域的参考价，不是这个仓库的精确仓价。",
            f"- 目前这票按 **{_format_price(weight_kg)}KG** 先做区域参考，正式对客前请找对应渠道确认是否直达、是否加收偏远或转运附加费。",
            "- 如果你愿意，我可以继续把同区域可参考渠道按时效和价格帮你排一版。",
        ]
    )

    sources: list[str] = []
    for item in reference_candidates:
        source = item["source"]
        if source and source not in sources:
            sources.append(source)
    if sources:
        lines.extend(["", f"报价来源：{'、'.join(sources)}"])

    return "\n".join(lines).strip()


def _build_full_tier_quote_response(
    message: str,
    warehouse_codes: list[str],
    origin_city: str | None,
    quote_records: List[Dict] | None,
    *,
    address_probe_context: str,
    limit: int,
) -> str:
    candidates: list[dict[str, Any]] = []
    for record in quote_records or []:
        price_system = record.get("价格体系") or {}
        full_tier_rows = _format_full_tier_rows(price_system)
        if not full_tier_rows:
            continue

        channel = str(record.get("渠道", "未知渠道")).strip()
        source = str(record.get("_source", "")).strip()
        origin_bucket = _detect_origin_bucket(channel, source)
        origin_hub_cities = _detect_origin_hub_cities(channel, source)
        nearest_origin_hub, origin_distance_km = _resolve_nearest_origin_hub(origin_city, origin_hub_cities)

        candidates.append(
            {
                "channel": channel,
                "warehouse_code": str(record.get("仓库代码", "")).strip(),
                "transit_time": str(record.get("宣称时效", "")).strip(),
                "note": str(record.get("附加备注", "")).strip(),
                "source": source,
                "origin_bucket": origin_bucket,
                "origin_hub_cities": origin_hub_cities,
                "nearest_origin_hub": nearest_origin_hub,
                "origin_distance_km": origin_distance_km,
                "origin_label": _format_origin_hub_label(origin_hub_cities, origin_bucket),
                "warehouse_exact_match": _record_matches_requested_warehouses(record, warehouse_codes),
                "all_tier_rows": full_tier_rows,
            }
        )

    if not candidates:
        return ""

    exact_candidates = [item for item in candidates if item.get("warehouse_exact_match")]
    display_pool = exact_candidates or candidates
    has_origin_hint = _has_origin_hint(message) or bool(origin_city)
    display_candidates = _select_full_tier_display_candidates(
        display_pool,
        message=message,
        has_origin_hint=has_origin_hint,
        origin_city=origin_city,
        limit=limit,
    )
    if not display_candidates:
        return ""

    warehouse_label = "/".join(warehouse_codes)
    lines = [
        f"结论：**{warehouse_label}** 的完整报价阶梯我先给你展开了，方便你直接对比重量档和方数档。",
        "",
        f"{warehouse_label} 报价明细：",
        "",
        "| 渠道 | 出发仓 | 重量/方数阶梯 | 价格 (RMB) | 宣称时效 | 备注 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for item in display_candidates:
        for tier_label, price_text in item["all_tier_rows"]:
            lines.append(
                f"| {item['channel']} | {item['origin_label']} | {tier_label} | {price_text} | "
                f"{item['transit_time'] or '待确认'} | {item['note'] or '-'} |"
            )

    if address_probe_context:
        lines.extend(["", "地址提醒：", address_probe_context])

    sources: list[str] = []
    for item in display_candidates:
        source = item["source"]
        if source and source not in sources:
            sources.append(source)
    if sources:
        lines.extend(["", f"报价来源：{'、'.join(sources)}"])

    return "\n".join(lines).strip()


def build_deterministic_quote_response(
    message: str,
    quote_records: List[Dict] | None,
    address_probe_context: str = "",
    limit: int = 3,
) -> str:
    details = extract_quote_request_details(message)
    warehouse_codes = details["warehouse_codes"]
    weight_kg = details["weight_kg"]
    volume_cbm = details["volume_cbm"]
    origin_city = details["origin_city"]

    if not warehouse_codes:
        return ""

    if weight_kg is None:
        return _build_full_tier_quote_response(
            message,
            warehouse_codes,
            origin_city,
            quote_records,
            address_probe_context=address_probe_context,
            limit=limit,
        )

    candidates: list[dict[str, Any]] = []
    for record in quote_records or []:
        price_system = record.get("价格体系") or {}
        weight_label, weight_price = pick_weight_price_tier(price_system, weight_kg)
        volume_label, volume_price = pick_volume_price_tier(price_system, volume_cbm)

        pricing_basis = None
        unit_price = None
        total_price = None
        tier_label = None

        if weight_label and weight_price is not None:
            pricing_basis = "weight"
            tier_label = weight_label
            unit_price = weight_price
            total_price = weight_price * weight_kg

        if volume_label and volume_price is not None and volume_cbm is not None:
            volume_total = volume_price * volume_cbm
            if total_price is None or volume_total > total_price:
                pricing_basis = "volume"
                tier_label = volume_label
                unit_price = volume_price
                total_price = volume_total

        if pricing_basis is None or unit_price is None or total_price is None:
            continue

        origin_bucket = _detect_origin_bucket(
            str(record.get("渠道", "")).strip(),
            str(record.get("_source", "")).strip(),
        )
        origin_hub_cities = _detect_origin_hub_cities(
            str(record.get("渠道", "")).strip(),
            str(record.get("_source", "")).strip(),
        )
        nearest_origin_hub, origin_distance_km = _resolve_nearest_origin_hub(origin_city, origin_hub_cities)

        candidates.append(
            {
                "channel": str(record.get("渠道", "未知渠道")).strip(),
                "warehouse_code": str(record.get("仓库代码", "")).strip(),
                "price_system": price_system,
                "tier_label": tier_label,
                "unit_price": unit_price,
                "total_price": total_price,
                "pricing_basis": pricing_basis,
                "transit_time": str(record.get("宣称时效", "")).strip(),
                "note": str(record.get("附加备注", "")).strip(),
                "source": str(record.get("_source", "")).strip(),
                "origin_bucket": origin_bucket,
                "origin_hub_cities": origin_hub_cities,
                "nearest_origin_hub": nearest_origin_hub,
                "origin_distance_km": origin_distance_km,
                "origin_label": _format_origin_hub_label(origin_hub_cities, origin_bucket),
            }
        )

        candidate = candidates[-1]
        candidate["channel"] = str(record.get("渠道", candidate["channel"])).strip()
        candidate["warehouse_code"] = str(record.get("仓库代码", candidate["warehouse_code"])).strip()
        candidate["destination_region"] = str(record.get("目的地区", "")).strip()
        candidate["transit_time"] = str(record.get("宣称时效", candidate["transit_time"])).strip()
        candidate["note"] = str(record.get("附加备注", candidate["note"])).strip()
        candidate["source"] = str(record.get("_source", candidate["source"])).strip()
        candidate["origin_bucket"] = _detect_origin_bucket(candidate["channel"], candidate["source"])
        candidate["origin_hub_cities"] = _detect_origin_hub_cities(candidate["channel"], candidate["source"])
        candidate["nearest_origin_hub"], candidate["origin_distance_km"] = _resolve_nearest_origin_hub(
            origin_city, candidate["origin_hub_cities"]
        )
        candidate["origin_label"] = _format_origin_hub_label(
            candidate["origin_hub_cities"], candidate["origin_bucket"]
        )
        candidate["warehouse_exact_match"] = _record_matches_requested_warehouses(record, warehouse_codes)
        candidate["match_scope"] = str(record.get("_match_scope", "")).strip()

    if not candidates:
        return (
            f"结论：当前报价表未收录 **{'、'.join(warehouse_codes)}** 的精确仓库报价。"
            "\n\n补充提醒：\n- 这票先别直接对客报死价，建议找对应渠道确认仓库是否直达及附加费。"
        )

    exact_candidates = [item for item in candidates if item.get("warehouse_exact_match")]
    # 不再激进删除非精确匹配，改为优先标记。
    # 除非精确匹配数量已经很多了（比如 > 5个），才只留精确匹配
    if exact_candidates and len(exact_candidates) >= 5:
        candidates = exact_candidates
    elif exact_candidates:
        # 将精确匹配排到最前面，但保留其他候选以便“参考”
        others = [item for item in candidates if not item.get("warehouse_exact_match")]
        candidates = exact_candidates + others
    else:
        return _build_reference_only_quote_response(
            warehouse_codes,
            weight_kg,
            candidates,
            address_probe_context=address_probe_context,
            limit=limit,
        )

    has_origin_hint = _has_origin_hint(message) or bool(origin_city)
    display_candidates = _select_display_candidates(
        candidates,
        has_origin_hint=has_origin_hint,
        origin_city=origin_city,
        limit=limit,
    )
    if not display_candidates:
        return ""

    best, prefers_mingrizhixing = _pick_recommended_candidate(
        display_candidates,
        has_origin_hint=has_origin_hint,
        origin_city=origin_city,
    )
    warehouse_label = "、".join(warehouse_codes)
    table_rows = _build_quote_table_rows(display_candidates, has_origin_hint, origin_city)
    conclusion_scope = "当前优先参考明日之星渠道里" if prefers_mingrizhixing else "当前命中渠道里"
    if origin_city and best.get("origin_label"):
        conclusion_scope = (
            f"按发货地【{origin_city}】就近匹配，优先参考【{best['origin_label']}】对应渠道里"
        )
    lines = [
        (
            f"结论：{_format_price(weight_kg)}KG 发往 {warehouse_label}，{conclusion_scope}，"
            f"{best['channel']} 最优，按 {best['tier_label']} **¥{_format_price(best['unit_price'])}/KG**，"
            f"预估总价 **¥{_format_price(best['total_price'])}**。"
        ),
        "",
        "报价明细：",
        "| 仓别 | 渠道 | 时效 | 对应阶梯 | 单价 | 预估总价 | 全阶梯 | 备注 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in table_rows:
        lines.append(
            f"| {row['bucket_label']} | {row['channel']} | {row['transit_time']} | {row['tier_label']} | "
            f"{row['unit_price']} | {row['total_price']} | {row['weight_tiers']} | {row['note']} |"
        )

    if address_probe_context:
        lines.extend(["", "地址提醒：", address_probe_context])

    reminder_lines = [
        "",
        "补充提醒：",
        (
            f"- 你现在只给了实重 {_format_price(weight_kg)}KG，"
            "还没给箱规/CBM/件数，也没补齐箱规、体积、品类，目前只能按实重阶梯先报。"
        ),
        "- 如果是泡货、超长货或抛货，最终可能改按体积重或按方计费。",
    ]
    if not has_origin_hint:
        reminder_lines.append("- 你还没说明起运仓/起运区域，以上只是按当前命中报价表粗排，正式对客前请先锁定起运仓。")
    if volume_cbm is not None:
        reminder_lines[2] = (
            f"- 本次同时识别到体积 {_format_price(volume_cbm)}CBM，仍建议再核对箱规后确认最终计费方式。"
        )
    lines.extend(reminder_lines)
    lines.extend(["", _build_old_bird_tip(table_rows, has_origin_hint, weight_kg, volume_cbm, address_probe_context)])

    sources = []
    for item in display_candidates:
        source = item["source"]
        if source and source not in sources:
            sources.append(source)

    if sources:
        lines.extend(["", f"报价来源：{'、'.join(sources)}"])

    return "\n".join(lines).strip()

def search_best_quotes(query: str, limit: int = 40) -> List[Dict]:
    """Search for relevant quotes based on relevance scoring to avoid 'South China bias'."""
    if not QUOTES_CACHE:
        load_all_quotes()
    
    found_whs = WH_CODE_PATTERN.findall(query.upper())
    
    # 建立仓库到区域的隐式映射
    import json
    map_file = os.path.join(DATA_DIR, "..", "warehouse_region_map.json")
    try:
        with open(map_file, "r", encoding="utf-8") as f:
            wh_to_region = json.load(f)
    except Exception:
        wh_to_region = {
            "ONT8": "美西", "LGB8": "美西", "LAX9": "美西",
            "FTW1": "美中", "IND9": "美中", "MDW2": "美中",
            "TEB9": "美东", "ABE2": "美东", "PHL7": "美东"
        }
    
    extra_regions = []
    for wh in found_whs:
        if wh in wh_to_region:
            extra_regions.append(wh_to_region[wh])

    region_map = {"美东": "美东", "美中": "美中", "美西": "美西",
                  "东部": "美东", "中部": "美中", "西部": "美西",
                  "华东": "华东", "华南": "华南",
                  "新加坡": "新加坡", "马来西亚": "马来西亚", "马代": "马来西亚", "西马": "西马", "东马": "东马",
                  "泰国": "泰国", "菲律宾": "菲律宾", "越南": "越南", "印尼": "印尼", "澳洲": "澳洲", "澳大利亚": "澳洲"}
    found_regions_from_query = [v for k, v in region_map.items() if k in query]
    all_found_regions = list(set(found_regions_from_query + extra_regions))
    
    # 显式代理商倾向
    explicit_agents = []
    for agent in ["锦联", "亿阳", "星夜", "腾信", "明日之星", "商壹", "澳鑫"]:
        if agent in query:
            explicit_agents.append(agent)

    # 地理/起运倾向打分器
    origin_city = _extract_origin_city(query)
    target_origin_bucket = None
    if "华东" in query: target_origin_bucket = "华东"
    elif "华南" in query: target_origin_bucket = "华南"
    elif origin_city: target_origin_bucket = _detect_origin_bucket(origin_city, "")

    # 全量匹配与打分
    scored_results = []
    seen_keys = set()
    
    search_keywords = ["海派", "海运", "空派", "空运", "美森", "限时达", "普货", "带电", "卡派"]
    found_keywords = [k for k in search_keywords if k in query]

    for filename, records in QUOTES_CACHE.items():
        is_prio_file = "明日之星" in filename or any(a in filename for a in explicit_agents)
        for r in records:
            # 基础关键词过滤 (初筛)
            wh_code = r.get("仓库代码", "").upper()
            region = r.get("目的地区", "")
            
            matches_wh = any(wh in wh_code for wh in found_whs) if found_whs else False
            matches_rg = any(rg in region for rg in all_found_regions) if all_found_regions else False
            matches_agent = any(a.lower() in filename.lower() or a.lower() in r.get("渠道", "").lower() for a in explicit_agents)
            matches_keyword = any(k.lower() in r.get("渠道", "").lower() for k in found_keywords)

            if not (matches_wh or matches_rg or matches_agent or matches_keyword or not (found_whs or all_found_regions or explicit_agents or found_keywords)):
                continue

            unique_key = (r.get("渠道", ""), r.get("仓库代码", ""), r.get("目的地区", ""), filename)
            if unique_key in seen_keys:
                continue
            seen_keys.add(unique_key)

            # 打分逻辑
            score = 0
            if matches_wh: score += 100
            if matches_agent: score += 50
            if matches_rg: score += 30
            if matches_keyword: score += 20
            if is_prio_file: score += 10
            
            # --- 【关键】起运地匹配度额外加分 ---
            rec_origin_bucket = _detect_origin_bucket(r.get("渠道", ""), filename)
            if target_origin_bucket and rec_origin_bucket == target_origin_bucket:
                score += 80 # 给起运倾向极高的权重，确保它能冲进 top N
            
            r_copy = r.copy()
            r_copy["_source"] = filename
            r_copy["_search_score"] = score
            scored_results.append(r_copy)

    # 根据总分排序并截断
    scored_results.sort(key=lambda x: x["_search_score"], reverse=True)
    final_raw_results = scored_results[:limit]
    
    # 二次分类（保持原有的精确/参考标记逻辑，供上层 UI 展示使用）
    exact_results = []
    other_results = []
    for res in final_raw_results:
        res_codes = _extract_record_warehouse_codes(res)
        if any(wh in res_codes for wh in found_whs):
            res["_match_scope"] = "warehouse_exact"
            exact_results.append(res)
        else:
            res["_match_scope"] = "region_reference"
            other_results.append(res)
            
    return exact_results + other_results

def get_quote_data_as_string(query: str = None, limit: int = 15) -> str:
    """Return quote data as formatted structured JSON text for the LLM to read."""
    if not QUOTES_CACHE:
        load_all_quotes()
        
    result = ""
    # If a query is provided, we search for specific relevant records instead of just showing the first 50
    if query:
        relevant_records = search_best_quotes(query, limit=limit)
        if relevant_records:
            result += f"--- 已为您锁定与“{query}”最相关的报价数据 ({len(relevant_records)} 条) ---\n"
            result += json.dumps(relevant_records, ensure_ascii=False, indent=2)
            return result
        else:
            result += "--- 未找到直接匹配仓库。以下展示部分参考渠道： ---\n"

    # Default fallback - very conservative
    for name, records in QUOTES_CACHE.items():
        result += f"--- 报价表预览: {name} ---\n"
        sample = records[:3]
        result += json.dumps(sample, ensure_ascii=False, indent=2)
        result += "\n\n"
            
    return result

# Initialize on module import
init_quote_directory()
try:
    load_all_quotes()
except Exception:
    pass
