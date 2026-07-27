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
    json_path = os.path.join(ROOT, 'ocr/output/words_export_完整.json')
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
    async def pronounce(text: str = Query(...)):
        """HTML页面：分离中英文分别朗读，读完自动返回App"""
        safe = text.replace('\\', '\\\\').replace("'", "\\'")

        # 分离英文和中文
        eng = re.sub(r'[一-鿿]+', '', safe).strip()
        chn = ''.join(re.findall(r'[一-鿿]+', safe))

        js_parts = []
        if eng:
            js_parts.append(f"""
total++;
var u1=new SpeechSynthesisUtterance('{eng}');
u1.lang='en-US';u1.rate=0.9;u1.onend=checkDone;speechSynthesis.speak(u1);""")
        if chn:
            js_parts.append(f"""
total++;
var u2=new SpeechSynthesisUtterance('{chn}');
u2.lang='zh-CN';u2.rate=0.9;u2.onend=checkDone;speechSynthesis.speak(u2);""")

        speech_js = '\n'.join(js_parts)

        display_text = safe[:300]
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh;
  background:#f5f5f5;font-family:sans-serif;padding:20px;box-sizing:border-box;}}
.box{{background:white;border-radius:20px;padding:40px;box-shadow:0 4px 24px rgba(0,0,0,.1);
  max-width:90%;word-break:break-word;}}
.word{{font-size:28px;line-height:1.6;color:#333;text-align:center;}}
.hint{{margin-top:20px;font-size:14px;color:#999;text-align:center;}}
</style>
</head><body>
<div class="box">
<div class="word">{display_text}</div>
<div class="hint">🔊 播放中，读完后自动返回...</div>
</div>
<script>
var done=0,total=0;
function checkDone(){{done++;if(done>=total){{
  window.close();
  setTimeout(function(){{window.location.href=window.location.origin+'/';}},200);
}}}}
{speech_js}
</script></body></html>"""
        return html

    # 挂载Flet应用
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
