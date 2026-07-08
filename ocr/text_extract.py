0   #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - PDF文本提取脚本（精确版）
======================================
直接从PDF文本层提取单词数据，比OCR精确得多。
《单词突围5200》书的格式非常统一，每条单词包含：
  音标、释义、带你背（记忆方法）、例句、常见搭配、词汇扩充等

使用方法：
  python ocr/text_extract.py                    # 提取所有PDF
  python ocr/text_extract.py --pages 1-50       # 只提取前50页（测试用）
  python ocr/text_extract.py --pdf "上册"        # 只提取上册

输出文件：
  - ocr/output/words_data.json   → 完整单词数据
  - ocr/output/words_data.csv    → Excel可打开的CSV
  - ocr/output/extract_stats.json → 提取统计
"""

import os
import sys
import json
import csv
import re
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

# ============================================================
# 配置
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(PROJECT_ROOT, "单词书")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# ============================================================
# 日志
# ============================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
console = logging.StreamHandler(sys.stdout)
console.setFormatter(fmt)
logger.addHandler(console)

os.makedirs(OUTPUT_DIR, exist_ok=True)
file_handler = logging.FileHandler(
    os.path.join(OUTPUT_DIR, 'extract_progress.log'),
    encoding='utf-8', mode='a'
)
file_handler.setFormatter(fmt)
logger.addHandler(file_handler)


# ============================================================
# PDF 文本提取
# ============================================================

def extract_text_from_pdf(pdf_path, start_page=0, end_page=None):
    """
    使用 PyMuPDF 提取 PDF 文本内容。
    返回 list[dict]: {page_num, text_lines}
    """
    try:
        import fitz
    except ImportError:
        logger.error("请先安装 PyMuPDF: pip install pymupdf")
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    if end_page is None:
        end_page = total_pages

    logger.info(f"PDF总页数: {total_pages}，提取范围: {start_page+1}-{min(end_page, total_pages)}")

    pages_text = []
    for i in range(start_page, min(end_page, total_pages)):
        page = doc[i]
        raw_text = page.get_text()

        # 按行分割，过滤空行
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

        pages_text.append({
            'page_num': i + 1,
            'lines': lines,
            'raw_text': raw_text,
        })

        if (i - start_page + 1) % 100 == 0:
            logger.info(f"  已提取 {i - start_page + 1} 页...")

    doc.close()
    logger.info(f"文本提取完成，共 {len(pages_text)} 页")
    return pages_text


# ============================================================
# 文本清洗
# ============================================================

def clean_text(text):
    """
    清洗文本中的噪声字符。
    《单词突围》PDF 的文本层有一些特殊格式字符：
    - 单词周围常被特殊字符包围：jwordj, word, word, word
    - 这些字符是 PDF 格式标记在提取时被保留的
    - 控制字符 \x01-\x1f（除了TAB/LF/CR）在PDF中是英文词之间的分隔符
    """
    if not text:
        return ''

    # PDF中控制字符（\x01-\x08, \x0e-\x1f, 不含TAB/LF/CR）是英文词之间的分隔符
    # 必须全部替换为空格，不是删除！
    for code in range(0x01, 0x09):  # \x01-\x08
        text = text.replace(chr(code), ' ')
    for code in range(0x0e, 0x20):  # \x0e-\x1f
        text = text.replace(chr(code), ' ')
    # \x0b (VT) 和 \x0c (FF) 也是分隔符
    text = text.replace('\x0b', ' ')
    text = text.replace('\x0c', ' ')
    # 对应的可见形式
    text = text.replace('', ' ')  # \x0c
    text = text.replace('', ' ')  # \x0b
    text = text.replace('', ' ')
    text = text.replace('￼', '')

    # j 是英文词边界标记 → 替换为空格
    text = text.replace('j', ' ')

    # 清理多余空格
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


def clean_line(line):
    """清洗单行文本"""
    return clean_text(line)


def is_page_number(text):
    """判断是否为页码"""
    return bool(re.match(r'^\d+$', text.strip())) or bool(re.match(r'^-\s*\d+\s*-$', text.strip()))


# ============================================================
# 单词条目解析器
# ============================================================

class WordEntryParser:
    """
    解析《单词突围5200》的结构化单词条目。

    书的标准格式：
        单词
        音标：/xxx/
        释义：xxx
        带你背：
            xxx（详细的记忆方法）
        词根词缀积累：（可选）
            xxx
        巧记：（可选，嵌套在词根词缀积累中）
        例句：xxx
        常见搭配：xxx（可选）
        词汇扩充：xxx（可选）
        词义辨析：xxx（可选）
        收藏

    为了鲁棒性，使用 音标： 作为条目的主要分隔符。
    """

    # 章节/Part标题模式
    PART_PATTERNS = [
        r'^Part\s*\d+', r'^第[一二三四五六七八九十百千]+[章节部]',
        r'^[Ll]esson\s*\d+', r'^[Uu]nit\s*\d+', r'^[Cc]hapter\s*\d+',
    ]

    # 需要跳过的行
    SKIP_LINES = [
        '收藏', '目录', '前言', '单词突围', 'Word Breakthrough',
    ]

    # 词性标记
    POS_TAGS = [
        'v.', 'vi.', 'vt.', 'n.', 'adj.', 'adv.', 'pron.', 'prep.',
        'conj.', 'int.', 'art.', 'num.', 'aux.', 'modal.',
        'a.', 'ad.', 'prep', 'conj',
        '及物动词', '不及物动词', '名词', '形容词', '副词',
        '介词', '连词', '感叹词', '代词', '数词', '冠词',
        '动词', '名', '形', '副', '介', '连',
    ]

    def __init__(self):
        self.current_part = ""
        self.pages_text = []

    def parse_all_pages(self, pages_text):
        """解析所有页面，提取单词条目"""
        self.pages_text = pages_text

        # 第一步：将所有文本连接成带页码标记的文本流
        full_text_flow = self._build_text_flow(pages_text)

        # 第二步：用 音标： 分割出单词条目
        raw_entries = self._split_into_entries(full_text_flow)

        # 第三步：解析每个条目
        parsed_entries = []
        for raw in raw_entries:
            entry = self._parse_single_entry(raw)
            if entry and entry.get('word'):
                parsed_entries.append(entry)

        logger.info(f"解析完成：共 {len(parsed_entries)} 个单词条目")
        return parsed_entries

    def _build_text_flow(self, pages_text):
        """
        构建带页码标记的文本流，每行一个 dict:
        {text, page_num, line_idx}
        """
        flow = []
        for page in pages_text:
            pn = page['page_num']
            for idx, line in enumerate(page['lines']):
                cleaned = clean_line(line)
                if cleaned:
                    flow.append({
                        'text': cleaned,
                        'page_num': pn,
                        'line_idx': idx,
                    })

        logger.info(f"文本流共 {len(flow)} 行")
        return flow

    def _split_into_entries(self, flow):
        """
        使用 音标： 作为主分隔符分割条目。
        一条完整的条目 = 从上一个 音标 之前到下一个 音标 之前的所有文本。
        """
        entries_raw = []
        current_lines = []

        for item in flow:
            text = item['text']

            # 跳过Part标题
            if self._is_part_header(text):
                self.current_part = text
                continue

            # 跳过纯跳过词
            if text in self.SKIP_LINES:
                continue

            if text.startswith('音标：'):
                if current_lines:
                    entries_raw.append(current_lines)
                current_lines = [item]
            else:
                if current_lines:
                    current_lines.append(item)

        # 最后一个条目
        if current_lines:
            entries_raw.append(current_lines)

        logger.info(f"按音标分割得到 {len(entries_raw)} 个原始条目")
        return entries_raw

    def _is_part_header(self, text):
        """判断是否为Part标题"""
        text = text.strip()
        for pat in self.PART_PATTERNS:
            if re.match(pat, text):
                return True
        return False

    def _parse_single_entry(self, lines):
        """解析单个单词条目的所有行，提取结构化字段"""
        if not lines:
            return None

        entry = {
            'word': '',
            'phonetic': '',
            'pos': '',
            'meaning': '',
            'examples': '',
            'memory_methods': '',
            'derivatives': '',
            'collocations': '',
            'extensions': '',
            'chapter': self.current_part,
            'source_page': lines[0].get('page_num', 0),
            'source_book': '',
            'confidence': 1.0,
        }

        # 提取音标所在行的内容
        first_line = lines[0]['text']

        # 从 音标：/xxx/ 中提取音标
        phonetic_match = re.match(r'音标[：:]\s*(.+?)$', first_line)
        if phonetic_match:
            entry['phonetic'] = phonetic_match.group(1).strip()

        # 从所有行中提取单词（在 音标： 之前或当前行的前面部分）
        # 单词通常在文本流中出现在 音标： 之前
        # 但在这个流程里，第一个line就是 音标： 开头的
        # 所以单词可能在上一条目的末尾部分
        # 我们需要从 音标 前面的内容找单词

        # 先用更可靠的方法：从文本中匹配英文单词
        # 收集所有文本
        full_text = ' '.join(item['text'] for item in lines)
        all_text_parts = [item['text'] for item in lines]

        # 解析：按顺序解析每个section
        self._parse_sections(entry, all_text_parts, full_text)

        # 如果单词为空，尝试从文本中提取
        if not entry['word']:
            entry['word'] = self._guess_word(all_text_parts, full_text)

        # 清理
        entry['word'] = entry['word'].strip().lower().rstrip('.').rstrip(',')

        # 如果单词还是空的或太短，丢弃
        if len(entry['word']) < 2:
            return None

        return entry

    def _parse_sections(self, entry, all_text_parts, full_text):
        """
        解析各个 section：释义 带你背 例句 常见搭配 词汇扩充 词义辨析 词根词缀积累
        """
        # 合并文本用于查找 section
        combined = ' ||| '.join(all_text_parts)

        # ---- 释义 ----
        meaning_match = re.search(
            r'释义[：:]\s*(.+?)(?=\s*(带你背|词根词缀|例句|常见搭配|词汇扩充|词义辨析|音标))',
            combined
        )
        if meaning_match:
            meaning_text = meaning_match.group(1).strip()
            # 提取词性和释义
            self._parse_pos_meaning(entry, meaning_text)

        # ---- 带你背（记忆方法）----
        memory_match = re.search(
            r'带你背[：:]\s*(.+?)(?=\s*(词根词缀|例句|常见搭配|词汇扩充|词义辨析|音标))',
            combined
        )
        if memory_match:
            memory_text = memory_match.group(1).strip()
            # 去掉 "属于熟悉单词，略" 标记
            if '属于熟悉单词' in memory_text or '略' in memory_text[:10]:
                entry['memory_methods'] = '（熟悉单词，无需额外记忆方法）'
            else:
                # 清理文本中的图片引用和URL
                memory_text = self._clean_memory_text(memory_text)
                entry['memory_methods'] = memory_text

        # ---- 例句 ----
        examples_match = re.search(
            r'例句[：:]\s*(.+?)(?=\s*(常见搭配|词汇扩充|词义辨析|音标))',
            combined
        )
        if examples_match:
            entry['examples'] = examples_match.group(1).strip()

        # 如果例句包含"收藏"标记，去掉
        if '收藏' in entry['examples']:
            entry['examples'] = entry['examples'].replace('收藏', '').strip()

        # ---- 常见搭配 ----
        coll_match = re.search(
            r'常见搭配[：:]\s*(.+?)(?=\s*(词汇扩充|词义辨析|例句|音标))',
            combined
        )
        if coll_match:
            entry['collocations'] = coll_match.group(1).strip()

        # ---- 词汇扩充 ----
        ext_match = re.search(
            r'词汇扩充[：:]\s*(.+?)(?=\s*(词义辨析|例句|音标))',
            combined
        )
        if ext_match:
            entry['extensions'] = ext_match.group(1).strip()

        # ---- 词义辨析 ----
        # 收集到下一个标记或结束
        disc_match = re.search(
            r'词义辨析[：:]\s*(.+?)(?=\s*(音标))',
            combined
        )
        if disc_match:
            disc_text = disc_match.group(1).strip()
            if entry['extensions']:
                entry['extensions'] += ' | ' + disc_text
            else:
                entry['extensions'] = disc_text

        # ---- 词根词缀积累 + 巧记 ----
        root_match = re.search(
            r'词根词缀积累[：:]\s*(.+?)(?=\s*(例句|常见搭配|词汇扩充|词义辨析|音标))',
            combined
        )
        if root_match:
            root_text = root_match.group(1).strip()
            # 如果记忆方法为空，用词根词缀分析填充
            if not entry['memory_methods'] or entry['memory_methods'] == '（熟悉单词，无需额外记忆方法）':
                entry['memory_methods'] = root_text
            else:
                # 附加到记忆方法
                entry['memory_methods'] += ' | 词根分析：' + root_text

        # 清理各字段中的 "收藏" 标记
        for field in ['examples', 'collocations', 'extensions', 'memory_methods']:
            if field in entry:
                entry[field] = entry[field].replace('收藏', '').strip()

        # 如果没有提取到记忆方法
        if not entry.get('memory_methods'):
            # 检查是否包含"属于熟悉单词"
            if '属于熟悉单词' in combined:
                entry['memory_methods'] = '（熟悉单词，无需额外记忆方法）'
            else:
                # 尝试从剩余文本找记忆内容
                mem_fallback = re.search(
                    r'带你背[：:]\s*(.+?)$',
                    combined
                )
                if mem_fallback:
                    entry['memory_methods'] = self._clean_memory_text(mem_fallback.group(1).strip())

    def _parse_pos_meaning(self, entry, meaning_text):
        """
        从释义文本中提取词性和中文释义。
        格式：v.进入； 或 v.进入；n.入口；
        有时释义会包含多个词性。
        """
        # 尝试匹配第一个词性标记
        pos_pattern = r'^(' + '|'.join(re.escape(t) for t in self.POS_TAGS) + r')\s*'
        pos_match = re.match(pos_pattern, meaning_text)
        if pos_match:
            entry['pos'] = pos_match.group(1)
            entry['meaning'] = meaning_text[pos_match.end():].strip()
        else:
            # 有些释义没有词性标记
            entry['meaning'] = meaning_text

    def _clean_memory_text(self, text):
        """清理记忆方法文本中的URL和图片引用"""
        # 移除URL
        text = re.sub(r'https?://\S+', '', text)
        # 移除图片引用
        text = re.sub(r'<img[^>]*>', '', text)
        text = re.sub(r'\!\[.*?\]\(.*?\)', '', text)
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        # 移除结尾的无关字符
        text = text.rstrip('；;')
        return text

    def _guess_word(self, all_text_parts, full_text):
        """
        从文本中猜测单词。
        策略：
        1. 查找第一个看起来像英文单词的词
        2. 优先从 音标： 前面或 释义： 前面找
        """
        # 策略1：找出现在 音标： 之前行的英文单词
        text_before_phonetic = ''
        for item in self._get_context_before(all_text_parts):
            text_before_phonetic += ' ' + item

        # 从中提取英文单词
        words = re.findall(r'\b([a-zA-Z][a-zA-Z\-\']{1,30})\b', text_before_phonetic)
        # 过滤明显的非单词
        real_words = [w for w in words if len(w) >= 2 and w.lower() not in
                      ['the', 'and', 'for', 'are', 'not', 'but', 'all', 'can', 'has', 'had',
                       'was', 'were', 'did', 'does', 'been', 'some', 'than', 'that', 'this',
                       'with', 'from', 'they', 'have', 'been', 'what', 'when', 'where',
                       'which', 'their', 'them', 'these', 'those', 'about', 'would', 'could',
                       'should', 'there', 'part', 'parts']]

        if real_words:
            return real_words[-1]  # 取最靠近音标的

        # 策略2：直接从 释义 后面提取英文单词
        meaning_match = re.search(r'释义[：:]\s*(.+?)(?=\s*(带你背|例句|常见搭配|音标))', full_text)
        if meaning_match:
            return ''  # 释义部分一般没有英文单词

        # 策略3：在音标后面找（极少数情况）
        phon_match = re.search(r'音标[：:]\s*/.+?/\s*(.+?)(?=\s*释义)', full_text)
        if phon_match:
            possible = phon_match.group(1).strip()
            if re.match(r'^[a-zA-Z][a-zA-Z\-\']{1,30}$', possible):
                return possible

        return ''

    def _get_context_before(self, all_text_parts):
        """
        获取单词条目中 音标 之前的内容。
        在文本流中，单词通常出现在 音标 之前（上一页底部或本页开头）。
        """
        # 由于我们是用 音标 分割条目的，所以current entry的lines中
        # 第一个就是 音标 行，之前的文本在上一批lines中
        # 这里我们用流中的全文
        return []


# ============================================================
# 改进版解析器：基于页面连续文本
# ============================================================

class ImprovedWordParser:
    """
    改进版解析器 —— 基于《单词突围》书的结构特点：

    结构特点：
    - 单词标题是页面中的"独立英文行"（一行只有英文单词）
    - 独立英文行出现在 音标 之前（或前一页的末尾）
    - 用 音标 作为条目切分标记
    - 正文中的 jwordj 是强调标记（类似斜体），应该清理掉

    解析策略：
    1. 扫描所有页面，收集"独立英文行"作为单词标题候选
    2. 用 音标 切分条目
    3. 每个条目取前面最近的独立英文行作为单词
    4. 清理所有 j 标记
    """

    POS_PATTERN = re.compile(r'^(?P<pos>v\.|vi\.|vt\.|n\.|adj\.|adv\.|pron\.|prep\.|conj\.|int\.|art\.|num\.|aux\.|a\.|ad\.)')
    PHONETIC_RE = re.compile(r'音标[：:]\s*/?\s*(.+?)\s*/?\s*$')
    PART_RE = re.compile(r'^(Part|第[一二三四五六七八九十百千]+[章节部])', re.IGNORECASE)
    WORD_RE = re.compile(r'\b([a-zA-Z][a-zA-Z\-\']{2,20})\b')

    # 一行只有英文单词（单词标题）
    STANDALONE_WORD_RE = re.compile(r'^[a-zA-Z][a-zA-Z\-\']{2,25}$')

    # 需要过滤的常见小词
    FILTER_WORDS = {
        'the', 'and', 'for', 'are', 'not', 'but', 'all', 'can', 'has', 'had',
        'was', 'were', 'did', 'does', 'been', 'some', 'than', 'that', 'this',
        'with', 'from', 'they', 'have', 'what', 'when', 'where',
        'which', 'their', 'them', 'these', 'those', 'about', 'would', 'could',
        'should', 'there', 'part', 'parts', 'into', 'over', 'also',
        'each', 'many', 'more', 'much', 'most', 'such', 'only', 'other',
        'very', 'just', 'than', 'then', 'said',
    }

    def __init__(self):
        self.current_part = ""
        self._standalone_words = []  # [(page_num, line_idx, word)]
        self._entries = []

    def parse(self, pages_text):
        """
        解析所有页面。
        第一步：扫描收集独立英文行 + 音标位置
        第二步：组装条目
        第三步：解析每个条目内容
        """
        # 第一步：扫描所有页面
        all_items = self._scan_pages(pages_text)

        # 第二步：用 音标 分割条目，并分配单词
        raw_entries = self._assemble_entries(all_items)

        # 第三步：解析每个条目的内容
        parsed = []
        for entry_data in raw_entries:
            entry = self._parse_entry_content(entry_data)
            if entry and entry.get('word'):
                parsed.append(entry)

        logger.info(f"文本解析完成：共 {len(parsed)} 个单词条目")
        return parsed

    def _scan_pages(self, pages_text):
        """
        扫描所有页面，收集所有文本行，同时识别独立英文行。
        返回 list of dicts: {text, page_num, line_idx, is_word_title, is_phonetic_start}
        """
        all_items = []
        self._standalone_words = []

        for page in pages_text:
            pn = page['page_num']
            raw = page['raw_text']
            lines = raw.split('\n')

            for idx, line in enumerate(lines):
                ls = line.strip()
                if not ls:
                    continue

                # 跳过 Part 标题
                if self.PART_RE.match(ls):
                    self.current_part = ls
                    continue

                # 跳过 收藏 标记
                if ls == '收藏':
                    continue

                # 跳过页码
                if is_page_number(ls):
                    continue

                # 跳过 目录、前言 等
                if ls in ('目录', '前言', '单词突围'):
                    continue

                item = {
                    'text': clean_line(ls),    # 清理后的文本（无j标记）
                    'raw_text': ls,            # 原始文本（保留j标记用于降级提取）
                    'page_num': pn,
                    'line_idx': idx,
                    'is_word_title': False,
                    'is_phonetic_start': False,
                    'is_meaning_start': False,
                    'part': self.current_part,
                }

                # 判断是否为独立英文行（单词标题）
                # j 是 PDF 格式标记（本PDF中用j标记强调词），如果一行有多个j很可能是垃圾
                if self.STANDALONE_WORD_RE.match(ls):
                    word = ls.lower()
                    j_count = word.count('j')
                    if j_count > 1:  # 多个j说明包含格式标记
                        pass
                    elif word not in self.FILTER_WORDS:
                        item['is_word_title'] = True
                        self._standalone_words.append((pn, idx, word))

                # 判断是否为 音标 开始
                if '音标' in ls and ('：' in ls or ':' in ls):
                    item['is_phonetic_start'] = True

                all_items.append(item)

        logger.info(f"页面扫描完成：{len(all_items)} 行，{len(self._standalone_words)} 个独立英文行")
        return all_items

    def _assemble_entries(self, all_items):
        """
        音标 切分条目 + 页面级单词分配。

        单词分配策略（核心思路）：
        在《单词突围》PDF中，单词标题（独立英文行）在页面上的位置有规律：
        每页上的独立英文行按顺序匹配该页上的音标条目。

        对于跨页条目，只考虑其音标所在页上的独立行。
        无匹配的条目降级使用 j...j 标记提取。
        """
        # ---- 第一步：用 音标 切分条目 ----
        raw_entries = []
        current_items = []
        entry_phon_page = 1  # 第一个条目的音标在第1页
        last_phon_page = 1   # 上一个音标的页号

        for item in all_items:
            if item['is_phonetic_start'] and current_items:
                raw_entries.append({
                    'items': current_items,
                    'part': current_items[0].get('part', ''),
                    'phon_page': entry_phon_page,
                    'phon_item': current_items[0],
                })
                current_items = []
                entry_phon_page = item['page_num']
            current_items.append(item)

        if current_items:
            raw_entries.append({
                'items': current_items,
                'part': current_items[0].get('part', ''),
                'phon_page': entry_phon_page,
                'phon_item': current_items[0],
            })

        for item in all_items:
            if item['is_phonetic_start'] and current_items:
                raw_entries.append({
                    'items': current_items,
                    'part': current_items[0].get('part', ''),
                    'phon_page': entry_phon_page,
                    'phon_item': current_items[0],
                })
                current_items = []
                entry_phon_page = item['page_num']
            current_items.append(item)

        if current_items:
            raw_entries.append({
                'items': current_items,
                'part': current_items[0].get('part', ''),
                'phon_page': entry_phon_page,
                'phon_item': current_items[0],
            })

        logger.info(f"  按音标切分: {len(raw_entries)} 个条目")

        # ---- 第二步：按页面收集独立行 ----
        # page_words[page_num] = [word1, word2, ...]
        page_words = {}
        for item in all_items:
            if item['is_word_title']:
                pn = item['page_num']
                if pn not in page_words:
                    page_words[pn] = []
                page_words[pn].append(item['text'].lower())

        # ---- 第三步：页面级分配 ----
        # 每页的独立行按顺序分配给该页的音标条目
        page_entry_count = {}  # page_num -> 该页音标条目数
        for i, e in enumerate(raw_entries):
            pn = e['phon_page']
            if pn > 0:
                page_entry_count[pn] = page_entry_count.get(pn, 0) + 1

        # {page_num: [word or '' for each entry on this page]}
        # 匹配规则：当独立行数量 < 条目数时，从末尾开始匹配
        # 因为页面底部的独立行（page-break标记）属于该页上最后的条目
        page_word_assign = {}
        for pn, wlist in page_words.items():
            if pn not in page_entry_count:
                continue
            n_entries = page_entry_count[pn]
            n_words = len(wlist)
            assigns = [''] * n_entries
            if n_words >= n_entries:
                # 一对一匹配
                for i in range(n_entries):
                    assigns[i] = wlist[i]
            else:
                # 单词少于条目：从末尾匹配
                # 页面底部单词属于该页上最后几个条目
                offset = n_entries - n_words
                for i in range(n_words):
                    assigns[offset + i] = wlist[i]
            page_word_assign[pn] = assigns

        # ---- 第四步：分配单词并处理跨页 ----
        # 每个条目按音标所在页取对应位置的单词
        page_counters = {}
        entries_with_words = []

        for i, entry in enumerate(raw_entries):
            pn = entry['phon_page']
            if pn not in page_counters:
                page_counters[pn] = 0

            idx_on_page = page_counters[pn]
            page_counters[pn] += 1

            word = ''
            if pn in page_word_assign and idx_on_page < len(page_word_assign[pn]):
                word = page_word_assign[pn][idx_on_page]

            if not word:
                # 降级：从 j...j 标记提取（使用原始raw_text，因为text已清洗）
                raw_texts = [it.get('raw_text', it['text']) for it in entry['items']]
                raw_full = ' '.join(raw_texts)
                j_words = re.findall(r'j([a-zA-Z][a-zA-Z\-\']{2,})j', raw_full)
                for w in j_words:
                    wl = w.lower()
                    if wl not in self.FILTER_WORDS and len(wl) >= 3:
                        word = wl
                        break

            entry['word'] = word.lower().strip() if word else ''

            if entry['word'] and len(entry['word']) >= 2:
                entries_with_words.append(entry)

        # ---- 第五步：补充分配不上的条目（降级用 j...j 原始文本）----
        wordless = [e for e in raw_entries if not e['word'] or len(e['word']) < 2]
        for entry in wordless:
            raw_texts = [it.get('raw_text', it['text']) for it in entry['items']]
            raw_full = ' '.join(raw_texts)
            j_words = re.findall(r'j([a-zA-Z][a-zA-Z\-\']{2,})j', raw_full)
            for w in j_words:
                wl = w.lower()
                if wl not in self.FILTER_WORDS and len(wl) >= 2:
                    entry['word'] = wl
                    if entry not in entries_with_words:
                        entries_with_words.append(entry)
                    break

        # ---- 去重 + 清理 ----
        seen = set()
        unique = []
        WORD_VALID_RE = re.compile(r'^[a-z]{2,15}$')
        for e in entries_with_words:
            w = e.get('word', '').lower().strip()
            # 过滤：只保留纯小写英文字母，2-15个字符
            if not WORD_VALID_RE.match(w):
                continue
            # 额外过滤：包含多个j的（PDF格式标记）
            if w.count('j') > 1:
                continue
            if w in seen:
                continue
            seen.add(w)
            e['word'] = w
            unique.append(e)

        logger.info(f"  单词分配: {len(entries_with_words)} → 去重 {len(unique)} 个")
        return unique

    def _parse_entry_content(self, entry_data):
        """
        解析一个条目的内容，提取各个结构化字段。
        """
        items = entry_data['items']
        full_text = ' '.join(it['text'] for it in items)
        plain_texts = [it['text'] for it in items]

        entry = {
            'word': entry_data['word'],
            'phonetic': '',
            'pos': '',
            'meaning': '',
            'examples': '',
            'memory_methods': '',
            'derivatives': '',
            'collocations': '',
            'extensions': '',
            'chapter': entry_data.get('part', ''),
            'source_page': entry_data.get('phon_page', 0),
            'source_book': '',
            'confidence': 1.0,
        }

        # 1. 提取音标
        phon_match = re.search(r'音标[：:]\s*(/?.+?)\s*(?=释义|音标|$)', full_text)
        if phon_match:
            entry['phonetic'] = phon_match.group(1).strip()

        # 2. 提取释义和词性
        meaning_match = re.search(r'释义[：:]\s*(.+?)(?=\s*带你背|\s*词根词缀|\s*例句|\s*常见搭配|\s*词汇扩充|\s*词义辨析|收藏|$)', full_text)
        if meaning_match:
            mtext = meaning_match.group(1).strip()
            pos_match = self.POS_PATTERN.match(mtext)
            if pos_match:
                entry['pos'] = pos_match.group('pos')
                entry['meaning'] = mtext[pos_match.end():].strip()
            else:
                entry['meaning'] = mtext

        # 3. 提取记忆方法（带你背）
        memory_match = re.search(r'带你背[：:]\s*(.*?)(?=\s*词根词缀|\s*例句|\s*常见搭配|\s*词汇扩充|\s*词义辨析|收藏|$)', full_text)
        if memory_match:
            mtext = memory_match.group(1).strip()
            if '属于熟悉单词' in mtext or mtext in ('略', '略；'):
                entry['memory_methods'] = '（熟悉单词，无需额外记忆方法）'
            else:
                entry['memory_methods'] = self._clean_j_markers(mtext)

        # 4. 提取词根词缀积累
        root_match = re.search(r'词根词缀积累[：:]\s*(.*?)(?=\s*巧记|\s*例句|\s*常见搭配|\s*词汇扩充|\s*词义辨析|收藏|$)', full_text)
        if root_match:
            rtext = self._clean_j_markers(root_match.group(1).strip())

            # 提取巧记
            qj_match = re.search(r'巧记[：:]\s*(.*?)(?=\s*例句|\s*常见搭配|\s*词汇扩充|\s*词义辨析|收藏|$)', full_text)
            if qj_match:
                qj_text = self._clean_j_markers(qj_match.group(1).strip())
                if qj_text and len(qj_text) > 5:
                    rtext += ' | 巧记：' + qj_text

            if rtext and len(rtext) > 5:
                if entry['memory_methods']:
                    # 已经有记忆方法了，附加词根分析
                    entry['memory_methods'] += ' | 词根分析：' + rtext
                else:
                    entry['memory_methods'] = rtext

        # 5. 提取例句
        examples_match = re.search(r'例句[：:]\s*(.*?)(?=\s*常见搭配|\s*词汇扩充|\s*词义辨析|收藏|$)', full_text)
        if examples_match:
            etext = self._clean_j_markers(examples_match.group(1).strip())
            if etext:
                entry['examples'] = etext

        # 6. 提取常见搭配
        coll_match = re.search(r'常见搭配[：:]\s*(.*?)(?=\s*词汇扩充|\s*词义辨析|收藏|$)', full_text)
        if coll_match:
            ctext = self._clean_j_markers(coll_match.group(1).strip())
            if ctext:
                entry['collocations'] = ctext

        # 7. 提取词汇扩充
        ext_match = re.search(r'词汇扩充[：:]\s*(.*?)(?=\s*词义辨析|收藏|$)', full_text)
        if ext_match:
            etext = self._clean_j_markers(ext_match.group(1).strip())
            if etext:
                entry['extensions'] = etext

        # 8. 提取词义辨析（合并到扩展内容）
        disc_match = re.search(r'词义辨析[：:]\s*(.*?)$', full_text)
        if disc_match:
            dtext = self._clean_j_markers(disc_match.group(1).strip())
            if dtext:
                if entry['extensions']:
                    entry['extensions'] += ' | 词义辨析：' + dtext
                else:
                    entry['extensions'] = '词义辨析：' + dtext

        # 清理各字段中的"收藏"和多余空格
        for k in entry:
            if isinstance(entry[k], str):
                entry[k] = entry[k].replace('收藏', '').strip()
                entry[k] = re.sub(r'\s+', ' ', entry[k]).strip()
                entry[k] = entry[k].rstrip(';；')

        # 检查单词是否有效
        word = entry['word'].lower().strip().rstrip('.').rstrip(',').rstrip('-')
        entry['word'] = word

        return entry

    def _clean_j_markers(self, text):
        """
        清理文本中的 j 标记和其他噪声字符。
        j 是 PDF 中用于标记强调文本的字符（相当于斜体）。
        同时处理 URL 和图片引用。
        """
        if not text:
            return ''

        # PDF中控制字符（\x01-\x08, \x0b-ff, \x0e-\x1f）是英文词之间的分隔符
        for code in range(0x01, 0x09):
            text = text.replace(chr(code), ' ')
        for code in range(0x0b, 0x0d):  # \x0b, \x0c
            text = text.replace(chr(code), ' ')
        for code in range(0x0e, 0x20):
            text = text.replace(chr(code), ' ')
        text = text.replace('', ' ')
        text = text.replace('', ' ')

        # j 标记 → 空格
        text = text.replace('j', ' ')

        # 清理其他格式控制字符
        text = text.replace('￼', '')
        text = text.replace('▓', '')

        # 移除URL
        text = re.sub(r'https?://\S+', '', text)

        # 合并多余空格
        text = re.sub(r'\s+', ' ', text).strip()

        return text


# ============================================================
# 去重和排序
# ============================================================

def dedup_and_sort(entries):
    """按单词去重（保留第一个），按字母排序"""
    seen = set()
    unique = []
    for entry in entries:
        word = entry.get('word', '').lower().strip()
        if word and word not in seen:
            seen.add(word)
            unique.append(entry)

    # unique.sort(key=lambda x: x.get(word, "").lower())  # 不按字母排序，保留书本原序
    return unique


# ============================================================
# 保存结果
# ============================================================

def save_results(entries, output_dir):
    """保存到 JSON 和 CSV"""
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"\n保存文件到: {output_dir}")

    # JSON
    json_path = os.path.join(output_dir, 'words_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    logger.info(f"  JSON: {json_path} ({len(entries)} 条目)")

    # CSV
    csv_path = os.path.join(output_dir, 'words_data.csv')
    fieldnames = [
        'word', 'phonetic', 'pos', 'meaning',
        'examples', 'memory_methods', 'derivatives',
        'collocations', 'extensions', 'chapter',
        'source_page', 'source_book', 'confidence',
    ]
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            row = {k: entry.get(k, '') for k in fieldnames}
            writer.writerow(row)
    logger.info(f"  CSV: {csv_path}")

    # 统计
    stats = {
        'total_words': len(entries),
        'source_book': '单词突围5200',
        'extract_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    stats_path = os.path.join(output_dir, 'extract_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info(f"\n提取完成！共 {len(entries)} 个单词")
    logger.info(f"文件已保存到: {output_dir}")
    return json_path


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='单词突围 - PDF文本提取工具')
    parser.add_argument('--pdf', type=str, default='',
                        help='PDF文件名关键词（如：上册）')
    parser.add_argument('--pages', type=str, default='',
                        help='提取页数范围（如：1-50）')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR,
                        help='输出目录')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("单词突围 - PDF文本提取工具（精确版）")
    logger.info(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 查找PDF
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.exists():
        pdf_dir = Path(PROJECT_ROOT)
    pdf_files = sorted(pdf_dir.glob('*.pdf')) + sorted(pdf_dir.glob('**/*.pdf'))
    pdf_files = [f for f in pdf_files if f.is_file()]

    if args.pdf:
        pdf_files = [f for f in pdf_files if args.pdf in f.name]

    if not pdf_files:
        logger.error(f"未找到PDF文件！")
        logger.error(f"请在以下目录放置PDF：{PDF_DIR}")
        return

    logger.info(f"找到 {len(pdf_files)} 个PDF文件:")
    for f in pdf_files:
        logger.info(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")

    # 解析页数范围
    start_page, end_page = 0, None
    if args.pages:
        try:
            parts = args.pages.split('-')
            start_page = int(parts[0]) - 1  # 转0-index
            if len(parts) > 1:
                end_page = int(parts[1])
        except ValueError:
            logger.warning(f"页数格式无效: {args.pages}，使用全部页数")

    # 处理每个PDF
    all_entries = []
    for pdf_path in pdf_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"处理: {pdf_path.name}")
        logger.info(f"{'='*60}")

        book_name = pdf_path.stem.replace('单词突围5200 ', '').replace('单词突围', '')
        book_name = book_name if book_name else pdf_path.stem

        try:
            # 提取文本
            pages_text = extract_text_from_pdf(str(pdf_path), start_page, end_page)

            # 解析
            word_parser = ImprovedWordParser()
            entries = word_parser.parse(pages_text)

            # 标记来源
            for e in entries:
                e['source_book'] = f"单词突围5200 {book_name}"

            all_entries.extend(entries)

        except Exception as e:
            logger.error(f"处理失败: {pdf_path.name} - {e}")
            traceback.print_exc()
            continue

    # 去重和排序
    if all_entries:
        entries = dedup_and_sort(all_entries)
        logger.info(f"\n去重: {len(all_entries)} → {len(entries)} 个唯一单词")
        save_results(entries, args.output)
    else:
        logger.warning("未提取到任何单词！")


if __name__ == '__main__':
    main()
