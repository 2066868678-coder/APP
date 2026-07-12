<div align="center">

# 🚀 单词突围

**Word Breakthrough**

基于《单词突围5200》的智能英语单词学习应用  
Web / 桌面 / 手机 · 即开即用 · 无需后端

</div>

---

## 📸 功能一览

| | 功能 | 说明 |
|---|------|------|
| 🃏 | **翻卡学习** | 正面英文 → 回想释义 → 翻转查看音标/例句/记忆方法/固定搭配 |
| 🧠 | **艾宾浩斯复习** | 自动调度遗忘曲线 1天→2天→4天→7天→15天→30天，忘记自动重置 |
| 📊 | **进度追踪** | 学习统计、掌握程度分布、成就徽章、连续学习天数 |
| ⏱️ | **完成预估** | 学习页显示「剩余N词·每日M词还需X天」，调整目标实时更新 |
| 📅 | **学习记录导出** | 选择日期 → 预览单词 → 一键下载 Word 文档（手机/电脑通用） |
| 🔄 | **跨设备同步** | 部署到云端后，手机/电脑/平板数据实时共享 |
| 🎨 | **Material 3 设计** | Teal 主题、圆角卡片、环形进度、统一设计系统 |

---

## 🚀 快速启动

```bash
pip install -r requirements.txt
python run_app.py
```

浏览器打开 **http://localhost:8551**  
手机（同 WiFi）打开 **http://192.168.3.59:8551**

---

## 📖 使用流程

```
第1天  开App → 背20个新词 → 第2天系统提示复习
第2天  先复习昨天的20个 → 再背20个新词
第3天  复习第2天学的20个 → 再背20个新词
  ...  每天新词 + 复习同步进行
第X天  2281词全部学完 → 进入长期复习周期
```

- 每日目标可在设置页调整（默认 20 词）
- 忘记的词自动重排在末尾，当天多练几次
- 连续签到不中断，保持学习动力

---

## 🎨 UI 设计

| 组件 | 设计 |
|------|------|
| 主色调 | Teal `#00897B` — 现代、沉静、专注 |
| 顶栏 | 底部圆角 28px + 阴影，区别于内容区 |
| 卡片 | 统一阴影/圆角，`AppCard` 组件一键复用 |
| 单词卡 | 顶部装饰色条 + 音标胶囊 + 左边缘色条 section |
| 进度环 | 圆形进度指示器替代传统进度条 |
| Snackbar | 漂浮圆角提示，带图标前缀 |
| 徽章 | 圆形彩色背景图标，取代纯 emoji |

---

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| UI 框架 | Flet (Material 3, Python) |
| 数据库 | SQLite（本地）/ PostgreSQL（云端） |
| 复习算法 | 艾宾浩斯遗忘曲线（6级间隔） |
| PDF 提取 | PyMuPDF（上册文字版） |
| OCR | PaddleOCR（下册扫描版 🔜） |
| 部署 | Render + GitHub 自动部署 |
| 同步优化 | 批量查询，单页加载仅 1 次 DB 会话 |

---

## 📁 项目结构

```
E:\APP
├── run_app.py               # 🏁 启动入口
├── app/
│   ├── main.py              # 主程序（顶栏/导航/Snackbar）
│   ├── theme.py             # 🎨 设计令牌（颜色/间距/圆角/阴影）
│   ├── components/
│   │   └── app_card.py      # 统一卡片组件
│   ├── pages/
│   │   ├── home_page.py     # 🏠 首页（统计/进度/快捷操作）
│   │   ├── study_page.py    # 🃏 学习页（翻卡模式）
│   │   ├── review_page.py   # 🔄 复习页（艾宾浩斯调度）
│   │   ├── statistics_page.py # 📊 统计页
│   │   └── settings_page.py # ⚙️ 设置页
│   └── services/
│       ├── api_service.py   # 数据服务路由
│       └── local_db.py      # 本地数据库访问层
├── backend/
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── ebbinghaus.py        # 🧠 艾宾浩斯算法核心
│   └── import_data.py       # 数据导入脚本
├── database/words.db        # 💾 2281 词 SQLite 数据库
├── ocr/
│   └── output/
│       └── words_export_完整.json  # 单词源数据
├── requirements.txt
├── render.yaml              # ☁️ Render 部署配置
└── start.bat                # Windows 快捷启动
```

---

## 📦 数据来源

| 来源 | 状态 |
|------|------|
| 📗 上册 PDF（文字版，1327页） | ✅ 已提取，2281 词已入库 |
| 📕 下册 PDF（扫描版，375页） | 🔜 待 PaddleOCR 提取 |

每个单词包含：**音标 · 词性 · 中文释义 · 原创例句 · 记忆方法（谐音/联想/词根）· 固定搭配 · 派生词**

---

## ☁️ 部署到云端

```bash
git push origin main
```

Render 自动读取 `render.yaml` 配置：
- Python 3 + Gunicorn + Flet Web
- PostgreSQL 数据库（自动切换）
- 启动时从 JSON 自动导入单词数据

---

<div align="center">

**v2.1.0** · 2026-07-12

</div>
