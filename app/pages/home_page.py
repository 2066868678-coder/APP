#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 首页（视觉增强版）
==============================
问候 + 今日进度 + 核心入口，带精致微交互与视觉层次
"""

import sys, os
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, SECONDARY, BACKGROUND, SURFACE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, TEXT_ON_PRIMARY,
    SUCCESS,
    PAGE_PADDING, CARD_GAP,
    RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_SM, RADIUS_FULL,
    FONT_XS, FONT_SM, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL, FONT_BODY,
    GRADIENT_PRIMARY,
    SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_XXL,
    SHADOW_CARD, SHADOW_SM,
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
        if h < 5: greet = "夜深了"
        elif h < 9: greet = "早上好"
        elif h < 12: greet = "上午好"
        elif h < 14: greet = "中午好"
        elif h < 18: greet = "下午好"
        else: greet = "晚上好"

        # --- emoji map ---
        greet_emoji = {"夜深了": "🌙", "早上好": "☀️", "上午好": "🌤️",
                       "中午好": "🌤️", "下午好": "⛅", "晚上好": "🌆"}

        progress_pct = round(learned / total * 100, 1) if total > 0 else 0

        # --- Greeting section with decoration ---
        greeting_section = ft.Container(
            content=ft.Stack([
                # subtle background decoration — soft gradient circle
                ft.Container(
                    width=180, height=180,
                    gradient=ft.RadialGradient(
                        colors=[
                            ft.Colors.with_opacity(0.08, PRIMARY),
                            ft.Colors.with_opacity(0.0, PRIMARY),
                        ],
                    ),
                    border_radius=90,
                    right=-30, top=-60,
                ),
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Text(greet, size=FONT_XXL,
                                    weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                            ft.Text(greet_emoji.get(greet, ""), size=FONT_XXL),
                        ], spacing=6),
                        ft.Container(height=4),
                        # streak badge
                        ft.Container(
                            content=ft.Row([
                                ft.Text("🔥", size=FONT_BODY),
                                ft.Container(width=4),
                                ft.Text(f"连续 {streak} 天",
                                        size=FONT_SM, weight=ft.FontWeight.W_600,
                                        color=PRIMARY),
                            ], spacing=0),
                            padding=ft.Padding(10, 4, 12, 4),
                            bgcolor=ft.Colors.with_opacity(0.08, PRIMARY),
                            border_radius=RADIUS_FULL,
                        ),
                    ], spacing=0),
                    ft.Container(expand=True),
                    # learned / total pill
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{learned}", size=FONT_XXL,
                                    weight=ft.FontWeight.BOLD, color=TEXT_ON_PRIMARY),
                            ft.Text(f"/ {total}", size=FONT_SM,
                                    color=ft.Colors.with_opacity(0.7, TEXT_ON_PRIMARY)),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                        padding=ft.Padding(18, 10, 18, 10),
                        gradient=GRADIENT_PRIMARY,
                        border_radius=RADIUS_XL,
                        shadow=SHADOW_CARD,
                    ),
                ], alignment=ft.MainAxisAlignment.START),
            ]),
            height=130,
        )

        # --- Total progress bar ---
        def _build_progress_bar():
            fill_color = GRADIENT_PRIMARY if progress_pct < 100 else SUCCESS
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("总进度", size=FONT_SM, color=TEXT_SECONDARY,
                                weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.Text(
                            f"{progress_pct}%",
                            size=FONT_SM, weight=ft.FontWeight.W_700, color=PRIMARY,
                        ),
                    ]),
                    ft.Container(height=8),
                    # track
                    ft.Container(
                        height=8, border_radius=4,
                        bgcolor=ft.Colors.with_opacity(0.08, PRIMARY),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Container(
                            height=8, border_radius=4,
                            gradient=fill_color if progress_pct < 100 else None,
                            bgcolor=fill_color if progress_pct == 100 else None,
                        ),
                    ),
                ]),
                padding=ft.Padding(SPACING_LG, SPACING_MD, SPACING_LG, SPACING_MD),
                bgcolor=SURFACE,
                border_radius=RADIUS_LG,
            )

        # --- Today task card ---
        def _task_card(icon, label, done, target, color, has_active, page_idx):
            pct = min(done / target, 1.0) if target > 0 else 0
            completed = done >= target
            fill = SUCCESS if completed else color
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(icon, size=20, color=TEXT_ON_PRIMARY),
                            width=36, height=36,
                            bgcolor=ft.Colors.with_opacity(0.15, color),
                            border_radius=10,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text(
                                "已完成" if completed else f"{done}/{target}",
                                size=FONT_XS,
                                color=SUCCESS if completed else TEXT_SECONDARY,
                                weight=ft.FontWeight.W_600,
                            ),
                            padding=ft.Padding(8, 3, 8, 3),
                            bgcolor=ft.Colors.with_opacity(0.10, SUCCESS) if completed
                                    else ft.Colors.with_opacity(0.06, TEXT_SECONDARY),
                            border_radius=RADIUS_SM,
                        ),
                    ]),
                    ft.Container(height=10),
                    ft.Text(label, size=FONT_LG, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    # thin progress bar
                    ft.Container(
                        height=5, border_radius=3, expand=True,
                        bgcolor=ft.Colors.with_opacity(0.08, color),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        content=ft.Container(
                            height=5, border_radius=3,
                            bgcolor=fill,
                        ),
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        f"{round(pct * 100)}%",
                        size=FONT_XS, color=TEXT_HINT,
                    ),
                ], spacing=0),
                padding=ft.Padding(SPACING_LG, SPACING_MD, SPACING_LG, SPACING_MD),
                bgcolor=SURFACE,
                border_radius=RADIUS_XL,
                expand=True, ink=True,
                shadow=SHADOW_CARD,
                # left accent border
                border=ft.Border(
                    left=ft.BorderSide(width=3, color=color),
                ),
                on_click=lambda e, idx=page_idx: self.app.switch_to_page(idx),
            )

        today_task_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.TODAY, size=16, color=PRIMARY),
                        width=28, height=28,
                        bgcolor=ft.Colors.with_opacity(0.1, PRIMARY),
                        border_radius=8,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(width=10),
                    ft.Text("今日任务", size=FONT_LG, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY),
                ]),
                ft.Container(height=SPACING_LG),
                ft.Row([
                    _task_card(ft.Icons.MENU_BOOK_OUTLINED, "新学",
                               new_done, new_target, PRIMARY, has_study, 1),
                    ft.Container(width=CARD_GAP),
                    _task_card(ft.Icons.AUTO_STORIES_OUTLINED, "复习",
                               review_done, review_target, PRIMARY, has_review, 2),
                ]),
            ]),
            padding=ft.Padding(SPACING_XL, SPACING_LG, SPACING_XL, SPACING_LG),
            bgcolor=SURFACE,
            border_radius=RADIUS_XL,
            shadow=ft.BoxShadow(
                blur_radius=16,
                color=ft.Colors.with_opacity(0.06, "#000000"),
                offset=ft.Offset(0, 4),
            ),
        )

        # --- Quick action buttons（极简：统一主色） ---
        btn_configs = [
            ("学习", ft.Icons.MENU_BOOK, 1),
            ("复习", ft.Icons.AUTO_STORIES, 2),
            ("统计", ft.Icons.BAR_CHART, 3),
            ("设置", ft.Icons.SETTINGS, 4),
        ]

        quick_actions = ft.Row(
            [self._big_btn(lb, ic, idx) for lb, ic, idx in btn_configs],
        )

        # --- Assemble page ---
        # expand=True 使内部 Column 的滚动获得有界高度：
        # 内容在这里滚动，底部导航固定在视口底部
        content = ft.Container(
            content=ft.Column([
                greeting_section,
                ft.Container(height=SPACING_XXL),
                _build_progress_bar(),
                ft.Container(height=CARD_GAP),
                today_task_card,
                ft.Container(height=SPACING_XXL),
                quick_actions,
                ft.Container(height=SPACING_XXL),
            ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.Padding(PAGE_PADDING, PAGE_PADDING, PAGE_PADDING, 0),
            expand=True,
        )
        self._container.content = content

    def _big_btn(self, label, icon, page_idx):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, size=22, color=TEXT_ON_PRIMARY),
                    width=44, height=44,
                    bgcolor=ft.Colors.with_opacity(0.15, PRIMARY),
                    border_radius=12,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(height=6),
                ft.Text(label, size=FONT_SM, color=TEXT_PRIMARY,
                        weight=ft.FontWeight.W_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            bgcolor=SURFACE, border_radius=RADIUS_LG,
            padding=ft.Padding(6, 14, 6, 12),
            shadow=SHADOW_SM,
            expand=True, ink=True,
            on_click=lambda e, idx=page_idx: self.app.switch_to_page(idx),
        )
