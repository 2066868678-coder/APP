#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 设置页面（全新设计）
==================
"""

import sys, os, json, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, SECONDARY, SURFACE, SUCCESS, ERROR, BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, TEXT_ON_PRIMARY,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_MD, RADIUS_SM, RADIUS_XL,
    SHADOW_SM, SHADOW_MD,
    FONT_XS, FONT_SM, FONT_BODY, FONT_LG,
)
from app.components.app_card import AppCard
from app.services import api_service, local_db
from backend.models import StudyRecord, DailyPlan


def _clear_study_records():
    s = local_db._get_session()
    try:
        s.query(StudyRecord).delete()
        s.query(DailyPlan).delete()
        s.commit()
        return True
    except:
        s.rollback()
        return False
    finally:
        s.close()


def _export_words():
    data = api_service.get_words(page=1, page_size=3000)
    if not data or not data.get('words'):
        return None, 0
    words = data['words']
    export_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'words_export.json'
    )
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    return export_path, len(words)


class SettingsPage:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self._target_value = ft.TextField(
            value=str(api_service.get_daily_target()),
            width=80,
            height=42,
            text_size=FONT_LG,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.OUTLINE,
            border_color=PRIMARY,
            content_padding=ft.Padding(left=8, right=8, top=6, bottom=6),
        )

    def build(self):
        return ft.ListView([
            # === 每日学习目标 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.TRACK_CHANGES,
                                            color=PRIMARY, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("每日学习目标", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=SPACING_MD),
                    ft.Row([
                        ft.Text("每天新学单词", size=FONT_BODY, color=TEXT_SECONDARY),
                        ft.Container(expand=True),
                        self._target_value,
                    ]),
                    ft.Container(height=SPACING_MD),
                    ft.Row([
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SAVE, color=ft.Colors.WHITE, size=16),
                                ft.Container(width=4),
                                ft.Text("保存目标", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                            ]),
                            padding=ft.Padding(20, 10, 20, 10),
                            bgcolor=PRIMARY,
                            border_radius=RADIUS_MD,
                            ink=True,
                            on_click=self._save_target,
                        ),
                    ]),
                    ft.Container(height=4),
                    ft.Text("建议：每天10-20个，有基础可30-50个",
                            size=FONT_SM, color=TEXT_HINT, italic=True),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # === 数据管理 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.STORAGE,
                                            color="#FF8F00", size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, "#FF8F00"),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("数据管理", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=SPACING_MD),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DOWNLOAD, color=PRIMARY, size=18),
                            ft.Container(width=8),
                            ft.Text("导出单词到 JSON", size=FONT_BODY,
                                    color=TEXT_PRIMARY, expand=True),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_HINT, size=18),
                        ]),
                        padding=ft.Padding(12, 10, 12, 10),
                        bgcolor=ft.Colors.with_opacity(0.04, PRIMARY),
                        border_radius=RADIUS_SM,
                        ink=True,
                        on_click=self._export_data,
                    ),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DELETE_SWEEP, color=ERROR, size=18),
                            ft.Container(width=8),
                            ft.Text("重置学习记录", size=FONT_BODY,
                                    color=ERROR, expand=True),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_HINT, size=18),
                        ]),
                        padding=ft.Padding(12, 10, 12, 10),
                        bgcolor=ft.Colors.with_opacity(0.04, ERROR),
                        border_radius=RADIUS_SM,
                        ink=True,
                        on_click=self._confirm_reset,
                    ),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # === 启动帮助 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE,
                                            color=SECONDARY, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("下次如何打开", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=8),
                    ft.Text("双击 start.bat 或在终端运行：", size=FONT_SM, color=TEXT_SECONDARY),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text("cd E:\\APP\npython run_app.py",
                                        size=13, color=PRIMARY, font_family="monospace"),
                        padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                        border_radius=RADIUS_SM,
                    ),
                    ft.Container(height=8),
                    ft.Text("浏览器打开 http://localhost:8551", size=FONT_SM, color=TEXT_SECONDARY),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # === 关于 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.INFO,
                                            color=TEXT_HINT, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.06, TEXT_HINT),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("关于", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=8),
                    self._info_row("应用", "单词突围 (独立版)"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("版本", "2.0.0"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("数据来源", "《单词突围5200》上册"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("复习算法", "艾宾浩斯遗忘曲线"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("单词总数", "2281 个"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("运行模式", "本地数据库 (无需后端)"),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=SPACING_LG),
        ], padding=ft.Padding(left=PAGE_PADDING, top=PAGE_PADDING,
                               right=PAGE_PADDING, bottom=0), spacing=0)

    def _info_row(self, label, value):
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=FONT_BODY, color=TEXT_SECONDARY),
                ft.Container(expand=True),
                ft.Text(value, size=FONT_BODY, color=TEXT_PRIMARY,
                        weight=ft.FontWeight.W_500),
            ]),
            padding=ft.Padding(left=4, top=10, right=4, bottom=10),
        )

    def _save_target(self, e):
        try:
            val = int(self._target_value.value)
            if val < 1:
                self.app.show_snackbar("每日目标至少为1", ERROR)
                return
            if val > 200:
                self.app.show_snackbar("目标太高了，建议不超过50", ERROR)
                return
            ok = api_service.set_daily_target(val)
            if ok:
                self.app.show_snackbar(f"每日新词目标已设为 {val} 个")
            else:
                self.app.show_snackbar("保存失败", ERROR)
        except ValueError:
            self.app.show_snackbar("请输入有效数字", ERROR)

    def _export_data(self, e):
        path, count = _export_words()
        if path and count > 0:
            self.app.show_snackbar(f"已导出 {count} 个单词到 words_export.json")
        else:
            self.app.show_snackbar("导出失败：没有数据")

    def _confirm_reset(self, e):
        dlg = ft.AlertDialog(
            title=ft.Text("确认重置"),
            content=ft.Text("确定要清除所有学习记录吗？单词数据不会丢失。"),
            actions=[
                ft.TextButton("取消",
                    on_click=lambda e: self.app.close_dialog(dlg)),
                ft.TextButton("确定重置",
                    style=ft.ButtonStyle(color=ERROR),
                    on_click=lambda e: self._do_reset(dlg)),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_reset(self, dlg):
        self.app.close_dialog(dlg)
        ok = _clear_study_records()
        if ok:
            self.app.show_snackbar("学习记录已清空")
        else:
            self.app.show_snackbar("重置失败")
