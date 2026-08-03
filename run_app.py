#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 启动脚本
==================
用法：
  python run_app.py            # Web模式（浏览器可看）
  python run_app.py --desktop  # 桌面窗口模式

Web模式下：
  电脑浏览器: http://localhost:8550
  手机(同WiFi): http://192.168.3.59:8550
"""

import sys, os, argparse, json

# 添加项目根目录到路径
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# 检查数据库是否为空，如果是则自动导入单词
DB_URL = os.environ.get('DATABASE_URL')
if DB_URL:
    DB_URL = DB_URL.replace('postgres://', 'postgresql://')
    print(f"使用云端数据库: PostgreSQL")
else:
    DB_PATH = os.path.join(ROOT, 'database', 'words.db')
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    DB_URL = f'sqlite:///{DB_PATH}'
    print(f"使用本地数据库: {DB_PATH}")

try:
    from backend.models import init_database, Word, Base
    from sqlalchemy.orm import Session
    engine = init_database(DB_URL)
    Base.metadata.create_all(engine)
    session = Session(engine)
    word_count = session.query(Word).count()

    # 检测旧数据（新数据2281词，老数据2315或1264词）
    need_reimport = False
    if word_count > 0:
        if word_count != 2281:
            print(f"检测到旧数据（{word_count}词，正确应为2281），需要重新导入...")
            need_reimport = True

    if word_count > 0 and not need_reimport:
        print(f"数据库已有 {word_count} 个单词")
    else:
        if need_reimport:
            # 清空旧数据（包括学习记录和每日计划）
            from backend.models import StudyRecord, DailyPlan
            session.query(StudyRecord).delete()
            session.query(DailyPlan).delete()
            session.query(Word).delete()
            session.commit()
            print("已清空旧数据")
        raise ValueError("需要导入数据")
except Exception as e:
    print(f"正在导入单词数据... ({e})")
    json_path = os.path.join(ROOT, 'database', 'words_seed.json')
    if os.path.exists(json_path):
        from backend.models import init_database, Word, Base
        from sqlalchemy.orm import Session
        engine = init_database(DB_URL)
        Base.metadata.create_all(engine)
        with open(json_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)
        session = Session(engine)
        count = 0
        for item in words_data:
            word = item.get('word', '').strip()
            if not word:
                continue

            # 清理chapter字段
            chapter = item.get('chapter', '')
            if chapter and chapter[:5] in ('Part1','Part2','Part3','Part4'):
                chapter = chapter[:5]
            elif 'part' in chapter.lower():
                chapter = chapter[:5].title() if chapter[:5].lower().startswith('part') else 'part'
            else:
                chapter = chapter[:5] if chapter else 'part'

            def to_str(val):
                if isinstance(val, list): return ' | '.join(val)
                return str(val) if val else ''
            new_word = Word(
                word=word, phonetic=to_str(item.get('phonetic', '')),
                pos=to_str(item.get('pos', '')), meaning=to_str(item.get('meaning', '')),
                examples=to_str(item.get('examples', '')),
                memory_methods=to_str(item.get('memory_methods', '')),
                derivatives=to_str(item.get('derivatives', '')),
                collocations=to_str(item.get('collocations', '')),
                extensions=to_str(item.get('extensions', '')),
                chapter=chapter,
                source_page=item.get('source_page', 0),
                source_book=item.get('source_book', '单词突围5200 上册'),
            )
            session.add(new_word)
            count += 1
        session.commit()
        session.close()
        print(f"✅ 导入完成！共 {count} 个单词")
    else:
        print(f"⚠️ 找不到单词数据文件: {json_path}")

# 检查后端是否运行
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
backend_running = sock.connect_ex(('127.0.0.1', 8000)) == 0
sock.close()

if not backend_running:
    print("后端未启动，使用本地数据库模式（独立运行）")

import flet as ft
from app.main import WordBreakthroughApp


def main(page: ft.Page):
    WordBreakthroughApp(page)


def _run_web(port):
    """Web模式：自定义FastAPI服务器 + /pronounce发音接口"""
    from fastapi import FastAPI, Query
    from fastapi.responses import HTMLResponse
    import uvicorn
    import re

    # 获取Flet ASGI应用
    flet_asgi = ft.run(
        main=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port,
        export_asgi_app=True,
    )

    # 创建主应用，添加发音接口
    app = FastAPI()

    @app.get("/pronounce", response_class=HTMLResponse)
    async def pronounce(text: str = Query(...), speed: float = Query(0.9)):
        """HTML页面：按顺序朗读中英文段落，读完自动返回App"""
        # 安全转义：反斜杠、单引号、换行、回车、制表符，防止JS语法中断
        safe = (text
                .replace('\\', '\\\\')
                .replace("'", "\\'")
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t')
               )

        # 按顺序提取中英文段落：原文本中交替出现的中英文片段
        segments = re.findall(r'[a-zA-Z][a-zA-Z\'\s\-.,!?;:]*|[一-鿿]+', safe)
        segments = [s.strip() for s in segments if s.strip()]

        if not segments:
            # 纯中文（无英文）或纯英文（无中文）
            has_cn = bool(re.findall(r'[一-鿿]', safe))
            lang = 'zh-CN' if has_cn else 'en-US'
            segments = [safe]
            lang_override = lang
        else:
            lang_override = None

        # 把段落编码为 JSON 供 JS 使用（避免手动拼接字符串的转义问题）
        import json as _json
        segs_json = _json.dumps([
            {"text": seg,
             "lang": lang_override or ('zh-CN' if re.findall(r'[一-鿿]', seg) else 'en-US')}
            for seg in segments
        ])

        display_text = safe[:300]
        html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{display:flex;align-items:center;justify-content:center;min-height:100vh;
  background:#f0f4ff;font-family:-apple-system,sans-serif;padding:20px;}}
.box{{background:white;border-radius:24px;padding:32px;box-shadow:0 8px 32px rgba(0,0,0,.08);
  max-width:92%;width:460px;word-break:break-word;text-align:center;}}
.word{{font-size:24px;line-height:1.7;color:#1e293b;margin-bottom:16px;}}
.hint{{font-size:14px;color:#94a3b8;margin-bottom:24px;}}
.speed-bar{{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-bottom:16px;}}
.speed-btn{{padding:8px 16px;border:2px solid #e2e8f0;border-radius:20px;
  background:white;color:#64748b;font-size:14px;cursor:pointer;transition:all .15s;touch-action:manipulation;}}
.speed-btn.active{{border-color:#4f46e5;background:#eef2ff;color:#4f46e5;font-weight:600;}}
.speed-btn:hover{{border-color:#4f46e5;}}
.back-btn{{display:inline-block;padding:10px 28px;background:#e2e8f0;
  border:none;border-radius:20px;color:#64748b;font-size:14px;cursor:pointer;
  transition:all .15s;touch-action:manipulation;text-decoration:none;}}
.back-btn:hover{{background:#cbd5e1;}}
</style>
</head><body>
<div class="box">
<div class="word" id="displayText">{display_text}</div>
<div class="speed-bar" id="speedBar">
  <button class="speed-btn" onclick="setSpeed(0.5)">0.5x</button>
  <button class="speed-btn" onclick="setSpeed(0.75)">0.75x</button>
  <button class="speed-btn active" onclick="setSpeed(1.0)">1.0x</button>
  <button class="speed-btn" onclick="setSpeed(1.25)">1.25x</button>
  <button class="speed-btn" onclick="setSpeed(1.5)">1.5x</button>
  <button class="speed-btn" onclick="setSpeed(2.0)">2.0x</button>
</div>
<div class="hint" id="statusHint">🔊 播放中，点击倍速可调整...</div>
<button class="back-btn" onclick="goBack()">← 返回</button>
</div>
<script>
var SEGMENTS = {segs_json};
var currentRate = {speed};
var currentIdx = 0;
var isPlaying = false;
var restartTimer = null;
var wasCancelled = false;

function speakSegment(idx){{
  if(idx >= SEGMENTS.length){{ checkDone(); return; }}
  if(wasCancelled) return;
  currentIdx = idx;
  var seg = SEGMENTS[idx];
  var u = new SpeechSynthesisUtterance(seg.text);
  u.lang = seg.lang;
  u.rate = currentRate;
  u.onend = function(){{
    if(wasCancelled) return;
    speakSegment(idx + 1);
  }};
  u.onerror = function(){{
    // cancel() 触发的 onerror 忽略，交给 setSpeed 的定时器处理
  }};
  isPlaying = true;
  speechSynthesis.speak(u);
}}

function setSpeed(rate){{
  currentRate = rate;
  document.querySelectorAll('.speed-btn').forEach(function(b){{
    b.classList.toggle('active', Math.abs(parseFloat(b.textContent) - rate) < 0.01);
  }});
  if(isPlaying){{
    if(restartTimer) clearTimeout(restartTimer);
    wasCancelled = true;
    var restartAt = currentIdx;
    speechSynthesis.cancel();
    restartTimer = setTimeout(function(){{
      restartTimer = null;
      wasCancelled = false;
      speakSegment(restartAt);
    }}, 150);
  }}
}}

function checkDone(){{
  isPlaying = false;
  document.getElementById('statusHint').textContent = '✅ 播放完成';
  setTimeout(function(){{ goBack(); }}, 800);
}}

function goBack(){{
  speechSynthesis.cancel();
  window.close();
  setTimeout(function(){{ window.location.href = window.location.origin + '/'; }}, 200);
}}

// 开始播放
speakSegment(0);
</script></body></html>'''
        return html

    @app.get("/export")
    async def export_words(fmt: str = Query("docx"), days: int = Query(None),
                           dates: str = Query(None)):
        """导出学习记录文件（docx/txt），通过 Content-Disposition 触发浏览器下载。

        参数：fmt=docx|txt；days=近N天 或 dates=逗号分隔的日期(2026-08-01,2026-08-02)
        """
        from urllib.parse import quote
        from fastapi.responses import Response as FastResponse

        from app.services.local_db import get_recent_study_words, get_words_by_dates

        # 组装数据
        words_by_date = None
        if days:
            words_by_date = get_recent_study_words(days)
        elif dates:
            dlist = [d.strip() for d in dates.split(',') if d.strip()]
            if dlist:
                words_by_date = get_words_by_dates(dlist)
        if not words_by_date:
            return FastResponse("没有学习记录可导出", media_type="text/plain",
                                status_code=404)
        total = sum(len(v) for v in words_by_date.values())

        # 生成文件
        if fmt == "txt":
            from app.pages.settings_page import _generate_txt
            content, total2 = _generate_txt(words_by_date)
            data = content.encode('utf-8')
            mime = "text/plain; charset=utf-8"
            ext = "txt"
        else:
            from app.pages.settings_page import _generate_docx, _DOCX_AVAILABLE
            if not _DOCX_AVAILABLE:
                return FastResponse("缺少 python-docx 库，无法导出 Word",
                                    media_type="text/plain", status_code=500)
            data, total2 = _generate_docx(words_by_date)
            mime = ("application/vnd.openxmlformats-officedocument"
                    ".wordprocessingml.document")
            ext = "docx"

        # RFC 5987 文件名编码（支持中文文件名）
        fname = f"学习记录_{total}词.{ext}"
        ascii_fname = quote(fname)
        return FastResponse(
            content=data,
            media_type=mime,
            headers={
                "Content-Disposition": (
                    f"attachment; filename=\"records.{ext}\"; "
                    f"filename*=UTF-8''{ascii_fname}"
                )
            },
        )

    # 挂载Flet应用（放最后，避免 catch-all 拦截 /export）
    app.mount("/", flet_asgi)

    print("=" * 50)
    print("单词突围 - Web模式（含发音服务）")
    print("=" * 50)
    print()
    print("电脑浏览器访问: http://localhost:8551")
    print("手机(同WiFi): http://192.168.3.59:8551")
    print()
    print("按 Ctrl+C 停止")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='启动单词突围App')
    parser.add_argument('--desktop', action='store_true', help='桌面窗口模式')
    args = parser.parse_args()

    if args.desktop:
        ft.app(target=main)
    else:
        port = int(os.getenv("PORT", 8551))
        _run_web(port)
