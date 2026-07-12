#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 学习页面（翻卡模式 · 全新设计）
===============================
标准背单词流程：
1. 展示英文单词（正面）
2. 用户回想意思
3. 点击翻转显示完整信息
4. 自评"记得"或"不记得"
"""

import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK, PRIMARY_CONTAINER,
    SECONDARY, BACKGROUND, SURFACE, SUCCESS, ERROR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    SHADOW_SM, SHADOW_MD, SHADOW_LG,
    FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL, FONT_DISPLAY,
)
from app.components.app_card import AppCard
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

        self.progress_text = ft.Text("加载中...", size=14, color=TEXT_SECONDARY)
        self.est_text = ft.Text("", size=12, color=TEXT_HINT)
        self.card_container = ft.Container(expand=True)

    def build(self):
        words, target, done = self._load_data()

        # 计算预计完成时间（剩余未学词 ÷ 每日目标）
        try:
            stats = api_service.get_stats()
            total = stats.get('total_words', 2281)
            learned = stats.get('learned_words', 0)
        except:
            total = 2281
            learned = 0
        remain = max(0, total - learned)
        cur_target = max(1, api_service.get_daily_target())  # 实时读取设置
        if remain > 0:
            est_days = (remain + cur_target - 1) // cur_target
            self.est_text.value = f"剩余{remain}词 · 每日{cur_target}词还需{est_days}天"
        else:
            self.est_text.value = "所有单词已学完！ 🎉"

        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.MENU_BOOK, color=PRIMARY, size=20),
                        padding=ft.Padding(8, 8, 8, 8),
                        bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                        border_radius=10,
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text("学习新词", size=FONT_LG, weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY),
                        self.progress_text,
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Text(f"{done}/{max(target, len(words))}",
                                        size=13, weight=ft.FontWeight.BOLD, color=PRIMARY),
                        padding=ft.Padding(10, 6, 10, 6),
                        bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                        border_radius=20,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=4),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.HOURGLASS_BOTTOM, size=12, color=TEXT_HINT),
                        ft.Container(width=4),
                        self.est_text,
                    ]),
                    padding=ft.Padding(left=2, top=0, right=2, bottom=0),
                ),
            ], spacing=0),
            padding=ft.Padding(left=PAGE_PADDING, top=SPACING_LG,
                               right=PAGE_PADDING, bottom=SPACING_SM),
        )

        if words:
            if not self.words or words != self.words:
                self.words = words
                self.word_index = 0
                self.remaining_queue = []
            self.total_new = target
            self.new_words_done = done
            # 先建按钮（_show_current_word 中会引用）
            self._build_action_buttons()
            self._show_current_word(initial=True)
        else:
            self.card_container.content = self._build_empty()
            self.progress_text.value = "今日: 0/0"
            self._build_action_buttons()

        return ft.Column([
            header,
            ft.Container(content=self.card_container, expand=True),
            self.action_buttons,
        ], spacing=0, tight=True)

    def _build_action_buttons(self):
        """操作按钮区域（需在 _show_current_word 之前调用）"""
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
        return self.action_buttons

    def _build_empty(self, msg="🎉 今日新词已学完！"):
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Icon(ft.Icons.CELEBRATION, size=64, color=PRIMARY),
                    padding=ft.Padding(20, 20, 20, 20),
                    bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                    border_radius=40,
                ),
                ft.Container(height=16),
                ft.Text(msg, size=FONT_LG, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                ft.Container(
                    content=ft.Text("返回首页", color=ft.Colors.WHITE, size=14,
                                   weight=ft.FontWeight.BOLD),
                    padding=ft.Padding(28, 12, 28, 12),
                    bgcolor=PRIMARY,
                    border_radius=RADIUS_XL,
                    ink=True,
                    on_click=lambda e: self.app.switch_to_page(0),
                ),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
        )

    def _load_data(self):
        if self.words and self.word_index < len(self.words):
            return self.words, self.total_new or 20, self.new_words_done
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
            if hasattr(self, 'action_buttons') and self.action_buttons:
                self.action_buttons.visible = False
            if not initial:
                self.page.update()
            return

        self.flipped = False

        # === 卡片正面 ===
        front = ft.Container(
            content=ft.Column([
                # 顶部装饰色条
                ft.Container(height=4, bgcolor=PRIMARY,
                             border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0)),
                ft.Container(expand=True),
                ft.Text(wd['word'], size=FONT_DISPLAY, weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=12),
                # 音标胶囊
                ft.Container(
                    content=ft.Text(wd.get('phonetic', ''), size=FONT_BODY,
                                    color=TEXT_SECONDARY, italic=True,
                                    text_align=ft.TextAlign.CENTER),
                    padding=ft.Padding(16, 6, 16, 6),
                    bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                    border_radius=20,
                ),
                ft.Container(height=30),
                ft.Row([
                    ft.Icon(ft.Icons.TOUCH_APP, size=14, color=TEXT_HINT),
                    ft.Container(width=4),
                    ft.Text("点击翻转查看详情", size=13, color=TEXT_HINT),
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

        self.card_container.content = ft.Column([front], spacing=0, tight=True)
        self.action_buttons.visible = False
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

        # === 基本信息区 ===
        sections.append(self._section_basic(wd))

        # === 例句 ===
        if wd.get('examples'):
            sections.append(self._section_info(
                "例句", ft.Icons.FORMAT_QUOTE, wd['examples'],
                "#F3E5F5", "#CE93D8",
            ))

        # === 记忆方法（高亮） ===
        if wd.get('memory_methods'):
            sections.append(self._section_info(
                "记忆方法", ft.Icons.LIGHTBULB_OUTLINE, wd['memory_methods'],
                "#FFF8E1", "#FFB300",
            ))

        # === 固定搭配 ===
        if wd.get('collocations'):
            sections.append(self._section_info(
                "固定搭配", ft.Icons.LINK, wd['collocations'],
                "#E3F2FD", "#64B5F6",
            ))

        # === 派生词/扩展 ===
        if wd.get('extensions'):
            sections.append(self._section_info(
                "派生词/扩展", ft.Icons.ACCOUNT_TREE_OUTLINED, wd['extensions'],
                "#F1F8E9", "#81C784",
            ))

        # === 卡片背面 ===
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

    def _section_basic(self, wd):
        """基本信息区 — 单词/音标/词性/释义"""
        return ft.Container(
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
                        bgcolor=PRIMARY,
                        border_radius=4,
                    ) if wd.get('pos') else ft.Container(),
                ], spacing=4),
                ft.Container(height=8),
                ft.Text(wd.get('meaning', ''), size=FONT_XL, weight=ft.FontWeight.W_500,
                        color=TEXT_PRIMARY),
            ], spacing=0),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
            bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(3, PRIMARY),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _section_info(self, title, icon, content, bg_color, accent_color):
        """信息区 — 带左边缘色条"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=16, color=accent_color),
                    ft.Container(width=6),
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                ], spacing=0),
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
            self.app.show_snackbar("💪 会再出现的！今天多练几次", ERROR)

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
        self.action_buttons.visible = False
        self.card_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CELEBRATION, size=72, color=PRIMARY),
                        padding=ft.Padding(20, 20, 20, 20),
                        bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                        border_radius=40,
                    ),
                    ft.Container(height=20),
                    ft.Text("太棒了！", size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=PRIMARY),
                    ft.Container(height=8),
                    ft.Text(f"今日新学 {self.new_words_done} 个单词",
                            size=FONT_BODY, color=TEXT_SECONDARY),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Text("返回首页", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(28, 12, 28, 12),
                        bgcolor=PRIMARY,
                        border_radius=RADIUS_XL,
                        ink=True,
                        on_click=lambda e: self.app.switch_to_page(0),
                    ),
                    ft.Container(height=8),
                    ft.TextButton("去复习",
                                  style=ft.ButtonStyle(color=PRIMARY),
                                  on_click=lambda e: self.app.switch_to_page(2)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Container(expand=True),
        ])
        self.progress_text.value = f"今日新词: {self.new_words_done}/{self.new_words_done} ✅"
        self.page.update()
