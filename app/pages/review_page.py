#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 复习页面（翻卡模式 · 增强视觉设计）
===============================
艾宾浩斯遗忘曲线复习
"""

import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, SECONDARY, SURFACE, SUCCESS, ERROR, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_XXL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_FULL, RADIUS_XS,
    SHADOW_SM, SHADOW_LG,
    FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL, FONT_DISPLAY,
    GRADIENT_REVIEW,
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
        self._counted_ids = set()  # 当天已计数的词ID（防重复）
        self._since_repeat = 0     # 距上次穿插不熟词复习过的词数
        self.REPEAT_GAP = 5        # 每复习5个词穿插一个"模糊/不记得"的词

        self.progress_text = ft.Text("加载中...", size=14, color=TEXT_SECONDARY)
        self.badge_text = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.card_container = ft.Container(expand=True)
        self.action_buttons = ft.Container(visible=False)

    def build(self):
        # 持久控件刷新当前色板（模式切换后重新取色）
        self.progress_text.color = TEXT_SECONDARY

        # === Enhanced Header (Sky-themed) ===
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    # Icon with gradient background + subtle shadow
                    ft.Container(
                        content=ft.Icon(ft.Icons.AUTO_STORIES, color=ft.Colors.WHITE, size=20),
                        padding=ft.Padding(10, 10, 10, 10),
                        gradient=GRADIENT_REVIEW,
                        border_radius=RADIUS_MD,
                        shadow=ft.BoxShadow(
                            blur_radius=8, color=ft.Colors.with_opacity(0.25, SECONDARY),
                            offset=ft.Offset(0, 2),
                        ),
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text("复习单词", size=FONT_LG, weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY),
                        self.progress_text,
                    ], spacing=2, expand=True),
                    # Progress badge with gradient background
                    ft.Container(
                        content=self.badge_text,
                        padding=ft.Padding(14, 6, 14, 6),
                        gradient=GRADIENT_REVIEW,
                        border_radius=RADIUS_FULL,
                        shadow=ft.BoxShadow(
                            blur_radius=6, color=ft.Colors.with_opacity(0.20, SECONDARY),
                            offset=ft.Offset(0, 2),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=0),
            padding=ft.Padding(left=PAGE_PADDING, top=SPACING_LG,
                               right=PAGE_PADDING, bottom=SPACING_SM),
        )

        # Action buttons with enhanced styling
        self._build_action_buttons()

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
            self.progress_text.value = "剩余 0 个"
            self.badge_text.value = "0"
        else:
            self.words = words
            self.review_total = len(words)
            self.review_done = today.get('review_done', 0) if today else 0
            self.word_index = 0
            self.remaining_queue = []
            self._counted_ids = set()
            self._since_repeat = 0
            self._show_current_word(initial=True)

        return ft.Column([
            header,
            ft.Container(content=self.card_container, expand=True),
            self.action_buttons,
        ], spacing=0, tight=True)

    def _build_action_buttons(self):
        """操作按钮区域 — 三档熟悉程度（增强视觉风格）"""
        def _make_button(icon, text, bg_color, tooltip_text, result_level):
            return ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(icon, color=ft.Colors.WHITE, size=18),
                        padding=ft.Padding(0, 2, 0, 0),
                    ),
                    ft.Text(text, color=ft.Colors.WHITE, size=11,
                            weight=ft.FontWeight.W_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                padding=ft.Padding(20, 12, 20, 12),
                bgcolor=bg_color,
                border_radius=RADIUS_FULL,
                shadow=ft.BoxShadow(
                    blur_radius=8, color=ft.Colors.with_opacity(0.25, bg_color),
                    offset=ft.Offset(0, 3),
                ),
                expand=True,
                tooltip=tooltip_text,
                on_click=lambda e: self._handle_result(result_level),
                ink=True,
            )

        self.action_buttons = ft.Container(
            content=ft.Column([
                ft.Row([
                    # 熟悉 — Emerald
                    _make_button(ft.Icons.STAR, "熟悉",
                                 SUCCESS, "近期不再复习", 'familiar'),
                    # 模糊 — Sky
                    _make_button(ft.Icons.AUTO_AWESOME, "模糊",
                                 SECONDARY, "正常艾宾浩斯复习", 'vague'),
                    # 不记得 — Red
                    _make_button(ft.Icons.REPLAY, "不记得",
                                 ERROR, "今天多练几次", 'forget'),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(height=6),
                ft.Text("回顾单词和固定搭配，点击翻转查看答案", size=11, color=TEXT_HINT,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=PAGE_PADDING, right=PAGE_PADDING, bottom=16),
            visible=False,
        )
        return self.action_buttons

    def _build_empty(self, msg=None):
        """空状态 — 增强视觉设计（Sky主题）"""
        from app.services import api_service
        try:
            stats = api_service.get_stats()
            learned = stats.get('learned_words', 0) if stats else 0
        except:
            learned = 0
        if learned > 0:
            msg = msg or f"今日无需复习 ✓\n已学习 {learned} 个单词\n\n新学的单词将在1天后进入复习"
        else:
            msg = msg or "暂无需要复习的单词\n\n先去学习页面学单词\n学完的单词将在1天后进入复习"
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                # Icon with gradient background
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=64, color=ft.Colors.WHITE),
                    padding=ft.Padding(20, 20, 20, 20),
                    gradient=GRADIENT_REVIEW,
                    border_radius=40,
                    shadow=ft.BoxShadow(
                        blur_radius=16, color=ft.Colors.with_opacity(0.25, SECONDARY),
                        offset=ft.Offset(0, 6),
                    ),
                ),
                ft.Container(height=16),
                ft.Text(msg, size=FONT_LG, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                # "去学新词" gradient button
                ft.Container(
                    content=ft.Text("去学新词", color=ft.Colors.WHITE, size=14,
                                   weight=ft.FontWeight.BOLD),
                    padding=ft.Padding(28, 12, 28, 12),
                    gradient=GRADIENT_REVIEW,
                    border_radius=RADIUS_XL,
                    shadow=ft.BoxShadow(
                        blur_radius=10, color=ft.Colors.with_opacity(0.25, SECONDARY),
                        offset=ft.Offset(0, 4),
                    ),
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
            self.progress_text.value = "剩余 0 个"
            self.badge_text.value = "0"
            self.action_buttons.visible = False
            return
        self.words = words
        self.review_total = len(words)
        self.review_done = 0
        self.word_index = 0
        self.remaining_queue = []
        self._counted_ids = set()
        self._since_repeat = 0
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

        # 提取固定搭配（仅英文部分，用于反推练习）
        collocation_en = []
        if wd.get('collocations'):
            raw_items = [t.strip() for t in wd['collocations'].replace('；', '|').replace(';', '|').split('|') if t.strip()]
            for item in raw_items:
                match = re.search(r'[一-鿿]', item)
                if match:
                    en_part = item[:match.start()].strip()
                    if en_part:
                        collocation_en.append(en_part)
                else:
                    collocation_en.append(item)

        # === Card Front (Enhanced) ===
        front = ft.Container(
            content=ft.Column([
                # Sky gradient decoration strip at top
                ft.Container(
                    height=4,
                    gradient=GRADIENT_REVIEW,
                    border_radius=ft.BorderRadius(top_left=20, top_right=20,
                                                   bottom_left=0, bottom_right=0),
                ),
                ft.Container(expand=True),
                # Word with subtle letter spacing
                ft.Text(
                    wd['word'],
                    size=FONT_DISPLAY,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=12),
                # Pronunciation button + phonetic badge row
                ft.Row([
                    ft.Container(expand=True),
                    # Phonetic badge with elegant pill shape
                    ft.Container(
                        content=ft.Text(wd.get('phonetic', ''), size=FONT_BODY,
                                        color=TEXT_SECONDARY, italic=True,
                                        text_align=ft.TextAlign.CENTER),
                        padding=ft.Padding(16, 6, 16, 6),
                        bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                        border_radius=RADIUS_FULL,
                    ),
                    ft.Container(width=8),
                    # Pronunciation button
                    self.app.pronounce_link(wd['word'], size=26),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.CENTER),
                # Collocations preview (keep original feature)
                *([
                    ft.Container(height=16),
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, PRIMARY)),
                    ft.Container(height=4),
                    ft.Text("固定搭配（回想含义）", size=11, color=TEXT_HINT,
                            italic=True, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=4),
                ] + [
                    ft.Container(
                        content=ft.Text(item, size=13, color=TEXT_SECONDARY,
                                        text_align=ft.TextAlign.CENTER,
                                        weight=ft.FontWeight.W_500),
                        padding=ft.Padding(8, 4, 8, 4),
                        bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                        border_radius=8,
                    ) for item in collocation_en
                ] if collocation_en else []),
                ft.Container(height=16),
                # "tap to flip" hint — subtle and elegant
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TOUCH_APP, size=14,
                                color=ft.Colors.with_opacity(0.45, TEXT_HINT)),
                        ft.Container(width=6),
                        ft.Text("回想意思和搭配，点击查看", size=12,
                                color=ft.Colors.with_opacity(0.45, TEXT_HINT)),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            padding=ft.Padding(left=24, top=0, right=24, bottom=24),
            bgcolor=SURFACE,
            border_radius=RADIUS_LG,
            shadow=ft.BoxShadow(
                blur_radius=24, color=ft.Colors.with_opacity(0.10, "#000000"),
                offset=ft.Offset(0, 8),
            ),
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

        # === 基本信息区（带发音按钮） ===
        sections.append(self._section_basic_with_audio(wd))

        # === 记忆方法（放前面，整个段落一次朗读） ===
        if wd.get('memory_methods'):
            sections.append(self._section_memory_block(
                "记忆方法", ft.Icons.LIGHTBULB_OUTLINE, wd['memory_methods'],
                SURFACE, PRIMARY, wd['word'],
            ))

        # === 例句（点击显示翻译） ===
        if wd.get('examples'):
            sections.append(self._build_examples_section(wd['examples']))

        # === 固定搭配（带发音） ===
        if wd.get('collocations'):
            sections.append(self._section_with_audio(
                "固定搭配", ft.Icons.LINK, wd['collocations'],
                SURFACE, PRIMARY, wd['word'],
            ))

        # === 派生词/扩展 ===
        if wd.get('extensions'):
            sections.append(self._sec_plain(
                "派生词/扩展", ft.Icons.ACCOUNT_TREE_OUTLINED, wd['extensions'],
                SURFACE, PRIMARY,
            ))

        # === 卡片背面 ===
        back = ft.Container(
            content=ft.Column(sections, spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=SURFACE,
            border_radius=RADIUS_LG,
            shadow=ft.BoxShadow(
                blur_radius=24, color=ft.Colors.with_opacity(0.10, "#000000"),
                offset=ft.Offset(0, 8),
            ),
            margin=ft.Margin(left=16, right=16, top=12, bottom=12),
        )
        self.action_buttons.visible = True
        self.card_container.content = ft.Column([back], spacing=0, tight=True)
        self.page.update()

    def _section_basic_with_audio(self, wd):
        """基本信息区 — 单词/音标/词性/释义 + 发音按钮（极简：统一主色）"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(wd['word'], size=FONT_XXXL, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True,
                        ),
                    self.app.pronounce_link(wd['word'], size=22),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                ft.Row([
                    ft.Text(wd.get('phonetic', ''), size=FONT_BODY,
                            color=TEXT_SECONDARY, italic=True),
                    ft.Container(width=10),
                    ft.Container(
                        content=ft.Text(wd.get('pos', ''), size=FONT_SM,
                                        color=ft.Colors.WHITE),
                        padding=ft.Padding(8, 3, 8, 3),
                        bgcolor=PRIMARY,
                        border_radius=RADIUS_XS,
                    ) if wd.get('pos') else ft.Container(),
                ], spacing=4),
                ft.Container(height=10),
                ft.Text(wd.get('meaning', ''), size=FONT_XL, weight=ft.FontWeight.W_500,
                        color=TEXT_PRIMARY),
            ], spacing=0),
            padding=ft.Padding(left=16, top=14, right=16, bottom=14),
            bgcolor=SURFACE,
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, PRIMARY),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _sec_plain(self, title, icon, content, bg_color, accent_color):
        """信息区 — 带左边缘色条（极简：统一主色）"""
        items = [item.strip() for item in content.split('|') if item.strip()]
        content_parts = []
        for item in items:
            content_parts.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Container(
                                width=6, height=6,
                                bgcolor=accent_color,
                                border_radius=3,
                            ),
                            width=20,
                        ),
                        ft.Text(item, size=FONT_BODY, color=TEXT_SECONDARY, expand=True),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.START),
                    padding=ft.Padding(left=4, top=4, right=4, bottom=4),
                )
            )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=16, color=accent_color),
                        padding=ft.Padding(2, 0, 2, 0),
                    ),
                    ft.Container(width=6),
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                *content_parts,
            ], spacing=0),
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            bgcolor=bg_color,
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, accent_color),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _section_with_audio(self, title, icon, content, bg_color, accent_color, word):
        """信息区 — 每项带发音按钮（极简：统一主色）"""
        items = [item.strip() for item in content.split('|') if item.strip()]
        content_parts = []
        for item in items[:5]:
            content_parts.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Container(
                                width=6, height=6,
                                bgcolor=accent_color,
                                border_radius=3,
                            ),
                            width=20,
                        ),
                        ft.Text(item, size=FONT_BODY, color=TEXT_SECONDARY, expand=True),
                        self.app.pronounce_link(item, size=16),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.START),
                    padding=ft.Padding(left=4, top=4, right=4, bottom=4),
                )
            )
        if len(items) > 5:
            content_parts.append(
                ft.Text(f"... 还有 {len(items)-5} 条", size=11, color=TEXT_HINT,
                        text_align=ft.TextAlign.CENTER)
            )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=16, color=accent_color),
                        padding=ft.Padding(2, 0, 2, 0),
                    ),
                    ft.Container(width=6),
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                *content_parts,
            ], spacing=0),
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            bgcolor=bg_color,
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, accent_color),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _section_memory_block(self, title, icon, content, bg_color, accent_color, word):
        """记忆方法区 — 整个段落作为一整块显示，一次朗读（极简：统一主色）"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=16, color=accent_color),
                        padding=ft.Padding(2, 0, 2, 0),
                    ),
                    ft.Container(width=6),
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                ft.Row([
                    ft.Container(expand=True),
                    self.app.pronounce_link(content[:500], size=18),
                ]),
                ft.Container(height=6),
                ft.Text(content, size=FONT_BODY, color=TEXT_SECONDARY,
                        selectable=True),
            ], spacing=0),
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            bgcolor=bg_color,
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, accent_color),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _build_examples_section(self, examples_text):
        """例句区 — 默认隐藏翻译，点击展开（极简：统一主色）"""
        pairs = self._split_en_zh(examples_text)
        ACCENT = PRIMARY

        example_items = []
        for i, (en, zh) in enumerate(pairs):
            zh_row = ft.Container(
                content=ft.Column([
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, ACCENT)),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.TRANSLATE, size=12, color=TEXT_HINT),
                            padding=ft.Padding(2, 0, 2, 0),
                        ),
                        ft.Container(width=4),
                        ft.Text(zh or "", size=FONT_BODY, color=TEXT_HINT, italic=True,
                                expand=True),
                    ]),
                ], spacing=0),
                visible=False,
            )

            example_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{i+1}. ", size=FONT_BODY, color=TEXT_HINT,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(en, size=FONT_BODY, color=TEXT_SECONDARY, expand=True),
                            self.app.pronounce_link(en[:100], size=16),
                            ft.IconButton(
                                icon=ft.Icons.EXPAND_MORE,
                                icon_size=16,
                                icon_color=ACCENT,
                                tooltip="显示/隐藏翻译",
                            ),
                        ], spacing=2, vertical_alignment=ft.CrossAxisAlignment.START),
                        ft.Container(height=2),
                        zh_row,
                    ], spacing=0),
                    padding=ft.Padding(left=4, top=6, right=4, bottom=6),
                    ink=True,
                    on_click=self._toggle_translation,
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.FORMAT_QUOTE, size=16, color=ACCENT),
                        padding=ft.Padding(2, 0, 2, 0),
                    ),
                    ft.Container(width=6),
                    ft.Text("例句", size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                    ft.Text("点击展开翻译", size=11, color=TEXT_HINT, italic=True),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, ACCENT)),
                ft.Container(height=2),
                *example_items,
            ], spacing=0),
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            bgcolor=SURFACE,
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, ACCENT),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    # ========== 翻译辅助 ==========
    def _split_en_zh(self, text):
        items = [t.strip() for t in text.split('|') if t.strip()]
        result = []
        for item in items:
            match = re.search(r'[一-鿿]', item)
            if match:
                result.append((item[:match.start()].strip(), item[match.start():].strip()))
            else:
                result.append((item, None))
        return result

    def _toggle_translation(self, e):
        col = e.control.content
        if col and isinstance(col, ft.Column) and len(col.controls) >= 3:
            zh_row = col.controls[2]
            if isinstance(zh_row, ft.Container):
                zh_row.visible = not zh_row.visible
                en_row = col.controls[0]
                if len(en_row.controls) >= 3:
                    arrow = en_row.controls[2]
                    arrow.name = ft.Icons.EXPAND_LESS if zh_row.visible else ft.Icons.EXPAND_MORE
                    arrow.update()
                zh_row.update()
                if hasattr(e.control, 'page') and e.control.page:
                    e.control.page.update()

    # ========== 三档熟悉程度 ==========
    def _handle_result(self, level):
        wd = self._get_word()
        if not wd:
            return
        word_id = wd.get('id', 0)

        if level == 'familiar':
            api_service.record_study(word_id, 'review', 'remember')
            from app.services.local_db import _get_session
            from backend.models import StudyRecord
            s = _get_session()
            try:
                last = s.query(StudyRecord).filter(StudyRecord.word_id == word_id
                    ).order_by(StudyRecord.id.desc()).first()
                if last:
                    last.review_interval = 4  # 3-4天后复习（不是60天）
                    s.commit()
            except: s.rollback()
            finally: s.close()
            if word_id not in self._counted_ids:
                self.review_done += 1
                self._counted_ids.add(word_id)
            self._next_word()
            self.app.show_snackbar("⭐ 已标记为熟悉，3-4天后复习", SUCCESS)
        elif level == 'vague':
            api_service.record_study(word_id, 'review', 'remember')
            if word_id not in self._counted_ids:
                self.review_done += 1
                self._counted_ids.add(word_id)
            if word_id not in self.remaining_queue:
                self.remaining_queue.append(word_id)  # 稍后再现
            self._next_word()
            self.app.show_snackbar("✅ 模糊记得，稍后再次出现", SUCCESS)
        else:
            api_service.record_study(word_id, 'review', 'forget')
            if word_id not in self.remaining_queue:
                self.remaining_queue.append(word_id)
            self._next_word()
            self.app.show_snackbar("💪 忘了没关系，今天稍后重学", ERROR)

    def _next_word(self):
        self.word_index += 1
        # 穿插再现：每复习 REPEAT_GAP 个词，把"模糊/不记得"的词插回队列，
        # 直到用户点"熟悉"才放过（当天反复出现）
        if self.remaining_queue:
            if self._since_repeat >= self.REPEAT_GAP - 1:
                self._since_repeat = 0
                wid = self.remaining_queue.pop(0)
                wd = next((x for x in self.words if x.get('id') == wid), None)
                if wd:
                    self.words.insert(self.word_index, wd)
            else:
                self._since_repeat += 1
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
        remaining = max(0, self.review_total - self.review_done)
        self.progress_text.value = f"剩余 {remaining} 个"
        self.badge_text.value = f"{remaining}"
        if not initial:
            self.progress_text.update()
            self.badge_text.update()

    def _show_completion(self):
        self.action_buttons.visible = False
        self.card_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    # Celebration icon with gradient background
                    ft.Container(
                        content=ft.Icon(ft.Icons.CELEBRATION, size=72, color=ft.Colors.WHITE),
                        padding=ft.Padding(20, 20, 20, 20),
                        gradient=GRADIENT_REVIEW,
                        border_radius=40,
                        shadow=ft.BoxShadow(
                            blur_radius=20, color=ft.Colors.with_opacity(0.25, SECONDARY),
                            offset=ft.Offset(0, 8),
                        ),
                    ),
                    ft.Container(height=20),
                    ft.Text("复习完成！", size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=PRIMARY),
                    ft.Container(height=8),
                    ft.Text(f"今日复习 {self.review_done} 个单词",
                            size=FONT_BODY, color=TEXT_SECONDARY),
                    ft.Container(height=24),
                    # "返回首页" gradient button
                    ft.Container(
                        content=ft.Text("返回首页", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(32, 14, 32, 14),
                        gradient=GRADIENT_REVIEW,
                        border_radius=RADIUS_XL,
                        shadow=ft.BoxShadow(
                            blur_radius=12, color=ft.Colors.with_opacity(0.25, SECONDARY),
                            offset=ft.Offset(0, 4),
                        ),
                        ink=True,
                        on_click=lambda e: self.app.switch_to_page(0),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Container(expand=True),
        ])
        self.progress_text.value = f"今日复习完成 {self.review_done} 个 ✅"
        self.badge_text.value = f"{self.review_done}"
        self.page.update()
