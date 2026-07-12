#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 统计页面（全新设计）
==================
展示学习进度和统计数据
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, SECONDARY, BACKGROUND, SURFACE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, SUCCESS, ERROR,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG,
    RADIUS_MD, RADIUS_SM,
    SHADOW_SM, SHADOW_MD,
    FONT_XS, FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL,
    BADGE_COLORS,
)
from app.components.app_card import AppCard
from app.services import api_service


class StatisticsPage:
    """统计页面"""

    def __init__(self, app):
        self.app = app
        self.page = app.page
        self._container = ft.Container(expand=True)

    def build(self):
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
        learning = max(0, learned - mastered)
        streak = s.get('streak_days', 0)
        study_days = s.get('study_days', 0)
        today = s.get('today', {}) or {}
        today_new = today.get('new_words_done', 0)
        today_review = today.get('review_done', 0)

        content = ft.ListView(
            controls=[
                # === 学习概览（2×2 网格） ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.BAR_CHART,
                                                color="#7E57C2", size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, "#7E57C2"),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("学习概览", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=12),
                        ft.Row([
                            self._ov("总单词", str(total), ft.Icons.LIBRARY_BOOKS, "#7E57C2"),
                            self._ov("已学习", str(learned), ft.Icons.CHECK_CIRCLE, PRIMARY_LIGHT),
                        ], spacing=8),
                        ft.Container(height=8),
                        ft.Row([
                            self._ov("已掌握", str(mastered), ft.Icons.STARS, "#FF8F00"),
                            self._ov("未学习", str(unlearned), ft.Icons.HOURGLASS_EMPTY, TEXT_HINT),
                        ], spacing=8),
                        ft.Container(height=SPACING_LG),
                        ft.Text("总进度", size=FONT_SM, color=TEXT_SECONDARY),
                        ft.Container(height=4),
                        ft.ProgressBar(
                            value=pct / 100,
                            color=PRIMARY_LIGHT,
                            bgcolor=ft.Colors.GREY_200,
                            height=8,
                            border_radius=4,
                        ),
                        ft.Container(height=2),
                        ft.Text(f"{pct}%", size=FONT_SM, color=TEXT_HINT,
                                text_align=ft.TextAlign.END),
                    ], spacing=0),
                    elevation="sm",
                ),

                ft.Container(height=CARD_GAP),

                # === 今日统计 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.CALENDAR_TODAY,
                                                color=SECONDARY, size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("今日统计", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=12),
                        ft.Row([
                            self._ov("新学", str(today_new), ft.Icons.PLAY_ARROW, SUCCESS),
                            self._ov("复习", str(today_review), ft.Icons.AUTO_STORIES, SECONDARY),
                            self._ov("学习天数", str(study_days), ft.Icons.CALENDAR_MONTH, "#7E57C2"),
                            self._ov("连续", f"{streak}天", ft.Icons.LOCAL_FIRE_DEPARTMENT,
                                     "#FF7043" if streak > 0 else TEXT_HINT),
                        ], spacing=4),
                    ], spacing=0),
                    elevation="sm",
                ),

                ft.Container(height=CARD_GAP),

                # === 掌握程度 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.PIE_CHART,
                                                color="#FF8F00", size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, "#FF8F00"),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("掌握程度", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=16),
                        # 三段彩色条
                        self._stacked_bar(unlearned, learning, mastered, total),
                        ft.Container(height=12),
                        ft.Row([
                            self._seg_label("未学习", unlearned, total, "#9E9E9E"),
                            self._seg_label("学习中", learning, total, SECONDARY),
                            self._seg_label("已掌握", mastered, total, PRIMARY_LIGHT),
                        ], spacing=8),
                    ], spacing=0),
                    elevation="sm",
                ),

                ft.Container(height=CARD_GAP),

                # === 成就徽章 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.EMOJI_EVENTS,
                                                color="#FF8F00", size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, "#FF8F00"),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("成就徽章", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=SPACING_LG),
                        ft.Row([
                            self._badge("🏆", "初学者", learned > 0, BADGE_COLORS['beginner']),
                            self._badge("🔥", "连续7天", streak >= 7, BADGE_COLORS['streak7']),
                            self._badge("💪", f"已学{learned}词", learned > 0, BADGE_COLORS['learned']),
                            self._badge("⭐", "坚持者", study_days >= 30, BADGE_COLORS['persistent']),
                        ], spacing=8),
                    ], spacing=0),
                    elevation="sm",
                ),

                ft.Container(height=CARD_GAP),

                # === 完整单词列表入口 ===
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.LIST_ALT,
                                            color="#78909C", size=20),
                            padding=ft.Padding(8, 8, 8, 8),
                            bgcolor=ft.Colors.with_opacity(0.10, "#78909C"),
                            border_radius=10,
                        ),
                        ft.Container(width=12),
                        ft.Text("完整单词列表", size=FONT_BODY,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_HINT, size=20),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding(left=SPACING_LG, top=14, right=SPACING_LG, bottom=14),
                    bgcolor=SURFACE,
                    border_radius=RADIUS_MD,
                    shadow=SHADOW_SM,
                    ink=True,
                    on_click=self._show_word_list,
                ),

                ft.Container(height=SPACING_LG),
            ],
            padding=ft.Padding(left=PAGE_PADDING, top=PAGE_PADDING,
                               right=PAGE_PADDING, bottom=0),
            spacing=0,
        )
        self._container.content = content

    def _ov(self, label, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=FONT_XXL, weight=ft.FontWeight.BOLD,
                        color=color, text_align=ft.TextAlign.CENTER),
                ft.Container(height=2),
                ft.Text(label, size=FONT_XS, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            expand=True,
            alignment=ft.alignment.center,
        )

    def _stacked_bar(self, unlearned, learning, mastered, total):
        if total <= 0:
            return ft.Container(height=12)
        u = max(unlearned, 1)
        l = max(learning, 1)
        m = max(mastered, 1)
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    expand=u, height=12,
                    bgcolor="#9E9E9E",
                    border_radius=ft.BorderRadius(top_left=6, bottom_left=6, top_right=0, bottom_right=0),
                ),
                ft.Container(
                    expand=l, height=12,
                    bgcolor=SECONDARY,
                    border_radius=0,
                ),
                ft.Container(
                    expand=m, height=12,
                    bgcolor=PRIMARY_LIGHT,
                    border_radius=ft.BorderRadius(top_left=0, bottom_left=0, top_right=6, bottom_right=6),
                ),
            ], spacing=0),
            border_radius=6,
        )

    def _seg_label(self, label, count, total, color):
        pct = round(count / total * 100, 1) if total > 0 else 0
        return ft.Row([
            ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
            ft.Container(width=4),
            ft.Text(f"{label} {pct}%", size=FONT_XS, color=TEXT_SECONDARY),
        ], spacing=0)

    def _badge(self, emoji, label, unlocked, color):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(emoji, size=24, text_align=ft.TextAlign.CENTER),
                    width=44, height=44,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.with_opacity(0.15 if unlocked else 0.05, color),
                    border_radius=22,
                ),
                ft.Container(height=4),
                ft.Text(label, size=FONT_XS, color=TEXT_PRIMARY if unlocked else TEXT_HINT,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            expand=True,
            opacity=1.0 if unlocked else 0.4,
        )

    def _show_word_list(self, e):
        data = api_service.get_all_words_with_status()
        if not data or not data.get('words'):
            self.app.show_snackbar('加载失败')
            return
        words = data['words']
        learned = [w for w in words if w['studied']]
        unlearned = [w for w in words if not w['studied']]

        def make_rows(items, limit=100):
            rows = []
            for w in items[:limit]:
                rows.append(ft.Row([
                    ft.Container(
                        width=6, height=6,
                        bgcolor=SUCCESS if w['studied'] else TEXT_HINT,
                        border_radius=3,
                    ),
                    ft.Container(width=8),
                    ft.Text(w['word'], size=FONT_BODY, expand=2, color=TEXT_PRIMARY),
                    ft.Text(w.get('meaning', '')[:30], size=FONT_SM,
                            color=TEXT_SECONDARY, expand=3),
                ], spacing=0))
            return rows

        segments = []
        segments.append(ft.Text(f'已学习 ({len(learned)})', size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=SUCCESS))
        if learned:
            segments.extend(make_rows(learned, 80))
            segments.append(ft.Container(height=8))
        else:
            segments.append(ft.Text('暂无', color=TEXT_SECONDARY, size=13))
        segments.append(ft.Divider())
        segments.append(ft.Text(f'未学习 ({len(unlearned)})', size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_HINT))
        if unlearned:
            segments.extend(make_rows(unlearned, 80))
        else:
            segments.append(ft.Text('暂无', color=TEXT_SECONDARY, size=13))

        dlg = ft.AlertDialog(
            title=ft.Text(f'总单词列表 ({len(words)}词)'),
            content=ft.Container(
                content=ft.Column(segments, scroll=ft.ScrollMode.AUTO),
                width=360, height=480,
            ),
            actions=[ft.TextButton('关闭',
                      on_click=lambda e: self._close_dlg(dlg))],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _close_dlg(self, dlg):
        dlg.open = False
        self.page.update()
