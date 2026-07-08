#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 数据导入工具
=======================
将 OCR/PDF 提取的 JSON 数据导入 SQLite 数据库。

使用方法：
    python backend/import_data.py                         # 默认导入上册
    python backend/import_data.py --file ocr/output/words_data.json
    python backend/import_data.py --file 单词书/下册_提取结果.json --book 下册
"""

import sys, os, json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import import_words_from_json, app, engine, Word, Session
from sqlalchemy import func


def main():
    import argparse
    parser = argparse.ArgumentParser(description='导入单词数据到数据库')
    parser.add_argument('--file', default='ocr/output/words_data.json',
                        help='JSON数据文件路径')
    parser.add_argument('--book', default='上册',
                        help='来源书名标记')
    args = parser.parse_args()

    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        args.file
    )

    if not os.path.exists(json_path):
        print(f"❌ 文件不存在: {json_path}")
        sys.exit(1)

    print(f"📖 导入来源: {args.book}")
    print(f"📄 数据文件: {json_path}")

    # 检查现有数据
    session = Session(engine)
    existing = session.query(func.count(Word.id)).scalar() or 0
    session.close()
    print(f"📊 数据库中已有: {existing} 个单词")

    # 导入
    count = import_words_from_json(json_path)
    print(f"✅ 成功导入: {count} 个新单词")

    # 导入后统计
    session = Session(engine)
    total = session.query(func.count(Word.id)).scalar() or 0
    session.close()
    print(f"📊 数据库总计: {total} 个单词")


if __name__ == '__main__':
    main()
