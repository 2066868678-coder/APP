# 单词突围 (Word Breakthrough)

一个帮助用户高效记忆英语单词的 Web 应用程序，支持艾宾浩斯遗忘曲线复习计划。

## 功能

- 📚 **系统化背词** — 上册收录 **2281 个核心词汇**，按 Part1-Part4 分章节
- 🧠 **智能记忆法** — 每个单词提供谐音法、联想法、词根词缀等记忆方法
- 📝 **原创例句** — 每个单词配有贴合场景的实用例句
- 🎯 **艾宾浩斯复习** — 根据遗忘曲线自动安排每日新词和复习计划
- 📱 **跨平台访问** — Web 模式可在电脑/手机上使用
- ☁️ **云端部署** — 支持 Render 一键部署，随时随地学习

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动（Web模式）
python run_app.py

# 启动（桌面窗口）
python run_app.py --desktop
```

Web 模式访问：`http://localhost:8551`

## 数据来源

单词数据来自《单词突围5200》纸质书（上册 PDF 文本提取）。

- 使用 PyMuPDF 按页面 Y 坐标排序精确提取每个单词的音标、释义、记忆方法、例句等
- 所有数据已校对入库，存储在 `database/words.db`
- 下册（扫描版 PDF）尚待 OCR 处理

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端/UI | Flet (Python) |
| 后端 | FastAPI |
| 数据库 | SQLite / PostgreSQL |
| PDF提取 | PyMuPDF |
| 部署 | Render |

## 部署到 Render

1. 将代码推送到 GitHub
2. 在 Render 中连接仓库，选择 `render.yaml` 配置
3. Render 自动部署，启动时从 JSON 导入单词数据到 PostgreSQL
4. 访问 `https://你的应用.onrender.com`

## 项目结构

```
E:\APP├── run_app.py              # 应用启动入口
├── app/                    # Flet 界面代码
│   └── main.py
├── backend/                # 后端 API + 数据模型
│   ├── main.py
│   ├── models.py
│   ├── ebbinghaus.py        # 艾宾浩斯复习算法
│   └── import_data.py
├── database/               # SQLite 数据库
│   └── words.db             # 2281 个单词数据
├── 单词书/                  # PDF 原文 + 扫描结果
│   ├── 单词突围5200 上册.pdf
│   └── 单词突围5200 下册.pdf
├── ocr/                    # PDF 提取代码
│   └── output/words_export_完整.json  # 修好的单词数据
├── fix_final.py            # 数据修复脚本
├── init_db.py              # 数据库初始化
├── requirements.txt        # 依赖列表
├── render.yaml             # Render 部署配置
└── start.bat               # Windows 快捷启动
```

## 许可证

个人学习项目
