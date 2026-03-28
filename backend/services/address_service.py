import json
import os
import re
import threading
import urllib.parse
import urllib.request

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ADDRESS_DATA_DIR = os.path.join(BASE_DIR, "偏远地址")
AMAZON_WAREHOUSE_FILE = os.path.join(ADDRESS_DATA_DIR, "亚马逊仓库名单.xlsx")
YIYANG_WAREHOUSE_FILE = os.path.join(ADDRESS_DATA_DIR, "亿阳仓库.xlsx")
REMOTE_TOTAL_FILE = os.path.join(ADDRESS_DATA_DIR, "偏远地址总汇.xlsx")


class AddressService:
    def __init__(self):
        self.warehouse_info = {}  # {code: {zip, address, city, state}}
        self.yiyang_warehouse_info = {}  # fallback warehouse source
        self.direct_remote_warehouses = {}  # {code: level_desc}
        self.zip_remote_rules = {}  # {level_name: [rules]}
        self.web_lookup_cache = {}  # {target: detail_dict}

        self.is_loaded = False
        self._lock = threading.Lock()

    @staticmethod
    def _normalize_text(value):
        text = str(value or "").strip().lower()
        text = re.sub(r"\s+", "", text)
        return text

    @staticmethod
    def _normalize_zip(zip_value):
        zip_text = str(zip_value or "").strip()
        if not zip_text or zip_text.upper() == "NAN":
            return ""

        if zip_text.endswith(".0"):
            zip_text = zip_text[:-2]

        digits = re.sub(r"\D", "", zip_text)
        if len(digits) >= 5:
            return digits[:5]
        if digits:
            return digits.zfill(5)
        return ""

    @staticmethod
    def _safe_cell(row, col_name):
        if not col_name:
            return ""
        value = row.get(col_name, "")
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _find_col(self, columns, keywords):
        for col in columns:
            normalized = self._normalize_text(col)
            if any(keyword in normalized for keyword in keywords):
                return col
        return None

    @staticmethod
    def _is_positive_marker(value):
        text = str(value or "").strip().lower()
        if not text or text in {"nan", "none", "null"}:
            return False

        markers = {"1", "y", "yes", "true", "是", "有", "√", "✓", "✔", "x", "*"}
        return text in markers or any(token in text for token in ("√", "✓", "✔", "是", "有", "偏远", "超偏远"))

    def _load_warehouse_data(self, file_path):
        if not os.path.exists(file_path):
            return {}

        try:
            df_wh = pd.read_excel(file_path)
        except Exception as exc:
            print(f"!! AddressService warehouse load error from {file_path}: {exc}")
            return {}

        columns = list(df_wh.columns)

        code_col = self._find_col(columns, ["fbacode", "warehousecode", "仓库代码", "仓库编码", "仓库代号", "仓库"])
        zip_col = self._find_col(columns, ["zipcode", "postalcode", "zip", "postal", "邮编"])
        addr_col = self._find_col(columns, ["address", "地址"])
        city_col = self._find_col(columns, ["city", "城市"])
        state_col = self._find_col(columns, ["state", "province", "州", "省"])

        if not code_col:
            return {}

        result = {}
        for _, row in df_wh.iterrows():
            code = self._safe_cell(row, code_col).upper().replace(" ", "")
            if not code or code == "NAN":
                continue

            detail = {
                "zip": self._normalize_zip(self._safe_cell(row, zip_col)),
                "address": self._safe_cell(row, addr_col),
                "city": self._safe_cell(row, city_col),
                "state": self._safe_cell(row, state_col),
            }
            result[code] = detail

        return result

    @staticmethod
    def _add_zip_rule(rules, raw_value):
        text = str(raw_value or "").strip()
        if not text:
            return

        text = text.replace("—", "-").replace("–", "-").replace("－", "-")
        text = text.replace("~", "-").replace("至", "-")
        text = text.replace(" ", "")
        if text.endswith(".0"):
            text = text[:-2]

        range_match = re.match(r"^(\d{1,5})-(\d{1,5})$", text)
        if range_match:
            low = int(range_match.group(1))
            high = int(range_match.group(2))
            rules.append(("range", min(low, high), max(low, high)))
            return

        if "*" in text:
            prefix = re.sub(r"[^0-9]", "", text)
            if prefix:
                rules.append(("prefix", prefix))
            return

        if text.isdigit() and len(text) <= 5:
            rules.append(("exact", text.zfill(5)))

    def _load_remote_rules(self):
        self.direct_remote_warehouses = {}
        self.zip_remote_rules = {}

        if not os.path.exists(REMOTE_TOTAL_FILE):
            return

        try:
            xl = pd.ExcelFile(REMOTE_TOTAL_FILE)
        except Exception as exc:
            print(f"!! AddressService remote file load error: {exc}")
            return

        direct_sheet = next(
            (s for s in xl.sheet_names if "偏远仓库" in self._normalize_text(s)),
            None,
        )

        if direct_sheet:
            df_direct = xl.parse(direct_sheet)
            columns = list(df_direct.columns)

            wh_col = self._find_col(columns, ["仓库代码", "仓库编码", "仓库代号", "仓库"])
            ups_col = self._find_col(columns, ["ups"])
            fedex_col = self._find_col(columns, ["联邦", "fedex"])
            super_col = self._find_col(columns, ["超偏远", "标红", "超偏"])

            for _, row in df_direct.iterrows():
                wh_code = self._safe_cell(row, wh_col).upper().replace(" ", "")
                if not wh_code or wh_code == "NAN":
                    continue

                levels = []
                if self._is_positive_marker(self._safe_cell(row, ups_col)):
                    levels.append("UPS偏远")
                if self._is_positive_marker(self._safe_cell(row, fedex_col)):
                    levels.append("联邦偏远")
                if self._is_positive_marker(self._safe_cell(row, super_col)):
                    levels.append("超偏远")

                if levels:
                    self.direct_remote_warehouses[wh_code] = "/".join(levels)

        for sheet in xl.sheet_names:
            if sheet == direct_sheet:
                continue

            try:
                df_zip = xl.parse(sheet, header=None)
            except Exception:
                continue

            rules = []
            for col in df_zip.columns:
                for val in df_zip[col].dropna():
                    self._add_zip_rule(rules, val)

            if rules:
                self.zip_remote_rules[sheet] = rules

    def _lookup_zip_geo(self, zip_code):
        if not zip_code:
            return {}

        try:
            url = f"https://api.zippopotam.us/us/{zip_code}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                payload = resp.read().decode("utf-8", errors="ignore")

            data = json.loads(payload)
            places = data.get("places") or []
            if not places:
                return {}

            place = places[0]
            return {
                "city": str(place.get("place name", "")).strip(),
                "state": str(place.get("state abbreviation", "") or place.get("state", "")).strip(),
            }
        except Exception:
            return {}

    def _lookup_zip_from_web(self, warehouse_code):
        if not warehouse_code:
            return ""

        query = f"{warehouse_code} warehouse zip code"
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded_query}"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        close_match = re.search(
            rf"{re.escape(warehouse_code)}.{{0,300}}?(?<!\d)(\d{{5}})(?:-\d{{4}})?(?!\d)",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if close_match:
            return close_match.group(1)

        fallback_match = re.search(r"(?<!\d)(\d{5})(?:-\d{4})?(?!\d)", html)
        if fallback_match:
            return fallback_match.group(1)

        return ""

    def _lookup_from_web(self, target):
        if not target:
            return {}

        normalized_target = target.strip().upper()
        if normalized_target in self.web_lookup_cache:
            return dict(self.web_lookup_cache[normalized_target])

        detail = {}

        try:
            if normalized_target.isdigit() and len(normalized_target) <= 5:
                zip_code = normalized_target.zfill(5)
                detail["zip"] = zip_code
                detail.update(self._lookup_zip_geo(zip_code))
            else:
                zip_code = self._lookup_zip_from_web(normalized_target)
                if zip_code:
                    detail["zip"] = zip_code
                    detail.update(self._lookup_zip_geo(zip_code))
        except Exception:
            detail = {}

        self.web_lookup_cache[normalized_target] = detail
        return dict(detail)

    def load_data(self):
        """加载所有地址和偏远数据到内存索引"""
        if self.is_loaded:
            return

        with self._lock:
            if self.is_loaded:
                return

            print(f">> AddressService: Starting to load data from {BASE_DIR}")
            try:
                self.warehouse_info = self._load_warehouse_data(AMAZON_WAREHOUSE_FILE)
                self.yiyang_warehouse_info = self._load_warehouse_data(YIYANG_WAREHOUSE_FILE)
                self._load_remote_rules()
                self.is_loaded = True
            except Exception as exc:
                print(f"!! AddressService load error: {exc}")

    def query(self, target: str):
        if not self.is_loaded:
            self.load_data()

        target = target.strip().upper()
        result = {
            "is_remote": False,
            "level": None,
            "target": target,
            "zip": None,
            "address": None,
            "city": None,
            "state": None,
            "source": None,
        }

        wh_detail = self.warehouse_info.get(target)
        if wh_detail:
            result.update(wh_detail)
            result["source"] = "primary"
        else:
            yiyang_detail = self.yiyang_warehouse_info.get(target)
            if yiyang_detail:
                result.update(yiyang_detail)
                result["source"] = "yiyang"
            else:
                web_detail = self._lookup_from_web(target)
                if web_detail:
                    result.update(web_detail)
                    result["source"] = "web"

        if target in self.direct_remote_warehouses:
            result["is_remote"] = True
            result["level"] = self.direct_remote_warehouses[target]
            return result

        lookup_zip = result["zip"]
        if not lookup_zip and target.isdigit() and len(target) <= 5:
            lookup_zip = target.zfill(5)
            result["zip"] = lookup_zip
            if not result["source"]:
                result["source"] = "input"

        if lookup_zip:
            matched_levels = []
            try:
                zip_int = int(lookup_zip)
                for level_name, rules in self.zip_remote_rules.items():
                    is_match = False
                    for r_type, *r_vals in rules:
                        if r_type == "exact" and lookup_zip == r_vals[0]:
                            is_match = True
                        elif r_type == "range" and r_vals[0] <= zip_int <= r_vals[1]:
                            is_match = True
                        elif r_type == "prefix" and lookup_zip.startswith(r_vals[0]):
                            is_match = True
                        if is_match:
                            break
                    if is_match:
                        matched_levels.append(level_name)
            except Exception:
                pass

            if matched_levels:
                result["is_remote"] = True

                def priority(name):
                    if "极" in name or "超" in name:
                        return 0
                    return 1

                matched_levels.sort(key=priority)
                result["level"] = "/".join(matched_levels)
                return result

        return result


# 单例模式
address_service = AddressService()
