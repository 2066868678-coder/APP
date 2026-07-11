#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - FastAPI后端服务
========================
提供：
1. 单词数据查询API
2. 每日学习计划API
3. 艾宾浩斯复习调度API
4. 学习进度统计API
5. 云同步API

启动方式：
    python backend/main.py
# 或者：
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os
import json
import csv
import math
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import Session

from backend.models import (
    Base, Word, StudyRecord, DailyPlan, SystemSettings, init_database
)
from backend.ebbinghaus import (
    get_next_review_interval, should_review_today,
    calculate_todays_review
)

# ============================================================
# 配置
# ============================================================

# 数据库路径（相对于项目根目录）
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "words.db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ocr", "output")

# 确保数据库目录存在
os.makedirs(DB_DIR, exist_ok=True)

# ============================================================
# 初始化FastAPI
# ============================================================

app = FastAPI(
    title="单词突围 API",
    description="单词突围App后端服务 - 学习计划、复习调度、进度统计、云同步",
    version="1.0.0",
)

# 跨域支持（手机App访问需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
engine = init_database(f'sqlite:///{DB_PATH}')


# ============================================================
# 数据导入
# ============================================================

def import_words_from_json(json_path: str) -> int:
    """从JSON文件导入单词数据到数据库"""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"找不到JSON文件：{json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    session = Session(engine)
    count = 0

    try:
        for item in words_data:
            word = item.get('word', '').strip()
            if not word:
                continue

            # 检查是否已存在
            existing = session.query(Word).filter(Word.word == word).first()
            if existing:
                continue

            # 列表字段转字符串
            def list_to_str(field):
                val = item.get(field, [])
                if isinstance(val, list):
                    return ' | '.join(val)
                return str(val) if val else ''

            new_word = Word(
                word=word,
                phonetic=item.get('phonetic', ''),
                pos=item.get('pos', ''),
                meaning=item.get('meaning', ''),
                examples=list_to_str('examples'),
                memory_methods=list_to_str('memory_methods'),
                derivatives=list_to_str('derivatives'),
                collocations=list_to_str('collocations'),
                extensions=list_to_str('extensions'),
                chapter=item.get('chapter', ''),
                source_page=item.get('source_page', 0),
                source_book=item.get('source_book', ''),
                confidence=item.get('confidence', 0.0),
            )
            session.add(new_word)
            count += 1

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    return count


def import_words_from_csv(csv_path: str) -> int:
    """从CSV文件导入单词数据"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"找不到CSV文件：{csv_path}")

    session = Session(engine)
    count = 0

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row.get('word', '').strip()
                if not word:
                    continue

                existing = session.query(Word).filter(Word.word == word).first()
                if existing:
                    continue

                new_word = Word(
                    word=word,
                    phonetic=row.get('phonetic', ''),
                    pos=row.get('pos', ''),
                    meaning=row.get('meaning', ''),
                    examples=row.get('examples', ''),
                    memory_methods=row.get('memory_methods', ''),
                    derivatives=row.get('derivatives', ''),
                    collocations=row.get('collocations', ''),
                    extensions=row.get('extensions', ''),
                    chapter=row.get('chapter', ''),
                    source_page=int(row.get('source_page', 0) or 0),
                    source_book=row.get('source_book', ''),
                    confidence=float(row.get('confidence', 0) or 0),
                )
                session.add(new_word)
                count += 1

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    return count


# ============================================================
# API端点
# ============================================================

# ----- 单词查询 -----
# 注意：静态路径必须在参数化路径之前定义！

@app.get("/api/words")
def list_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    chapter: Optional[str] = None,
    search: Optional[str] = None,
):
    """获取单词列表（分页）"""
    session = Session(engine)
    try:
        query = session.query(Word)

        if chapter:
            query = query.filter(Word.chapter == chapter)
        if search:
            query = query.filter(Word.word.like(f'%{search}%'))

        total = query.count()
        total_pages = math.ceil(total / page_size)

        words = query.order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return JSONResponse(content={
            'words': [w.to_dict() for w in words],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        })
    finally:
        session.close()


@app.get("/api/words/random")
def get_random_words(count: int = Query(10, ge=1, le=50)):
    """随机获取N个单词"""
    session = Session(engine)
    try:
        words = session.query(Word).order_by(func.random()).limit(count).all()
        return JSONResponse(content={
            'words': [w.to_dict() for w in words],
        })
    finally:
        session.close()


@app.get("/api/words/new-for-study")
def get_new_words_for_study(count: int = Query(10, ge=1, le=50)):
    """获取今日新词（从未学习过的单词）"""
    session = Session(engine)
    try:
        studied_ids = session.query(StudyRecord.word_id).distinct().all()
        studied_ids = [r[0] for r in studied_ids]

        query = session.query(Word)
        if studied_ids:
            query = query.filter(~Word.id.in_(studied_ids))

        words = query.order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).limit(count).all()

        return JSONResponse(content={
            'words': [w.to_dict() for w in words],
            'remaining': query.count(),
        })
    finally:
        session.close()


@app.get("/api/words/{word_id}")
def get_word(word_id: int):
    """获取单个单词的完整信息"""
    session = Session(engine)
    try:
        word = session.query(Word).filter(Word.id == word_id).first()
        if not word:
            raise HTTPException(status_code=404, detail="单词不存在")
        return JSONResponse(content=word.to_dict())
    finally:
        session.close()


# ----- 学习记录 -----

@app.post("/api/study/record")
def record_study(
    word_id: int = Body(...),
    study_type: str = Body(...),
    result: str = Body(...),
):
    """记录一次学习行为"""
    if study_type not in ['new', 'review']:
        raise HTTPException(status_code=400, detail="study_type 必须是 'new' 或 'review'")
    if result not in ['remember', 'forget']:
        raise HTTPException(status_code=400, detail="result 必须是 'remember' 或 'forget'")

    session = Session(engine)
    try:
        # 验证单词存在
        word = session.query(Word).filter(Word.id == word_id).first()
        if not word:
            raise HTTPException(status_code=404, detail="单词不存在")

        # 计算复习间隔
        last_record = session.query(StudyRecord).filter(
            StudyRecord.word_id == word_id
        ).order_by(StudyRecord.id.desc()).first()

        if last_record:
            current_interval = last_record.review_interval
        else:
            current_interval = 0

        remembered = (result == 'remember')
        next_interval = get_next_review_interval(current_interval, remembered)

        # 创建学习记录
        record = StudyRecord(
            word_id=word_id,
            study_type=study_type,
            result=result,
            review_interval=next_interval,
        )
        session.add(record)

        # 更新今日计划
        today = date.today()
        plan = session.query(DailyPlan).filter(
            DailyPlan.plan_date == today
        ).first()

        if plan:
            if study_type == 'new':
                plan.new_words_done += 1
            else:
                plan.review_done += 1
        else:
            # 创建今日计划（如果还没有）
            plan = DailyPlan(
                plan_date=today,
                new_words_target=get_setting(session, 'daily_new_words_target', 20),
                new_words_done=1 if study_type == 'new' else 0,
                review_done=1 if study_type == 'review' else 0,
            )
            session.add(plan)

        session.commit()

        return JSONResponse(content={
            'success': True,
            'record': record.to_dict(),
            'next_review_interval': next_interval,
        })
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ----- 每日计划 -----

@app.get("/api/plan/today")
def get_today_plan():
    """获取今日学习计划"""
    session = Session(engine)
    try:
        today = date.today()
        plan = session.query(DailyPlan).filter(
            DailyPlan.plan_date == today
        ).first()

        if not plan:
            # 自动创建今日计划
            new_words_target = int(get_setting(session, 'daily_new_words_target', 20))

            # 计算今日复习量
            all_records = session.query(StudyRecord).all()
            word_records_map = {}
            for r in all_records:
                if r.word_id not in word_records_map:
                    word_records_map[r.word_id] = []
                word_records_map[r.word_id].append(r.to_dict())

            review_ids = calculate_todays_review(word_records_map, today)
            review_target = len(review_ids)

            plan = DailyPlan(
                plan_date=today,
                new_words_target=new_words_target,
                new_words_done=0,
                review_target=review_target,
                review_done=0,
                word_ids_review=','.join(str(rid) for rid in review_ids[:50]),
            )
            session.add(plan)
            session.commit()

        # 获取统计数据
        total_words = session.query(func.count(Word.id)).scalar() or 0
        learned_words = session.query(StudyRecord.word_id).distinct().count()
        mastered_words = session.query(
            StudyRecord.word_id
        ).filter(
            StudyRecord.result == 'remember',
            StudyRecord.review_interval >= 15
        ).distinct().count()

        return JSONResponse(content={
            'plan': plan.to_dict(),
            'stats': {
                'total_words': total_words,
                'learned_words': learned_words,
                'mastered_words': mastered_words,
            },
        })
    finally:
        session.close()


@app.post("/api/plan/today/new-words")
def set_new_words_target(target: int = Body(..., embed=True)):
    """设置每日新词目标"""
    if target < 1 or target > 200:
        raise HTTPException(status_code=400, detail="目标值应在1-200之间")

    session = Session(engine)
    try:
        set_setting(session, 'daily_new_words_target', str(target))

        # 更新今日计划
        today = date.today()
        plan = session.query(DailyPlan).filter(
            DailyPlan.plan_date == today
        ).first()
        if plan:
            plan.new_words_target = target
            session.commit()

        return JSONResponse(content={'success': True, 'target': target})
    finally:
        session.close()


@app.get("/api/plan/today/unlocked-words")
def get_todays_unlocked_words():
    """获取今日学习计划中的单词"""
    session = Session(engine)
    try:
        plan = session.query(DailyPlan).filter(
            DailyPlan.plan_date == date.today()
        ).first()

        if not plan:
            return JSONResponse(content={
                'new_words': [],
                'review_words': [],
                'daily_target': int(get_setting(session, 'daily_new_words_target', 20)),
            })

        # 解析今日新词ID（如果没有预设，从未学过的词中取）
        new_word_ids = []
        if plan.word_ids_new:
            new_word_ids = [int(x) for x in plan.word_ids_new.split(',') if x]

        # 今日复习词
        review_word_ids = []
        if plan.word_ids_review:
            review_word_ids = [int(x) for x in plan.word_ids_review.split(',') if x]

        # 获取单词详情
        new_words = []
        if new_word_ids:
            new_words = session.query(Word).filter(
                Word.id.in_(new_word_ids)
            ).order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).all()

        review_words = []
        if review_word_ids:
            review_words = session.query(Word).filter(
                Word.id.in_(review_word_ids)
            ).order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).all()

        return JSONResponse(content={
            'new_words': [w.to_dict() for w in new_words],
            'review_words': [w.to_dict() for w in review_words],
            'new_words_done': plan.new_words_done,
            'new_words_target': plan.new_words_target,
            'review_done': plan.review_done,
            'review_target': plan.review_target,
        })
    finally:
        session.close()


# ----- 统计信息 -----

@app.get("/api/stats")
def get_statistics():
    """获取学习统计数据"""
    session = Session(engine)
    try:
        total_words = session.query(func.count(Word.id)).scalar() or 0
        learned_words = session.query(StudyRecord.word_id).distinct().count()

        # 掌握：完成15天复习间隔的单词
        mastered_words = session.query(
            StudyRecord.word_id
        ).filter(
            StudyRecord.review_interval >= 15,
            StudyRecord.result == 'remember'
        ).distinct().count()

        # 今日统计
        today = date.today()
        today_plan = session.query(DailyPlan).filter(
            DailyPlan.plan_date == today
        ).first()

        # 本周学习量
        week_ago = today - timedelta(days=7)
        week_study = session.query(func.count(StudyRecord.id)).filter(
            StudyRecord.studied_at >= week_ago
        ).scalar() or 0

        # 学习天数
        study_days = session.query(DailyPlan.plan_date).filter(
            DailyPlan.new_words_done > 0
        ).distinct().count()

        # 连续学习天数
        streak = 0
        check_date = today
        while True:
            day_plan = session.query(DailyPlan).filter(
                DailyPlan.plan_date == check_date
            ).first()
            if day_plan and (day_plan.new_words_done > 0 or day_plan.review_done > 0):
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return JSONResponse(content={
            'total_words': total_words,
            'learned_words': learned_words,
            'mastered_words': mastered_words,
            'progress_percent': round(learned_words / total_words * 100, 1) if total_words > 0 else 0,
            'today': today_plan.to_dict() if today_plan else None,
            'week_study_count': week_study,
            'study_days': study_days,
            'streak_days': streak,
        })
    finally:
        session.close()


@app.get("/api/stats/history")
def get_study_history(days: int = Query(30, ge=7, le=365)):
    """获取学习历史（用于图表展示）"""
    session = Session(engine)
    try:
        start_date = date.today() - timedelta(days=days)
        plans = session.query(DailyPlan).filter(
            DailyPlan.plan_date >= start_date
        ).order_by(DailyPlan.plan_date).all()

        history = []
        for p in plans:
            history.append({
                'date': p.plan_date.isoformat() if p.plan_date else None,
                'new_words_done': p.new_words_done,
                'review_done': p.review_done,
                'total_done': p.new_words_done + p.review_done,
            })

        return JSONResponse(content={'history': history, 'days': days})
    finally:
        session.close()


@app.get("/api/words/all-with-status")
def get_all_words_with_status():
    """返回全部单词及其学习状态"""
    session = Session(engine)
    try:
        studied_ids = set(r[0] for r in session.query(StudyRecord.word_id).distinct().all())
        words = session.query(Word).order_by(Word.chapter, Word.source_page, Word.id).all()
        result = []
        for w in words:
            result.append({
                'id': w.id, 'word': w.word, 'chapter': w.chapter,
                'source_page': w.source_page, 'studied': w.id in studied_ids,
            })
        return JSONResponse(content={'words': result, 'total': len(result), 'studied': len(studied_ids)})
    finally:
        session.close()


# ----- 数据导入/导出 -----

@app.post("/api/admin/import-json")
def import_json_data(json_filename: str = Body(...)):
    """从OCR输出的JSON文件导入单词数据"""
    json_path = os.path.join(DATA_DIR, json_filename)
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail=f"文件不存在：{json_path}")

    try:
        count = import_words_from_json(json_path)
        return JSONResponse(content={
            'success': True,
            'imported_count': count,
            'message': f'成功导入 {count} 个单词',
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/import-csv")
def import_csv_data(csv_filename: str = Body(...)):
    """从OCR输出的CSV文件导入单词数据"""
    csv_path = os.path.join(DATA_DIR, csv_filename)
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"文件不存在：{csv_path}")

    try:
        count = import_words_from_csv(csv_path)
        return JSONResponse(content={
            'success': True,
            'imported_count': count,
            'message': f'成功导入 {count} 个单词',
        })
    finally:
        pass


@app.get("/api/admin/export-json")
def export_words_json():
    """导出所有单词为JSON"""
    session = Session(engine)
    try:
        words = session.query(Word).order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).all()
        return JSONResponse(content={
            'words': [w.to_dict() for w in words],
            'total': len(words),
        })
    finally:
        session.close()


# ----- 云同步 -----

@app.post("/api/sync/upload")
def sync_upload(data: dict = Body(...)):
    """
    上传学习数据到云端

    请求格式：
    {
        "user_id": "用户的唯一标识",
        "records": [学习记录...],
        "settings": {设置...}
    }
    """
    # 将数据保存到同步表中
    session = Session(engine)
    try:
        user_id = data.get('user_id', 'default')
        records = data.get('records', [])
        settings = data.get('settings', {})

        # 保存同步数据到数据库
        sync_data = json.dumps({
            'records': records,
            'settings': settings,
            'synced_at': datetime.now().isoformat(),
        })

        # 更新系统设置中的同步数据
        set_setting(session, f'sync_data_{user_id}', sync_data)
        set_setting(session, 'last_sync_time', datetime.now().isoformat())

        return JSONResponse(content={
            'success': True,
            'synced_at': datetime.now().isoformat(),
            'records_count': len(records),
        })
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/api/sync/download")
def sync_download(user_id: str = Query('default')):
    """从云端下载学习数据"""
    session = Session(engine)
    try:
        # 获取同步数据
        sync_data_str = get_setting(session, f'sync_data_{user_id}', '{}')
        sync_data = json.loads(sync_data_str)

        # 获取所有单词数据
        words = session.query(Word).order_by(Word.source_book, Word.chapter, Word.source_page, Word.id).all()
        records = session.query(StudyRecord).order_by(StudyRecord.id).all()

        return JSONResponse(content={
            'words': [w.to_dict() for w in words],
            'records': [r.to_dict() for r in records],
            'sync_data': sync_data,
            'last_sync_time': get_setting(session, 'last_sync_time', ''),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ----- 健康检查 -----

@app.get("/api/health")
def health_check():
    """健康检查接口"""
    session = Session(engine)
    try:
        word_count = session.query(func.count(Word.id)).scalar() or 0
        record_count = session.query(func.count(StudyRecord.id)).scalar() or 0
        return JSONResponse(content={
            'status': 'ok',
            'database': os.path.basename(DB_PATH),
            'words_count': word_count,
            'records_count': record_count,
            'time': datetime.now().isoformat(),
        })
    finally:
        session.close()


# ============================================================
# 辅助函数
# ============================================================

def get_setting(session: Session, key: str, default: str = '') -> str:
    """获取系统设置"""
    setting = session.query(SystemSettings).filter(
        SystemSettings.key == key
    ).first()
    return setting.value if setting else default


def set_setting(session: Session, key: str, value: str):
    """设置系统设置"""
    setting = session.query(SystemSettings).filter(
        SystemSettings.key == key
    ).first()
    if setting:
        setting.value = value
        setting.updated_at = datetime.now()
    else:
        setting = SystemSettings(key=key, value=value)
        session.add(setting)
    session.commit()


# ============================================================
# 启动入口
# ============================================================

if __name__ == '__main__':
    import uvicorn

    print("=" * 50)
    print("单词突围 - 后端服务")
    print(f"数据库：{DB_PATH}")
    print("=" * 50)
    print()
    print("启动服务后，在浏览器访问：")
    print("  http://localhost:8000/api/health  → 检查服务状态")
    print()
    print("按 Ctrl+C 停止服务")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
