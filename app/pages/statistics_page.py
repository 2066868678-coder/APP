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
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, SUCCESS, ERROR, WARNING,
    COLOR_STATS,
    PAGE_PADDING, CARD_GAP,
    SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_XS, RADIUS_SM, RADIUS_MD,
    SHADOW_SM, SHADOW_MD,
    FONT_XS, FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL,
    BADGE_COLORS,
    BORDER, PROGRESS_BG,
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
                # === 学习概览 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.BAR_CHART,
                                                color=COLOR_STATS, size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, COLOR_STATS),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("学习概览", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=BORDER),
                        ft.Container(height=SPACING_SM),
                        ft.Row([
                            self._ov("总单词", str(total),
                                     ft.Icons.LIBRARY_BOOKS, COLOR_STATS),
                            self._ov("已学习", str(learned),
                                     ft.Icons.CHECK_CIRCLE, SUCCESS),
                        ], spacing=SPACING_SM),
                        ft.Container(height=SPACING_SM),
                        ft.Row([
                            self._ov("已掌握", str(mastered),
                                     ft.Icons.STARS, WARNING),
                            self._ov("未学习", str(unlearned),
                                     ft.Icons.HOURGLASS_EMPTY, TEXT_HINT),
                        ], spacing=SPACING_SM),
                        ft.Container(height=SPACING_XL),
                        ft.Row([
                            ft.Text("总进度", size=FONT_SM, color=TEXT_SECONDARY),
                            ft.Text(f"{pct}%", size=FONT_SM, color=COLOR_STATS,
                                    weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=SPACING_XS),
                        self._progress_bar(pct),
                    ], spacing=0),
                ),

                ft.Container(height=CARD_GAP),

                # === 今日统计 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.CALENDAR_TODAY,
                                                color=COLOR_STATS, size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, COLOR_STATS),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("今日统计", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=BORDER),
                        ft.Container(height=SPACING_SM),
                        ft.Row([
                            self._today_mini("新学", str(today_new),
                                             ft.Icons.PLAY_ARROW, SUCCESS),
                            self._today_mini("复习", str(today_review),
                                             ft.Icons.AUTO_STORIES, SECONDARY),
                            self._today_mini("学习天数", str(study_days),
                                             ft.Icons.CALENDAR_MONTH, COLOR_STATS),
                            self._today_mini("连续", f"{streak}天",
                                             ft.Icons.LOCAL_FIRE_DEPARTMENT,
                                             WARNING if streak > 0 else TEXT_HINT),
                        ], spacing=4),
                    ], spacing=0),
                ),

                ft.Container(height=CARD_GAP),

                # === 掌握程度 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.PIE_CHART,
                                                color=COLOR_STATS, size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, COLOR_STATS),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("掌握程度", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=BORDER),
                        ft.Container(height=SPACING_MD),
                        self._stacked_bar(unlearned, learning, mastered, total),
                        ft.Container(height=SPACING_MD),
                        ft.Row([
                            self._seg_label("未学习", unlearned, total, "#94A3B8"),
                            self._seg_label("学习中", learning, total, SECONDARY),
                            self._seg_label("已掌握", mastered, total, COLOR_STATS),
                        ], spacing=SPACING_SM),
                    ], spacing=0),
                ),

                ft.Container(height=CARD_GAP),

                # === 成就徽章 ===
                AppCard(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.EMOJI_EVENTS,
                                                color=WARNING, size=18),
                                padding=ft.Padding(6, 6, 6, 6),
                                bgcolor=ft.Colors.with_opacity(0.10, WARNING),
                                border_radius=8,
                            ),
                            ft.Container(width=8),
                            ft.Text("成就徽章", size=FONT_LG,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ]),
                        ft.Divider(height=1, color=BORDER),
                        ft.Container(height=SPACING_LG),
                        ft.Row([
                            self._badge("🏆", "初学者", learned > 0,
                                        BADGE_COLORS['beginner']),
                            self._badge("🔥", "连续7天", streak >= 7,
                                        BADGE_COLORS['streak7']),
                            self._badge("💪", f"已学{learned}词", learned > 0,
                                        BADGE_COLORS['learned']),
                            self._badge("⭐", "坚持者", study_days >= 30,
                                        BADGE_COLORS['persistent']),
                        ], spacing=SPACING_SM),
                    ], spacing=0),
                ),

                ft.Container(height=CARD_GAP),

                # === 完整单词列表入口 ===
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.LIST_ALT,
                                            color=COLOR_STATS, size=20),
                            padding=ft.Padding(8, 8, 8, 8),
                            bgcolor=ft.Colors.with_opacity(0.10, COLOR_STATS),
                            border_radius=10,
                        ),
                        ft.Container(width=12),
                        ft.Text("完整单词列表", size=FONT_BODY,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY,
                                expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_HINT, size=20),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding(left=SPACING_LG, top=14, right=SPACING_LG,
                                       bottom=14),
                    bgcolor=SURFACE,
                    border_radius=RADIUS_MD,
                    shadow=SHADOW_SM,
                    ink=True,
                    on_click=self._show_word_list,
                ),

                ft.Container(height=SPACING_LG),
            ],
            spacing=0,
        )
        self._container.content = ft.Container(
            content=content,
            padding=ft.Padding(left=PAGE_PADDING, top=PAGE_PADDING,
                               right=PAGE_PADDING, bottom=0),
        )

    def _progress_bar(self, pct):
        """Gradient progress bar"""
        pct = max(0, min(100, pct))
        fill = max(pct, 1)
        empty = max(100 - pct, 1) if pct < 100 else 0
        return ft.Container(
            content=ft.Row(spacing=0, controls=[
                ft.Container(
                    expand=fill,
                    height=8,
                    gradient=ft.LinearGradient(
                        colors=[PRIMARY, COLOR_STATS],
                        begin=ft.Alignment(-1, 0),
                        end=ft.Alignment(1, 0),
                    ),
                ),
                ft.Container(
                    expand=empty,
                    height=8,
                    bgcolor=PROGRESS_BG,
                ),
            ]),
            border_radius=4,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    def _ov(self, label, value, icon, color):
        """Stat overview block with icon, value, label"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=16),
                    width=34, height=34,
                    bgcolor=ft.Colors.with_opacity(0.12, color),
                    border_radius=8,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(value, size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=color),
                    ft.Text(label, size=FONT_XS, color=TEXT_SECONDARY),
                ], spacing=0, tight=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            bgcolor=ft.Colors.with_opacity(0.04, color),
            border_radius=RADIUS_SM,
            expand=True,
        )

    def _today_mini(self, label, value, icon, color):
        """Compact mini stat for today section"""
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=14),
                    width=30, height=30,
                    bgcolor=ft.Colors.with_opacity(0.12, color),
                    border_radius=8,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(height=4),
                ft.Text(value, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                        color=color, text_align=ft.TextAlign.CENTER),
                ft.Text(label, size=FONT_XS, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               spacing=0, tight=True),
            expand=True,
            padding=ft.Padding(top=4, bottom=4),
        )

    def _stacked_bar(self, unlearned, learning, mastered, total):
        if total <= 0:
            return ft.Container(height=12)
        u = max(unlearned, 1)
        l = max(learning, 1)
        m = max(mastered, 1)
        return ft.Container(
            content=ft.Row([
                ft.Container(expand=u, height=14, bgcolor="#94A3B8"),
                ft.Container(expand=l, height=14, bgcolor=SECONDARY),
                ft.Container(expand=m, height=14, bgcolor=COLOR_STATS),
            ], spacing=0),
            border_radius=7,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    def _seg_label(self, label, count, total, color):
        pct = round(count / total * 100, 1) if total > 0 else 0
        return ft.Row([
            ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
            ft.Container(width=4),
            ft.Text(f"{label} {pct}%", size=FONT_XS, color=TEXT_SECONDARY),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _badge(self, emoji, label, unlocked, color):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(emoji, size=28,
                                    text_align=ft.TextAlign.CENTER),
                    width=48, height=48,
                    alignment=ft.alignment.Alignment(0, 0),
                    bgcolor=ft.Colors.with_opacity(0.15 if unlocked else 0.06,
                                                    color),
                    border_radius=24,
                    border=ft.BorderSide(
                        1.5, ft.Colors.with_opacity(0.20 if unlocked else 0.08,
                                                    color)
                    ) if unlocked else None,
                ),
                ft.Container(height=4),
                ft.Text(label, size=FONT_XS,
                        color=TEXT_PRIMARY if unlocked else TEXT_HINT,
                        weight=ft.FontWeight.W_500 if unlocked
                               else ft.FontWeight.NORMAL,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               spacing=0, tight=True),
            expand=True,
            opacity=1.0 if unlocked else 0.35,
        )

    def _show_word_list(self, e):
        data = api_service.get_all_words_with_status()
        if not data or not data.get('words'):
            self.app.show_snackbar('加载失败')
            return
        words = data['words']
        learned = [w for w in words if w['studied']]
        unlearned = [w for w in words if not w['studied']]

        def make_rows(items, limit=200):
            rows = []
            for w in items[:limit]:
                ch = w.get('chapter', '') or ''
                ph = w.get('phonetic', '') or ''
                rows.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                width=8, height=8,
                                bgcolor=SUCCESS if w['studied'] else TEXT_HINT,
                                border_radius=4,
                            ),
                            ft.Container(width=8),
                            ft.Text(w['word'], size=FONT_BODY, expand=1,
                                    color=TEXT_PRIMARY,
                                    weight=ft.FontWeight.W_600),
                            ft.Text(ph, size=FONT_SM, color=TEXT_HINT,
                                    expand=1, italic=True,
                                    text_align=ft.TextAlign.END),
                            ft.Container(
                                content=ft.Text(ch, size=9, color=ft.Colors.WHITE,
                                                weight=ft.FontWeight.W_500),
                                padding=ft.Padding(6, 2, 6, 2),
                                bgcolor=COLOR_STATS,
                                border_radius=RADIUS_XS,
                            ) if ch else ft.Container(),
                        ], spacing=4,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Container(width=16),
                            ft.Text(w.get('meaning', '')[:60], size=FONT_SM,
                                    color=TEXT_SECONDARY, max_lines=1,
                                    italic=True),
                        ], spacing=0),
                    ], spacing=1),
                    padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                    border=ft.Border(
                        bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08,
                                            BORDER)),
                        left=ft.BorderSide(0, None),
                        right=ft.BorderSide(0, None),
                        top=ft.BorderSide(0, None),
                    ),
                    ink=True,
                ))
            if len(items) > limit:
                rows.append(
                    ft.Container(
                        content=ft.Text(f"... 还有 {len(items) - limit} 个单词",
                                       size=FONT_SM, color=TEXT_HINT,
                                       text_align=ft.TextAlign.CENTER),
                        padding=ft.Padding(top=8, bottom=8),
                    )
                )
            return rows

        segments = []
        segments.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=SUCCESS),
                ft.Container(width=6),
                ft.Text(f'已学习 ({len(learned)})', size=FONT_LG,
                        weight=ft.FontWeight.BOLD, color=SUCCESS),
            ]),
            padding=ft.Padding(top=8, bottom=4),
        ))
        if learned:
            segments.extend(make_rows(learned, 100))
            segments.append(ft.Container(height=8))
        else:
            segments.append(ft.Text('暂无', color=TEXT_SECONDARY, size=13))
        segments.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.HOURGLASS_EMPTY, size=18, color=TEXT_HINT),
                ft.Container(width=6),
                ft.Text(f'未学习 ({len(unlearned)})', size=FONT_LG,
                        weight=ft.FontWeight.BOLD, color=TEXT_HINT),
            ]),
            padding=ft.Padding(top=4, bottom=4),
        ))
        if unlearned:
            segments.extend(make_rows(unlearned, 100))
        else:
            segments.append(ft.Text('暂无', color=TEXT_SECONDARY, size=13))

        dlg = ft.AlertDialog(
            title=ft.Text(f'总单词列表 ({len(words)}词)'),
            content=ft.Container(
                content=ft.Column(segments, scroll=ft.ScrollMode.AUTO),
                width=380, height=500,
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
