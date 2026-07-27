<div align="center">

# 单词突围 · WordBreakthrough

**基于艾宾浩斯遗忘曲线的智能背词应用**  
收录《单词突围5200》上册 2281 个单词

[![Python](https://img.shields.io/badge/Python-3.13+-blue)](https://python.org)
[![Flet](https://img.shields.io/badge/Flet-0.86-green)](https://flet.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[快速开始](#快速开始) • [功能](#功能) • [使用流程](#使用流程) • [技术栈](#技术栈) • [项目结构](#项目结构) • [部署](#部署)

</div>

---

## 快速开始

```bash
pip install -r requirements.txt
python run_app.py
```

浏览器打开 **http://localhost:8551**  
手机（同 WiFi）打开 **http://192.168.3.59:8551**

首次启动自动创建数据库并导入 2281 个单词，无需额外配置。

---

## 功能

### 翻卡学习

显示英文单词 → 回想中文释义 → 点击翻转查看完整信息（音标/释义/例句/记忆方法/固定搭配/派生词）→ 自评熟悉程度。

### 艾宾浩斯自动复习

按遗忘曲线自动安排复习：

| 复习次数 | 间隔 | 说明 |
|---------|------|------|
| 第1次 | 1天 | 学习后第2天 |
| 第2次 | 2天 | 学习后第3天 |
| 第3次 | 4天 | 学习后第5天 |
| 第4次 | 7天 | 学习后第8天 |
| 第5次 | 15天 | 学习后第16天 |
| 之后 | 30天 | 长期记忆维护 |

### 三档熟悉程度

| 按钮 | 效果 |
|------|------|
| ⭐ **熟悉** | 间隔设为 60 天，近期不再出现 |
| 🔄 **模糊** | 正常艾宾浩斯递进 |
| 💪 **不记得** | 间隔重置为 1 天，当天多次出现 |

> 某天没复习不会跳过——词会"超期"，下次打开时照样出现。

### 一键发音

点击 🔊 按钮发音，支持：
- **英文** → 美式语音
- **中文** → 普通话
- **中英混合** → 自动分段依次朗读
- 单词 / 搭配 / 例句 / 记忆方法全覆盖

### 其他

- 例句翻译默认隐藏，点击展开
- 复习页固定搭配反推中文含义
- 学习记录导出为 Word 文档
- 跨设备同步（PostgreSQL 云端）
- 当日目标完成后自动停止分配新词

---

## 使用流程

```
第1天  打开App → 学习20个新词 → 系统记录
第2天  复习第1天的20个 → 再学20个新词
第3天  复习第2天的20个 → 再学20个新词
 ...
第X天  2281词全部学完 → 进入长期复习
```

每日目标可在设置页调整（默认 20 词）。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | [Flet](https://flet.dev) 0.86（基于 Flutter Web） |
| 后端 | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) |
| 数据库 | SQLite（本地）/ PostgreSQL（云端） |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org) 2.0 |
| 部署 | [Render.com](https://render.com) |
| 复习算法 | 艾宾浩斯遗忘曲线（6级间隔） |

---

## 项目结构

```
APP/
├── run_app.py                # 启动入口（含 /pronounce 发音接口）
├── app/
│   ├── main.py               # 主程序 / 导航 / 发音链接
│   ├── theme.py              # 设计系统（颜色 / 间距 / 圆角）
│   ├── components/
│   │   └── app_card.py       # 统一卡片组件
│   ├── pages/
│   │   ├── home_page.py      # 首页统计 + 快捷入口
│   │   ├── study_page.py     # 学习翻卡页
│   │   ├── review_page.py    # 复习翻卡页
│   │   ├── statistics_page.py# 统计与成就
│   │   └── settings_page.py  # 设置与导出
│   └── services/
│       ├── api_service.py    # 数据服务接口
│       └── local_db.py       # 数据库访问层
├── backend/
│   ├── models.py             # 数据模型
│   └── ebbinghaus.py         # 艾宾浩斯算法
├── database/                 # SQLite 数据库（自动生成）
├── ocr/output/               # 单词源数据 JSON
├── requirements.txt
└── README.md
```

---

## 部署

### Render

1. Fork 仓库到 GitHub
2. Render 新建 Web Service
3. 构建设置：`pip install -r requirements.txt`
4. 启动命令：`python run_app.py`
5. 可选：设置 `DATABASE_URL` 环境变量使用 PostgreSQL

### 桌面模式

```bash
python run_app.py --desktop
```

---

## License

MIT

---

<div align="center">

**v2.2.0** · 2026-07-28

</div>
