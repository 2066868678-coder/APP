#!/usr/bin/env python3
"""
最终修复：按Y坐标排序提取单词
PDF文本块的返回顺序是创建顺序（随机），但Y坐标反映视觉位置
规律：单词标题块（Y值小）始终在音标块（Y值大）的上面
全局处理解决跨页问题（单词标题在page N，音标在page N+1）
"""
import json, re, os, fitz

ROOT = r'E:\APP'
PDF_PATH = os.path.join(ROOT, '单词书', '单词突围5200 上册.pdf')
JSON_PATH = os.path.join(ROOT, 'ocr', 'output', 'words_export_完整.json')
DB_PATH = os.path.join(ROOT, 'database', 'words.db')

def main():
    print('=' * 60)
    print('最终修复：Y坐标排序法（全局版）')
    print('=' * 60)

    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f'总页数: {total_pages}')

    FILTER = {'the','and','for','are','not','but','all','can','has','had',
              'was','were','did','does','been','some','than','that','this',
              'with','from','they','have','what','when','where','which',
              'their','them','these','those','about','would','could','should',
              'there','part','parts','into','over','also','each','many','more',
              'much','most','such','only','other','very','just','then','said'}
    PART_RE = re.compile(r'^(Part\s*\d+)', re.IGNORECASE)
    POS_RE = re.compile(r'^(v\.|vi\.|vt\.|n\.|adj\.|adv\.|pron\.|prep\.|conj\.|int\.|art\.|num\.|aux\.|a\.|ad\.)')
    WORD_RE = re.compile(r'^[a-zA-Z][a-zA-Z\-\']{2,25}$')

    current_part = ''
    all_blocks = []

    for pg in range(total_pages):
        page = doc[pg]
        blocks = page.get_text('dict')['blocks']
        for block in blocks:
            if block['type'] != 0: continue
            bbox = block['bbox']
            for line in block['lines']:
                lt = ''
                for span in line['spans']:
                    st = span['text']
                    # 跳过单独的j标记（PDF强调标记），替换为空格
                    if st.strip() == 'j': lt += ' '; continue
                    # jtextj → text（去包裹型标记）
                    if len(st) >= 2 and st[0] == 'j' and st[-1] == 'j':
                        st = st[1:-1]
                    lt += st
                lt = lt.strip()
                if not lt: continue

                clean = lt
                for code in range(0x01, 0x09): clean = clean.replace(chr(code), ' ')
                for code in range(0x0b, 0x0d): clean = clean.replace(chr(code), ' ')
                for code in range(0x0e, 0x20): clean = clean.replace(chr(code), ' ')
                clean = clean.replace('\x0b', ' ').replace('\x0c', ' ')
                clean = clean.replace('￼', '')
                # 清理残余的j标记（不影响单词中的j字母如enjoy）
                clean = re.sub(r'j(?![a-zA-Z])', ' ', clean)
                clean = re.sub(r'\s+', ' ', clean).strip()

                if clean in ('目录', '前言', '单词突围', 'Word Breakthrough', '收藏', ''): continue
                if re.match(r'^\d+$', clean) or re.match(r'^-\s*\d+\s*-$', clean): continue
                if PART_RE.match(clean): current_part = clean[:5]

                all_blocks.append({
                    'clean': clean, 'y': bbox[1], 'page': pg + 1,
                    'is_phonetic': '音标' in clean and ('：' in clean or ':' in clean),
                    'is_standalone': bool(WORD_RE.match(clean)) and clean.lower() not in FILTER,
                    'part': current_part,
                })

    doc.close()
    print(f'总文本块: {len(all_blocks)}')

    # 全局排序：(page, y)
    all_blocks.sort(key=lambda x: (x['page'], x['y']))

    phon_indices = [i for i, b in enumerate(all_blocks) if b['is_phonetic']]
    print(f'音标块: {len(phon_indices)}')

    # 分配单词：每个音标找前面最近且未使用的独立英文词
    used_words = set()
    raw_entries = []

    for idx, pi in enumerate(phon_indices):
        word = ''
        for j in range(pi - 1, -1, -1):
            if all_blocks[j]['is_phonetic']:
                break  # 越过上一个音标就不找了
            if all_blocks[j]['is_standalone']:
                w = all_blocks[j]['clean'].lower().strip()
                if w not in used_words:
                    word = w
                    used_words.add(w)
                    break

        start = pi
        end = phon_indices[idx + 1] if idx + 1 < len(phon_indices) else len(all_blocks)
        content = ' '.join(all_blocks[k]['clean'] for k in range(start, end))

        raw_entries.append({
            'word': word, 'content': content,
            'page': all_blocks[pi]['page'], 'part': all_blocks[pi]['part'],
        })

    print(f'条目: {len(raw_entries)}')

    # 解析每个条目的内容字段
    results = []
    for entry in raw_entries:
        word = entry['word']
        if not word or len(word) < 2: continue

        content = entry['content']

        # 音标
        phonetic = ''
        m = re.search(r'音标[：:]\s*(.+?)(?=\s*释义|音标|$)', content)
        if m: phonetic = m.group(1).strip()

        # 释义
        pos = ''; meaning = ''
        m = re.search(r'释义[：:]\s*(.+?)(?=\s*带你背|词根词缀|例句|常见搭配|词汇扩充|词义辨析|收藏|$)', content)
        if m:
            mt = m.group(1).strip()
            pm = POS_RE.match(mt)
            if pm: pos = pm.group(1); meaning = mt[pm.end():].strip()
            else: meaning = mt

        # 记忆方法
        mem = ''
        m = re.search(r'带你背[：:]\s*(.*?)(?=\s*词根词缀|例句|常见搭配|词汇扩充|词义辨析|收藏|$)', content)
        if m:
            mm = m.group(1).strip()
            mem = '（熟悉单词，无需额外记忆方法）' if ('属于熟悉单词' in mm or mm in ('略','略；')) else mm

        # 词根词缀积累
        m = re.search(r'词根词缀积累[：:]\s*(.+?)(?=\s*巧记|例句|常见搭配|词汇扩充|词义辨析|收藏|$)', content)
        if m:
            rt = m.group(1).strip()
            qm = re.search(r'巧记[：:]\s*(.+?)(?=\s*例句|常见搭配|词汇扩充|词义辨析|收藏|$)', content)
            if qm: rt += ' | 巧记：' + qm.group(1).strip()
            if mem and len(rt) > 5: mem += ' | 词根分析：' + rt
            elif len(rt) > 5: mem = rt

        # 例句
        examples = ''
        m = re.search(r'例句[：:]\s*(.*?)(?=\s*常见搭配|词汇扩充|词义辨析|收藏|$)', content)
        if m: examples = m.group(1).strip()

        # 搭配
        collocations = ''
        m = re.search(r'常见搭配[：:]\s*(.*?)(?=\s*词汇扩充|词义辨析|收藏|$)', content)
        if m: collocations = m.group(1).strip()

        # 扩充
        extensions = ''
        m = re.search(r'词汇扩充[：:]\s*(.*?)(?=\s*词义辨析|收藏|$)', content)
        if m: extensions = m.group(1).strip()
        m = re.search(r'词义辨析[：:]\s*(.*?)$', content)
        if m:
            dt = m.group(1).strip()
            extensions = (extensions + ' | 词义辨析：' + dt) if extensions else ('词义辨析：' + dt)

        # 统一清理
        for fname in [('phonetic',phonetic),('pos',pos),('meaning',meaning),('mem',mem),('examples',examples),('collocations',collocations),('extensions',extensions)]:
            val = fname[1]
            val = val.replace('收藏','').strip()
            val = re.sub(r'\s+',' ',val).strip().rstrip(';；')
            if fname[0] == 'phonetic': phonetic = val
            elif fname[0] == 'pos': pos = val
            elif fname[0] == 'meaning': meaning = val
            elif fname[0] == 'mem': mem = val
            elif fname[0] == 'examples': examples = val
            elif fname[0] == 'collocations': collocations = val
            elif fname[0] == 'extensions': extensions = val

        results.append({
            'word': word.rstrip('.').rstrip(','),
            'phonetic': phonetic, 'pos': pos, 'meaning': meaning,
            'examples': examples, 'memory_methods': mem, 'derivatives': '',
            'collocations': collocations, 'extensions': extensions,
            'chapter': entry['part'],
            'source_page': entry['page'],
            'source_book': '单词突围5200 上册',
        })

    print(f'提取到: {len(results)}')

    # 去重
    seen = set()
    unique = []
    for r in results:
        wk = r['word']
        if wk and wk not in seen:
            seen.add(wk)
            unique.append(r)
    print(f'去重后: {len(unique)}')

    # 预览前20
    print('\n前20:')
    for i in range(min(20, len(unique))):
        w = unique[i]
        print(f'  [{i:3d}] {w["word"]:20s} | {w["pos"]:4s} | {str(w["meaning"])[:60]}')

    # 检查常见问题词
    for cw in ['specialist','photo','tragedy','good','play','courtyard','moody','catastrophe','depiction','graphic','funding','benefit']:
        for r in unique:
            if r['word'] == cw:
                print(f'  {cw:15s} 音标={r["phonetic"]:25s} 释义={str(r["meaning"])[:50]}')
                break

    # 保存
    if os.path.exists(JSON_PATH):
        import shutil
        shutil.copy2(JSON_PATH, JSON_PATH + '.bak')
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f'\nJSON已保存')

    # 更新DB
    print(f'更新数据库...')
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM study_records')
    cur.execute('DELETE FROM daily_plans')
    cur.execute('DELETE FROM words')
    for item in unique:
        def ts(v):
            if isinstance(v, list): return ' | '.join(v)
            return str(v) if v else ''
        ch = item['chapter']
        cur.execute('''INSERT INTO words (word,phonetic,pos,meaning,examples,memory_methods,
            derivatives,collocations,extensions,chapter,source_page,source_book,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            item['word'], ts(item['phonetic']), ts(item['pos']),
            ts(item['meaning']), ts(item['examples']),
            ts(item['memory_methods']), '',
            ts(item['collocations']), ts(item['extensions']),
            ch, item['source_page'], item['source_book'], 1.0))
    conn.commit()
    conn.close()
    print(f'DB更新: {len(unique)} 词')

    print(f'\n完成！')

if __name__ == '__main__':
    main()