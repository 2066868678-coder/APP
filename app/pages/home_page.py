#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 首页（全新设计）
==============
显示今日学习计划和进度概览（直读本地数据库，飞快）
"""

import sys, os
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SECONDARY, BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, TEXT_ON_PRIMARY,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_MD, RADIUS_LG, RADIUS_SM,
    SHADOW_SM, SHADOW_MD,
    FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL,
)
from app.components.app_card import AppCard, AppCardSmall
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
            plan = api_service.get_today_plan()
            stats = api_service.get_stats()
        except Exception:
            plan = None
            stats = None

        p = plan.get('plan', {}) if plan else {}
        s = stats if stats else {}

        total = s.get('total_words', 0)
        learned = s.get('learned_words', 0)
        mastered = s.get('mastered_words', 0)
        streak = s.get('streak_days', 0)
        new_target = p.get('new_words_target', 20)
        new_done = p.get('new_words_done', 0)
        review_target = p.get('review_target', 0)
        review_done = p.get('review_done', 0)

        new_pct = min(new_done / new_target, 1.0) if new_target > 0 else 0
        review_pct = min(review_done / review_target, 1.0) if review_target > 0 else 0

        # 欢迎语
        china_tz = timezone(timedelta(hours=8))
        hour = datetime.now(china_tz).hour
        if hour < 6: greet = "夜深了，早点休息 🌙"
        elif hour < 9: greet = "早上好！开始背词 🌅"
        elif hour < 12: greet = "上午好，继续加油 ☀️"
        elif hour < 14: greet = "中午好，饭后背一词 🌤️"
        elif hour < 18: greet = "下午好，保持节奏 🌥️"
        else: greet = "晚上好，今日功课 🌆"

        content = ft.ListView(
            controls=[
                # === 问候语 & 今日概览 ===
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WB_SUNNY_OUTLINED,
                                color=PRIMARY, size=28),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Text(greet, size=FONT_LG, weight=ft.FontWeight.W_600,
                                    color=TEXT_PRIMARY),
                            ft.Text("总进度 " + self._pct_str(learned, total),
                                    size=FONT_SM, color=TEXT_SECONDARY),
                        ], spacing=2, expand=True),
                    ]),
                    padding=SPACING_LG,
                    bgcolor=ft.Colors.with_opacity(0.08, PRIMARY),
                    border_radius=RADIUS_MD,
                ),

                ft.Container(height=CARD_GAP),

                # === 统计 2×2 网格 ===
                ft.Row([
                    self._stat_card(LIBRARY_BOOKS, total, "总单词", PRIMARY),
                    self._stat_card(CHECK_CIRCLE, learned, "已学习", PRIMARY_LIGHT),
                ], spacing=8),
                ft.Container(height=6),
                ft.Row([
                    self._stat_card(STARS, mastered, "已掌握",
                                    ft.Colors.AMBER_700 if mastered else TEXT_HINT),
                    self._stat_card(LOCAL_FIRE_DEPARTMENT, f"{streak}天", "连续",
                                    ft.Colors.DEEP_ORANGE_500 if streak > 0 else TEXT_HINT),
                ], spacing=8),

                ft.Container(height=CARD_GAP),

                # === 今日学习进度 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.TODAY, color=PRIMARY, size=20),
                            ft.Container(width=8),
                            ft.Text("今日学习", size=FONT_LG, weight=ft.FontWeight.BOLD,
                                    color=TEXT_PRIMARY),
                            ft.Container(expand=True),
                            ft.TextButton("去学习 →",
                                          style=ft.ButtonStyle(color=PRIMARY),
                                          on_click=lambda e: self.app.switch_to_page(1)),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(height=12),
                        ft.Row([
                            self._ring_progress(new_pct, f"{new_done}", "新学",
                                                PRIMARY, ft.Icons.MENU_BOOK_OUTLINED),
                            ft.Container(width=16),
                            self._ring_progress(review_pct, f"{review_done}", "复习",
                                                SECONDARY, ft.Icons.AUTO_STORIES_OUTLINED),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                    ], spacing=0),
                    elevation="sm",
                ),

                ft.Container(height=CARD_GAP),

                # === 快捷操作 ===
                AppCard(
                    content=ft.Column([
                        ft.Text("快捷操作", size=FONT_LG, weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY),
                        ft.Container(height=SPACING_MD),
                        ft.Row([
                            self._action_btn("学习", ft.Icons.MENU_BOOK, PRIMARY,
                                            lambda e: self.app.switch_to_page(1)),
                            self._action_btn("复习", ft.Icons.AUTO_STORIES, SECONDARY,
                                            lambda e: self.app.switch_to_page(2)),
                            self._action_btn("统计", ft.Icons.BAR_CHART,
                                            "#7E57C2",
                                            lambda e: self.app.switch_to_page(3)),
                            self._action_btn("设置", ft.Icons.SETTINGS,
                                            "#78909C",
                                            lambda e: self.app.switch_to_page(4)),
                        ], spacing=8),
                    ], spacing=0),
                    elevation="sm",
                ),

                ft.Container(height=CARD_GAP),

                # === Info Banner ===
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=3, height=32,
                                     bgcolor=SECONDARY, border_radius=2),
                        ft.Container(width=12),
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=TEXT_SECONDARY),
                        ft.Container(width=6),
                        ft.Column([
                            ft.Text("提示", size=FONT_SM, weight=ft.FontWeight.BOLD,
                                    color=TEXT_PRIMARY),
                            ft.Text("双击 start.bat 启动浏览器", size=FONT_SM,
                                    color=TEXT_SECONDARY),
                        ], spacing=0, tight=True),
                    ]),
                    padding=ft.Padding(left=16, top=12, right=16, bottom=12),
                    bgcolor=ft.Colors.with_opacity(0.06, SECONDARY),
                    border_radius=RADIUS_MD,
                ),

                ft.Container(height=16),
            ],
            padding=ft.Padding(left=PAGE_PADDING, top=PAGE_PADDING,
                               right=PAGE_PADDING, bottom=0),
            spacing=0,
        )
        self._container.content = content

    def _pct_str(self, done, total):
        if total <= 0:
            return "0%"
        return f"{round(done/total*100, 1)}%"

    def _stat_card(self, icon, value, label, color):
        is_str = isinstance(value, str)
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=20),
                    width=40, height=40,
                    bgcolor=ft.Colors.with_opacity(0.10, color),
                    border_radius=20,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(str(value), size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                    ft.Text(label, size=FONT_XS, color=TEXT_SECONDARY),
                ], spacing=0, tight=True, expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=14, top=12, right=14, bottom=12),
            bgcolor=SURFACE,
            border_radius=RADIUS_MD,
            shadow=SHADOW_SM,
            expand=True,
            ink=True,
            on_click=lambda e: self.app.switch_to_page(3),
        )

    def _ring_progress(self, pct, value, label, color, icon):
        """环形进度指示器"""
        return ft.Container(
            content=ft.Column([
                ft.Stack([
                    # 背景环
                    ft.Container(
                        width=72, height=72,
                        border_radius=36,
                        bgcolor=ft.Colors.with_opacity(0.10, color),
                    ),
                    # 前景环（用圆形模拟）
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(icon, color=color, size=20),
                            ft.Text(value, size=FONT_XXL, weight=ft.FontWeight.BOLD,
                                    color=TEXT_PRIMARY),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0, tight=True),
                        width=72, height=72,
                        alignment=ft.alignment.center,
                    ),
                ], width=72, height=72),
                ft.Container(height=4),
                ft.Text(label, size=FONT_SM, color=TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            expand=True,
            alignment=ft.alignment.center,
        )

    def _action_btn(self, label, icon, color, cb):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=28),
                    padding=ft.Padding(left=12, top=12, right=12, bottom=12),
                    bgcolor=ft.Colors.with_opacity(0.12, color),
                    border_radius=RADIUS_MD,
                ),
                ft.Container(height=6),
                ft.Text(label, size=FONT_XS, color=TEXT_SECONDARY,
                        weight=ft.FontWeight.W_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            expand=True,
            alignment=ft.alignment.center,
            ink=True,
            on_click=cb,
        )


# 导入 ft.Icons 别名
LIBRARY_BOOKS = ft.Icons.LIBRARY_BOOKS
CHECK_CIRCLE = ft.Icons.CHECK_CIRCLE
STARS = ft.Icons.STARS
LOCAL_FIRE_DEPARTMENT = ft.Icons.LOCAL_FIRE_DEPARTMENT
