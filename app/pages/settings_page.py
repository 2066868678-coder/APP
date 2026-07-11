#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 设置页面
==================
系统设置：每日目标、数据导出、重置、关于
"""

import sys, os, json, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.services import api_service, local_db
from backend.models import StudyRecord, DailyPlan


def _clear_study_records():
    """清空学习记录"""
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
    """导出单词到文件"""
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
        # 每日目标相关状态
        self._target_value = ft.TextField(
            value=str(api_service.get_daily_target()),
            width=80,
            height=42,
            text_size=16,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.GREEN,
            content_padding=ft.Padding(left=8, right=8, top=6, bottom=6),
        )

    def build(self):
        # 每日学习目标
        daily = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.TRACK_CHANGES, color=ft.Colors.GREEN, size=20),
                        ft.Text("每日学习目标", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=12),
                ft.Row([
                    ft.Text("每天新学单词", size=14, color=ft.Colors.GREY_700),
                    ft.Container(expand=True),
                    self._target_value,
                ]),
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "保存目标",
                        icon=ft.Icons.SAVE,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=self._save_target,
                    ),
                ]),
                ft.Container(height=4),
                ft.Text("建议：每天10-20个，有基础可30-50个",
                        size=12, color=ft.Colors.GREY_400, italic=True),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=ft.Colors.WHITE, border_radius=12,
        )

        # 数据管理
        data_mgmt = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.STORAGE, color=ft.Colors.ORANGE, size=20),
                        ft.Text("数据管理", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=12),
                ft.ElevatedButton("导出单词到 words_export.json", icon=ft.Icons.DOWNLOAD,
                    on_click=self._export_data, width=280),
                ft.Container(height=8),
                ft.ElevatedButton("重置学习记录", icon=ft.Icons.DELETE_SWEEP,
                    color=ft.Colors.RED, on_click=self._confirm_reset, width=280),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=ft.Colors.WHITE, border_radius=12,
        )

        # 启动帮助
        launch_help = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, color=ft.Colors.BLUE, size=20),
                        ft.Text("下次如何打开", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                ft.Text("在项目目录双击 start.bat 即可启动", size=14, color=ft.Colors.BLACK87),
                ft.Container(height=4),
                ft.Text("或手动运行:", size=13, color=ft.Colors.GREY_600),
                ft.Container(
                    content=ft.Text("cd E:\\APP\npython run_app.py", size=13,
                                    color=ft.Colors.BLUE_700, font_family="monospace"),
                    padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                    bgcolor=ft.Colors.BLUE_50, border_radius=6,
                ),
                ft.Container(height=4),
                ft.Text("浏览器打开 http://localhost:8551", size=13, color=ft.Colors.GREY_600),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=ft.Colors.WHITE, border_radius=12,
        )

        # 关于
        about = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.INFO, color=ft.Colors.GREY, size=20),
                        ft.Text("关于", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                self._row("应用", "单词突围 (独立版)"),
                self._row("版本", "2.0.0"),
                self._row("数据来源", "《单词突围5200》上册"),
                self._row("复习算法", "艾宾浩斯遗忘曲线"),
                self._row("单词总数", "2281 个"),
                self._row("运行模式", "本地数据库 (无需后端)"),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=ft.Colors.WHITE, border_radius=12,
        )

        return ft.ListView([
            daily, ft.Container(height=8),
            data_mgmt, ft.Container(height=8),
            launch_help, ft.Container(height=8),
            about, ft.Container(height=16),
        ], padding=ft.Padding(left=16, top=16, right=16, bottom=16), spacing=0)

    def _row(self, label, value):
        return ft.Row([
            ft.Text(label, size=14, color=ft.Colors.GREY_700),
            ft.Container(expand=True),
            ft.Text(value, size=14, color=ft.Colors.BLACK87),
        ])

    def _save_target(self, e):
        try:
            val = int(self._target_value.value)
            if val < 1:
                self.app.show_snackbar("每日目标至少为1", ft.Colors.ORANGE)
                return
            if val > 200:
                self.app.show_snackbar("目标太高了，建议不超过50", ft.Colors.ORANGE)
                return
            ok = api_service.set_daily_target(val)
            if ok:
                self.app.show_snackbar(f"每日新词目标已设为 {val} 个")
            else:
                self.app.show_snackbar("保存失败", ft.Colors.RED)
        except ValueError:
            self.app.show_snackbar("请输入有效数字", ft.Colors.ORANGE)

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
                ft.TextButton("取消", on_click=lambda e: self.app.close_dialog(dlg)),
                ft.TextButton("确定重置",
                    style=ft.ButtonStyle(color=ft.Colors.RED),
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
