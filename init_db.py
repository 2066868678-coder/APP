#!/usr/bin/env python3
"""初始化数据库并导入单词样本"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models import init_database, Word
from sqlalchemy.orm import Session

def main():
    db_path = os.path.join('E:/APP/database', 'words.db')

    # 删除旧数据库（如果存在）
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"已删除旧数据库: {db_path}")
        except PermissionError:
            print(f"无法删除旧数据库（文件被占用），尝试覆盖...")

    # 初始化新数据库
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = init_database(f'sqlite:///{db_path}')
    print(f"数据库已创建: {db_path}")

    # 导入单词数据
    json_path = 'ocr/output/words_data.json'
    if not os.path.exists(json_path):
        print(f"错误: 找不到 {json_path}")
        # 尝试从测试输出目录找
        json_path = 'ocr/output_test/words_data.json'
        if not os.path.exists(json_path):
            print("也没有找到测试输出")
            return

    with open(json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    session = Session(engine)
    count = 0
    for item in words_data:
        word = item.get('word', '').strip().lower()
        if not word or len(word) < 2:
            continue

        def to_str(val):
            if isinstance(val, list):
                return ' | '.join(val)
            return str(val) if val else ''

        new_word = Word(
            word=word,
            phonetic=to_str(item.get('phonetic', '')),
            pos=to_str(item.get('pos', '')),
            meaning=to_str(item.get('meaning', '')),
            examples=to_str(item.get('examples', '')),
            memory_methods=to_str(item.get('memory_methods', '')),
            derivatives=to_str(item.get('derivatives', '')),
            collocations=to_str(item.get('collocations', '')),
            extensions=to_str(item.get('extensions', '')),
            chapter=item.get('chapter', ''),
            source_page=item.get('source_page', 0),
            source_book=item.get('source_book', '单词突围5200'),
        )
        session.add(new_word)
        count += 1

    session.commit()
    session.close()
    print(f"\n导入完成！共 {count} 个单词")

    # 验证
    session2 = Session(engine)
    total = session2.query(Word).count()
    print(f"数据库中总计: {total} 个单词")
    sample = session2.query(Word).limit(5).all()
    for w in sample:
        print(f"  {w.word} - {w.meaning[:30] if w.meaning else '(空)'}")
    session2.close()

if __name__ == '__main__':
    main()
