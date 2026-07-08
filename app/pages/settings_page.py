#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 设置页面
==================
系统设置：每日目标、复习设置、数据管理、云同步
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.services import api_service


class SettingsPage:
    """设置页面"""

    def __init__(self, app):
        self.app = app
        self.page = app.page

    def build(self):
        # 后端状态
        backend_ok = api_service.is_backend_running()
        backend_status = "✅ 已连接" if backend_ok else "❌ 未连接"

        daily = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.TRACK_CHANGES, color=ft.Colors.GREEN, size=20),
                        ft.Text("每日学习目标", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                self._row("每天新学单词", "20 个"),
                ft.Container(height=4),
                ft.Text("建议：每天10-20个，有基础可30-50个",
                        size=12, color=ft.Colors.GREY_400, italic=True),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        review = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.AUTO_STORIES, color=ft.Colors.BLUE, size=20),
                        ft.Text("复习设置", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                self._row("艾宾浩斯复习", "已开启"),
                ft.Container(height=8),
                self._row("复习间隔", "第1、2、4、7、15天"),
                ft.Container(height=8),
                self._row("掌握标准", "连续记得5次"),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        data_mgmt = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.STORAGE, color=ft.Colors.ORANGE, size=20),
                        ft.Text("数据管理", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=12),
                ft.ElevatedButton("导出学习数据", icon=ft.Icons.DOWNLOAD,
                    on_click=self._export_data, width=280),
                ft.Container(height=8),
                ft.ElevatedButton("重置学习记录", icon=ft.Icons.DELETE_SWEEP,
                    color=ft.Colors.RED, on_click=self._confirm_reset, width=280),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        cloud = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CLOUD_SYNC, color=ft.Colors.BLUE, size=20),
                        ft.Text("云同步", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                self._row("同步状态", "本地存储"),
                ft.Container(height=8),
                self._row("后端服务", backend_status),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        about = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.INFO, color=ft.Colors.GREY, size=20),
                        ft.Text("关于", size=16, weight=ft.FontWeight.BOLD)]),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                self._row("应用名称", "单词突围"),
                self._row("版本", "1.0.0"),
                self._row("数据来源", "《单词突围5200》上册"),
                self._row("复习算法", "艾宾浩斯遗忘曲线"),
                self._row("单词总数", "2315 个"),
            ], spacing=0),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16), bgcolor=ft.Colors.WHITE, border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        return ft.ListView([
            daily, ft.Container(height=8),
            review, ft.Container(height=8),
            data_mgmt, ft.Container(height=8),
            cloud, ft.Container(height=8),
            about, ft.Container(height=16),
        ], padding=ft.Padding(left=16, top=16, right=16, bottom=16), spacing=0)

    def _row(self, label, value):
        return ft.Row([
            ft.Text(label, size=14, color=ft.Colors.GREY_700),
            ft.Container(expand=True),
            ft.Text(value, size=14, color=ft.Colors.BLACK87),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def _export_data(self, e):
        self.app.show_snackbar("数据导出中...")

    def _do_export(self):
        try:
            data = api_service.get_words(page=1, page_size=3000)
            if data:
                self.app.page.schedule(
                    lambda: self.app.show_snackbar(f"✅ 已导出 {data['total']} 个单词"))
        except Exception:
            self.app.page.schedule(
                lambda: self.app.show_snackbar("❌ 导出失败，后端未连接"))

    def _confirm_reset(self, e):
        dlg = ft.AlertDialog(
            title=ft.Text("确认重置"),
            content=ft.Text("确定要重置所有学习记录吗？此操作不可撤销！"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.app.close_dialog(dlg)),
                ft.TextButton("确定重置", color=ft.Colors.RED,
                    on_click=lambda e: self._do_reset(dlg)),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _do_reset(self, dlg):
        self.app.close_dialog(dlg)
        self.app.show_snackbar("重置功能需后端支持")
