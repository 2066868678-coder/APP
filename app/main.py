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

import urllib.parse
import flet as ft
import app.theme as theme
from app.theme import (
    PRIMARY, BACKGROUND, SURFACE,
    TEXT_ON_PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    HEADER_PADDING_TOP,
    NAV_BAR_HEIGHT, RADIUS_MD, RADIUS_XL, SHADOW_LG,
    FONT_BODY, FONT_XS, ERROR, BORDER,
    GRADIENT_HEADER,
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
    VERSION = "2.2.0"

    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()

        # 初始化各页面
        self.home_page = HomePage(self)
        self.study_page = StudyPage(self)
        self.review_page = ReviewPage(self)
        self.statistics_page = StatisticsPage(self)
        self.settings_page = SettingsPage(self)

        # 页面索引
        self.current_index = 0

        # 构建UI
        self.build_ui()

    def setup_page(self):
        """设置页面属性（应用当前色板，浅色为默认）"""
        theme.set_mode('light')
        self.page.title = self.APP_NAME
        self.page.theme = make_theme()
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.bgcolor = BACKGROUND

    def build_ui(self):
        """构建主界面"""
        # 浅色/深色切换按钮（浅色模式下显示"切到深色"图标）
        self.theme_toggle_btn = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED, icon_color=TEXT_SECONDARY,
            tooltip="切换到深色模式", on_click=self.toggle_theme,
        )

        self.page_container = ft.Container(
            content=self.home_page.build(),
            expand=True,
            animate_opacity=ft.Animation(200),
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
            indicator_color=PRIMARY,
        )

        # 内容区与导航边框（供主题切换时更新配色）
        self.content_area = ft.Container(
            content=self.page_container,
            expand=True,
            bgcolor=BACKGROUND,
        )
        self.nav_border = ft.Container(
            content=self.nav_bar,
            border=ft.Border(top=ft.BorderSide(width=0.5, color=TEXT_SECONDARY)),
        )

        self.page.add(
            ft.Column([
                # 顶部简洁标题栏（极简：白底 + 细分割线）
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(self.APP_NAME, size=17,
                                    weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ft.Text(f"v{self.VERSION}", size=10,
                                    color=TEXT_HINT),
                        ], spacing=0),
                        ft.Container(expand=True),
                        # 浅色/深色切换
                        self.theme_toggle_btn,
                        ft.IconButton(
                            icon=ft.Icons.INFO_OUTLINE, icon_color=TEXT_SECONDARY,
                            tooltip="关于", on_click=self.show_about,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.Padding(left=20, right=4, top=HEADER_PADDING_TOP, bottom=10),
                    bgcolor=SURFACE,
                    border=ft.Border(
                        left=ft.BorderSide(0, None),
                        right=ft.BorderSide(0, None),
                        top=ft.BorderSide(0, None),
                        bottom=ft.BorderSide(width=0.5, color=BORDER),
                    ),
                ),
                # 页面内容（内容区固定高度，滚动由各页面内部处理，
                # 底部导航因此固定在视口底部不随内容跳动）
                self.content_area,
                # 底部导航
                self.nav_border,
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
            self.page_container.update()
            self.page.update()

    def toggle_theme(self, e):
        """浅色/深色模式切换"""
        mode = theme.toggle_mode()
        self._apply_theme()
        self.show_snackbar(
            "已切换到深色模式" if mode == 'dark' else "已切换到浅色模式"
        )

    def _apply_theme(self):
        """把当前色板应用到页面框架并重建当前页面内容"""
        mode = theme.get_mode()
        is_dark = mode == 'dark'

        # 页面级主题
        self.page.theme = make_theme()
        self.page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        self.page.bgcolor = BACKGROUND

        # 内容区/导航配色
        self.content_area.bgcolor = BACKGROUND
        self.nav_bar.bgcolor = SURFACE
        self.nav_bar.indicator_color = PRIMARY
        self.nav_border.border = ft.Border(
            top=ft.BorderSide(width=0.5, color=TEXT_SECONDARY)
        )

        # 切换按钮图标
        self.theme_toggle_btn.icon = (
            ft.Icons.LIGHT_MODE_OUTLINED if is_dark else ft.Icons.DARK_MODE_OUTLINED
        )
        self.theme_toggle_btn.tooltip = (
            "切换到浅色模式" if is_dark else "切换到深色模式"
        )

        # 重新构建当前页面（各页面 build() 会按新色板取色）
        self.switch_to_page(self.current_index)
        self.page.update()

    def show_about(self, e):
        VERSION = "2.2.0"
        VERSION_DATE = "2026-07-25"
        CHANGES = (
            "【2.2.0】2026-07-25\n"
            "  - 三档熟悉程度：熟悉/模糊/不记得\n"
            "  - 例句翻译默认隐藏，点击展开\n"
            "  - 单词/搭配/例句一键发音（免费TTS）\n"
            "  - 复习页展示固定搭配反推含义\n"
            "  - 记忆方法/例句卡片顺序互换\n"
            "  - 修复benefit/economic记忆方法\n"
            "  - 单词列表显示更多信息\n"
            "  - 当日计划完成后不再分配新词\n"
            "  - 修复页面切换显示异常bug\n"
            "【2.1.0】2026-07-12\n"
            "  - UI全面美化（Teal主题+设计系统）\n"
            "  - 学习页增加剩余天数预估\n"
            "  - 学习记录导出为Word文档\n"
            "  - 批量查询优化跨设备同步速度\n"
            "【2.0.0】2026-07-11\n"
            "  - 全面修复上册2281个单词数据\n"
            "  - 修复释义/音标/记忆方法/例句错配\n"
            "  - 清除PDF提取遗留的格式错误字符\n"
            "  - 优化数据格式和排版"
        )
        about_dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=PRIMARY),
                ft.Container(width=8),
                ft.Text("关于 单词突围", weight=ft.FontWeight.BOLD),
            ], tight=True),
            content=ft.Column(
                controls=[
                    ft.Text(f"版本 {VERSION}（{VERSION_DATE}）", weight=ft.FontWeight.BOLD),
                    ft.Text("基于《单词突围5200》的智能背词应用", size=FONT_XS, color=TEXT_SECONDARY),
                    ft.Divider(height=1, color=BORDER),
                    ft.Text(CHANGES, size=FONT_XS, color=TEXT_SECONDARY),
                ],
                tight=True,
                spacing=8,
                width=320,
            ),
            actions=[
                ft.TextButton("确定", on_click=lambda e: self.close_dialog(about_dlg)),
            ],
            shape=ft.RoundedRectangleBorder(radius=RADIUS_MD),
        )
        self.page.overlay.append(about_dlg)
        about_dlg.open = True
        self.page.update()

    def close_dialog(self, dlg):
        """关闭对话框"""
        dlg.open = False
        self.page.update()

    def pronounce_link(self, text, size=24):
        """发音链接 — 用TextSpan.url直接导航（不走WebSocket，不被弹窗拦截）"""
        if not text or not text.strip():
            return ft.Container(width=0, height=0)
        url = f"/pronounce?text={urllib.parse.quote(text.strip()[:600])}"
        return ft.Text(
            spans=[ft.TextSpan(
                text="🔊",
                url=url,
                style=ft.TextStyle(size=size),
            )],
        )

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

