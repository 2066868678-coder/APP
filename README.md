# 单词突围 (Word Breakthrough)

基于《单词突围5200》的智能英语单词学习应用，Web/桌面双模式，无需后端，即开即用。

## 功能

- **2281 单词** — 上册完整收录，书本原序，全部数据已校对
- **翻卡学习** — 正面英文 → 回想 → 翻转查看释义/例句/记忆方法/搭配
- **艾宾浩斯复习** — 自动调度遗忘曲线：1天→3天→7天→15天→30天
- **进度追踪** — 学习统计、掌握程度、成就徽章、连续学习天数
- **本地优先** — 直接读写 SQLite，零配置零依赖零后端
- **跨平台** — Web 浏览器 + 桌面窗口，手机同 WiFi 可访问

## 快速启动

```bash
pip install -r requirements.txt
python run_app.py
```

浏览器打开 `http://localhost:8551`

## UI 设计

2026-07 全面 UI 美化，Teal 主题色 + 统一设计系统：

- `app/theme.py` — 设计令牌（颜色/间距/圆角/阴影）
- `app/components/app_card.py` — 统一卡片组件
- 顶栏底部圆角 + 漂浮圆角 Snackbar
- 学习卡：顶部装饰色条 + 音标胶囊 + 左边缘色条 section
- 首页：2×2 统计网格 + 环形进度 + 大图标快捷按钮

## 技术栈

| 组件 | 技术 |
|------|------|
| UI 框架 | Flet (Material 3) |
| 数据库 | SQLite / PostgreSQL |
| 部署 | Render (+ UptimeRobot 保活) |
| OCR | PyMuPDF (上册) / PaddleOCR (下册待提取) |

## 项目结构

```
E:\APP
├── run_app.py              # 启动入口
├── app/
│   ├── main.py             # Flet 主程序 (顶栏/导航/Snackbar)
│   ├── theme.py            # 设计令牌系统
│   ├── components/
│   │   └── app_card.py     # 统一卡片组件
│   ├── pages/
│   │   ├── home_page.py    # 首页 (统计/进度/快捷操作)
│   │   ├── study_page.py   # 学习页 (翻卡)
│   │   ├── review_page.py  # 复习页 (翻卡)
│   │   ├── statistics_page.py # 统计页
│   │   └── settings_page.py   # 设置页
│   └── services/
│       ├── api_service.py  # API 路由
│       └── local_db.py     # 本地数据库访问
├── backend/
│   ├── models.py           # 数据模型
│   ├── ebbinghaus.py       # 艾宾浩斯算法
│   └── import_data.py      # 数据导入
├── database/words.db       # 2281 词 SQLite 数据库
├── ocr/output/words_export_完整.json
├── requirements.txt
├── render.yaml
└── start.bat
```

## 数据来源

《单词突围5200》上册 PDF 提取，2281 词，含音标/释义/词性/例句/记忆方法/固定搭配/派生词。
下册（扫描版 375 页）待 PaddleOCR 提取。

## 部署

推送到 GitHub 后 Render 自动部署：

```bash
git push origin main
```

Render `render.yaml` 配置：Python 3 + Gunicorn + Flet Web，启动时自动从 JSON 导入数据至 PostgreSQL。
