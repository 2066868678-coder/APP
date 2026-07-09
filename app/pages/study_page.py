#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 学习页面（翻卡模式）
===============================
标准背单词流程：
1. 展示英文单词（正面）
2. 用户回想意思
3. 点击翻转显示完整信息（来自书本的释义、例句、记忆法、搭配）
4. 自评"记得"或"不记得"
5. 记得 → 按艾宾浩斯进入下一复习间隔
6. 不记得 → 留在今日任务，稍后重排出现

数据来源：后端API（真实书本数据）
"""

import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import threading
import flet as ft
from app.services import api_service


class StudyPage:
    """学习新词页面 - 翻卡模式"""

    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.words = []
        self.word_index = 0
        self.remaining_queue = []
        self.new_words_done = 0
        self.total_new = 0
        self.flipped = False

        self.progress_text = ft.Text("加载中...", size=14, color=ft.Colors.GREY)
        self.card_container = ft.Container(expand=True)
        self.action_buttons = ft.Container(visible=False)

    def build(self):
        # 先加载数据
        words, target, done = self._load_data()

        header = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.GREEN, size=22),
                        ft.Text("学习新词", size=18, weight=ft.FontWeight.BOLD)]),
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

        if words:
            self.words = words
            self.total_new = target
            self.new_words_done = done
            self.word_index = 0
            self.remaining_queue = []
            self._show_current_word(initial=True)
        else:
            self.card_container.content = ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=64, color=ft.Colors.GREY_300),
                    ft.Text("暂无新词可学\n请先在设置中查看每日目标", size=16, color=ft.Colors.GREY,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=12),
                    ft.ElevatedButton("去设置", icon=ft.Icons.SETTINGS,
                        on_click=lambda e: self.app.switch_to_page(4)),
                    ft.Container(expand=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True,
            )
            self.progress_text.value = "今日: 0/0"

        return ft.Column([header, ft.Container(content=self.card_container, expand=True),
                          self.action_buttons], spacing=0, tight=True)

    def _build_empty(self, msg="🎉 今日新词已学完！"):
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Icon(ft.Icons.CELEBRATION, size=64, color=ft.Colors.GREEN),
                ft.Container(height=16),
                ft.Text(msg, size=16, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                ft.ElevatedButton("返回首页", icon=ft.Icons.HOME,
                    on_click=lambda e: self.app.switch_to_page(0)),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
        )

    def _load_data(self):
        """返回 (words, target, done)"""
        try:
            plan = api_service.get_today_plan()
            today_words = api_service.get_today_words()
            words = []
            target = api_service.get_daily_target()
            done = 0
            if plan and plan.get('plan'):
                target = plan['plan'].get('new_words_target', target)
                done = plan['plan'].get('new_words_done', 0)
            if today_words and today_words.get('new_words'):
                words = today_words['new_words']
            if not words:
                resp = api_service.get_new_words_for_study()
                if resp and resp.get('words'):
                    words = resp['words']
        except Exception:
            words = []
            target = api_service.get_daily_target()
            done = 0
        return words, target, done

    def _show_current_word(self, initial=False):
        wd = self._get_word()
        if not wd:
            self.card_container.content = self._build_empty()
            self.action_buttons.visible = False
            if not initial:
                self.page.update()
            return

        self.flipped = False
        # 正面：只显示英文单词
        front = ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Text(wd['word'], size=40, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87, text_align=ft.TextAlign.CENTER),
                ft.Container(height=12),
                ft.Text(wd.get('phonetic', ''), size=16, color=ft.Colors.GREY, italic=True,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=30),
                ft.Text("👆 点击查看详情", size=13, color=ft.Colors.GREY_400,
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
        # 基本信息
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

        # 直接从书本提取的例句
        if wd.get('examples'):
            sections.append(self._sec("📖 例句", wd['examples'], None, None))
        # 记忆方法（重点高亮）
        if wd.get('memory_methods'):
            sections.append(self._sec("💡 记忆方法", wd['memory_methods'],
                                      ft.Colors.AMBER_50, ft.Colors.AMBER_200))
        # 固定搭配
        if wd.get('collocations'):
            sections.append(self._sec("📝 固定搭配", wd['collocations'], None, None))
        # 派生词/扩展
        if wd.get('extensions'):
            sections.append(self._sec("🔗 派生词/扩展", wd['extensions'], None, None))

        back = ft.Container(
            content=ft.Column(sections, spacing=6, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
        )
        # 重新组装卡片
        card = ft.Container(
            content=back, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.BLACK12, offset=ft.Offset(0, 6)),
            margin=ft.Margin(left=24, right=24, top=16, bottom=16),
        )
        self.action_buttons.visible = True
        self.card_container.content = ft.Column([card], spacing=0, tight=True)
        self.page.update()

    def _sec(self, title, content, bg, border):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)]),
                ft.Container(height=4),
                ft.Text(content, size=14, color=ft.Colors.BLACK87),
            ], spacing=0),
            padding=ft.Padding(left=10, top=10, right=10, bottom=10),
            bgcolor=bg or ft.Colors.GREY_50,
            border_radius=8,
            border=ft.Border(left=ft.BorderSide(1, border), right=ft.BorderSide(1, border), top=ft.BorderSide(1, border), bottom=ft.BorderSide(1, border)) if border else None,
        )

    def _handle_result(self, result):
        wd = self._get_word()
        if not wd:
            return
        threading.Thread(target=lambda: api_service.record_study(
            wd.get('id', 0), 'new', result), daemon=True).start()

        if result == 'remember':
            self.new_words_done += 1
            self._next_word()
            self.app.show_snackbar("✅ 已记住！按艾宾浩斯安排下次复习")
        else:
            word_id = wd.get('id', 0)
            if word_id not in self.remaining_queue:
                self.remaining_queue.append(word_id)
            self._next_word()
            self.app.show_snackbar("💪 会再出现的！今天多练几次", ft.Colors.ORANGE)

    def _next_word(self):
        self.word_index += 1
        if self.word_index >= len(self.words) and self.remaining_queue:
            self._reshuffle()
        if self.word_index >= len(self.words):
            self._show_completion()
        else:
            self._show_current_word()

    def _reshuffle(self):
        """忘记的词再次插入队列"""
        forgot = list(set(self.remaining_queue))
        forgot_words = [w for w in self.words if w.get('id') in forgot]
        rest = [w for w in self.words[self.word_index:] if w.get('id') not in forgot]
        self.words = rest + forgot_words
        self.word_index = 0
        self.remaining_queue = []

    def _get_word(self):
        if not self.words or self.word_index >= len(self.words):
            return None
        return self.words[self.word_index]

    def _update_progress(self, initial=False):
        total = max(self.total_new, len(self.words))
        cur = self.word_index + 1
        done = self.new_words_done
        self.progress_text.value = f"今日新词: {done}/{total}  |  当前 {cur}/{total}"
        if not initial:
            self.progress_text.update()

    def _show_completion(self):
        self.card_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CELEBRATION, size=64, color=ft.Colors.GREEN),
                    ft.Container(height=16),
                    ft.Text("🎉 今日新词学完了！", size=24, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN),
                    ft.Container(height=8),
                    ft.Text(f"今日新学: {self.new_words_done} 个单词", size=16, color=ft.Colors.BLACK87),
                    ft.Container(height=20),
                    ft.ElevatedButton("返回首页", icon=ft.Icons.HOME,
                        on_click=lambda e: self.app.switch_to_page(0)),
                    ft.Container(height=8),
                    ft.ElevatedButton("去复习", icon=ft.Icons.AUTO_STORIES,
                        on_click=lambda e: self.app.switch_to_page(2)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Container(expand=True),
        ])
        self.action_buttons.visible = False
        self.progress_text.value = f"今日新词: {self.new_words_done}/{self.new_words_done} ✅"
        self.page.update()
