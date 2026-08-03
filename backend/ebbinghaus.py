#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 艾宾浩斯遗忘曲线算法
===============================
实现基于艾宾浩斯遗忘曲线的复习安排逻辑。

复习间隔（天）：1, 2, 4, 7, 15
- 第1次复习：学习后第1天
- 第2次复习：学习后第2天
- 第3次复习：学习后第4天
- 第4次复习：学习后第7天
- 第5次复习：学习后第15天
- 之后进入长期记忆，间隔30天后再复习

如果用户标记"忘记"，则复习间隔重置为1天。
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

# 标准艾宾浩斯复习间隔（天）
STANDARD_INTERVALS = [1, 2, 4, 7, 15, 30]


def get_next_review_interval(current_interval: int, remembered: bool) -> int:
    """
    根据记忆结果计算下次复习间隔

    参数:
        current_interval: 当前复习间隔（天）
        remembered: 是否记得（True=记得, False=忘记）

    返回:
        下次复习间隔（天）
    """
    if not remembered:
        # 忘记了 → 重置为1天
        return 1

    # 记得 → 按照标准间隔推进
    for i, interval in enumerate(STANDARD_INTERVALS):
        if current_interval < interval:
            return interval

    # 如果已经完成所有标准间隔，按30天周期复习
    return 30


def get_review_schedule(start_date: date, remembered_list: List[bool]) -> List[date]:
    """
    根据一系列记忆结果，计算完整的复习日期安排

    参数:
        start_date: 初次学习日期
        remembered_list: 每次复习是否记得（按顺序）

    返回:
        每次复习的日期列表
    """
    schedule = []
    current_interval = 0

    for remembered in remembered_list:
        next_interval = get_next_review_interval(current_interval, remembered)
        next_date = start_date + timedelta(days=next_interval)
        schedule.append(next_date)
        current_interval = next_interval

    return schedule


def should_review_today(
    word_id: int,
    study_records: List[Dict[str, Any]],
    today: Optional[date] = None
) -> bool:
    """
    判断某个单词今天是否需要复习

    参数:
        word_id: 单词ID
        study_records: 该单词的所有学习记录
        today: 今天的日期（默认使用当前日期）

    返回:
        True 需要复习 / False 不需要
    """
    if today is None:
        today = date.today()

    # 过滤出该单词的记录
    word_records = [r for r in study_records if r.get('word_id') == word_id]
    if not word_records:
        return False  # 还没学过的单词不需要复习

    # 按时间排序
    word_records.sort(key=lambda r: r.get('studied_at', ''))

    # 取最后一次学习记录
    last_record = word_records[-1]
    last_study_str = last_record.get('studied_at')

    if not last_study_str:
        return False

    # 解析日期
    if isinstance(last_study_str, str):
        last_date = datetime.fromisoformat(last_study_str).date()
    elif isinstance(last_study_str, datetime):
        last_date = last_study_str.date()
    else:
        return False

    # 获取当前复习间隔
    last_interval = last_record.get('review_interval', 1)
    last_result = last_record.get('result', 'forget')

    # 距离上次学习的天数
    days_passed = (today - last_date).days

    # 如果已经过了复习间隔
    if days_passed >= last_interval:
        return True

    return False


def calculate_todays_review(
    word_records_map: Dict[int, List[Dict[str, Any]]],
    today: Optional[date] = None
) -> List[int]:
    """
    计算今天所有需要复习的单词ID

    参数:
        word_records_map: { word_id: [学习记录] }
        today: 今天的日期

    返回:
        需要复习的单词ID列表
    """
    if today is None:
        today = date.today()

    review_ids = []
    for word_id, records in word_records_map.items():
        if should_review_today(word_id, records, today):
            review_ids.append(word_id)

    return review_ids


