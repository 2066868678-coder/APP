#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 首页
==============
显示今日学习计划和进度概览（直读本地数据库，飞快）
"""

import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
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

        hour = datetime.datetime.now().hour
        if hour < 6: greet = "夜深了"
        elif hour < 9: greet = "早上好"
        elif hour < 12: greet = "上午好"
        elif hour < 14: greet = "中午好"
        elif hour < 18: greet = "下午好"
        else: greet = "晚上好"

        self._container.content = ft.ListView([
            ft.Container(
                content=ft.Column([
                    ft.Text(f"{greet}！", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ft.Text("每天进步一点点", size=14, color=ft.Colors.GREY),
                ], spacing=4),
            ),
            ft.Container(height=8),
            ft.Container(
                content=ft.Row(controls=[
                    self._sc("总单词", str(total), ft.Icons.LIBRARY_BOOKS, "#2196F3"),
                    self._sc("已学", str(learned), ft.Icons.CHECK_CIRCLE, "#4CAF50"),
                    self._sc("已掌握", str(mastered), ft.Icons.STARS, "#FF9800"),
                    self._sc("连续", f"{streak}天", ft.Icons.LOCAL_FIRE_DEPARTMENT, "#F44336"),
                ], spacing=8),
            ),
            ft.Container(height=8),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.TODAY, color=ft.Colors.GREEN, size=20),
                            ft.Text("今日学习", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.TextButton("学习", on_click=lambda e: self.app.switch_to_page(1))]),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=8),
                    self._pr("新学单词", new_done, new_target),
                    ft.Container(height=6),
                    self._pr("复习单词", review_done, review_target),
                ], spacing=0),
                padding=ft.Padding(left=16, top=16, right=16, bottom=16),
                bgcolor=ft.Colors.WHITE, border_radius=12,
            ),
            ft.Container(height=8),
            ft.Container(
                content=ft.Column([
                    ft.Text("快捷操作", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=12),
                    ft.Row(controls=[
                        self._ab("学习", ft.Icons.MENU_BOOK, ft.Colors.GREEN,
                                lambda e: self.app.switch_to_page(1)),
                        self._ab("复习", ft.Icons.AUTO_STORIES, ft.Colors.BLUE,
                                lambda e: self.app.switch_to_page(2)),
                        self._ab("统计", ft.Icons.BAR_CHART, ft.Colors.PURPLE,
                                lambda e: self.app.switch_to_page(3)),
                        self._ab("设置", ft.Icons.SETTINGS, ft.Colors.GREY,
                                lambda e: self.app.switch_to_page(4)),
                    ], spacing=8),
                ], spacing=0),
                padding=ft.Padding(left=16, top=16, right=16, bottom=16),
                bgcolor=ft.Colors.WHITE, border_radius=12,
            ),
        ], padding=ft.Padding(left=16, top=16, right=16, bottom=16), spacing=0)
        # self._container已由build()返回，不需要update()

    def _sc(self, label, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=22),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                ft.Text(label, size=11, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            padding=ft.Padding(left=10, top=10, right=10, bottom=10),
            bgcolor=ft.Colors.WHITE, border_radius=12, expand=True,
            ink=True, on_click=lambda e: self.app.switch_to_page(3),
        )

    def _pr(self, label, done, total):
        pct = min(done/total, 1.0) if total > 0 else 0
        return ft.Column([
            ft.Row([ft.Text(label), ft.Container(expand=True),
                    ft.Text(f"{done}/{total}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)]),
            ft.ProgressBar(value=pct, color=ft.Colors.GREEN, bgcolor=ft.Colors.GREY_200, height=6),
        ], spacing=2)

    def _ab(self, label, icon, color, cb):
        return ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Icon(icon, color=color, size=28),
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                    bgcolor=ft.Colors.with_opacity(0.1, color), border_radius=12),
                ft.Text(label, size=12, color=ft.Colors.BLACK87),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            expand=True, alignment=ft.alignment.Alignment.CENTER, ink=True, on_click=cb,
        )
