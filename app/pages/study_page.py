#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 学习页面（翻卡模式 · 增强视觉设计）
===============================
标准背单词流程：
1. 展示英文单词（正面）
2. 用户回想意思
3. 点击翻转显示完整信息
4. 自评"记得"或"不记得"
"""

import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK, PRIMARY_CONTAINER,
    SECONDARY, BACKGROUND, SURFACE, SUCCESS, ERROR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_XXL,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_FULL,
    SHADOW_SM, SHADOW_MD, SHADOW_LG,
    FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL, FONT_DISPLAY,
    GRADIENT_PRIMARY, GRADIENT_HEADER, BORDER,
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
        self.badge_text = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.est_text = ft.Text("", size=12, color=TEXT_HINT)
        self.card_container = ft.Container(expand=True)

    def build(self):
        # 批量获取学习页数据（1次DB会话 vs 原来4次）
        study_data = self._load_data()
        words = study_data['words']
        target = study_data['target']
        done = study_data['done']

        # 预计完成时间
        stats = study_data['stats']
        total = stats.get('total_words', 2281)
        learned = stats.get('learned_words', 0)
        remain = max(0, total - learned)
        cur_target = max(1, study_data.get('daily_target', 20))
        self._fresh_target = cur_target  # 供 _update_progress 使用，避免重复查询
        if remain > 0:
            est_days = (remain + cur_target - 1) // cur_target
            self.est_text.value = f"剩余{remain}词 · 每日{cur_target}词还需{est_days}天"
        else:
            self.est_text.value = "所有单词已学完！ 🎉"

        # === Enhanced Header ===
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    # Icon with gradient background + subtle shadow
                    ft.Container(
                        content=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.WHITE, size=20),
                        padding=ft.Padding(10, 10, 10, 10),
                        gradient=GRADIENT_PRIMARY,
                        border_radius=RADIUS_MD,
                        shadow=ft.BoxShadow(
                            blur_radius=8, color=ft.Colors.with_opacity(0.25, PRIMARY),
                            offset=ft.Offset(0, 2),
                        ),
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text("学习新词", size=FONT_LG, weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY),
                        self.progress_text,
                    ], spacing=2, expand=True),
                    # Progress badge with gradient background
                    ft.Container(
                        content=self.badge_text,
                        padding=ft.Padding(14, 6, 14, 6),
                        gradient=GRADIENT_PRIMARY,
                        border_radius=RADIUS_FULL,
                        shadow=ft.BoxShadow(
                            blur_radius=6, color=ft.Colors.with_opacity(0.20, PRIMARY),
                            offset=ft.Offset(0, 2),
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                # Estimate row with cleaner icon container
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.HOURGLASS_BOTTOM, size=12,
                                            color=TEXT_HINT),
                            padding=ft.Padding(4, 2, 4, 2),
                        ),
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
        """操作按钮区域 — 三档熟悉程度（新视觉风格）"""
        from app.theme import COLOR_REVIEW

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
                    _make_button(ft.Icons.CHECK_CIRCLE_OUTLINE, "熟悉",
                                 SUCCESS, "近期不再复习", 'familiar'),
                    # 模糊 — Sky
                    _make_button(ft.Icons.AUTO_AWESOME, "模糊",
                                 SECONDARY, "正常艾宾浩斯复习", 'vague'),
                    # 不记得 — Rose/Red
                    _make_button(ft.Icons.REPLAY, "不记得",
                                 ERROR, "今天多练几次", 'forget'),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(height=6),
                ft.Text("点按下方按钮记录学习结果", size=11, color=TEXT_HINT,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=PAGE_PADDING, right=PAGE_PADDING, bottom=16),
            visible=False,
        )
        return self.action_buttons

    def _build_empty(self, msg="🎉 今日新词已学完！"):
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                # Celebration icon with gradient background
                ft.Container(
                    content=ft.Icon(ft.Icons.CELEBRATION, size=64, color=ft.Colors.WHITE),
                    padding=ft.Padding(20, 20, 20, 20),
                    gradient=GRADIENT_PRIMARY,
                    border_radius=40,
                    shadow=ft.BoxShadow(
                        blur_radius=16, color=ft.Colors.with_opacity(0.25, PRIMARY),
                        offset=ft.Offset(0, 6),
                    ),
                ),
                ft.Container(height=16),
                ft.Text(msg, size=FONT_LG, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.Text("明天继续加油！", size=FONT_BODY, color=TEXT_HINT,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                # "返回首页" gradient button
                ft.Container(
                    content=ft.Text("返回首页", color=ft.Colors.WHITE, size=14,
                                   weight=ft.FontWeight.BOLD),
                    padding=ft.Padding(28, 12, 28, 12),
                    gradient=GRADIENT_PRIMARY,
                    border_radius=RADIUS_XL,
                    shadow=ft.BoxShadow(
                        blur_radius=10, color=ft.Colors.with_opacity(0.25, PRIMARY),
                        offset=ft.Offset(0, 4),
                    ),
                    ink=True,
                    on_click=lambda e: self.app.switch_to_page(0),
                ),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
        )

    def _load_data(self):
        """从数据库读取今日新词数据（批量1次查询）"""
        try:
            return api_service.get_study_data()
        except Exception:
            return {
                'words': [],
                'target': api_service.get_daily_target(),
                'done': 0,
                'daily_target': api_service.get_daily_target(),
                'stats': {'total_words': 2281, 'learned_words': 0, 'mastered_words': 0},
            }

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

        # === Card Front (Enhanced) ===
        front = ft.Container(
            content=ft.Column([
                # Gradient decoration strip at top
                ft.Container(
                    height=4,
                    gradient=GRADIENT_PRIMARY,
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
                ft.Container(height=30),
                # "tap to flip" hint — more subtle and elegant
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TOUCH_APP, size=14,
                                color=ft.Colors.with_opacity(0.45, TEXT_HINT)),
                        ft.Container(width=6),
                        ft.Text("轻触卡片翻转", size=12,
                                color=ft.Colors.with_opacity(0.45, TEXT_HINT)),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    animate_opacity=True,
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

        # === 基本信息区（带发音按钮） ===
        sections.append(self._section_basic_with_audio(wd))

        # === 记忆方法（暖琥珀色，放前面，整个段落一次朗读） ===
        if wd.get('memory_methods'):
            sections.append(self._section_memory_block(
                "记忆方法", ft.Icons.LIGHTBULB_OUTLINE, wd['memory_methods'],
                "#FFF8E1", "#FFB300", wd['word'],
            ))

        # === 例句（点击显示翻译） ===
        if wd.get('examples'):
            sections.append(self._build_examples_section(wd['examples']))

        # === 固定搭配（带发音） ===
        if wd.get('collocations'):
            sections.append(self._section_with_audio(
                "固定搭配", ft.Icons.LINK, wd['collocations'],
                "#E3F2FD", "#64B5F6", wd['word'],
            ))

        # === 派生词/扩展 ===
        if wd.get('extensions'):
            sections.append(self._section_info(
                "派生词/扩展", ft.Icons.ACCOUNT_TREE_OUTLINED, wd['extensions'],
                "#F1F8E9", "#81C784",
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
        """基本信息区 — 单词/音标/词性/释义 + 发音按钮（增强设计）"""
        return ft.Container(
            content=ft.Column([
                # Word row with pronunciation
                ft.Row([
                    ft.Text(wd['word'], size=FONT_XXXL, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True,
                        ),
                    self.app.pronounce_link(wd['word'], size=22),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                # Phonetic + POS row
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
                # Meaning
                ft.Text(wd.get('meaning', ''), size=FONT_XL, weight=ft.FontWeight.W_500,
                        color=TEXT_PRIMARY),
            ], spacing=0),
            padding=ft.Padding(left=16, top=14, right=16, bottom=14),
            bgcolor=ft.Colors.with_opacity(0.05, PRIMARY),
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, PRIMARY),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _section_with_audio(self, title, icon, content, bg_color, accent_color, word):
        """信息区 — 每项带发音按钮（增强设计）"""
        items = [item.strip() for item in content.split('|') if item.strip()]
        content_parts = []
        for item in items[:5]:  # 最多5条，避免太长
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
        """记忆方法区 — 整个段落作为一整块显示，一次朗读（增强设计）"""
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
                    self.app.pronounce_link(content[:200], size=18),
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
        """例句区 — 默认隐藏翻译，点击展开（增强设计）"""
        pairs = self._split_en_zh(examples_text)
        ACCENT = "#CE93D8"

        example_items = []
        for i, (en, zh) in enumerate(pairs):
            # 每条例句：英文 + 展开按钮 + (隐藏的翻译)
            zh_row = ft.Container(
                content=ft.Column([
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.25, ACCENT)),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.TRANSLATE, size=12, color=ACCENT),
                            padding=ft.Padding(2, 0, 2, 0),
                        ),
                        ft.Container(width=4),
                        ft.Text(zh or "", size=FONT_BODY, color=TEXT_HINT, italic=True,
                                expand=True),
                    ]),
                ], spacing=0),
                visible=False,  # 默认隐藏翻译
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
            bgcolor="#F3E5F5",
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(4, ACCENT),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        )

    def _section_info(self, title, icon, content, bg_color, accent_color):
        """信息区 — 带左边缘色条（增强设计）"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=16, color=accent_color),
                        padding=ft.Padding(2, 0, 2, 0),
                    ),
                    ft.Container(width=6),
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                ], spacing=0),
                ft.Container(height=8),
                ft.Text(content, size=FONT_BODY, color=TEXT_SECONDARY),
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

    # ========== 例句拆分：英文+中文 ==========
    def _split_en_zh(self, text):
        """将例句拆分为英文部分和中文翻译"""
        items = [t.strip() for t in text.split('|') if t.strip()]
        result = []
        for item in items:
            # 找到中文字符起始位置
            match = re.search(r'[一-鿿]', item)
            if match:
                en = item[:match.start()].strip()
                zh = item[match.start():].strip()
                result.append((en, zh))
            else:
                result.append((item, None))
        return result

    def _toggle_translation(self, e):
        """点击例句切换翻译显示/隐藏"""
        col = e.control.content
        if col and isinstance(col, ft.Column) and len(col.controls) >= 3:
            # col.controls: [en_row, spacer, zh_row]
            zh_row = col.controls[2]
            if isinstance(zh_row, ft.Container):
                zh_row.visible = not zh_row.visible
                # 更新箭头图标
                en_row = col.controls[0]
                if len(en_row.controls) >= 3:
                    arrow = en_row.controls[2]
                    arrow.name = ft.Icons.EXPAND_LESS if zh_row.visible else ft.Icons.EXPAND_MORE
                    arrow.update()
                zh_row.update()
                if hasattr(e.control, 'page') and e.control.page:
                    e.control.page.update()

    # ========== 熟悉程度处理 ==========
    def _handle_result(self, level):
        """处理学习结果（3级熟悉程度）
        level: 'familiar' 熟悉 / 'vague' 模糊 / 'forget' 不记得
        """
        wd = self._get_word()
        if not wd:
            return

        word_id = wd.get('id', 0)

        if level == 'familiar':
            # 熟悉 → 设review_interval=60天，近期不再复习
            api_service.record_study(word_id, 'new', 'remember')
            # 手动覆盖为60天
            from app.services.local_db import _get_session
            from backend.models import StudyRecord
            s = _get_session()
            try:
                last = s.query(StudyRecord).filter(
                    StudyRecord.word_id == word_id
                ).order_by(StudyRecord.id.desc()).first()
                if last:
                    last.review_interval = 60
                    s.commit()
            except:
                s.rollback()
            finally:
                s.close()
            self.new_words_done += 1
            self._next_word()
            self.app.show_snackbar("⭐ 已标记为熟悉，近期不再复习")

        elif level == 'vague':
            # 模糊 → 正常艾宾浩斯
            api_service.record_study(word_id, 'new', 'remember')
            self.new_words_done += 1
            self._next_word()
            self.app.show_snackbar("✅ 模糊记得，按艾宾浩斯安排复习")

        else:  # forget
            # 不记得 → 重置间隔 + 今日多次出现
            api_service.record_study(word_id, 'new', 'forget')
            if word_id not in self.remaining_queue:
                self.remaining_queue.append(word_id)
            self._next_word()
            self.app.show_snackbar("💪 不记得！等会再出现，多看几次", ERROR)

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
        fresh_target = max(1, self._fresh_target)
        total = max(fresh_target, len(self.words))
        cur = self.word_index + 1
        done = self.new_words_done
        self.progress_text.value = f"今日新词: {done}/{total}  |  当前 {cur}/{total}"
        self.badge_text.value = f"{done}/{total}"
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
                        gradient=GRADIENT_PRIMARY,
                        border_radius=40,
                        shadow=ft.BoxShadow(
                            blur_radius=20, color=ft.Colors.with_opacity(0.25, PRIMARY),
                            offset=ft.Offset(0, 8),
                        ),
                    ),
                    ft.Container(height=20),
                    ft.Text("太棒了！", size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=PRIMARY),
                    ft.Container(height=8),
                    ft.Text(f"今日新学 {self.new_words_done} 个单词",
                            size=FONT_BODY, color=TEXT_SECONDARY),
                    ft.Container(height=24),
                    # "返回首页" gradient button
                    ft.Container(
                        content=ft.Text("返回首页", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(32, 14, 32, 14),
                        gradient=GRADIENT_PRIMARY,
                        border_radius=RADIUS_XL,
                        shadow=ft.BoxShadow(
                            blur_radius=12, color=ft.Colors.with_opacity(0.25, PRIMARY),
                            offset=ft.Offset(0, 4),
                        ),
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
