#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 复习页面（翻卡模式 · 全新设计）
===============================
艾宾浩斯遗忘曲线复习
"""

import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, SECONDARY, SURFACE, SUCCESS, ERROR, BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, SPACING_SM, SPACING_MD, SPACING_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    SHADOW_SM, SHADOW_LG,
    FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL, FONT_DISPLAY,
)
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

        self.progress_text = ft.Text("加载中...", size=14, color=TEXT_SECONDARY)
        self.card_container = ft.Container(expand=True)
        self.action_buttons = ft.Container(visible=False)

    def build(self):
        header = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_STORIES, color=SECONDARY, size=20),
                    padding=ft.Padding(8, 8, 8, 8),
                    bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                    border_radius=10,
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text("复习单词", size=FONT_LG, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                    self.progress_text,
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text("0/0", size=13, weight=ft.FontWeight.BOLD, color=SECONDARY),
                    padding=ft.Padding(10, 6, 10, 6),
                    bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                    border_radius=20,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(left=PAGE_PADDING, top=SPACING_LG,
                               right=PAGE_PADDING, bottom=SPACING_SM),
        )

        self.action_buttons = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CLOSE, color=ft.Colors.WHITE, size=22),
                        ft.Text("忘记", color=ft.Colors.WHITE, size=14,
                                weight=ft.FontWeight.BOLD),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    padding=ft.Padding(36, 14, 36, 14),
                    bgcolor=ERROR,
                    border_radius=RADIUS_LG,
                    ink=True,
                    shadow=SHADOW_SM,
                    on_click=lambda e: self._handle_result('forget'),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK, color=ft.Colors.WHITE, size=22),
                        ft.Text("记得", color=ft.Colors.WHITE, size=14,
                                weight=ft.FontWeight.BOLD),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    padding=ft.Padding(36, 14, 36, 14),
                    bgcolor=SUCCESS,
                    border_radius=RADIUS_LG,
                    ink=True,
                    shadow=SHADOW_SM,
                    on_click=lambda e: self._handle_result('remember'),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=24),
            padding=ft.Padding(left=PAGE_PADDING, right=PAGE_PADDING, bottom=24),
            visible=False,
        )

        hint = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.TOUCH_APP, size=14, color=TEXT_HINT),
                ft.Container(width=4),
                ft.Text("点击翻转，自评记得/忘记", size=13, color=TEXT_HINT),
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding(left=8, top=4, right=8, bottom=8),
        )

        # 加载数据
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
        from app.services import api_service
        try:
            stats = api_service.get_study_stats()
            learned = stats.get('total_studied', 0) if stats else 0
        except:
            learned = 0
        if learned > 0:
            msg = msg or f"今日无需复习 ✓\n已学习 {learned} 个单词\n\n新学的单词将在1天后进入复习"
        else:
            msg = msg or "暂无需要复习的单词\n\n先去学习页面学单词\n学完的单词将在1天后进入复习"
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=64, color=TEXT_HINT),
                    padding=ft.Padding(20, 20, 20, 20),
                    bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                    border_radius=40,
                ),
                ft.Container(height=16),
                ft.Text(msg, size=FONT_LG, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                ft.Container(
                    content=ft.Text("去学新词", color=ft.Colors.WHITE, size=14,
                                   weight=ft.FontWeight.BOLD),
                    padding=ft.Padding(28, 12, 28, 12),
                    bgcolor=SECONDARY,
                    border_radius=RADIUS_XL,
                    ink=True,
                    on_click=lambda e: self.app.switch_to_page(1),
                ),
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
                ft.Container(height=4, bgcolor=SECONDARY,
                             border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0)),
                ft.Container(expand=True),
                ft.Text(wd['word'], size=FONT_DISPLAY, weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Text(wd.get('phonetic', ''), size=FONT_BODY,
                                    color=TEXT_SECONDARY, italic=True,
                                    text_align=ft.TextAlign.CENTER),
                    padding=ft.Padding(16, 6, 16, 6),
                    bgcolor=ft.Colors.with_opacity(0.06, SECONDARY),
                    border_radius=20,
                ),
                ft.Container(height=30),
                ft.Row([
                    ft.Icon(ft.Icons.TOUCH_APP, size=14, color=TEXT_HINT),
                    ft.Container(width=4),
                    ft.Text("回想意思，点击查看", size=13, color=TEXT_HINT),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            padding=ft.Padding(left=24, top=0, right=24, bottom=24),
            bgcolor=SURFACE,
            border_radius=RADIUS_LG,
            shadow=SHADOW_LG,
            margin=ft.Margin(left=20, right=20, top=12, bottom=12),
            ink=True,
            on_click=self._flip_card,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        self.action_buttons.visible = False
        self.card_container.content = ft.Column([front], spacing=0, tight=True)
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
        # 基本信息区
        sections.append(ft.Container(
            content=ft.Column([
                ft.Text(wd['word'], size=FONT_XXXL, weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY),
                ft.Container(height=4),
                ft.Row([
                    ft.Text(wd.get('phonetic', ''), size=FONT_BODY,
                            color=TEXT_SECONDARY, italic=True),
                    ft.Container(width=8),
                    ft.Container(
                        content=ft.Text(wd.get('pos', ''), size=FONT_SM,
                                        color=ft.Colors.WHITE),
                        padding=ft.Padding(8, 3, 8, 3),
                        bgcolor=SECONDARY,
                        border_radius=4,
                    ) if wd.get('pos') else ft.Container(),
                ], spacing=4),
                ft.Container(height=8),
                ft.Text(wd.get('meaning', ''), size=FONT_XL, weight=ft.FontWeight.W_500,
                        color=TEXT_PRIMARY),
            ], spacing=0),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
            bgcolor=ft.Colors.with_opacity(0.06, SECONDARY),
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(3, SECONDARY),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        ))

        if wd.get('examples'):
            sections.append(self._sec("📖 例句", wd['examples'],
                                      "#F3E5F5", "#CE93D8"))
        if wd.get('memory_methods'):
            sections.append(self._sec("💡 记忆方法", wd['memory_methods'],
                                      "#FFF8E1", "#FFB300"))
        if wd.get('collocations'):
            sections.append(self._sec("📝 固定搭配", wd['collocations'],
                                      "#E3F2FD", "#64B5F6"))
        if wd.get('extensions'):
            sections.append(self._sec("🔗 派生词/扩展", wd['extensions'],
                                      "#F1F8E9", "#81C784"))

        back = ft.Container(
            content=ft.Column(sections, spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=SURFACE,
            border_radius=RADIUS_LG,
            shadow=SHADOW_LG,
            margin=ft.Margin(left=16, right=16, top=12, bottom=12),
        )
        self.action_buttons.visible = True
        self.card_container.content = ft.Column([back], spacing=0, tight=True)
        self.page.update()

    def _sec(self, title, content, bg_color, accent_color):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                ]),
                ft.Container(height=6),
                ft.Text(content, size=FONT_BODY, color=TEXT_SECONDARY),
            ], spacing=0),
            padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            bgcolor=bg_color,
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(3, accent_color),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
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
            self.app.show_snackbar("✅ 记得！下次复习间隔增加", SUCCESS)
        else:
            wid = wd.get('id', 0)
            if wid not in self.remaining_queue:
                self.remaining_queue.append(wid)
            self._next_word()
            self.app.show_snackbar("💪 忘了没关系，今天稍后重学", ERROR)

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
        self.action_buttons.visible = False
        self.card_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CELEBRATION, size=72, color=SECONDARY),
                        padding=ft.Padding(20, 20, 20, 20),
                        bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                        border_radius=40,
                    ),
                    ft.Container(height=20),
                    ft.Text("复习完成！", size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=SECONDARY),
                    ft.Container(height=8),
                    ft.Text(f"今日复习 {self.review_done} 个单词",
                            size=FONT_BODY, color=TEXT_SECONDARY),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Text("返回首页", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(28, 12, 28, 12),
                        bgcolor=SECONDARY,
                        border_radius=RADIUS_XL,
                        ink=True,
                        on_click=lambda e: self.app.switch_to_page(0),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Container(expand=True),
        ])
        self.progress_text.value = f"今日复习: {self.review_done}/{self.review_total} ✅"
        self.page.update()
