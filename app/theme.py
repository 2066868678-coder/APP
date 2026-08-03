#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - Deep Focus 设计系统
==============================
现代精致的深色系设计语言，靛蓝主色调传递信任与专注，
暖琥珀色点缀传递能量与成就感。
所有页面引用此文件，禁止硬编码颜色值。
"""

import flet as ft


# ============================================================
# 颜色 Palette
# ============================================================
PRIMARY = "#4F46E5"            # Indigo 600 — 顶栏、导航选中、按钮主色
PRIMARY_DARK = "#3730A3"       # Indigo 800 — 顶栏加深
PRIMARY_LIGHT = "#A5B4FC"      # Indigo 200 — 轻量强调
PRIMARY_CONTAINER = "#EEF2FF"  # Indigo 50 — 卡片内标签底色

SECONDARY = "#0EA5E9"          # Sky 500 — 复习页等辅助色

BACKGROUND = "#F0F4FF"         # 暖调靛白 — 页面背景（比纯白更柔和）
SURFACE = "#FFFFFF"            # 白 — 卡片底色

SUCCESS = "#10B981"            # Emerald 500 — 记得按钮、完成态
ERROR = "#EF4444"              # Red 500 — 忘记按钮、重置
WARNING = "#F59E0B"            # Amber 500 — 警告
WARM_LIGHT = "#FFFBEB"         # Amber 50 — 记忆方法等暖色背景

# 语义色 — 各模块专用
COLOR_LEARN = PRIMARY           # 学习页主色 (Indigo)
COLOR_REVIEW = SECONDARY        # 复习页主色 (Sky)
COLOR_STATS = "#8B5CF6"         # 统计页主色 (Violet 500)
COLOR_SETTINGS = "#64748B"      # 设置页主色 (Slate 500)

# 成就徽章色
BADGE_COLORS = {
    'beginner': "#10B981",      # Emerald 500 — 新手
    'streak7': "#F59E0B",       # Amber 500 — 连续7天
    'learned': "#4F46E5",       # Indigo 600 — 已学
    'persistent': "#8B5CF6",    # Violet 500 — 坚持
}

# 文字色
TEXT_PRIMARY = "#1E293B"       # Slate 800 — 主要正文（比纯黑更柔和）
TEXT_SECONDARY = "#64748B"     # Slate 500 — 次要文字
TEXT_HINT = "#94A3B8"          # Slate 400 — 提示文字
TEXT_ON_PRIMARY = "#FFFFFF"    # 主色上的文字

# 进度色
PROGRESS_BG = "#E2E8F0"        # Slate 200 — 进度条背景

# 边框/分割线
BORDER = "#E2E8F0"             # Slate 200 — 一致的分割线/边框


# ============================================================
# 渐变色 Gradients (NEW)
# ============================================================
GRADIENT_HEADER = ft.LinearGradient(
    colors=["#4F46E5", "#7C3AED", "#6366F1"],  # Indigo → Violet → Indigo
    begin=ft.Alignment(-1, 0),                  # left
    end=ft.Alignment(1, 0),                     # right
)
GRADIENT_PRIMARY = ft.LinearGradient(
    colors=["#4F46E5", "#6366F1"],              # Indigo → slightly lighter Indigo
    begin=ft.Alignment(-1, 0),
    end=ft.Alignment(1, 0),
)
GRADIENT_REVIEW = ft.LinearGradient(
    colors=["#0EA5E9", "#38BDF8"],              # Sky 500 → Sky 400
    begin=ft.Alignment(-1, 0),
    end=ft.Alignment(1, 0),
)


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
SPACING_2XL = 24    # alias for SPACING_XXL
SPACING_3XL = 32    # alias for SPACING_XXXL
SPACING_4XL = 40


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
    blur_radius=20, color=ft.Colors.with_opacity(0.10, "#000000"),
    offset=ft.Offset(0, 8),
)
SHADOW_CARD = ft.BoxShadow(
    blur_radius=12, color=ft.Colors.with_opacity(0.06, "#000000"),
    offset=ft.Offset(0, 4),
)
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

# 字重
W_NORMAL = ft.FontWeight.NORMAL
W_MEDIUM = ft.FontWeight.W_500
W_SEMIBOLD = ft.FontWeight.W_600
W_BOLD = ft.FontWeight.BOLD

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
HEADER_HEIGHT = 100           # 顶栏总高度（含状态栏）
HEADER_PADDING_TOP = 45       # 状态栏高度
NAV_BAR_HEIGHT = 65           # 底部导航栏高度


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
        ),
    )


def make_gradient_container(
    content: ft.Control,
    colors: list[str] | None = None,
    padding: int = SPACING_LG,
    radius: int = RADIUS_MD,
) -> ft.Container:
    """用渐变色背景包裹内容"""
    gradient = ft.LinearGradient(
        colors=colors or ["#4F46E5", "#6366F1"],
        begin=ft.Alignment(-1, 0),
        end=ft.Alignment(1, 0),
    )
    return ft.Container(
        content=content,
        gradient=gradient,
        padding=padding,
        border_radius=radius,
    )


def section_divider() -> ft.Divider:
    """返回一条细分割线"""
    return ft.Divider(
        height=1,
        thickness=1,
        color=BORDER,
    )
