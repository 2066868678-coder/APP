#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 统计页面
==================
展示学习进度和统计数据（直接从本地数据库读取）
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.services import api_service


class StatisticsPage:
    """统计页面"""

    def __init__(self, app):
        self.app = app
        self.page = app.page
        self._container = ft.Container(expand=True)

    def build(self):
        # 直接从本地数据库加载数据（瞬间完成）
        stats = self._safe_get_stats()
        self._render(stats)
        return self._container

    def _safe_get_stats(self):
        try:
            return api_service.get_stats()
        except Exception:
            return None

    def _render(self, stats):
        s = stats or {}
        total = s.get('total_words', 0)
        learned = s.get('learned_words', 0)
        mastered = s.get('mastered_words', 0)
        pct = s.get('progress_percent', 0)
        unlearned = max(0, total - learned)
        streak = s.get('streak_days', 0)
        study_days = s.get('study_days', 0)
        today = s.get('today', {}) or {}
        today_new = today.get('new_words_done', 0)
        today_review = today.get('review_done', 0)
        learning = max(0, learned - mastered)

        overview = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.PURPLE, size=20),
                        ft.Text("学习概览", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=12),
                ft.Row(controls=[
                    self._ov("总单词", str(total), ft.Colors.BLUE),
                    self._ov("已学习", str(learned), ft.Colors.GREEN),
                    self._ov("已掌握", str(mastered), ft.Colors.ORANGE),
                    self._ov("未学习", str(unlearned), ft.Colors.GREY),
                ], spacing=8),
                ft.Container(height=16),
                ft.Text("总进度", size=13),
                ft.ProgressBar(value=pct/100, color=ft.Colors.GREEN, bgcolor=ft.Colors.GREY_200,
                              height=8, border_radius=4),
                ft.Text(f"{pct}%", size=12, color=ft.Colors.GREY, text_align=ft.TextAlign.END),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        today_card = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, color=ft.Colors.BLUE, size=20),
                        ft.Text("今日统计", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=12),
                ft.Row(controls=[
                    self._ov("新学", str(today_new), ft.Colors.GREEN),
                    self._ov("复习", str(today_review), ft.Colors.BLUE),
                    self._ov("学习天数", str(study_days), ft.Colors.PURPLE),
                    self._ov("连续", f"{streak}天", ft.Colors.RED),
                ], spacing=8),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        mastery = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.PIE_CHART, color=ft.Colors.ORANGE, size=20),
                        ft.Text("掌握程度", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=16),
                ft.Row(controls=[
                    self._seg("未学习", round(unlearned/total*100) if total > 0 else 0, "#9E9E9E"),
                    self._seg("学习中", round(learning/total*100) if total > 0 else 0, "#2196F3"),
                    self._seg("已掌握", round(mastered/total*100) if total > 0 else 0, "#4CAF50"),
                ], spacing=4),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        badges_list = [
            ("🏆", "初学者", learned > 0),
            ("🔥", "连续7天", streak >= 7),
            ("💪", f"已学{learned}词", learned > 0),
            ("⭐", "坚持者", study_days >= 30),
        ]
        badges = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.AMBER, size=20),
                        ft.Text("成就徽章", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=16),
                ft.Row(controls=[
                    ft.Container(content=ft.Column([
                        ft.Text(e, size=32, text_align=ft.TextAlign.CENTER),
                        ft.Text(l, size=10, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, tight=True),
                    expand=True, opacity=1.0 if u else 0.3)
                    for e, l, u in badges_list
                ], spacing=8),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        content = ft.ListView([
            overview, ft.Container(height=8),
            today_card, ft.Container(height=8),
            mastery, ft.Container(height=8),
            badges, ft.Container(height=16),
        ], padding=ft.Padding(left=16, top=16, right=16, bottom=16), spacing=0)

        self._container.content = content

    def _ov(self, label, value, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=11, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            expand=True, alignment=ft.alignment.Alignment.CENTER,
        )

    def _seg(self, label, pct, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(f"{pct}%", size=18, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=12, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            expand=True, alignment=ft.alignment.Alignment.CENTER,
        )
