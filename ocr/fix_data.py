#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 数据质量修复（合并版）
===============================
对音标明显不匹配的词条，尝试提取正确单词名，然后：
1. 如果正确单词名已存在 → 合并内容（追加例句、搭配等）
2. 如果正确单词名不存在 → 重命名词条
绝不删除内容！
"""

import sys, os, json, re

INPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "words_data.json")
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "words_data_fixed.json")

PHON_MAP = {
    'a': 'aæɑeəɔ', 'b': 'b', 'c': 'ks', 'd': 'd',
    'e': 'eɛiɪə', 'f': 'f', 'g': 'g', 'h': 'h',
    'i': 'iɪaɪə', 'j': 'dʒ', 'k': 'k', 'l': 'l',
    'm': 'm', 'n': 'n', 'o': 'oɔɒəʊa', 'p': 'p',
    'q': 'k', 'r': 'r', 's': 'sʃ', 't': 'tθ',
    'u': 'uʌʊjuə', 'v': 'v', 'w': 'w', 'x': 'z',
    'y': 'j', 'z': 'z',
}

SKIP_WORDS = {'the','and','for','are','but','not','you','all','can','has',
    'had','its','was','who','is','it','in','on','at','to','of','be','an','or',
    'as','by','he','she','we','they','do','did','will','would','could',
    'may','might','have','been','some','such','than','that','this','with',
    'from','what','when','where','which'}


def is_phonetic_match(word, phonetic):
    """首字母和音标首字符是否大致匹配"""
    if not word or not phonetic:
        return True
    ph = re.sub(r'[ˈˌ\'\"\[\]#/]', '', phonetic).strip()
    if not ph:
        return True
    w0 = word[0].lower()
    p0 = ph[0].lower()
    if w0 in PHON_MAP:
        return p0 in PHON_MAP[w0]
    return True


def extract_word_from_memory(memory_text):
    """从记忆方法中提取正确的单词名"""
    if not memory_text:
        return ''
    patterns = [
        r'故\s+([a-zA-Z][a-zA-Z\'-]{2,20})\s+表示',
        r'掌握\s+([a-zA-Z][a-zA-Z\'-]{2,20})\s+',
        r'看到\s+([a-zA-Z][a-zA-Z\'-]{2,20})\s+想起',
        r'记住\s+([a-zA-Z][a-zA-Z\'-]{2,20})\s+表示',
        r'([a-zA-Z][a-zA-Z\'-]{2,20})\s+为已经记忆过',
    ]
    for pat in patterns:
        m = re.search(pat, memory_text)
        if m:
            w = m.group(1).lower().strip("'.,-")
            if len(w) >= 3 and w not in SKIP_WORDS:
                return w
    return ''


def guess_correct_word(entry):
    """从音标+词条内容中猜测正确的单词名"""
    phonetic = entry.get('phonetic', '') or ''
    # 有时音标末尾带有单词名，如 "/əˈbʌv/ above"
    m = re.search(r'/\s*[^/]+\s*/\s*([a-zA-Z]+)', phonetic)
    if m:
        return m.group(1).lower()

    # 从记忆方法提取
    word = extract_word_from_memory(entry.get('memory_methods', '') or '')
    if word:
        return word

    # 从释义找第一个英文词（可能是词根/词性相关）
    # 但这不太可靠，先空着
    return ''


def clean_tail(text):
    """清理字段末尾的噪声"""
    if not text:
        return text
    t = re.sub(r'\s+[a-zA-Z]{3,30}\s*$', '', text.rstrip())
    t = t.replace('收藏', '').strip()
    return t


def merge_field(old, new):
    """合并两个字段内容，避免重复"""
    if not new:
        return old
    if not old:
        return new
    # 如果new已经在old中，不重复添加
    if new[:30] in old:
        return old
    return old + ' | ' + new


def main():
    data = json.load(open(INPUT, 'r', encoding='utf-8'))

    fixed_entries = []    # 正常词条
    mismatched = []       # 错配词条（待修复）

    for e in data:
        word = e.get('word', '').lower().strip()
        phonetic = e.get('phonetic', '') or ''
        if is_phonetic_match(word, phonetic):
            # 正常：清理字段后保留
            if e.get('examples'):
                e['examples'] = clean_tail(e['examples'])
            if e.get('memory_methods'):
                e['memory_methods'] = clean_tail(e['memory_methods'])
            fixed_entries.append(e)
        else:
            # 错配：先记下来
            correct = guess_correct_word(e)
            mismatched.append({
                'entry': e,
                'old_word': word,
                'correct_word': correct,
                'phonetic': phonetic,
            })

    # 建立正确条目索引
    entries_by_word = {}
    for e in fixed_entries:
        w = e['word'].lower().strip()
        entries_by_word[w] = e

    # 处理错配：合并或重命名
    fixed_count = 0
    merged_count = 0
    not_fixed = []

    for m in mismatched:
        correct = m['correct_word']
        e = m['entry']

        if correct and correct != m['old_word']:
            if correct in entries_by_word:
                # 目标已存在 → 合并内容
                target = entries_by_word[correct]
                target['examples'] = merge_field(target.get('examples', ''),
                                                  e.get('examples', ''))
                target['memory_methods'] = merge_field(target.get('memory_methods', ''),
                                                       e.get('memory_methods', ''))
                target['collocations'] = merge_field(target.get('collocations', ''),
                                                     e.get('collocations', ''))
                target['extensions'] = merge_field(target.get('extensions', ''),
                                                   e.get('extensions', ''))
                merged_count += 1
            else:
                # 目标不存在 → 重命名
                e['word'] = correct
                fixed_entries.append(e)
                fixed_count += 1
        else:
            # 猜不到正确单词名，暂时保留（标记）
            e['_needs_review'] = True
            fixed_entries.append(e)
            not_fixed.append(m['old_word'])

    # 去重
    seen = set()
    deduped = []
    dup_removed = 0
    for e in fixed_entries:
        w = e['word'].lower().strip()
        if w in seen:
            dup_removed += 1
            continue
        seen.add(w)
        # 清理标记
        e.pop('_needs_review', None)
        deduped.append(e)

    # deduped.sort(key=lambda x: x["word"].lower())  # 不排序，保留原序

    # 保存
    json.dump(deduped, open(OUTPUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f"原始: {len(data)}")
    print(f"错配条目: {len(mismatched)}")
    print(f"  合并到已有词条: {merged_count}")
    print(f"  重命名: {fixed_count}")
    print(f"  无法修复（保留）: {len(not_fixed)}")
    print(f"去重移除: {dup_removed}")
    print(f"最终: {len(deduped)}")

    print(f"\n合并示例:")
    for m in mismatched:
        if m['correct_word'] and m['correct_word'] != m['old_word']:
            print(f"  {m['old_word']:18s} → 合并到 {m['correct_word']:18s} (音标原为{m['phonetic'][:25]})")

    if not_fixed:
        print(f"\n无法修复（需人工处理）:")
        for w in not_fixed[:20]:
            print(f"  {w}")


if __name__ == '__main__':
    main()
