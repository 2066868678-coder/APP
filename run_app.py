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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='启动单词突围App')
    parser.add_argument('--desktop', action='store_true', help='桌面窗口模式')
    args = parser.parse_args()

    if args.desktop:
        ft.app(target=main)
    else:
        print("=" * 50)
        print("单词突围 - Web模式")
        print("=" * 50)
        print()
        print("电脑浏览器访问: http://localhost:8551")
        print("手机(同WiFi) : http://192.168.3.59:8551")
        print()
        print("按 Ctrl+C 停止")
        print("=" * 50)
        port = int(os.getenv("PORT", 8551))
        ft.run(main=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
