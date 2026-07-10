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

from sqlalchemy import create_engine, func, and_, asc
from sqlalchemy.orm import Session
from backend.models import Base, Word, StudyRecord, DailyPlan, SystemSettings, init_database

# 数据库路径（相对于项目根目录）
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database")
os.makedirs(DB_DIR, exist_ok=True)

# 优先使用环境变量中的数据库URL（部署时用PostgreSQL）
DB_URL = os.environ.get('DATABASE_URL')
if DB_URL:
    DB_URL = DB_URL.replace('postgres://', 'postgresql://')
    print(f"使用云端数据库: PostgreSQL")
else:
    DB_PATH = os.path.join(DB_DIR, "words.db")
    DB_URL = f'sqlite:///{DB_PATH}'
    print(f"使用本地数据库: {DB_PATH}")

_engine = init_database(DB_URL)


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
        words = q.order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).offset((page-1)*page_size).limit(page_size).all()
        return {'total': total, 'words': [w.to_dict() for w in words]}
    finally:
        s.close()


def get_new_words(count=None):
    """获取从未学过的词"""
    if count is None:
        saved = get_setting('daily_new_words_target', '20')
        try:
            count = int(saved)
        except ValueError:
            count = 10
    s = _get_session()
    try:
        studied = s.query(StudyRecord.word_id).distinct().all()
        studied_ids = [r[0] for r in studied]
        q = s.query(Word)
        if studied_ids:
            q = q.filter(~Word.id.in_(studied_ids))
        remaining = q.count()
        words = q.order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).limit(count).all()
        return {'words': [w.to_dict() for w in words], 'remaining': remaining}
    finally:
        s.close()


# ========== 设置 ==========

def get_setting(key, default=None):
    s = _get_session()
    try:
        setting = s.query(SystemSettings).filter(SystemSettings.key == key).first()
        return setting.value if setting else default
    finally:
        s.close()

def set_setting(key, value):
    s = _get_session()
    try:
        setting = s.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            setting.value = str(value)
            setting.updated_at = datetime.now()
        else:
            setting = SystemSettings(key=key, value=str(value))
            s.add(setting)
        s.commit()
        return True
    except:
        s.rollback()
        return False
    finally:
        s.close()


# ========== 学习记录 ==========

def record_study(word_id, study_type, result):
    """记录学习行为（防重复计数）"""
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
        s.flush()  # 写入DB，获得record.id

        today = date.today()
        # 防重复：同词同天同类型之前是否已经计过数了
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        already_counted = s.query(StudyRecord).filter(
            StudyRecord.word_id == word_id,
            StudyRecord.study_type == study_type,
            StudyRecord.studied_at.between(today_start, today_end),
            StudyRecord.id != record.id,
        ).count() > 0

        # 更新今日计划
        plan = s.query(DailyPlan).filter(DailyPlan.plan_date == today).first()
        if not already_counted:
            if plan:
                if study_type == 'new':
                    plan.new_words_done = (plan.new_words_done or 0) + 1
                elif study_type == 'review':
                    plan.review_done = (plan.review_done or 0) + 1
            else:
                plan = DailyPlan(
                    plan_date=today,
                    new_words_target=20,
                    new_words_done=1 if study_type == 'new' else 0,
                    review_done=1 if study_type == 'review' else 0,
                )
                s.add(plan)
        elif not plan:
            plan = DailyPlan(plan_date=today, new_words_target=20)
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
            # 自动创建，目标从设置中读取
            saved_target = get_setting('daily_new_words_target', '20')
            try:
                target = int(saved_target)
            except ValueError:
                target = 20
            plan = DailyPlan(
                plan_date=today, new_words_target=target,
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
    """获取今日要学的单词（新词+复习），锁定当日单词列表"""
    s = _get_session()
    try:
        today = date.today()
        plan = s.query(DailyPlan).filter(DailyPlan.plan_date == today).first()

        new_words = []
        review_words = []

        if plan and plan.word_ids_new:
            ids = [int(x) for x in plan.word_ids_new.split(',') if x.strip()]
            new_words = s.query(Word).filter(Word.id.in_(ids)).order_by(Word.id).all() if ids else []

        if plan and plan.word_ids_review:
            ids = [int(x) for x in plan.word_ids_review.split(',') if x.strip()]
            review_words = s.query(Word).filter(Word.id.in_(ids)).order_by(Word.id).all() if ids else []

        # 今日新词未锁定时：从本地算出并锁定
        if not new_words:
            studied = s.query(StudyRecord.word_id).distinct().all()
            studied_ids = [r[0] for r in studied]
            q = s.query(Word)
            if studied_ids:
                q = q.filter(~Word.id.in_(studied_ids))

            saved_target = get_setting('daily_new_words_target', '20')
            try:
                limit_n = int(saved_target)
            except ValueError:
                limit_n = 10

            available = q.order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).limit(limit_n).all()
            new_words = available

            # 锁定到plan中
            if available:
                ids_str = ','.join(str(w.id) for w in available)
                if plan:
                    plan.word_ids_new = ids_str
                else:
                    plan = DailyPlan(
                        plan_date=today,
                        new_words_target=limit_n,
                        word_ids_new=ids_str,
                    )
                    s.add(plan)
                s.commit()

        # 今日复习未锁定时：用艾宾浩斯算法计算
        if not review_words:
            from backend.ebbinghaus import calculate_todays_review
            all_records = s.query(StudyRecord).all()
            records_map = {}
            for rec in all_records:
                records_map.setdefault(rec.word_id, []).append({
                    'word_id': rec.word_id,
                    'studied_at': rec.studied_at.isoformat() if rec.studied_at else '',
                    'review_interval': rec.review_interval,
                    'result': rec.result,
                })
            due_ids = calculate_todays_review(records_map, today)
            if due_ids:
                review_words = s.query(Word).filter(Word.id.in_(due_ids)).order_by(Word.id).all()
                if plan:
                    plan.word_ids_review = ','.join(str(w.id) for w in review_words)
                else:
                    plan = DailyPlan(plan_date=today, word_ids_review=','.join(str(w.id) for w in review_words))
                    s.add(plan)
                s.commit()

        return {
            'new_words': [w.to_dict() for w in new_words],
            'review_words': [w.to_dict() for w in review_words],
            'new_words_done': plan.new_words_done if plan else 0,
            'new_words_target': plan.new_words_target if plan else 20,
            'review_done': plan.review_done if plan else 0,
            'review_target': plan.review_target if plan else len(review_words),
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
