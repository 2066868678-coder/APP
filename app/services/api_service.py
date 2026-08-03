#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 本地数据服务（直接读写SQLite，不需要后端）
====================================================
"""

from app.services import local_db

def record_study(word_id, study_type, result):
    ok = local_db.record_study(word_id, study_type, result)
    return {'success': ok}

# ========== 今日计划 ==========

def get_today_plan():
    return local_db.get_today_plan()

def get_today_words():
    return local_db.get_today_words()

def set_daily_target(target):
    return local_db.set_setting('daily_new_words_target', str(target))

def get_daily_target():
    v = local_db.get_setting('daily_new_words_target', '20')
    try:
        return int(v)
    except ValueError:
        return 20

# ========== 统计 ==========

def get_stats():
    return local_db.get_stats()

def get_all_words_with_status():
    return local_db.get_all_words_with_status()

# ========== 优化批量接口 ==========

def get_home_data():
    return local_db.get_home_data()

def get_study_data():
    return local_db.get_study_data()

# ========== 学习记录导出 ==========

def get_study_dates():
    return local_db.get_study_dates()

def get_words_by_dates(date_list):
    return local_db.get_words_by_dates(date_list)

def get_recent_study_words(days):
    return local_db.get_recent_study_words(days)
