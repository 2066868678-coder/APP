#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - OCR文字提取脚本
===========================
功能：从扫描版PDF中提取单词数据，输出JSON和CSV文件
使用PaddleOCR（中文识别率最高，免费，本地运行）

使用方法：
  python ocr/ocr_extract.py

输出文件：
  - ocr/output/raw_words.json     → 完整单词数据（JSON格式）
  - ocr/output/words_data.csv     → Excel可打开的CSV（方便人工校对）
  - ocr/output/ocr_progress.log  → OCR处理日志

注意事项：
  1. 首次运行时会自动下载模型文件（约100MB）
  2. PDF扫描件识别准确率约90-95%
  3. 输出CSV文件请用Excel/WPS打开校对
"""

import os
import sys
import json
import csv
import re
import logging
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置区域（你可以根据需要修改这些参数）
# ============================================================

# PDF文件目录（程序会自动扫描此目录下的所有PDF）
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "单词书")

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# OCR语言设置（ch：中文，en：英文）
OCR_LANGS = ['ch', 'en']

# DPI设置（越大越清晰，但也越慢）
PDF_DPI = 300

# 每页识别后等待时间（秒），防止内存溢出
PAGE_DELAY = 0.5

# ============================================================
# 日志设置
# ============================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# 控制台输出
console = logging.StreamHandler(sys.stdout)
console.setFormatter(formatter)
logger.addHandler(console)

# 文件输出
os.makedirs(OUTPUT_DIR, exist_ok=True)
file_handler = logging.FileHandler(
    os.path.join(OUTPUT_DIR, 'ocr_progress.log'),
    encoding='utf-8', mode='a'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# ============================================================
# PDF处理模块
# ============================================================

def find_pdf_files():
    """扫描PDF目录，返回所有PDF文件路径"""
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.exists():
        logger.error(f"PDF目录不存在：{PDF_DIR}")
        logger.error("请将《单词突围》PDF文件放到目录中，或修改配置文件中的PDF_DIR路径")
        # 尝试找项目根目录下的PDF
        pdf_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pdf_files = list(pdf_dir.glob("*.pdf")) + list(pdf_dir.glob("**/*.pdf"))
        if pdf_files:
            logger.info(f"在项目根目录找到PDF：{len(pdf_files)}个")
            return sorted(pdf_files)
        return []

    pdf_files = list(pdf_dir.glob("*.pdf")) + list(pdf_dir.glob("**/*.pdf"))
    pdf_files = [f for f in pdf_files if f.is_file()]

    if not pdf_files:
        logger.warning(f"在 {PDF_DIR} 下未找到PDF文件")
        # 尝试递归搜索
        pdf_files = list(pdf_dir.rglob("*.pdf"))
        pdf_files = [f for f in pdf_files if f.is_file()]

    pdf_files = sorted(pdf_files)
    logger.info(f"找到 {len(pdf_files)} 个PDF文件：")
    for f in pdf_files:
        logger.info(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")

    return pdf_files


def pdf_page_to_image(pdf_path, page_num, dpi=None):
    """将PDF指定页面转换为图片（使用PyMuPDF）"""
    if dpi is None:
        dpi = PDF_DPI

    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("请先安装PyMuPDF库：pip install pymupdf")
        return None

    try:
        doc = fitz.open(str(pdf_path))
        if page_num < 0 or page_num >= len(doc):
            doc.close()
            return None

        page = doc[page_num]
        # 按DPI缩放
        zoom = dpi / 72.0  # PDF默认72 DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # 转换为numpy数组（PaddleOCR需要）
        import numpy as np
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        # 如果是灰度图，转成3通道
        if pix.n == 1:
            img_data = np.stack([img_data] * 3, axis=-1)
        elif pix.n == 4:
            img_data = img_data[:, :, :3]

        doc.close()
        return img_data

    except Exception as e:
        logger.error(f"PDF页面转换失败（第{page_num+1}页）：{e}")
        return None


def get_pdf_page_count(pdf_path):
    """获取PDF总页数"""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"读取PDF失败：{e}")
        return 0


# ============================================================
# OCR识别模块
# ============================================================

class OCREngine:
    """OCR识别引擎封装"""

    def __init__(self, lang_ch='ch', lang_en='en'):
        self.lang_ch = lang_ch
        self.lang_en = lang_en
        self._ocr = None

    def _init_engine(self):
        """延迟初始化OCR引擎（首次使用时才加载）"""
        if self._ocr is not None:
            return

        try:
            from paddleocr import PaddleOCR
            logger.info("正在初始化PaddleOCR引擎（首次运行会自动下载模型文件，约需几分钟）...")
            self._ocr = PaddleOCR(
                use_angle_cls=True,  # 文字方向分类
                lang='ch',           # 中英文混合
                show_log=False,      # 不显示详细日志
                use_gpu=False,       # 使用CPU（兼容性更好）
                det_db_thresh=0.3,   # 检测阈值
                rec_batch_num=6,     # 批量识别数量
            )
            logger.info("PaddleOCR引擎初始化完成！")
        except ImportError:
            logger.error("=" * 60)
            logger.error("请先安装PaddleOCR库！")
            logger.error("运行命令：pip install paddlepaddle paddleocr")
            logger.error("如安装缓慢，可使用清华镜像：")
            logger.error("pip install paddlepaddle paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple")
            logger.error("=" * 60)
            raise
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败：{e}")
            raise

    def recognize_page(self, image):
        """识别一页图片，返回文字及其位置信息"""
        self._init_engine()

        if image is None:
            return []

        try:
            result = self._ocr.ocr(image, cls=True)
            if result is None or len(result) == 0 or result[0] is None:
                return []

            # 解析结果
            lines = []
            for line in result[0]:
                box = line[0]  # 四个角坐标
                text_info = line[1]
                text = text_info[0]       # 识别出的文字
                confidence = text_info[1]  # 置信度

                # 计算中心Y坐标（用于排序）
                y_center = sum(p[1] for p in box) / 4

                lines.append({
                    'text': text,
                    'confidence': confidence,
                    'box': box,
                    'y_center': y_center,
                    'x_min': min(p[0] for p in box),
                })

            # 按从上到下、从左到右排序
            lines.sort(key=lambda x: (round(x['y_center'] / 20) * 20, x['x_min']))

            return lines

        except Exception as e:
            logger.error(f"OCR识别失败：{e}")
            return []


# ============================================================
# 单词提取模块
# ============================================================

class WordParser:
    """从OCR结果中提取单词信息的解析器"""

    # 常见的词性标记
    POS_TAGS = [
        'v.', 'vi.', 'vt.', 'n.', 'adj.', 'adv.', 'pron.', 'prep.',
        'conj.', 'int.', 'art.', 'num.', 'aux.', 'modal.',
        'a.', 'ad.', 'prep', 'conj',
        '及物动词', '不及物动词', '名词', '形容词', '副词',
        '介词', '连词', '感叹词', '代词', '数词', '冠词',
        '动词', '名', '形', '副', '介', '连',
    ]

    # 章节标题模式
    CHAPTER_PATTERNS = [
        r'第[一二三四五六七八九十百千]+[章节]',
        r'[Ll]esson\s*\d+',
        r'[Uu]nit\s*\d+',
        r'[Cc]hapter\s*\d+',
        r'[Pp]art\s*\d+',
        r'[Ss]ection\s*\d+',
        r'[Ww]ord\s*[Ll]ist\s*\d+',
        r'^\d+[\.、]',
        r'^第\d+[章节]',
    ]

    def __init__(self):
        self.current_chapter = ""
        self.current_unit = ""

    def is_chapter_header(self, text):
        """判断是否为章节标题"""
        text = text.strip()
        for pattern in self.CHAPTER_PATTERNS:
            if re.match(pattern, text):
                return True
        return False

    def is_word_entry_start(self, line_text):
        """判断一行是否是单词条目的开始"""
        text = line_text.strip()

        # 跳过空行和太短的行
        if len(text) < 2:
            return False

        # 跳过章节标题
        if self.is_chapter_header(text):
            return False

        # 跳过页码
        if re.match(r'^\d+$', text) or re.match(r'^-\s*\d+\s*-$', text):
            return False

        # 跳过明显的非单词行
        skip_patterns = [
            r'^单词突围',
            r'^Word Breakthrough',
            r'^目录',
            r'^前言',
            r'^\d+\s*/\s*\d+',
            r'^www\.',
            r'^http',
            r'^第.*页',
        ]
        for pat in skip_patterns:
            if re.match(pat, text):
                return False

        # 检查是否包含词性标记（这通常意味着在单词行中）
        # 单词行通常：单词 + 音标 + 词性 + 释义
        # 我们检测：至少包含一个英文字母，且包含词性标记
        has_english = bool(re.search(r'[a-zA-Z]', text))

        # 检测是否有词性标记
        has_pos = False
        for tag in self.POS_TAGS:
            if tag in text:
                has_pos = True
                break

        # 检测是否包含音标（用斜杠或方括号括起来的）
        has_phonetic = bool(re.search(r'[/\[].*?[/\]]', text))

        # 如果包含英文字母并且有词性或音标，很可能是单词条目
        if has_english and (has_pos or has_phonetic):
            return True

        # 如果行首是一个英文单词（可能单词和释义在同一行）
        if has_english and len(text) >= 3:
            # 行首英文单词后跟空格或标点
            first_word_match = re.match(r'^([a-zA-Z\-]+)\s*[/\[(]', text)
            if first_word_match:
                return True

        return False

    def extract_word_from_line(self, line_text):
        """从一行文字中提取单词信息"""
        text = line_text.strip()

        # 尝试匹配：单词 音标 词性 释义
        # 模式1：单词 /音标/ 词性. 释义
        pattern1 = re.match(
            r'^([a-zA-Z][a-zA-Z\-\'\.]*)\s*'
            r'([/\[][^/\]]+[/\]])\s*'  # 音标
            r'([a-zA-Z]+[\.]?)?\s*'    # 词性
            r'[\s,;]*'
            r'(.+)?$',                  # 释义
            text
        )

        if pattern1:
            word = pattern1.group(1).strip().lower()
            phonetic = pattern1.group(2).strip() if pattern1.group(2) else ""
            pos = pattern1.group(3).strip() if pattern1.group(3) else ""
            meaning = pattern1.group(4).strip() if pattern1.group(4) else ""
            return word, phonetic, pos, meaning

        # 模式2：单词 (无音标) 词性. 释义
        pattern2 = re.match(
            r'^([a-zA-Z][a-zA-Z\-\'\.]*)\s*'
            r'([a-zA-Z]+[\.]?)\s+'    # 词性
            r'(.+)?$',                 # 释义
            text
        )

        if pattern2:
            word = pattern2.group(1).strip().lower()
            pos = pattern2.group(2).strip() if pattern2.group(2) else ""
            meaning = pattern2.group(3).strip() if pattern2.group(3) else ""
            return word, "", pos, meaning

        return None, None, None, None

    def parse_section_type(self, line_text):
        """判断一行文字属于哪个信息字段"""
        text = line_text.strip()

        # 例句标记
        if re.match(r'^[【\[\(]?\s*(例如?|例句?|例|比如|e\.g\.)[】\]\)]?\s*[:：]?\s*', text):
            return 'example'
        if re.match(r'^[【\[\(]?\s*(例句?)[】\]\)]?\s*[:：]?\s*', text):
            return 'example'

        # 记忆方法标记
        if re.match(r'^[【\[\(]?\s*(记忆|记|谐音|联想|词根|词缀|词源|图像|形象)[】\]\)]?\s*[:：]?\s*', text):
            return 'memory'
        if re.search(r'(记忆方法?|记忆技巧?|巧记|速记|助记)', text):
            return 'memory'

        # 派生词标记
        if re.match(r'^[【\[\(]?\s*(派生|衍生|派生词|衍生词|变形)[】\]\)]?\s*[:：]?\s*', text):
            return 'derivative'
        if re.search(r'^(派生|衍生)', text):
            return 'derivative'

        # 固定搭配标记
        if re.match(r'^[【\[\(]?\s*(搭配|固定搭配|常用搭配|短语|词组|用法)[】\]\)]?\s*[:：]?\s*', text):
            return 'collocation'
        if re.search(r'^(搭配|短语|词组|用法)', text):
            return 'collocation'

        # 扩展信息标记
        if re.match(r'^[【\[\(]?\s*(扩展|拓展|补充|注意|近义|同义|反义|同根|相关)[】\]\)]?\s*[:：]?\s*', text):
            return 'extension'
        if re.search(r'(近义词|反义词|同义词|同根词|扩展)', text):
            return 'extension'

        return 'unknown'

    def parse_page_lines(self, lines):
        """解析一页中的所有文字行，提取单词条目"""
        entries = []
        current_entry = None
        current_section = None

        for line in lines:
            text = line['text'].strip()
            if not text:
                continue

            # 检查是否为章节标题
            if self.is_chapter_header(text):
                self.current_chapter = text
                logger.info(f"  发现章节：{text}")
                continue

            # 尝试提取单词（判断是否为单词条目的开始）
            word, phonetic, pos, meaning = self.extract_word_from_line(text)

            if word:
                # 保存之前的条目
                if current_entry and current_entry.get('word'):
                    entries.append(current_entry)

                # 创建新条目
                current_entry = {
                    'word': word,
                    'phonetic': phonetic,
                    'pos': pos,
                    'meaning': meaning,
                    'examples': [],
                    'memory_methods': [],
                    'derivatives': [],
                    'collocations': [],
                    'extensions': [],
                    'chapter': self.current_chapter,
                    'source_page': line.get('page_num', 0),
                    'raw_text': text,
                    'confidence': line.get('confidence', 0),
                }
                current_section = None
                logger.info(f"  识别单词：{word} {phonetic} {pos} {meaning[:30] if meaning else ''}")
            elif current_entry:
                # 判断是否为信息字段（例句、记忆方法等）
                section_type = self.parse_section_type(text)

                # 移除标记前缀
                cleaned_text = re.sub(
                    r'^[【\[\(]?\s*(例句?|例如?|e\.g\.|记忆|谐音|联想|词根|词缀|词源|'
                    r'派生|衍生|搭配|短语|词组|扩展|拓展|近义|反义|同义|同根|'
                    r'注意|补充|用法)[】\]\)]?\s*[:：]?\s*',
                    '', text
                ).strip()

                if section_type == 'example':
                    if cleaned_text:
                        current_entry['examples'].append(cleaned_text)
                    else:
                        current_entry['examples'].append(text)
                elif section_type == 'memory':
                    if cleaned_text:
                        current_entry['memory_methods'].append(cleaned_text)
                    else:
                        current_entry['memory_methods'].append(text)
                elif section_type == 'derivative':
                    if cleaned_text:
                        current_entry['derivatives'].append(cleaned_text)
                    else:
                        current_entry['derivatives'].append(text)
                elif section_type == 'collocation':
                    if cleaned_text:
                        current_entry['collocations'].append(cleaned_text)
                    else:
                        current_entry['collocations'].append(text)
                elif section_type == 'extension':
                    if cleaned_text:
                        current_entry['extensions'].append(cleaned_text)
                    else:
                        current_entry['extensions'].append(text)
                else:
                    # 如果是上一节内容的延续，追加到当前节
                    if current_entry['examples'] and len(text) > 3:
                        current_entry['examples'][-1] += ' ' + text
                    elif current_entry['memory_methods'] and len(text) > 3:
                        current_entry['memory_methods'][-1] += ' ' + text
                    elif current_entry['derivatives'] and len(text) > 3:
                        current_entry['derivatives'][-1] += ' ' + text
                    elif current_entry['collocations'] and len(text) > 3:
                        current_entry['collocations'][-1] += ' ' + text
                    elif current_entry['extensions'] and len(text) > 3:
                        current_entry['extensions'][-1] += ' ' + text

        # 保存最后一个条目
        if current_entry and current_entry.get('word'):
            entries.append(current_entry)

        return entries


# ============================================================
# 主流程
# ============================================================

def process_pdf(pdf_path, ocr_engine, parser, start_page=0, end_page=None):
    """处理一个PDF文件"""
    pdf_name = Path(pdf_path).name
    total_pages = get_pdf_page_count(pdf_path)
    if total_pages == 0:
        logger.error(f"无法读取PDF：{pdf_path}")
        return []

    if end_page is None:
        end_page = total_pages

    logger.info(f"\n{'='*60}")
    logger.info(f"开始处理：{pdf_name}")
    logger.info(f"总页数：{total_pages}，处理范围：第{start_page+1}-{end_page}页")
    logger.info(f"{'='*60}")

    all_entries = []
    page_range = range(start_page, min(end_page, total_pages))

    for page_num in page_range:
        try:
            logger.info(f"  处理第 {page_num+1}/{total_pages} 页...")

            # PDF页面转图片
            image = pdf_page_to_image(pdf_path, page_num)

            if image is None:
                logger.warning(f"  第{page_num+1}页转换失败，跳过")
                continue

            # OCR识别
            lines = ocr_engine.recognize_page(image)
            if not lines:
                logger.info(f"  第{page_num+1}页未识别到文字")
                continue

            # 为每行添加页码信息
            for line in lines:
                line['page_num'] = page_num + 1

            # 解析单词
            entries = parser.parse_page_lines(lines)
            all_entries.extend(entries)

            logger.info(f"  第{page_num+1}页完成，识别出 {len(entries)} 个单词条目")

            # 清理内存
            del image
            if page_num % 10 == 9:
                import gc
                gc.collect()

            time.sleep(PAGE_DELAY)

        except KeyboardInterrupt:
            logger.info("\n用户中断处理")
            break
        except Exception as e:
            logger.error(f"  第{page_num+1}页处理失败：{e}")
            continue

    logger.info(f"\n{pdf_name} 处理完成！共提取 {len(all_entries)} 个单词条目")
    return all_entries


def save_results(all_entries, output_dir):
    """保存结果到JSON和CSV文件"""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 去重（按单词名去重，保留第一个出现的）
    seen_words = set()
    unique_entries = []
    for entry in all_entries:
        word = entry['word'].lower().strip()
        if word not in seen_words:
            seen_words.add(word)
            unique_entries.append(entry)

    logger.info(f"\n去重前：{len(all_entries)} 个条目")
    logger.info(f"去重后：{len(unique_entries)} 个唯一单词")

    # 按单词字母排序
    unique_entries.sort(key=lambda x: x['word'].lower())

    # --- 保存JSON ---
    json_path = os.path.join(output_dir, f"words_data.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(unique_entries, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON文件保存：{json_path}")

    # --- 保存CSV（方便Excel校对）---
    csv_path = os.path.join(output_dir, f"words_data.csv")
    fieldnames = [
        'word', 'phonetic', 'pos', 'meaning',
        'examples', 'memory_methods', 'derivatives',
        'collocations', 'extensions', 'chapter',
        'source_page', 'confidence'
    ]

    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in unique_entries:
            row = {k: entry.get(k, '') for k in fieldnames}
            # 将列表字段转换为可读字符串
            for list_field in ['examples', 'memory_methods', 'derivatives',
                               'collocations', 'extensions']:
                if isinstance(row[list_field], list):
                    row[list_field] = ' | '.join(row[list_field])
            writer.writerow(row)

    logger.info(f"CSV文件保存：{csv_path}")

    # 统计信息
    stats = {
        'total_words': len(unique_entries),
        'total_pages_processed': len(set(e['source_page'] for e in all_entries)),
        'files': {
            'json': json_path,
            'csv': csv_path,
        }
    }

    stats_path = os.path.join(output_dir, "ocr_stats.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*60}")
    logger.info(f"OCR提取完成！统计信息：")
    logger.info(f"  总单词数：{stats['total_words']}")
    logger.info(f"  保存文件：")
    logger.info(f"    JSON: {json_path}")
    logger.info(f"    CSV:  {csv_path}")
    logger.info(f"{'='*60}")

    return unique_entries


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("单词突围 - OCR文字提取工具")
    logger.info(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 查找PDF文件
    pdf_files = find_pdf_files()
    if not pdf_files:
        logger.error("未找到PDF文件！请将《单词突围》PDF放到以下目录：")
        logger.error(f"  {PDF_DIR}")
        logger.error("或者放到项目根目录下。")
        sys.exit(1)

    # 初始化OCR引擎
    try:
        ocr_engine = OCREngine()
    except Exception as e:
        logger.error(f"OCR引擎初始化失败：{e}")
        sys.exit(1)

    # 初始化解析器
    parser = WordParser()

    # 处理每个PDF
    all_entries = []
    for pdf_path in pdf_files:
        try:
            entries = process_pdf(pdf_path, ocr_engine, parser)
            all_entries.extend(entries)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"处理PDF失败：{pdf_path.name} - {e}")
            continue

    # 保存结果
    if all_entries:
        save_results(all_entries, OUTPUT_DIR)
    else:
        logger.warning("未提取到任何单词，请检查PDF文件或OCR配置。")

    logger.info("\n提示：")
    logger.info("1. CSV文件可用Excel/WPS打开，逐条校对")
    logger.info("2. 校对完成后，将校对后的CSV保存为 words_data_corrected.csv")
    logger.info("3. 后续导入数据库时会使用校对后的数据")
    logger.info("\n处理完成！")


if __name__ == '__main__':
    main()
