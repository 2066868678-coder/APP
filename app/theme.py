#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - Deep Focus 设计系统（LIGHT / DARK 双色板）
======================================================
靛蓝主色 + 极简主义风格（单色系、大留白、高对比）。

浅色/深色切换机制：
- `set_mode(mode)` / `toggle_mode()` 切换色板
- 模块级颜色常量（PRIMARY、SURFACE 等）会立即指向新色板
- 通过 `_sync_importers()` 把新色值同步到所有 `from app.theme import X`
  的模块（页面模块的全局变量会被重绑），因此页面 build() 时取到的
  永远是当前模式的色值，无需在页面里做任何动态取值改造。

用法（main.py）：
    import app.theme as theme
    theme.set_mode('dark')
    page.theme = theme.make_theme()
    page.theme_mode = ft.ThemeMode.DARK
    然后重新执行页面 build() 即可整体换肤。
"""

import sys
import flet as ft


# ============================================================
# 色板定义 Palette（浅色 LIGHT / 深色 DARK）
# ============================================================
_LIGHT = {
    'PRIMARY': "#4F46E5",            # Indigo 600 — 主色
    'PRIMARY_DARK': "#3730A3",       # Indigo 800
    'PRIMARY_LIGHT': "#A5B4FC",      # Indigo 200
    'PRIMARY_CONTAINER': "#EEF2FF",  # Indigo 50
    'SECONDARY': "#0EA5E9",          # Sky 500 — 模糊档/次要强调
    'BACKGROUND': "#F8FAFC",         # 极浅灰 — 页面背景
    'SURFACE': "#FFFFFF",            # 白 — 卡片底色
    'SUCCESS': "#16A34A",            # Green 600 — 记得/完成
    'ERROR': "#DC2626",              # Red 600 — 忘记/重置
    'WARNING': "#F59E0B",            # Amber 500 — 警告
    'WARM_LIGHT': "#FFF8E1",         # Amber 50（保留兼容）
    'TEXT_PRIMARY': "#111827",       # 主要正文
    'TEXT_SECONDARY': "#6B7280",     # 次要文字
    'TEXT_HINT': "#94A3B8",          # 提示文字
    'TEXT_ON_PRIMARY': "#FFFFFF",    # 主色上的文字
    'PROGRESS_BG': "#E5E7EB",        # 进度条背景
    'BORDER': "#E5E7EB",             # 分割线/边框
    'COLOR_LEARN': "#4F46E5",        # 学习页主色（统一主色）
    'COLOR_REVIEW': "#0EA5E9",       # 复习页主色（统一主色）
    'COLOR_STATS': "#4F46E5",        # 统计页主色（统一主色）
    'COLOR_SETTINGS': "#4F46E5",     # 设置页主色（统一主色）
}

_DARK = {
    'PRIMARY': "#818CF8",            # Indigo 300 — 暗色下更亮
    'PRIMARY_DARK': "#6366F1",       # Indigo 400
    'PRIMARY_LIGHT': "#C7D2FE",      # Indigo 200
    'PRIMARY_CONTAINER': "#312E81",  # Indigo 900
    'SECONDARY': "#38BDF8",          # Sky 400
    'BACKGROUND': "#0F172A",         # Slate 900 — 页面背景
    'SURFACE': "#1F2937",            # Slate 800 — 卡片底色
    'SUCCESS': "#34D399",            # Emerald 400
    'ERROR': "#F87171",              # Red 400
    'WARNING': "#FBBF24",            # Amber 400
    'WARM_LIGHT': "#451A03",
    'TEXT_PRIMARY': "#F9FAFB",       # 主要正文
    'TEXT_SECONDARY': "#9CA3AF",     # 次要文字
    'TEXT_HINT': "#6B7280",          # 提示文字
    'TEXT_ON_PRIMARY': "#FFFFFF",
    'PROGRESS_BG': "#374151",        # Slate 700
    'BORDER': "#374151",             # Slate 700
    'COLOR_LEARN': "#818CF8",
    'COLOR_REVIEW': "#38BDF8",
    'COLOR_STATS': "#818CF8",
    'COLOR_SETTINGS': "#818CF8",
}

# 成就徽章色（极简：统一主色，仅靠解锁态透明度区分）
_BADGE_COLORS_LIGHT = {
    'beginner': "#4F46E5",
    'streak7': "#4F46E5",
    'learned': "#4F46E5",
    'persistent': "#4F46E5",
}
_BADGE_COLORS_DARK = {
    'beginner': "#818CF8",
    'streak7': "#818CF8",
    'learned': "#818CF8",
    'persistent': "#818CF8",
}


# ============================================================
# 当前模式状态
# ============================================================
_MODE = 'light'


def get_mode() -> str:
    """返回当前模式：'light' 或 'dark'"""
    return _MODE


def _make_gradients(palette):
    """按当前色板生成渐变对象"""
    p = palette
    return {
        # 顶部渐变 Header（品牌感，两模式共用靛蓝渐变）
        'GRADIENT_HEADER': ft.LinearGradient(
            colors=["#4F46E5", "#7C3AED", "#6366F1"],
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 0),
        ),
        # 主色渐变（学习页/按钮/强调）
        'GRADIENT_PRIMARY': ft.LinearGradient(
            colors=[p['PRIMARY_DARK'], p['PRIMARY']],
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 0),
        ),
        # 复习页渐变（统一主色系，略提亮区分）
        'GRADIENT_REVIEW': ft.LinearGradient(
            colors=[p['PRIMARY'], p['PRIMARY_LIGHT']],
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 0),
        ),
    }


def set_mode(mode: str) -> str:
    """切换色板并同步所有引用方，返回当前模式。

    会重绑本模块颜色常量、重建渐变对象，并把新值同步到所有
    `from app.theme import X` 的页面/组件模块（重绑其模块全局变量）。
    页面在 build() 时读取的即是最新色值。
    """
    global _MODE
    mode = 'dark' if mode == 'dark' else 'light'
    _MODE = mode
    palette = _DARK if mode == 'dark' else _LIGHT

    # 1) 重绑本模块颜色常量
    for name, value in palette.items():
        globals()[name] = value
    globals()['BADGE_COLORS'] = dict(
        _BADGE_COLORS_DARK if mode == 'dark' else _BADGE_COLORS_LIGHT
    )

    # 2) 重建渐变对象
    for name, gradient in _make_gradients(palette).items():
        globals()[name] = gradient

    # 3) 同步到所有导入方模块
    _sync_importers()
    return _MODE


def toggle_mode() -> str:
    """浅/深色互切，返回新模式"""
    return set_mode('dark' if _MODE == 'light' else 'light')


# ------------------------------------------------------------
# 初始绑定（默认浅色）。注意：BORDER 等名称也参与同步。
# ------------------------------------------------------------
for _name, _value in _LIGHT.items():
    globals()[_name] = _value
BADGE_COLORS = dict(_BADGE_COLORS_LIGHT)
for _gname, _gradient in _make_gradients(_LIGHT).items():
    globals()[_gname] = _gradient
del _name, _value, _gname, _gradient

# 语义色 — 各模块专用（随色板同步，见 _SYNC_NAMES）
# COLOR_LEARN / COLOR_REVIEW / COLOR_STATS / COLOR_SETTINGS 已在上面重绑

# ============================================================
# 颜色同步（关键机制）
# ============================================================
# 所有模块级颜色/渐变 token 名。set_mode 时会把这些名字的当前值
# 重绑到下列模块的全局命名空间，使 `from app.theme import X` 生效。
_SYNC_NAMES = tuple(_LIGHT.keys()) + ('BADGE_COLORS',) + (
    'GRADIENT_HEADER', 'GRADIENT_PRIMARY', 'GRADIENT_REVIEW',
)

_IMPORTER_MODULES = (
    'app.main',
    'app.pages.home_page',
    'app.pages.study_page',
    'app.pages.review_page',
    'app.pages.statistics_page',
    'app.pages.settings_page',
    'app.components.app_card',
)


def _sync_importers():
    """把当前色板值重绑到所有 from app.theme 导入过颜色的模块"""
    for mod_name in _IMPORTER_MODULES:
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        for name in _SYNC_NAMES:
            if hasattr(mod, name):
                setattr(mod, name, globals()[name])


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
# 阴影 Shadows（两模式共用中性阴影）
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
    """生成 Flet Theme 对象（使用当前色板）"""
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


