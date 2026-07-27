#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 首页（极简版）
========================
问候 + 今日进度 + 核心入口，去掉冗余信息
"""

import sys, os
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, SECONDARY, BACKGROUND, SURFACE,
    TEXT_PRIMARY, TEXT_SECONDARY,
    PAGE_PADDING, CARD_GAP,
    RADIUS_MD, RADIUS_LG,
    FONT_XS, FONT_SM, FONT_LG, FONT_XL,
)
from app.services import api_service


class HomePage:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self._container = ft.Container(expand=True)

    def build(self):
        self._render()
        return self._container

    def _render(self):
        try:
            data = api_service.get_home_data()
            plan = data.get('plan', {}) if data else {}
            stats = data.get('stats', {}) if data else {}
        except Exception:
            plan = {}; stats = {}

        p = plan; s = stats
        total = s.get('total_words', 0) or 0
        learned = s.get('learned_words', 0) or 0
        streak = s.get('streak_days', 0) or 0
        new_done = p.get('new_words_done', 0) or 0
        new_target = p.get('new_words_target', 20) or 20
        review_done = p.get('review_done', 0) or 0
        review_target = p.get('review_target', 1) or 1

        new_pct = min(new_done / new_target, 1.0) if new_target > 0 else 0
        review_pct = min(review_done / review_target, 1.0) if review_target > 0 else 0
        has_study = new_done < new_target
        has_review = review_done < review_target

        h = datetime.now(timezone(timedelta(hours=8))).hour
        if h < 5: greet = "夜深了 🌙"
        elif h < 9: greet = "早上好 ☀️"
        elif h < 12: greet = "上午好 🌤️"
        elif h < 14: greet = "中午好 🌤️"
        elif h < 18: greet = "下午好 ⛅"
        else: greet = "晚上好 🌆"

        content = ft.Column([
            # 顶部：问候 + 连续天数
            ft.Row([
                ft.Column([
                    ft.Text(greet, size=FONT_XL, weight=ft.FontWeight.W_600,
                            color=TEXT_PRIMARY),
                    ft.Text(f"连续 {streak} 天", size=FONT_SM,
                            color=TEXT_SECONDARY),
                ], spacing=2),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(f"{learned}/{total}", size=FONT_XL,
                                    weight=ft.FontWeight.BOLD, color=PRIMARY),
                    padding=ft.Padding(16, 8, 16, 8),
                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY),
                    border_radius=RADIUS_LG,
                ),
            ]),
            ft.Container(height=32),

            # 总进度条
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("总进度", size=FONT_SM, color=TEXT_SECONDARY),
                        ft.Container(expand=True),
                        ft.Text(f"{round(learned/total*100,1)}%" if total > 0 else "0%",
                                size=FONT_SM, weight=ft.FontWeight.W_600, color=PRIMARY),
                    ]),
                    ft.Container(height=6),
                    ft.Container(
                        height=6, border_radius=3,
                        bgcolor=ft.Colors.with_opacity(0.1, PRIMARY),
                        content=ft.Container(
                            height=6, border_radius=3,
                            bgcolor=PRIMARY,
                        ),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                ]),
            ),
            ft.Container(height=CARD_GAP),

            # 今日任务卡片
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.TODAY, size=18, color=TEXT_PRIMARY),
                        ft.Container(width=8),
                        ft.Text("今日任务", size=FONT_LG, weight=ft.FontWeight.W_600,
                                color=TEXT_PRIMARY),
                    ]),
                    ft.Container(height=16),
                    ft.Row([
                        # 新学
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=24, color=PRIMARY),
                                ft.Container(height=6),
                                ft.Text("新学", size=FONT_XS, color=TEXT_SECONDARY),
                                ft.Text(f"{new_done}/{new_target}", size=FONT_XL,
                                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Container(
                                    height=4, border_radius=2, expand=True,
                                    bgcolor=ft.Colors.with_opacity(0.1, PRIMARY),
                                    content=ft.Container(height=4, border_radius=2,
                                        bgcolor=PRIMARY if has_study else ft.Colors.GREEN_400),
                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                            padding=16, bgcolor=SURFACE, border_radius=RADIUS_LG,
                            shadow=ft.BoxShadow(1, 2, ft.Colors.BLACK12),
                            expand=True, ink=True,
                            on_click=lambda e: self.app.switch_to_page(1),
                        ),
                        ft.Container(width=CARD_GAP),
                        # 复习
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=24, color=SECONDARY),
                                ft.Container(height=6),
                                ft.Text("复习", size=FONT_XS, color=TEXT_SECONDARY),
                                ft.Text(f"{review_done}/{review_target}", size=FONT_XL,
                                        weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Container(
                                    height=4, border_radius=2, expand=True,
                                    bgcolor=ft.Colors.with_opacity(0.1, SECONDARY),
                                    content=ft.Container(height=4, border_radius=2,
                                        bgcolor=SECONDARY if has_review else ft.Colors.GREEN_400),
                                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                            padding=16, bgcolor=SURFACE, border_radius=RADIUS_LG,
                            shadow=ft.BoxShadow(1, 2, ft.Colors.BLACK12),
                            expand=True, ink=True,
                            on_click=lambda e: self.app.switch_to_page(2),
                        ),
                    ]),
                ]),
                padding=20, bgcolor=SURFACE, border_radius=RADIUS_LG,
                shadow=ft.BoxShadow(2, 4, ft.Colors.BLACK12),
            ),

            ft.Container(height=CARD_GAP),

            # 底部导航快捷按钮
            ft.Row([
                self._big_btn("学习", ft.Icons.MENU_BOOK, PRIMARY, 1),
                ft.Container(width=8),
                self._big_btn("复习", ft.Icons.AUTO_STORIES, SECONDARY, 2),
                ft.Container(width=8),
                self._big_btn("统计", ft.Icons.BAR_CHART, "#7E57C2", 3),
                ft.Container(width=8),
                self._big_btn("设置", ft.Icons.SETTINGS, "#78909C", 4),
            ]),

            ft.Container(height=24),
        ],
            spacing=0,
            padding=ft.Padding(PAGE_PADDING, PAGE_PADDING, PAGE_PADDING, 0),
            scroll=ft.ScrollMode.AUTO,
        )
        self._container.content = content

    def _big_btn(self, label, icon, color, page_idx):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=24, color=color),
                ft.Container(height=4),
                ft.Text(label, size=FONT_XS, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            bgcolor=SURFACE, border_radius=RADIUS_LG,
            padding=ft.Padding(8, 14, 8, 10),
            shadow=ft.BoxShadow(1, 2, ft.Colors.BLACK12),
            expand=True, ink=True,
            on_click=lambda e: self.app.switch_to_page(page_idx),
        )
