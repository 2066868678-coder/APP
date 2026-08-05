<div align="center">

# 单词突围 · WordBreakthrough

**基于艾宾浩斯遗忘曲线的智能背词应用**  
收录《单词突围5200》上册 2281 个单词

[![Python](https://img.shields.io/badge/Python-3.13+-blue)](https://python.org)
[![Flet](https://img.shields.io/badge/Flet-0.26+-green)](https://flet.dev)

[快速开始](#快速开始) • [功能](#功能) • [使用流程](#使用流程) • [项目结构](#项目结构)

</div>

---

## 快速开始

### 📱 手机使用（主要方式）
手机浏览器直接访问部署网址即可，无需安装、无需配置。

### 💻 电脑本地运行
```bash
pip install -r requirements.txt
python run_app.py
```
- 电脑浏览器打开 **http://localhost:8551**
- 手机（同 WiFi）打开 **http://192.168.3.59:8551**

首次启动自动创建数据库并导入 2281 个单词，无需额外配置。**无需启动后端服务。**

---

## 功能

### 翻卡学习
显示英文 → 回想释义 → 点击翻转查看详情（音标/释义/例句/记忆方法/搭配/派生词）→ 三档自评。

### 艾宾浩斯自动复习
| 复习次数 | 间隔 |
|---------|------|
| 第1次 | 1天 |
| 第2次 | 2天 |
| 第3次 | 4天 |
| 第4次 | 7天 |
| 第5次 | 15天 |
| 之后 | 30天 |

### 三档熟悉程度
| 按钮 | 效果 |
|------|------|
| ⭐ **熟悉** | 间隔 60 天，近期不出现 |
| 🔄 **模糊** | 正常艾宾浩斯递进 |
| 💪 **不记得** | 重置为 1 天，当天多次出现 |

### 发音（倍速可调）
点击 🔊 自动分段朗读中英文，支持 **0.5x~2.0x 倍速**，播放中随时切换。

### 其他
- 例句翻译默认隐藏，点击展开
- 复习页固定搭配反推中文含义
- 学习记录导出为 Word 文档
- Deep Focus 靛蓝主题设计系统

---

## 使用流程

```
第1天  打开App → 学习20个新词
第2天  复习第1天 → 学20个新词
第3天  复习第2天 → 学20个新词
 ...
第X天  2281词学完 → 长期复习
```

每日目标可在设置页调整（默认 20 词）。

---

## 项目结构

```
APP/
├── run_app.py                # 启动入口（含 /pronounce 发音+倍速）
├── start.bat                 # Windows 双击启动
├── app/
│   ├── main.py               # 主程序 / 导航 / 发音链接
│   ├── theme.py              # Deep Focus 设计令牌
│   ├── components/
│   │   └── app_card.py       # 统一卡片组件
│   ├── pages/
│   │   ├── home_page.py      # 首页
│   │   ├── study_page.py     # 学习翻卡
│   │   ├── review_page.py    # 复习翻卡
│   │   ├── statistics_page.py# 统计与成就
│   │   └── settings_page.py  # 设置与导出
│   └── services/
│       ├── api_service.py    # 数据接口
│       └── local_db.py       # 数据库访问（核心）
├── backend/
│   ├── models.py             # 数据模型
│   └── ebbinghaus.py         # 艾宾浩斯算法
└── database/words.db         # SQLite 数据库
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| UI | Flet 0.26+（Flutter Web） |
| 数据库 | SQLite（本地，无后端模式） |
| ORM | SQLAlchemy 2.0 |
| 发音 | 浏览器 SpeechSynthesis API |
| 复习算法 | 艾宾浩斯遗忘曲线（6级间隔） |

---

<div align="center">

**v2.4.0**

</div>
