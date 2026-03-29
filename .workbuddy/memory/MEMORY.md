# 仲易达智能助手 - 项目核心记忆

## 1. 项目概述

**项目名称**：仲易达智能助手（小易）
**定位**：为"仲易达集团(ZHONGYIDA GROUP)"量身定制的高效AI工作台系统

### 核心理念
- **视觉风格**：严谨、高效、专业的企业级桌面工作台风格
- **配色方案**：白/浅灰底 + 蓝紫色主题键(#5c52e6) + 深灰字
- **绝对避免**：花哨移动端拟态、重玻璃特效、无意义渐变色

## 2. 技术栈

### 后端
- **框架**：FastAPI (Python 3.12+)
- **数据库**：SQLite (`backend/data/app.db`)
- **向量数据库**：ChromaDB (`backend/data/chromadb`)
- **大模型**：豆包系列 (Doubao-pro-32k, Doubao-embedding-vision-250615)
- **爬虫**：Playwright (物流轨迹查询)
- **依赖管理**：venv虚拟环境

### 前端Web
- **框架**：Vue 3 + Vite
- **状态管理**：Pinia
- **路由**：Vue Router
- **UI库**：Lucide Vue Next图标库
- **Markdown渲染**：marked

### 前端小程序
- **框架**：Uni-app (Vue 3 + Vite)
- **目标平台**：微信小程序 (mp-weixin)
- **HTTP库**：axios
- **支持构建**：H5、多端小程序

## 3. 核心功能模块

### 3.1 AI对话模式（3种）
1. **全能助手(general)**：处理常规业务与日常流程
2. **知识教练(coach)**：沉浸式培训平台，三层串联场景筛选
3. **专家指导(expert)**：多轮对话深度策略拆解

### 3.2 RAG知识库
- **文档上传**：支持Word(.docx)和PDF解析
- **多模态向量化**：豆包Vision模型适配
- **智能检索**：ChromaDB向量检索+重排+来源摘要

### 3.3 报价查询系统
- **多渠道解析**：锦联、亿阳、星夜、腾信、商壹、澳鑫、天航
- **智能推荐**：基于起运地、仓库代码、重量体积的评分排序
- **底价表管理**：Excel报价单解析与缓存

### 3.4 偏远地址识别
- **亚马逊仓库名单**：`偏远地址/亚马逊仓库名单.xlsx`
- **偏远地址总汇**：`偏远地址/偏远地址总汇.xlsx`
- **支持范围/前缀/精确匹配**

### 3.5 物流轨迹查询
- **集成Playwright爬虫**：抓取第三方轨迹网站
- **反爬处理**：验证码超时防护

### 3.6 教练对练系统
- **剧本管理**：`data/coach_cases.json`
- **场景分类**：美国线/欧洲线 × 行业小白/江湖老手
- **实时情报面板**：侧边滑动辅导

## 4. 项目结构

```
仲易达智能助手/
├── backend/
│   ├── routers/          # API路由层
│   │   ├── chat.py        # 核心聊天流式接口(/api/chat/stream)
│   │   ├── auth.py        # 登录认证
│   │   ├── staff.py       # 员工管理
│   │   ├── upload.py      # 文件上传
│   │   ├── notices.py     # 通知管理
│   │   ├── settings.py    # 系统设置
│   │   ├── tools.py       # 工具路由
│   │   ├── coach_quiz.py  # 教练问答
│   │   ├── chat_logs.py   # 聊天日志
│   │   └── client_logs.py # 客户端日志
│   ├── services/          # 业务逻辑服务层
│   │   ├── llm_client.py      # 豆包API封装
│   │   ├── rag_service.py     # 向量数据库
│   │   ├── quote_service.py   # 报价服务
│   │   ├── address_service.py # 偏远地址
│   │   ├── tracking_service.py # 轨迹查询
│   │   ├── chat_intelligence.py # 意图分类/检索
│   │   └── [各报价解析器]      # jinlian/yiyang/xingye等
│   ├── models/            # SQLAlchemy模型
│   ├── data/              # 数据存储
│   │   ├── docs/          # 上传文档
│   │   ├── quotes/         # 报价表
│   │   └── chromadb/       # 向量数据库
│   └── tests/             # 单元测试
├── frontend/              # Vue3 Web端
│   └── src/
│       ├── views/         # 页面视图
│       │   ├── ChatView.vue       # 主聊天页
│       │   ├── LoginView.vue       # 登录页
│       │   ├── AdminView.vue       # 管理后台
│       │   └── [其他页面]
│       ├── components/     # 通用组件
│       └── store/          # Pinia状态
├── frontend-uniapp/        # Uni-app小程序端
│   └── src/
│       └── pages/          # 小程序页面
└── docs/plans/            # 开发计划文档
```

## 5. 版本历史

### v1.1.0 (2026-02-27)
- 视觉PDF解析(AI视力)：PyMuPDF + 豆包Vision
- 批量上传支持
- 局域网共享测试
- 人格化对话优化

### v1.0.0 (2026-02-26)
- 双端分离架构
- 知识库上传与RAG对话
- 多模态向量化适配
- 桌面一键启动

## 6. 进行中的开发计划

1. **后端聊天重构**(2026-03-20)：拆分Intent/消息编排/Tracking Service
2. **小程序深度适配**：微信小程序环境验证与功能迁移
3. **管理台联调**：员工CRUD与实验室配置
4. **云端部署标准化**：阿里云Nginx+PM2方案

## 7. 关键API接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/chat/stream` | POST | 核心聊天流式接口 |
| `/api/auth/login` | POST | 登录认证 |
| `/api/upload/document` | POST | 文档上传 |
| `/api/upload/quote` | POST | 报价表上传 |
| `/api/staff/users` | GET/POST/PATCH/DELETE | 员工管理 |

## 8. 角色权限体系

- **owner**：老板（全部权限）
- **super_admin**：超级管理员
- **daily_admin**：日常管理员（含隐式权限）
- **staff_admin**：普通管理员
- **branch_admin**：分公司管理员
- **employee**：员工

## 9. 关键配置

- **环境变量**：`backend/.env`
- **CORS白名单**：`ALLOWED_ORIGINS`
- **AI模型端点**：`DOUBAO_MODEL_ENDPOINT`
- **向量模型**：`DOUBAO_EMBEDDING_ENDPOINT`

## 10. 小易人格设定

- **身份**：金牌物流合伙人/仲易达内部专家顾问
- **用户**：公司业务同事（战友）
- **风格**：幽默与共情，绝对严谨
- **禁止**：称呼用户为"老板/客户"，应像老鸟搭档
- **专有名词**：将"明日"优先理解为"明日之星"渠道
