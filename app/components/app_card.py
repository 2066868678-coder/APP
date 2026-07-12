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
