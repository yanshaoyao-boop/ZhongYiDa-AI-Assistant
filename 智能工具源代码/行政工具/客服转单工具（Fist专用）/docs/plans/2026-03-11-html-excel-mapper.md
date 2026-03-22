# HTML Excel 映射工具 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个本地可运行的 HTML 工具，把 A 表每行数据按映射规则写入 B 表模板并批量生成独立 Excel 文件。

**Architecture:** 使用 Python 标准库 HTTP server 提供本地接口和静态页面，前端用原生 HTML/CSS/JS 完成文件选择、字段映射、配置导入导出与结果展示。Excel 处理由 `openpyxl` 完成，始终基于 B 模板重新加载后写入少量目标单元格，确保模板公式、样式、颜色和布局尽量保持不变。

**Tech Stack:** Python 3, openpyxl, unittest, HTML, CSS, JavaScript

---

### Task 1: 建立项目骨架

**Files:**
- Create: `app.py`
- Create: `excel_mapper.py`
- Create: `templates/index.html`
- Create: `static/app.js`
- Create: `static/styles.css`
- Create: `tests/test_excel_mapper.py`

**Step 1: Write the failing test**

```python
def test_generate_workbooks_creates_one_file_per_row():
    ...
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: FAIL with missing module or missing function

**Step 3: Write minimal implementation**

```python
def generate_workbooks(...):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: PASS

### Task 2: 实现 Excel 映射核心

**Files:**
- Modify: `excel_mapper.py`
- Modify: `tests/test_excel_mapper.py`

**Step 1: Write the failing test**

```python
def test_generate_workbooks_applies_fixed_and_custom_mappings():
    ...
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: FAIL with wrong cell values or missing output

**Step 3: Write minimal implementation**

```python
FIXED_MAPPINGS = ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: PASS

### Task 3: 提供模板字段提取能力

**Files:**
- Modify: `excel_mapper.py`
- Modify: `tests/test_excel_mapper.py`

**Step 1: Write the failing test**

```python
def test_extract_template_targets_returns_field_labels_and_cells():
    ...
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: FAIL because extraction function does not exist

**Step 3: Write minimal implementation**

```python
def extract_template_targets(...):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: PASS

### Task 4: 实现本地 HTML 工具

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `static/app.js`
- Modify: `static/styles.css`

**Step 1: Write the failing test**

由于当前环境未安装 Web test framework，本任务以核心接口自测替代页面自动化测试：

```text
启动本地服务后访问首页，确认可读取页面且包含上传、映射、导入导出和生成按钮。
```

**Step 2: Run check to verify it fails**

Run: `python app.py`
Expected: 页面或接口不可用

**Step 3: Write minimal implementation**

实现静态页面服务与 `/api/inspect`、`/api/generate` 接口。

**Step 4: Run check to verify it passes**

Run: `python app.py`
Expected: 首页可访问，接口返回正确 JSON

### Task 5: 完成验证

**Files:**
- Modify: `开发日志.txt`

**Step 1: Run automated verification**

Run: `python -m unittest tests.test_excel_mapper -v`
Expected: PASS

**Step 2: Run manual verification**

Run: `python app.py`
Expected: 能生成输出目录与 zip 文件

**Step 3: Record verification result**

在 `开发日志.txt` 记录本次验证命令和结果。
