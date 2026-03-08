import pandas as pd
import os
import re

# 文件路径
# 如果 __file__ 是 backend/services/address_service.py
# 那么 root 就是 backend/services 的上上层
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AMAZON_WAREHOUSE_FILE = os.path.join(BASE_DIR, "偏远地址", "亚马逊仓库名单.xlsx")
REMOTE_TOTAL_FILE = os.path.join(BASE_DIR, "偏远地址", "偏远地址总汇.xlsx")

import threading

class AddressService:
    def __init__(self):
        self.warehouse_info = {} # {code: {zip, address, city, state}}
        self.direct_remote_warehouses = {} # {code: level_desc}
        self.zip_remote_rules = {} # {level_name: set_of_zips}
        self.is_loaded = False
        self._lock = threading.Lock()

    def load_data(self):
        """加载所有地址和偏远数据到内存索引"""
        if self.is_loaded:
            return
        
        with self._lock:
            if self.is_loaded:
                return
            
            print(f">> AddressService: Starting to load data from {BASE_DIR}")
            try:
                # 1. 加载亚马逊仓库名单
                if os.path.exists(AMAZON_WAREHOUSE_FILE):
                    df_wh = pd.read_excel(AMAZON_WAREHOUSE_FILE)
                    # 兼容不同列名
                    code_col = next((c for c in df_wh.columns if 'FBA Code' in c), 'FBA Code')
                    zip_col = next((c for c in df_wh.columns if 'Zip' in c), 'Zip')
                    addr_col = next((c for c in df_wh.columns if '址' in c or 'Address' in c), '地  址')
                    city_col = next((c for c in df_wh.columns if 'City' in c), 'City')
                    state_col = next((c for c in df_wh.columns if 'State' in c), 'State')
                    
                    for _, row in df_wh.iterrows():
                        code = str(row.get(code_col, '')).strip().upper()
                        zip_val = str(row.get(zip_col, '')).strip()
                        if code and zip_val and code != 'NAN':
                            if zip_val.endswith('.0'): zip_val = zip_val[:-2]
                            if zip_val.isdigit(): zip_val = zip_val.zfill(5)
                            
                            self.warehouse_info[code] = {
                                "zip": zip_val,
                                "address": str(row.get(addr_col, '')).strip(),
                                "city": str(row.get(city_col, '')).strip(),
                                "state": str(row.get(state_col, '')).strip()
                            }

                # 2. 加载偏远地址总汇
                if os.path.exists(REMOTE_TOTAL_FILE):
                    xl = pd.ExcelFile(REMOTE_TOTAL_FILE)
                    # A. 解析"偏远仓库"页签
                    if '偏远仓库' in xl.sheet_names:
                        df_direct = xl.parse('偏远仓库')
                        wh_col = next((c for c in df_direct.columns if '仓库' in c), '仓库代码')
                        for _, row in df_direct.iterrows():
                            wh_code = str(row.get(wh_col, '')).strip().upper()
                            if wh_code and wh_code != 'NAN':
                                levels = []
                                if '√' in str(row.get('UPS', '')): levels.append('UPS偏远')
                                if '√' in str(row.get('联邦', '')): levels.append('联邦偏远')
                                if str(row.get('标红为超偏远', '')).strip().lower() not in ['', 'nan', 'none']: 
                                    levels.append('超偏远')
                                if levels:
                                    self.direct_remote_warehouses[wh_code] = "/".join(levels)

                    # B. 解析基于邮编的页签 (支持范围和单个邮编)
                    self.zip_remote_rules = {} # {level_name: [list_of_rules]}
                    for sheet in xl.sheet_names:
                        if sheet == '偏远仓库': continue
                        df_zip = xl.parse(sheet, header=None)
                        rules = []
                        for col in df_zip.columns:
                            for val in df_zip[col].dropna():
                                s_val = str(val).strip()
                                if s_val.endswith('.0'): s_val = s_val[:-2]
                                
                                # 处理范围: 12345-12350
                                if '-' in s_val:
                                    parts = s_val.split('-')
                                    if len(parts) == 2:
                                        try:
                                            low = int(parts[0].strip())
                                            high = int(parts[1].strip())
                                            rules.append(('range', low, high))
                                        except: pass
                                # 处理带有通配符的: 123*
                                elif '*' in s_val:
                                    prefix = s_val.replace('*', '')
                                    rules.append(('prefix', prefix))
                                # 处理单个邮编
                                elif s_val.isdigit() and len(s_val) <= 5:
                                    rules.append(('exact', s_val.zfill(5)))
                        
                        if rules:
                            self.zip_remote_rules[sheet] = rules
                self.is_loaded = True
            except Exception as e:
                print(f"!! AddressService load error: {e}")

    def query(self, target: str):
        if not self.is_loaded: self.load_data()
        target = target.strip().upper()
        result = {"is_remote": False, "level": None, "target": target, "zip": None, "address": None, "city": None, "state": None}

        wh_detail = self.warehouse_info.get(target)
        if wh_detail:
            result.update(wh_detail)
        
        if target in self.direct_remote_warehouses:
            result["is_remote"] = True
            result["level"] = self.direct_remote_warehouses[target]
            return result

        lookup_zip = result["zip"]
        if not lookup_zip and target.isdigit() and len(target) <= 5:
            lookup_zip = target.zfill(5)
            result["zip"] = lookup_zip

        if lookup_zip:
            matched_levels = []
            try:
                zip_int = int(lookup_zip)
                for level_name, rules in self.zip_remote_rules.items():
                    is_match = False
                    for r_type, *r_vals in rules:
                        if r_type == 'exact' and lookup_zip == r_vals[0]: is_match = True
                        elif r_type == 'range' and r_vals[0] <= zip_int <= r_vals[1]: is_match = True
                        elif r_type == 'prefix' and lookup_zip.startswith(r_vals[0]): is_match = True
                        if is_match: break
                    if is_match: matched_levels.append(level_name)
            except: pass
            
            if matched_levels:
                result["is_remote"] = True
                # 优先级排序：把“极偏远”和“超偏远”放在前面
                def priority(name):
                    if '极' in name or '超' in name: return 0
                    return 1
                matched_levels.sort(key=priority)
                result["level"] = "/".join(matched_levels)
                return result
        return result

# 单例模式
address_service = AddressService()
