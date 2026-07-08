#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 复习页面（翻卡模式）
===============================
艾宾浩斯遗忘曲线复习：
1. 展示英文单词（正面）→ 回想意思
2. 点击翻转 → 查看完整信息
3. 自评"记得" → 间隔递增，进入下一轮
4. 自评"忘记" → 保留在今日复习中，稍后重排出现
"""

import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import threading
import flet as ft
from app.services import api_service


class ReviewPage:
    """复习页面 - 翻卡模式"""

    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.words = []
        self.word_index = 0
        self.remaining_queue = []
        self.review_done = 0
        self.review_total = 0
        self.flipped = False

        self.progress_text = ft.Text("加载中...", size=14, color=ft.Colors.GREY)
        self.card_container = ft.Container(expand=True)
        self.action_buttons = ft.Container(visible=False)

    def build(self):
        header = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.AUTO_STORIES, color=ft.Colors.BLUE, size=22),
                        ft.Text("复习单词", size=18, weight=ft.FontWeight.BOLD)]),
                ft.Container(height=4),
                self.progress_text,
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
        )

        self.action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("忘记", icon=ft.Icons.CLOSE, color=ft.Colors.RED,
                    bgcolor=ft.Colors.RED_50,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: self._handle_result('forget')),
                ft.Container(width=20),
                ft.ElevatedButton("记得", icon=ft.Icons.CHECK, color=ft.Colors.GREEN,
                    bgcolor=ft.Colors.GREEN_50,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: self._handle_result('remember')),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding(left=16, right=16, bottom=24),
            visible=False,
        )

        hint = ft.Container(
            content=ft.Row([
                ft.Text("👆 点击翻转，自评记得/忘记", size=12, color=ft.Colors.GREY_400),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding(left=8, top=8, right=8, bottom=8),
        )

        # 直接加载数据（本地数据库，很快）
        try:
            today = api_service.get_today_words()
            words = []
            if today and today.get('review_words'):
                words = today['review_words']
        except Exception:
            words = []

        if not words:
            self.card_container.content = self._build_empty()
            self.progress_text.value = "今日复习: 0/0"
        else:
            self.words = words
            self.review_total = len(words)
            self.word_index = 0
            self.remaining_queue = []
            self._show_current_word(initial=True)

        return ft.Column([
            header,
            ft.Container(content=self.card_container, expand=True),
            self.action_buttons, hint,
        ], spacing=0, tight=True)

    def _build_empty(self, msg=None):
        msg = msg or "暂无需要复习的单词\n学完新词后系统会根据艾宾浩斯遗忘曲线自动安排复习"
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=64, color=ft.Colors.GREY_300),
                ft.Container(height=16),
                ft.Text(msg, size=16, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                ft.ElevatedButton("去学新词", icon=ft.Icons.MENU_BOOK,
                    on_click=lambda e: self.app.switch_to_page(1)),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
        )

    def _load_data(self):
        try:
            today = api_service.get_today_words()
            words = []
            if today and today.get('review_words'):
                words = today['review_words']
        except Exception:
            words = []
        self._data_loaded(words)

    def _data_loaded(self, words):
        if not words:
            self.card_container.content = self._build_empty()
            self.progress_text.value = "今日复习: 0/0"
            self.action_buttons.visible = False
            return
        self.words = words
        self.review_total = len(words)
        self.review_done = 0
        self.word_index = 0
        self.remaining_queue = []
        self._show_current_word(initial=True)
        self.page.update()

    def _show_current_word(self, initial=False):
        wd = self._get_word()
        if not wd:
            self.card_container.content = self._build_empty("🎉 今日复习已完成！")
            self.action_buttons.visible = False
            if not initial:
                self.page.update()
            return
        self.flipped = False
        front = ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Text(wd['word'], size=40, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK87, text_align=ft.TextAlign.CENTER),
                ft.Container(height=12),
                ft.Text(wd.get('phonetic', ''), size=16, color=ft.Colors.GREY, italic=True,
                    text_align=ft.TextAlign.CENTER),
                ft.Container(height=30),
                ft.Text("👆 回想意思，点击查看", size=13, color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            padding=ft.Padding(left=30, top=30, right=30, bottom=30),
        )
        card = ft.Container(
            content=front, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.BLACK12, offset=ft.Offset(0, 6)),
            margin=ft.Margin(left=24, right=24, top=16, bottom=16),
            ink=True, on_click=self._flip_card,
        )
        self.action_buttons.visible = False
        self.card_container.content = ft.Column([card], spacing=0, tight=True)
        self._update_progress(initial=initial)
        if not initial:
            self.page.update()

    def _flip_card(self, e):
        if self.flipped:
            return
        self.flipped = True
        wd = self._get_word()
        if not wd:
            return
        sections = []
        sections.append(ft.Container(
            content=ft.Column([
                ft.Text(wd['word'], size=26, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text(wd.get('phonetic', ''), size=14, color=ft.Colors.GREY, italic=True),
                    ft.Container(width=8),
                    ft.Container(content=ft.Text(wd.get('pos', ''), size=12, color=ft.Colors.WHITE),
                        padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                        bgcolor=ft.Colors.GREEN, border_radius=4,
                    ) if wd.get('pos') else ft.Container(),
                ], spacing=4),
                ft.Container(height=6),
                ft.Text(wd.get('meaning', ''), size=18, weight=ft.FontWeight.W_500,
                    color=ft.Colors.BLACK87),
            ], spacing=4),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12), bgcolor=ft.Colors.INDIGO_50, border_radius=8,
        ))
        if wd.get('examples'):
            sections.append(self._sec("📖 例句", wd['examples']))
        if wd.get('memory_methods'):
            sections.append(self._sec("💡 记忆方法", wd['memory_methods']))
        if wd.get('collocations'):
            sections.append(self._sec("📝 固定搭配", wd['collocations']))
        if wd.get('extensions'):
            sections.append(self._sec("🔗 派生词/扩展", wd['extensions']))
        back = ft.Container(
            content=ft.Column(sections, spacing=6, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
        )
        card = ft.Container(
            content=back, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.BLACK12, offset=ft.Offset(0, 6)),
            margin=ft.Margin(left=24, right=24, top=16, bottom=16),
        )
        self.action_buttons.visible = True
        self.card_container.content = ft.Column([card], spacing=0, tight=True)
        self.page.update()

    def _sec(self, title, content):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Container(height=4),
                ft.Text(content, size=14, color=ft.Colors.BLACK87),
            ], spacing=0),
            padding=ft.Padding(left=10, top=10, right=10, bottom=10), bgcolor=ft.Colors.GREY_50, border_radius=8,
        )

    def _handle_result(self, result):
        wd = self._get_word()
        if not wd:
            return
        threading.Thread(target=lambda: api_service.record_study(
            wd.get('id', 0), 'review', result), daemon=True).start()
        if result == 'remember':
            self.review_done += 1
            self._next_word()
            self.app.show_snackbar("✅ 记得！下次复习间隔增加", ft.Colors.GREEN)
        else:
            wid = wd.get('id', 0)
            if wid not in self.remaining_queue:
                self.remaining_queue.append(wid)
            self._next_word()
            self.app.show_snackbar("💪 忘了没关系，今天稍后重学", ft.Colors.ORANGE)

    def _next_word(self):
        self.word_index += 1
        if self.word_index >= len(self.words) and self.remaining_queue:
            self._reshuffle()
        if self.word_index >= len(self.words):
            self._show_completion()
        else:
            self._show_current_word()

    def _reshuffle(self):
        forgot = list(set(self.remaining_queue))
        fw = [w for w in self.words if w.get('id') in forgot]
        rest = [w for w in self.words[self.word_index:] if w.get('id') not in forgot]
        self.words = rest + fw
        self.word_index = 0
        self.remaining_queue = []

    def _get_word(self):
        if not self.words or self.word_index >= len(self.words):
            return None
        return self.words[self.word_index]

    def _update_progress(self, initial=False):
        self.progress_text.value = f"今日复习: {self.review_done}/{self.review_total}  |  当前 {min(self.word_index+1, self.review_total)}/{self.review_total}"
        if not initial:
            self.progress_text.update()

    def _show_completion(self):
        self.card_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CELEBRATION, size=64, color=ft.Colors.GREEN),
                    ft.Container(height=16),
                    ft.Text("🎉 复习完成！", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ft.Container(height=8),
                    ft.Text(f"今日复习: {self.review_done} 个单词", size=16, color=ft.Colors.BLACK87),
                    ft.Container(height=20),
                    ft.ElevatedButton("返回首页", icon=ft.Icons.HOME,
                        on_click=lambda e: self.app.switch_to_page(0)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Container(expand=True),
        ])
        self.action_buttons.visible = False
        self.progress_text.value = f"今日复习: {self.review_done}/{self.review_total} ✅"
        self.page.update()
