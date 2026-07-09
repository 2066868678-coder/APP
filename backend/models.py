#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 数据模型
==================
定义单词和学习记录的SQLAlchemy数据模型
"""

from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    Float, DateTime, Boolean, JSON, ForeignKey, Date, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()


class Word(Base):
    """单词表 - 存储所有单词数据"""
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False, index=True)
    phonetic = Column(String(200), default='')
    pos = Column(String(50), default='')          # 词性
    meaning = Column(Text, default='')             # 中文释义
    examples = Column(Text, default='')            # 例句（JSON列表或'|'分隔）
    memory_methods = Column(Text, default='')      # 记忆方法（'|'分隔）
    derivatives = Column(Text, default='')         # 派生词
    collocations = Column(Text, default='')        # 固定搭配
    extensions = Column(Text, default='')          # 扩展内容
    chapter = Column(String(100), default='')      # 所属章节
    source_page = Column(Integer, default=0)       # 来源页码
    source_book = Column(String(50), default='')   # 来源书本（上下册）
    confidence = Column(Float, default=0.0)        # OCR置信度
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'phonetic': self.phonetic,
            'pos': self.pos,
            'meaning': self.meaning,
            'examples': self.examples,
            'memory_methods': self.memory_methods,
            'derivatives': self.derivatives,
            'collocations': self.collocations,
            'extensions': self.extensions,
            'chapter': self.chapter,
            'source_page': self.source_page,
            'source_book': self.source_book,
        }


class StudyRecord(Base):
    """学习记录表 - 存储每次学习行为"""
    __tablename__ = 'study_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey('words.id'), nullable=False)
    study_type = Column(String(20), nullable=False)  # 'new' 新词 / 'review' 复习
    result = Column(String(10), nullable=False)       # 'remember' 记得 / 'forget' 忘记
    studied_at = Column(DateTime, default=datetime.now)
    review_interval = Column(Integer, default=1)      # 下次复习间隔（天）

    def to_dict(self):
        return {
            'id': self.id,
            'word_id': self.word_id,
            'study_type': self.study_type,
            'result': self.result,
            'studied_at': self.studied_at.isoformat() if self.studied_at else None,
            'review_interval': self.review_interval,
        }


class DailyPlan(Base):
    """每日学习计划表"""
    __tablename__ = 'daily_plans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_date = Column(Date, nullable=False)
    new_words_target = Column(Integer, default=20)     # 每日新词目标
    new_words_done = Column(Integer, default=0)        # 今日已学新词数
    review_target = Column(Integer, default=0)         # 今日应复习数
    review_done = Column(Integer, default=0)           # 今日已复习数
    word_ids_new = Column(Text, default='')            # 今日新词ID列表（逗号分隔）
    word_ids_review = Column(Text, default='')         # 今日复习词ID列表
    completed = Column(Boolean, default=False)          # 是否已完成
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'plan_date': self.plan_date.isoformat() if self.plan_date else None,
            'new_words_target': self.new_words_target,
            'new_words_done': self.new_words_done,
            'review_target': self.review_target,
            'review_done': self.review_done,
            'word_ids_new': self.word_ids_new,
            'word_ids_review': self.word_ids_review,
            'completed': self.completed,
        }


class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = 'system_settings'

    key = Column(String(100), primary_key=True)
    value = Column(Text, default='')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def get_db_url():
    """获取数据库URL：优先使用环境变量（PostgreSQL），否则用SQLite"""
    env_url = os.environ.get('DATABASE_URL')
    if env_url:
        # Render的DATABASE_URL是postgres://格式，SQLAlchemy需要postgresql://
        return env_url.replace('postgres://', 'postgresql://')
    return 'sqlite:///database/words.db'


def init_database(db_url=None):
    """初始化数据库，创建所有表"""
    if db_url is None:
        db_url = get_db_url()
    is_sqlite = db_url.startswith('sqlite')
    connect_args = {'check_same_thread': False} if is_sqlite else {}
    engine = create_engine(db_url, echo=False, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine
