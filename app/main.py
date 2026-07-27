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
import asyncio
import tempfile
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib.parse
import httpx
import flet as ft
import flet_audio as fta
from app.theme import (
    PRIMARY, BACKGROUND, SURFACE,
    TEXT_ON_PRIMARY, HEADER_PADDING_TOP,
    NAV_BAR_HEIGHT, RADIUS_MD, RADIUS_XL, SHADOW_LG,
    FONT_BODY, ERROR,
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
    VERSION = "2.1.0"

    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()

        # 初始化各页面
        self.home_page = HomePage(self)
        self.study_page = StudyPage(self)
        self.review_page = ReviewPage(self)
        self.statistics_page = StatisticsPage(self)
        self.settings_page = SettingsPage(self)

        # 全局音频播放器 + 离线 TTS 引擎
        self._audio_player = fta.Audio(src="", volume=1.0)
        page.services.append(self._audio_player)
        self._audio_busy = False  # 防重复发音锁
        self._tts_engine = None
        self._tts_lock = threading.Lock()

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
                    border_radius=ft.BorderRadius(0, 0, RADIUS_XL, RADIUS_XL),
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
            # 重建页面容器确保完全刷新
            self.page_container.content = pages[index]()
            self.nav_bar.selected_index = index
            # 强制同步：先清空再更新
            self.page_container.update()
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

    def _get_tts(self):
        """懒初始化 TTS 引擎（线程安全，只在用到时 import）"""
        if self._tts_engine is None:
            with self._tts_lock:
                if self._tts_engine is None:  # double-check
                    import pyttsx3
                    self._tts_engine = pyttsx3.init()
        return self._tts_engine

    def play_audio(self, text):
        """播放单词发音（离线 TTS，无需网络）"""
        if not text or not text.strip():
            return
        if self._audio_busy:
            self.show_snackbar("正在发音，请稍候...")
            return
        self._audio_busy = True
        self.page.run_task(self._play_audio_async, text.strip())

    async def _play_audio_async(self, text):
        """用 pyttsx3 生成 WAV → 从文件播放（完全离线）"""
        tmp_path = None
        try:
            # 在子线程中生成语音文件（pyttsx3 是同步的）
            loop = asyncio.get_event_loop()
            tmp_path = await loop.run_in_executor(None, self._tts_to_file, text)

            # 从文件路径播放（比 bytes / data URI 稳定得多）
            self._audio_player.src = tmp_path
            self._audio_player.update()
            await asyncio.sleep(0.15)  # 给 Flutter 时间加载文件
            await self._audio_player.play()
            print(f"✅ 发音成功: {text}")

            # 30 秒后清理临时文件
            asyncio.get_event_loop().call_later(30,
                lambda p=tmp_path: self._try_cleanup(p))
        except Exception as e:
            print(f"❌ 离线发音失败 [{text}]: {e}")
            if tmp_path:
                self._try_cleanup(tmp_path)
            # 降级：尝试网络拉取
            await self._play_network_fallback(text)
        finally:
            self._audio_busy = False

    def _tts_to_file(self, text):
        """同步：用系统 TTS 生成临时 WAV 文件"""
        engine = self._get_tts()
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp.close()
        engine.save_to_file(text, tmp.name)
        engine.runAndWait()
        return tmp.name

    def _try_cleanup(self, path):
        """安全删除临时文件"""
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass

    async def _play_network_fallback(self, text):
        """网络 TTS 降级（多源轮询）"""
        encoded = urllib.parse.quote(text)
        sources = [
            f"https://dict.youdao.com/dictvoice?audio={encoded}&type=2",
            f"https://translate.google.com/translate_tts?tl=en&client=tw-ob&q={encoded}",
        ]
        for url in sources:
            try:
                async with httpx.AsyncClient(timeout=5) as c:
                    r = await c.get(url)
                if r.status_code == 200 and r.content:
                    # 存临时文件再播放
                    tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    tmp.write(r.content)
                    p = tmp.name
                    tmp.close()
                    self._audio_player.src = p
                    self._audio_player.update()
                    await asyncio.sleep(0.15)
                    await self._audio_player.play()
                    print(f"✅ 网络发音成功: {text}")
                    asyncio.get_event_loop().call_later(30,
                        lambda pp=p: self._try_cleanup(pp))
                    return
            except Exception as e:
                print(f"  网络源失败: {e}")
                continue
        self.show_snackbar("发音失败，请检查系统语音设置", ERROR)

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

