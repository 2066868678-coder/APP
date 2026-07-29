#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 统一卡片组件
======================
提供一致样式的卡片容器，所有页面使用此组件代替直接定义 Container。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    SURFACE, RADIUS_MD, RADIUS_SM,
    SHADOW_MAP, SPACING_LG,
    GRADIENT_PRIMARY,
)


class AppCard(ft.Container):
    """统一卡片组件

    用法：
        AppCard(content=ft.Text("内容"))
        AppCard(content=..., elevation="lg", radius=20, padding=20)

    参数：
        content: 卡片内容控件
        padding: 内边距（默认 16）
        elevation: 阴影层级 "sm" | "md" | "lg"（默认 "md"）
        radius: 圆角（默认 12）
        ink: 是否有点击水波纹（默认 False）
        on_click: 点击回调
    """

    def __init__(
        self,
        content: ft.Control = None,
        padding: int = None,
        elevation: str = "md",
        radius: int = None,
        ink: bool = False,
        on_click=None,
        **kwargs,
    ):
        padding = padding if padding is not None else SPACING_LG
        radius = radius if radius is not None else RADIUS_MD

        super().__init__(
            content=content,
            bgcolor=SURFACE,
            border_radius=radius,
            padding=padding if isinstance(padding, (ft.Padding, int)) else padding,
            shadow=SHADOW_MAP.get(elevation, SHADOW_MAP["md"]),
            ink=ink,
            on_click=on_click,
            **kwargs,
        )


class AppCardSmall(ft.Container):
    """小卡片 — 用于统计数据等紧凑场景"""

    def __init__(self, content: ft.Control = None, **kwargs):
        super().__init__(
            content=content,
            bgcolor=SURFACE,
            border_radius=RADIUS_SM,
            shadow=SHADOW_MAP["sm"],
            **kwargs,
        )


class AppCardGradient(ft.Container):
    """渐变背景卡片

    用法与 AppCard 一致，仅底色替换为渐变。
    适用于顶栏下方突出区域、模块入口、升级/成就卡片。

    参数：
        gradient: 渐变对象（默认 GRADIENT_PRIMARY）
        content: 卡片内容控件
        padding: 内边距（默认 16）
        elevation: 阴影层级 "sm" | "md" | "lg"（默认 "md"）
        radius: 圆角（默认 12）
    """

    def __init__(
        self,
        content: ft.Control = None,
        gradient=None,
        padding: int = None,
        elevation: str = "md",
        radius: int = None,
        **kwargs,
    ):
        padding = padding if padding is not None else SPACING_LG
        radius = radius if radius is not None else RADIUS_MD

        super().__init__(
            content=content,
            gradient=gradient or GRADIENT_PRIMARY,
            border_radius=radius,
            padding=padding if isinstance(padding, (ft.Padding, int)) else padding,
            shadow=SHADOW_MAP.get(elevation, SHADOW_MAP["md"]),
            **kwargs,
        )


# Attach accent-card helper as a classmethod on AppCard
def _accent_card(content: ft.Control, accent_color: str = None, **kwargs):
    """返回带左侧彩色强调边框的卡片"""
    color = accent_color or "#4F46E5"
    return AppCard(
        content=content,
        border=ft.Border(
            left=ft.BorderSide(width=4, color=color),
        ),
        **kwargs,
    )


AppCard.with_accent = staticmethod(_accent_card)
