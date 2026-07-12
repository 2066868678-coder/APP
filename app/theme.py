#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 设计系统令牌
======================
集中管理所有颜色、间距、圆角、阴影等设计常量。
所有页面引用此文件，禁止硬编码颜色值。
"""

import flet as ft


# ============================================================
# 颜色 Palette
# ============================================================
PRIMARY = "#00897B"           # Teal 700 — 顶栏、导航选中、按钮主色
PRIMARY_DARK = "#00695C"      # Teal 800 — 顶栏加深
PRIMARY_LIGHT = "#4DB6AC"     # Teal 300 — 轻量强调
PRIMARY_CONTAINER = "#B2DFDB" # Teal 100 — 卡片内标签底色

SECONDARY = "#5C6BC0"         # Indigo 400 — 复习页等辅助色

BACKGROUND = "#F5F7FA"        # 微冷灰 — 页面背景
SURFACE = "#FFFFFF"           # 白 — 卡片底色

SUCCESS = "#43A047"           # Green 600 — 记得按钮、完成态
ERROR = "#E53935"             # Red 600 — 忘记按钮、重置

# 语义色 — 各模块专用
COLOR_LEARN = PRIMARY         # 学习页主色
COLOR_REVIEW = SECONDARY      # 复习页主色
COLOR_STATS = "#7E57C2"       # 统计页主色 (Deep Purple 400)
COLOR_SETTINGS = "#78909C"    # 设置页主色 (Blue Grey 400)

# 成就徽章色
BADGE_COLORS = {
    'beginner': "#43A047",
    'streak7': "#FF7043",
    'learned': "#42A5F5",
    'persistent': "#AB47BC",
}

# 文字色
TEXT_PRIMARY = "#212121"      # 主要正文
TEXT_SECONDARY = "#616161"    # 次要文字
TEXT_HINT = "#9E9E9E"        # 提示文字
TEXT_ON_PRIMARY = "#FFFFFF"   # 主色上的文字

# 进度色
PROGRESS_BG = "#E0E0E0"      # 进度条背景


# ============================================================
# 间距 Spacing
# ============================================================
PAGE_PADDING = 16
CARD_GAP = 8
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 20
SPACING_XXL = 24
SPACING_XXXL = 32


# ============================================================
# 圆角 Border Radius
# ============================================================
RADIUS_XS = 4
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 20
RADIUS_XL = 28
RADIUS_FULL = 999


# ============================================================
# 阴影 Shadows
# ============================================================
SHADOW_SM = ft.BoxShadow(
    blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 1),
)
SHADOW_MD = ft.BoxShadow(
    blur_radius=8, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2),
)
SHADOW_LG = ft.BoxShadow(
    blur_radius=16, color=ft.Colors.with_opacity(0.08, "#000000"),
    offset=ft.Offset(0, 6),
)
SHADOW_CARD = SHADOW_MD
SHADOW_ELEVATED = SHADOW_LG

SHADOW_MAP = {
    'sm': SHADOW_SM,
    'md': SHADOW_MD,
    'lg': SHADOW_LG,
}


# ============================================================
# 排版 Typography
# ============================================================
FONT_FAMILY = "sans-serif"

# 字号
FONT_XXS = 10
FONT_XS = 11
FONT_SM = 12
FONT_MD = 13
FONT_BODY = 14
FONT_LG = 16
FONT_XL = 18
FONT_XXL = 22
FONT_XXXL = 26
FONT_DISPLAY = 40
FONT_DISPLAY_LG = 44


# ============================================================
# 布局 Layout
# ============================================================
HEADER_HEIGHT = 100          # 顶栏总高度（含状态栏）
HEADER_PADDING_TOP = 45      # 状态栏高度
NAV_BAR_HEIGHT = 65          # 底部导航栏高度


# ============================================================
# 便捷函数
# ============================================================

def make_theme():
    """生成 Flet Theme 对象"""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=PRIMARY,
            primary_container=PRIMARY_CONTAINER,
            secondary=SECONDARY,
            surface=SURFACE,
        ),
        font_family=FONT_FAMILY,
        use_material3=True,
    )


def icon_bg_circle(color: str, size: int = 44) -> ft.Container:
    """带圆形背景的图标"""
    return ft.Container(
        content=ft.Container(
            width=size,
            height=size,
            bgcolor=ft.Colors.with_opacity(0.12, color),
            border_radius=size // 2,
            alignment=ft.alignment.CENTER,
        ),
    )
