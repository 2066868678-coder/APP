#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 本地数据库访问层
==========================
直接读写SQLite，不需要后端服务器。
这样App可以独立运行，也可以打包成手机App。
"""

import sys, os, json, math
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import Session
from backend.models import Base, Word, StudyRecord, DailyPlan, SystemSettings, init_database

# 数据库路径（相对于项目根目录）
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database")
DB_PATH = os.path.join(DB_DIR, "words.db")
os.makedirs(DB_DIR, exist_ok=True)

_engine = init_database(f'sqlite:///{DB_PATH}')


def _get_session():
    return Session(_engine)


# ========== 单词查询 ==========

def get_word_count() -> int:
    s = _get_session()
    try:
        return s.query(func.count(Word.id)).scalar() or 0
    finally:
        s.close()


def get_words(page=1, page_size=20, search=None):
    s = _get_session()
    try:
        q = s.query(Word)
        if search:
            q = q.filter(Word.word.like(f'%{search}%'))
        total = q.count()
        words = q.order_by(Word.id).offset((page-1)*page_size).limit(page_size).all()
        return {'total': total, 'words': [w.to_dict() for w in words]}
    finally:
        s.close()


def get_new_words(count=10):
    """获取从未学过的词"""
    s = _get_session()
    try:
        studied = s.query(StudyRecord.word_id).distinct().all()
        studied_ids = [r[0] for r in studied]
        q = s.query(Word)
        if studied_ids:
            q = q.filter(~Word.id.in_(studied_ids))
        remaining = q.count()
        words = q.order_by(Word.id).limit(count).all()
        return {'words': [w.to_dict() for w in words], 'remaining': remaining}
    finally:
        s.close()


# ========== 学习记录 ==========

def record_study(word_id, study_type, result):
    """记录学习行为"""
    s = _get_session()
    try:
        from backend.ebbinghaus import get_next_review_interval
        last = s.query(StudyRecord).filter(
            StudyRecord.word_id == word_id
        ).order_by(StudyRecord.id.desc()).first()
        cur_interval = last.review_interval if last else 0
        remembered = (result == 'remember')
        next_interval = get_next_review_interval(cur_interval, remembered)

        record = StudyRecord(
            word_id=word_id, study_type=study_type,
            result=result, review_interval=next_interval,
        )
        s.add(record)

        # 更新今日计划
        today = date.today()
        plan = s.query(DailyPlan).filter(DailyPlan.plan_date == today).first()
        if plan:
            if study_type == 'new':
                plan.new_words_done += 1
            else:
                plan.review_done += 1
        else:
            plan = DailyPlan(
                plan_date=today, new_words_target=20,
                new_words_done=1 if study_type == 'new' else 0,
                review_done=1 if study_type == 'review' else 0,
            )
            s.add(plan)
        s.commit()
        return True
    except Exception as e:
        s.rollback()
        return False
    finally:
        s.close()


# ========== 今日计划 ==========

def get_today_plan():
    """获取今日计划"""
    s = _get_session()
    try:
        today = date.today()
        plan = s.query(DailyPlan).filter(DailyPlan.plan_date == today).first()

        if not plan:
            # 自动创建
            plan = DailyPlan(
                plan_date=today, new_words_target=20,
                new_words_done=0, review_done=0,
            )
            s.add(plan)
            s.commit()

        total = s.query(func.count(Word.id)).scalar() or 0
        learned = s.query(StudyRecord.word_id).distinct().count()
        mastered = s.query(StudyRecord.word_id).filter(
            StudyRecord.result == 'remember',
            StudyRecord.review_interval >= 15
        ).distinct().count()

        return {
            'plan': plan.to_dict(),
            'stats': {
                'total_words': total,
                'learned_words': learned,
                'mastered_words': mastered,
            }
        }
    finally:
        s.close()


def get_today_words():
    """获取今日要学的单词（新词+复习）"""
    s = _get_session()
    try:
        today = date.today()
        plan = s.query(DailyPlan).filter(DailyPlan.plan_date == today).first()

        new_words = []
        review_words = []

        if plan and plan.word_ids_new:
            ids = [int(x) for x in plan.word_ids_new.split(',') if x]
            new_words = s.query(Word).filter(Word.id.in_(ids)).all() if ids else []

        if plan and plan.word_ids_review:
            ids = [int(x) for x in plan.word_ids_review.split(',') if x]
            review_words = s.query(Word).filter(Word.id.in_(ids)).all() if ids else []

        # 如果没有预设新词，取未学过的
        if not new_words:
            studied = s.query(StudyRecord.word_id).distinct().all()
            studied_ids = [r[0] for r in studied]
            q = s.query(Word)
            if studied_ids:
                q = q.filter(~Word.id.in_(studied_ids))
            new_words = q.order_by(Word.id).limit(10).all()

        return {
            'new_words': [w.to_dict() for w in new_words],
            'review_words': [w.to_dict() for w in review_words],
            'new_words_done': plan.new_words_done if plan else 0,
            'new_words_target': plan.new_words_target if plan else 20,
            'review_done': plan.review_done if plan else 0,
            'review_target': plan.review_target if plan else 0,
        }
    finally:
        s.close()


# ========== 统计 ==========

def get_stats():
    """获取统计数据"""
    s = _get_session()
    try:
        today = date.today()
        total = s.query(func.count(Word.id)).scalar() or 0
        learned = s.query(StudyRecord.word_id).distinct().count()
        mastered = s.query(StudyRecord.word_id).filter(
            StudyRecord.review_interval >= 15,
            StudyRecord.result == 'remember'
        ).distinct().count()

        today_plan = s.query(DailyPlan).filter(DailyPlan.plan_date == today).first()

        week_ago = today - timedelta(days=7)
        week_study = s.query(func.count(StudyRecord.id)).filter(
            StudyRecord.studied_at >= week_ago
        ).scalar() or 0

        study_days = s.query(DailyPlan.plan_date).filter(
            DailyPlan.new_words_done > 0
        ).distinct().count()

        streak = 0
        check = today
        while True:
            dp = s.query(DailyPlan).filter(DailyPlan.plan_date == check).first()
            if dp and (dp.new_words_done > 0 or dp.review_done > 0):
                streak += 1
                check -= timedelta(days=1)
            else:
                break

        return {
            'total_words': total,
            'learned_words': learned,
            'mastered_words': mastered,
            'progress_percent': round(learned / total * 100, 1) if total > 0 else 0,
            'today': today_plan.to_dict() if today_plan else None,
            'week_study_count': week_study,
            'study_days': study_days,
            'streak_days': streak,
        }
    finally:
        s.close()
