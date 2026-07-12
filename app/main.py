#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - Flet手机App入口
=========================
主程序文件，启动Flet应用

启动方式：
    python app/main.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_DARK, BACKGROUND, SURFACE,
    TEXT_ON_PRIMARY, HEADER_HEIGHT, HEADER_PADDING_TOP,
    NAV_BAR_HEIGHT, PAGE_PADDING, RADIUS_MD, RADIUS_XL, SHADOW_LG,
    FONT_BODY,
    make_theme,
)
from app.pages.home_page import HomePage
from app.pages.study_page import StudyPage
from app.pages.review_page import ReviewPage
from app.pages.statistics_page import StatisticsPage
from app.pages.settings_page import SettingsPage


class WordBreakthroughApp:
    """单词突围 - 主应用"""

    APP_NAME = "单词突围"
    VERSION = "2.0.0"

    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()

        # 初始化各页面
        self.home_page = HomePage(self)
        self.study_page = StudyPage(self)
        self.review_page = ReviewPage(self)
        self.statistics_page = StatisticsPage(self)
        self.settings_page = SettingsPage(self)

        # 当前页面索引
        self.current_index = 0

        # 构建UI
        self.build_ui()

    def setup_page(self):
        """设置页面属性"""
        self.page.title = self.APP_NAME
        self.page.theme = make_theme()
        self.page.padding = 0
        self.page.bgcolor = BACKGROUND
        self.page.scroll = ft.ScrollMode.AUTO

    def build_ui(self):
        """构建主界面"""
        self.page_container = ft.Container(
            content=self.home_page.build(),
            expand=True,
        )

        # 底部导航栏
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self.on_nav_change,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME, label="首页"),
                ft.NavigationBarDestination(icon=ft.Icons.MENU_BOOK_OUTLINED,
                    selected_icon=ft.Icons.MENU_BOOK, label="学习"),
                ft.NavigationBarDestination(icon=ft.Icons.AUTO_STORIES_OUTLINED,
                    selected_icon=ft.Icons.AUTO_STORIES, label="复习"),
                ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART_OUTLINED,
                    selected_icon=ft.Icons.BAR_CHART, label="统计"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS, label="设置"),
            ],
            height=NAV_BAR_HEIGHT,
            bgcolor=SURFACE,
            shadow_color=ft.Colors.BLACK12,
        )

        self.page.add(
            ft.Column([
                # 顶部圆角 Header
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(self.APP_NAME, size=20, weight=ft.FontWeight.BOLD,
                                    color=TEXT_ON_PRIMARY),
                            ft.Text(f"v{self.VERSION}", size=11,
                                    color=ft.Colors.with_opacity(0.7, TEXT_ON_PRIMARY)),
                        ]),
                        ft.Container(expand=True),
                        ft.IconButton(icon=ft.Icons.INFO_OUTLINE, icon_color=TEXT_ON_PRIMARY,
                            tooltip="关于", on_click=self.show_about),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding(left=20, right=8, top=HEADER_PADDING_TOP, bottom=16),
                    bgcolor=PRIMARY,
                    border_radius=ft.BorderRadius(bottom_left=RADIUS_XL, bottom_right=RADIUS_XL),
                    shadow=SHADOW_LG,
                ),
                # 页面内容
                ft.Container(
                    content=self.page_container,
                    expand=True,
                    bgcolor=BACKGROUND,
                ),
                # 底部导航
                self.nav_bar,
            ],
                spacing=0,
                tight=True,
            )
        )

    def on_nav_change(self, e):
        """导航栏切换"""
        self.current_index = e.control.selected_index
        self.switch_to_page(self.current_index)

    def switch_to_page(self, index: int):
        """切换到指定页面"""
        pages = [
            self.home_page.build,
            self.study_page.build,
            self.review_page.build,
            self.statistics_page.build,
            self.settings_page.build,
        ]

        if 0 <= index < len(pages):
            self.page_container.content = pages[index]()
            self.nav_bar.selected_index = index
            self.page.update()

    def show_about(self, e):
        VERSION = "2.0.0"
        VERSION_DATE = "2026-07-11"
        CHANGES = (
            "【2.0.0】2026-07-11\n"
            "  - 全面修复上册2281个单词数据\n"
            "  - 修复释义/音标/记忆方法/例句错配\n"
            "  - 清除PDF提取遗留的格式错误字符\n"
            "  - 优化数据格式和排版"
        )
        about_dlg = ft.AlertDialog(
            title=ft.Text("关于 单词突围"),
            content=ft.Column(
                controls=[
                    ft.Text(f"版本 {VERSION}（{VERSION_DATE}）", weight=ft.FontWeight.BOLD),
                    ft.Text("基于《单词突围5200》的智能背词应用", size=12),
                    ft.Divider(),
                    ft.Text(f"上册收录 {2281} 个单词", size=12),
                    ft.Text("艾宾浩斯遗忘曲线智能复习", size=12),
                    ft.Divider(),
                    ft.Text(CHANGES, size=11, color=ft.Colors.GREY),
                ],
                tight=True,
                spacing=5,
                width=320,
            ),
            actions=[
                ft.TextButton("确定", on_click=lambda e: self.close_dialog(about_dlg)),
            ],
        )
        self.page.overlay.append(about_dlg)
        about_dlg.open = True
        self.page.update()

    def close_dialog(self, dlg):
        """关闭对话框"""
        dlg.open = False
        self.page.update()

    def show_snackbar(self, message: str, color: str = None):
        """显示漂浮提示（圆角+图标）"""
        if color is None:
            color = PRIMARY
        has_error = color == ERROR
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE if has_error else ft.Icons.CHECK_CIRCLE,
                       color=ft.Colors.WHITE, size=18),
                ft.Container(width=8),
                ft.Text(message, color=ft.Colors.WHITE, size=FONT_BODY),
            ]),
            bgcolor=color,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_MD),
            duration=2500,
            open=True,
        )
        self.page.overlay.append(snack)
        self.page.update()


def main(page: ft.Page):
    """Flet应用入口"""
    WordBreakthroughApp(page)


if __name__ == '__main__':
    # 检查后端是否运行
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backend_running = sock.connect_ex(('127.0.0.1', 8000)) == 0
    sock.close()

    if not backend_running:
        print("=" * 50)
        print("⚠️  后端服务未启动！")
        print("请在另一个终端中运行：")
        print("  python backend/main.py")
        print("=" * 50)
        print()
        print("现在将启动App（但部分功能可能不可用）...")
        print()

    ft.app(target=main)

