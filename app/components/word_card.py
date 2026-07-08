#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 单词卡片组件
======================
可复用的单词卡片，用于学习和复习
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft


class WordCard:
    """单词卡片组件"""

    # 分类显示名称
    SECTION_LABELS = {
        'examples': '📖 例句',
        'memory_methods': '💡 记忆方法',
        'derivatives': '🔗 派生词',
        'collocations': '📝 固定搭配',
        'extensions': '📌 扩展内容',
    }

    # 分类图标
    SECTION_ICONS = {
        'examples': ft.Icons.FORMAT_QUOTE,
        'memory_methods': ft.Icons.LIGHTBULB_OUTLINE,
        'derivatives': ft.Icons.ACCOUNT_TREE_OUTLINED,
        'collocations': ft.Icons.LINK,
        'extensions': ft.Icons.EXPAND,
    }

    def __init__(self, word_data: dict, on_remember=None, on_forget=None):
        """
        初始化单词卡片

        参数:
            word_data: 单词数据字典
            on_remember: 点击"记得"的回调
            on_forget: 点击"忘记"的回调
        """
        self.word_data = word_data
        self.on_remember = on_remember
        self.on_forget = on_forget
        self.is_front = True  # 卡片是否正面朝上（复习模式）

    def build_front(self):
        """卡片正面 - 显示英文单词"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(expand=True),
                    # 英文单词（大号加粗）
                    ft.Text(
                        self.word_data.get('word', ''),
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=8),
                    # 音标
                    ft.Text(
                        self.word_data.get('phonetic', ''),
                        size=16,
                        color=ft.Colors.GREY,
                        text_align=ft.TextAlign.CENTER,
                        italic=True,
                    ),
                    ft.Container(height=16),
                    # 点击提示
                    ft.Text(
                        "👆 点击翻转查看详情",
                        size=13,
                        color=ft.Colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(expand=True),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                tight=True,
            ),
            padding=ft.Padding(left=30, top=30, right=30, bottom=30),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 4),
            ),
            ink=True,
            on_click=self._flip_card,
        )

    def build_back(self):
        """卡片背面 - 显示完整信息"""
        word = self.word_data.get('word', '')
        phonetic = self.word_data.get('phonetic', '')
        pos = self.word_data.get('pos', '')
        meaning = self.word_data.get('meaning', '')

        sections_content = [self._build_header_section(word, phonetic, pos, meaning)]

        # 例句
        examples = self.word_data.get('examples', '')
        if examples:
            sections_content.append(
                self._build_info_section('examples', examples)
            )

        # 记忆方法（核心！）
        memory = self.word_data.get('memory_methods', '')
        if memory:
            sections_content.append(
                self._build_info_section('memory_methods', memory, highlighted=True)
            )

        # 派生词
        derivatives = self.word_data.get('derivatives', '')
        if derivatives:
            sections_content.append(
                self._build_info_section('derivatives', derivatives)
            )

        # 固定搭配
        collocations = self.word_data.get('collocations', '')
        if collocations:
            sections_content.append(
                self._build_info_section('collocations', collocations)
            )

        # 扩展内容
        extensions = self.word_data.get('extensions', '')
        if extensions:
            sections_content.append(
                self._build_info_section('extensions', extensions)
            )

        # 操作按钮
        sections_content.append(self._build_action_buttons())

        return ft.Container(
            content=ft.Column(
                controls=sections_content,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.Padding(left=20, top=20, right=20, bottom=20),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 4),
            ),
            height=500,
            ink=True,
            on_click=self._flip_card,
        )

    def build(self):
        """构建完整的卡片"""
        return self.build_front()

    def _flip_card(self, e):
        """翻转卡片（正反面切换）"""
        self.is_front = not self.is_front

    def _build_header_section(self, word, phonetic, pos, meaning):
        """基本信息区域"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        word,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87,
                    ),
                    ft.Container(height=4),
                    ft.Row(
                        controls=[
                            ft.Text(phonetic, size=14, color=ft.Colors.GREY, italic=True) if phonetic else ft.Container(),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Text(pos, size=12, color=ft.Colors.WHITE),
                                padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                                bgcolor=ft.Colors.GREEN,
                                border_radius=4,
                            ) if pos else ft.Container(),
                        ],
                        spacing=4,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        meaning,
                        size=16,
                        color=ft.Colors.BLACK87,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
            bgcolor=ft.Colors.INDIGO_50,
            border_radius=8,
        )

    def _build_info_section(self, section_type: str, content: str, highlighted: bool = False):
        """信息区域（例句、记忆方法等）"""
        label = self.SECTION_LABELS.get(section_type, section_type)
        icon = self.SECTION_ICONS.get(section_type)

        # 内容按 '|' 分割为多条
        items = [item.strip() for item in content.split('|') if item.strip()]

        content_widgets = []
        for item in items:
            content_widgets.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text("•", size=14, color=ft.Colors.GREY_600),
                                width=16,
                            ),
                            ft.Container(
                                content=ft.Text(item, size=14, color=ft.Colors.BLACK87),
                                expand=True,
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=ft.Padding(left=4, top=2, bottom=2),
                )
            )

        bg_color = ft.Colors.AMBER_50 if highlighted else ft.Colors.GREY_50
        border_color = ft.Colors.AMBER_200 if highlighted else None

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, size=16, color=ft.Colors.GREY_700) if icon else ft.Container(),
                            ft.Container(width=4),
                            ft.Text(
                                label,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_800,
                            ),
                        ],
                        spacing=0,
                    ),
                    ft.Container(height=4),
                    ft.Column(controls=content_widgets, spacing=0),
                ],
                spacing=0,
            ),
            padding=ft.Padding(left=10, top=10, right=10, bottom=10),
            bgcolor=bg_color,
            border_radius=8,
            border=ft.Border(left=ft.BorderSide(1, border_color), right=ft.BorderSide(1, border_color), top=ft.BorderSide(1, border_color), bottom=ft.BorderSide(1, border_color)) if border_color else None,
        )

    def _build_action_buttons(self):
        """记得/忘记操作按钮"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.CLOSE, color=ft.Colors.WHITE, size=24),
                                ft.Text("忘记", color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.BOLD),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        padding=ft.Padding(left=30, right=30, top=12, bottom=12),
                        bgcolor=ft.Colors.RED_400,
                        border_radius=12,
                        ink=True,
                        on_click=lambda e: self._handle_result('forget'),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.CHECK, color=ft.Colors.WHITE, size=24),
                                ft.Text("记得", color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.BOLD),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        padding=ft.Padding(left=30, right=30, top=12, bottom=12),
                        bgcolor=ft.Colors.GREEN_400,
                        border_radius=12,
                        ink=True,
                        on_click=lambda e: self._handle_result('remember'),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=ft.Padding(top=8),
        )

    def _handle_result(self, result: str):
        """处理学习结果"""
        if result == 'remember' and self.on_remember:
            self.on_remember(self.word_data)
        elif result == 'forget' and self.on_forget:
            self.on_forget(self.word_data)
