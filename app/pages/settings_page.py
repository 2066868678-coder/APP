#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 设置页面
==================
"""

import sys, os, threading, io, base64, urllib.parse
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, SECONDARY, SURFACE, SUCCESS, ERROR, BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_XXL,
    RADIUS_MD, RADIUS_SM, RADIUS_XL, RADIUS_LG,
    SHADOW_SM, SHADOW_MD,
    FONT_XS, FONT_SM, FONT_BODY, FONT_LG,
    COLOR_SETTINGS, BORDER, W_MEDIUM, W_SEMIBOLD,
)
from app.components.app_card import AppCard
from app.services import api_service, local_db
from backend.models import StudyRecord, DailyPlan

# 检查Word文档依赖
try:
    from docx import Document
    from docx.shared import Pt
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False


def _clear_study_records():
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


def _generate_docx(words_by_date):
    """生成Word文档（内存中）"""
    doc = Document()

    # 标题
    title = doc.add_heading('学习记录', level=0)
    doc.add_paragraph(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
    doc.add_paragraph('')

    total = sum(len(words) for words in words_by_date.values())
    for date, words in words_by_date.items():
        doc.add_heading(f'{date}（{len(words)}词）', level=1)
        for w in words:
            result_icon = '\u2713' if w.get('result') == 'remember' else '\u2717'
            p = doc.add_paragraph()
            run = p.add_run(f"{w['word']}")
            run.bold = True
            run.font.size = Pt(12)
            if w.get('phonetic'):
                run2 = p.add_run(f"  {w['phonetic']}")
                run2.font.size = Pt(10)
            if w.get('pos'):
                run3 = p.add_run(f"  [{w['pos']}]")
                run3.font.size = Pt(10)
            doc.add_paragraph(f"\u91ca\u4e49\uff1a{w.get('meaning', '')}", style='List Bullet')
            doc.add_paragraph(f"\u7ed3\u679c\uff1a{result_icon}", style='List Bullet')

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue(), total


def _format_date(d_str):
    """2026-07-12 \u2192 7\u670812\u65e5"""
    try:
        dt = datetime.strptime(d_str, '%Y-%m-%d')
        return f"{dt.month}\u6708{dt.day}\u65e5"
    except:
        return d_str


class SettingsPage:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self._target_value = ft.TextField(
            value=str(api_service.get_daily_target()),
            width=80, height=42,
            text_size=FONT_LG,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.OUTLINE,
            border_color=COLOR_SETTINGS,
            focused_border_color=COLOR_SETTINGS,
            content_padding=ft.Padding(left=8, right=8, top=6, bottom=6),
        )
        # 日期选择状态
        self._date_checks = {}    # { date_str: Checkbox }
        self._preview_container = ft.Container(
            content=ft.Text("\u9009\u62e9\u4e0a\u65b9\u65e5\u671f\u67e5\u770b\u5355\u8bcd",
                           size=FONT_SM, color=TEXT_HINT),
            padding=SPACING_MD,
        )
        self._download_btn = ft.Container(
            content=ft.Text("\u4e0b\u8f7d Word \u6587\u6863", color=ft.Colors.WHITE,
                           size=14, weight=ft.FontWeight.BOLD),
            padding=ft.Padding(24, 12, 24, 12),
            bgcolor=ft.Colors.GREY_400,
            border_radius=RADIUS_XL,
            ink=True,
            on_click=None,
        )

    def build(self):
        # 加载学习日期
        dates = []
        try:
            dates = api_service.get_study_dates()
        except:
            dates = []
        self._date_checks = {}

        date_rows = []
        for d_idx, d in enumerate(dates):
            cb = ft.Checkbox(
                label=f"{_format_date(d['date'])}\uff08{d['count']}\u8bcd\uff09",
                value=False,
                on_change=self._on_date_toggle,
                active_color=COLOR_SETTINGS,
                check_color=ft.Colors.WHITE,
            )
            self._date_checks[d['date']] = cb
            date_rows.append(
                ft.Container(
                    content=cb,
                    padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                    border_radius=RADIUS_SM,
                    bgcolor=ft.Colors.with_opacity(0.03, COLOR_SETTINGS) if d_idx % 2 == 1 else None,
                )
            )

        if not date_rows:
            date_rows = [
                ft.Container(
                    content=ft.Text("\u6682\u65e0\u5b66\u4e60\u8bb0\u5f55",
                                   size=FONT_SM, color=TEXT_HINT),
                    padding=SPACING_MD,
                )
            ]

        # 预览区域（初始空）
        self._preview_container.content = ft.Column([
            ft.Text("\u9009\u62e9\u65e5\u671f\u540e\u9884\u89c8\u5355\u8bcd",
                   size=FONT_SM, color=TEXT_HINT),
        ], spacing=0)

        # 关于信息
        about_items = [
            ("\u5e94\u7528", "\u5355\u8bcd\u7a81\u56f4 (\u72ec\u7acb\u7248)"),
            ("\u7248\u672c", "2.1.0"),
            ("\u6570\u636e\u6765\u6e90", "\u300a\u5355\u8bcd\u7a81\u56f45200\u300b\u4e0a\u518c"),
            ("\u590d\u4e60\u7b97\u6cd5", "\u827e\u5bbe\u6d69\u65af\u9057\u5fd8\u66f2\u7ebf"),
            ("\u5355\u8bcd\u603b\u6570", "2281 \u4e2a"),
            ("\u8fd0\u884c\u6a21\u5f0f", "\u672c\u5730\u6570\u636e\u5e93 (\u65e0\u9700\u540e\u7aef)"),
        ]
        about_rows = []
        for i, (label, value) in enumerate(about_items):
            about_rows.append(self._info_row(label, value, i))
            if i < len(about_items) - 1:
                about_rows.append(ft.Divider(height=1, color=BORDER))

        return ft.ListView([
            # ================================================================
            # 每日学习目标
            # ================================================================
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.TRACK_CHANGES,
                                            color=COLOR_SETTINGS, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, COLOR_SETTINGS),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("\u6bcf\u65e5\u5b66\u4e60\u76ee\u6807", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    ft.Container(height=SPACING_MD),
                    ft.Row([
                        ft.Text("\u6bcf\u5929\u65b0\u5b66\u5355\u8bcd", size=FONT_BODY,
                                color=TEXT_SECONDARY, weight=W_MEDIUM),
                        ft.Container(expand=True),
                        self._target_value,
                    ]),
                    ft.Container(height=SPACING_MD),
                    ft.Row([
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.SAVE, color=ft.Colors.WHITE, size=16),
                                ft.Container(width=4),
                                ft.Text("\u4fdd\u5b58\u76ee\u6807", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                            ]),
                            padding=ft.Padding(20, 10, 20, 10),
                            gradient=ft.LinearGradient(
                                colors=["#64748B", "#94A3B8"],
                                begin=ft.Alignment(-1, 0),
                                end=ft.Alignment(1, 0),
                            ),
                            border_radius=RADIUS_MD,
                            ink=True,
                            on_click=self._save_target,
                        ),
                    ]),
                    ft.Container(height=4),
                    ft.Text("\u5efa\u8bae\uff1a\u6bcf\u592910-20\u4e2a\uff0c\u6709\u57fa\u7840\u53ef30-50\u4e2a",
                            size=FONT_SM, color=TEXT_HINT, italic=True),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # ================================================================
            # 学习记录
            # ================================================================
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.DATE_RANGE,
                                            color=COLOR_SETTINGS, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, COLOR_SETTINGS),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("\u5b66\u4e60\u8bb0\u5f55", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    ft.Container(height=SPACING_SM),
                    # 日期列表（可多选）
                    *([ft.Container(
                        content=ft.Column([
                            ft.Text("\u9009\u62e9\u65e5\u671f", size=FONT_SM,
                                    color=TEXT_SECONDARY, weight=W_MEDIUM),
                            ft.Container(height=4),
                            *date_rows,
                        ], spacing=0),
                    )] if date_rows else [
                        ft.Container(
                            content=ft.Text("\u6682\u65e0\u5b66\u4e60\u8bb0\u5f55",
                                           size=FONT_SM, color=TEXT_HINT),
                            padding=SPACING_MD,
                        )
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    ft.Container(height=SPACING_SM),
                    # 预览区域
                    ft.Container(
                        content=ft.Column([
                            ft.Text("\u5355\u8bcd\u9884\u89c8", size=FONT_SM,
                                    color=TEXT_SECONDARY, weight=W_MEDIUM),
                            ft.Container(height=4),
                            ft.Container(
                                content=self._preview_container,
                                border=ft.Border(
                                    left=ft.BorderSide(3, COLOR_SETTINGS),
                                ),
                                border_radius=RADIUS_SM,
                                padding=ft.Padding(
                                    left=SPACING_SM, top=0, right=0, bottom=0
                                ),
                                bgcolor=ft.Colors.with_opacity(0.02, COLOR_SETTINGS),
                            ),
                        ], spacing=0),
                    ),
                    ft.Container(height=SPACING_MD),
                    # 下载按钮
                    ft.Container(
                        content=self._download_btn,
                    ),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # ================================================================
            # 数据管理
            # ================================================================
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.STORAGE, color="#FF8F00", size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, "#FF8F00"),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("\u6570\u636e\u7ba1\u7406", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    ft.Container(height=SPACING_MD),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.Icons.DELETE_SWEEP,
                                                color=ERROR, size=20),
                                padding=ft.Padding(4, 4, 4, 4),
                                bgcolor=ft.Colors.with_opacity(0.10, ERROR),
                                border_radius=6,
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text("\u91cd\u7f6e\u5b66\u4e60\u8bb0\u5f55",
                                        size=FONT_BODY, color=ERROR, weight=W_SEMIBOLD),
                                ft.Text("\u6e05\u7a7a\u6240\u6709\u5b66\u4e60\u8bb0\u5f55\uff0c"
                                        "\u5355\u8bcd\u6570\u636e\u4e0d\u53d7\u5f71\u54cd",
                                        size=FONT_XS, color=TEXT_HINT),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Icon(ft.Icons.CHEVRON_RIGHT,
                                                color=ERROR, size=20),
                            ),
                        ]),
                        padding=ft.Padding(12, 10, 12, 10),
                        bgcolor=ft.Colors.with_opacity(0.06, ERROR),
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ERROR)),
                        border_radius=RADIUS_SM,
                        ink=True,
                        on_click=self._confirm_reset,
                    ),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # ================================================================
            # 启动帮助
            # ================================================================
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE,
                                            color=SECONDARY, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("\u4e0b\u6b21\u5982\u4f55\u6253\u5f00", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    ft.Container(height=8),
                    ft.Text("\u53cc\u51fb start.bat \u6216\u5728\u7ec8\u7aef\u8fd0\u884c\uff1a",
                            size=FONT_SM, color=TEXT_SECONDARY),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text(
                            "cd E:\\APP\npython run_app.py",
                            size=13, color="#34D399", font_family="monospace",
                            weight=W_MEDIUM,
                        ),
                        padding=ft.Padding(left=16, top=12, right=16, bottom=12),
                        bgcolor="#1E293B",
                        border_radius=RADIUS_SM,
                    ),
                    ft.Container(height=8),
                    ft.Text("\u6d4f\u89c8\u5668\u6253\u5f00 http://localhost:8551",
                            size=FONT_SM, color=TEXT_SECONDARY),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # ================================================================
            # 关于
            # ================================================================
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.INFO, color=COLOR_SETTINGS, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, COLOR_SETTINGS),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("\u5173\u4e8e", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    ft.Container(height=8),
                    *about_rows,
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=SPACING_LG),
        ], padding=ft.Padding(left=PAGE_PADDING, top=PAGE_PADDING,
                               right=PAGE_PADDING, bottom=0), spacing=0)

    def _info_row(self, label, value, index=0):
        is_alt = index % 2 == 1
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=FONT_BODY, color=TEXT_SECONDARY, weight=W_MEDIUM),
                ft.Container(expand=True),
                ft.Text(value, size=FONT_BODY, color=TEXT_PRIMARY, weight=W_SEMIBOLD),
            ]),
            padding=ft.Padding(left=SPACING_MD, top=10, right=SPACING_MD, bottom=10),
            bgcolor=ft.Colors.with_opacity(0.04, COLOR_SETTINGS) if is_alt else None,
        )

    def _save_target(self, e):
        try:
            val = int(self._target_value.value)
            if val < 1:
                self.app.show_snackbar("\u6bcf\u65e5\u76ee\u6807\u81f3\u5c11\u4e3a1", ERROR)
                return
            if val > 200:
                self.app.show_snackbar("\u76ee\u6807\u592a\u9ad8\u4e86\uff0c\u5efa\u8bae\u4e0d\u8d85\u8fc750", ERROR)
                return
            ok = api_service.set_daily_target(val)
            if ok:
                self.app.show_snackbar(f"\u6bcf\u65e5\u65b0\u8bcd\u76ee\u6807\u5df2\u8bbe\u4e3a {val} \u4e2a")
            else:
                self.app.show_snackbar("\u4fdd\u5b58\u5931\u8d25", ERROR)
        except ValueError:
            self.app.show_snackbar("\u8bf7\u8f93\u5165\u6709\u6548\u6570\u5b57", ERROR)

    def _on_date_toggle(self, e):
        """日期选择变化 → 刷新预览和下载按钮"""
        selected = [d for d, cb in self._date_checks.items() if cb.value]
        if not selected:
            self._preview_container.content = ft.Column([
                ft.Text("\u9009\u62e9\u65e5\u671f\u540e\u9884\u89c8\u5355\u8bcd",
                       size=FONT_SM, color=TEXT_HINT),
            ], spacing=0)
            self._download_btn.on_click = None
            self._download_btn.bgcolor = ft.Colors.GREY_400
            self.page.update()
            return

        # 异步加载预览
        threading.Thread(target=self._load_preview, args=(selected,), daemon=True).start()

    def _load_preview(self, selected):
        """加载选中日期的单词预览"""
        try:
            words_by_date = api_service.get_words_by_dates(selected)
        except Exception:
            words_by_date = {}

        total = sum(len(v) for v in words_by_date.values())
        preview_rows = []
        for date in sorted(words_by_date.keys()):
            words = words_by_date[date]
            preview_rows.append(
                ft.Container(
                    content=ft.Text(
                        f"{_format_date(date)}\uff08{len(words)}\u8bcd\uff09",
                        size=FONT_SM, weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY,
                    ),
                    padding=ft.Padding(top=4, bottom=2),
                )
            )
            for w in words[:5]:  # 最多显示5个
                preview_rows.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                width=6, height=6,
                                bgcolor=COLOR_SETTINGS,
                                border_radius=3,
                            ),
                            ft.Container(width=6),
                            ft.Text(w['word'], size=FONT_SM, color=TEXT_PRIMARY,
                                    expand=True),
                            ft.Text(
                                "\u2713" if w.get('result') == 'remember' else "\u2717",
                                size=FONT_XS,
                                color=SUCCESS if w.get('result') == 'remember' else ERROR,
                            ),
                        ], spacing=0),
                        padding=ft.Padding(left=2, top=2, right=2, bottom=2),
                    )
                )
            if len(words) > 5:
                preview_rows.append(
                    ft.Text(
                        f"... \u8fd8\u6709{len(words)-5}\u8bcd",
                        size=FONT_XS, color=TEXT_HINT,
                    )
                )

        if not preview_rows:
            preview_rows = [ft.Text("\u6682\u65e0\u6570\u636e", size=FONT_SM, color=TEXT_HINT)]

        self._preview_container.content = ft.Column(
            preview_rows, spacing=2, scroll=ft.ScrollMode.AUTO
        )
        # 启用下载按钮
        self._download_btn.on_click = lambda e: self._do_download(selected)
        self._download_btn.bgcolor = COLOR_SETTINGS
        self._download_btn.update()
        self._preview_container.update()

    def _do_download(self, selected):
        """生成并通过浏览器下载Word文档（手机/电脑通用）"""
        if not _DOCX_AVAILABLE:
            self.app.show_snackbar(
                "\u7f3a\u5c11 python-docx \u5e93\uff0c\u8fd0\u884c pip install python-docx",
                ERROR,
            )
            return
        try:
            words_by_date = api_service.get_words_by_dates(selected)
            if not words_by_date:
                self.app.show_snackbar("\u6ca1\u6709\u6570\u636e", ERROR)
                return

            docx_bytes, total = _generate_docx(words_by_date)
            b64 = base64.b64encode(docx_bytes).decode()
            # 构造一个自动下载的HTML页面，用Blob方式下载（解决data URI不下载的问题）
            html = (
                '<html><head><meta charset="utf-8"><title>\u4e0b\u8f7d</title></head><body>'
                '<p>\u23f3 \u6b63\u5728\u4e0b\u8f7d...</p>'
                '<script>'
                'var b64="' + b64 + '";'
                'var raw=atob(b64);var arr=new Uint8Array(raw.length);'
                'for(var i=0;i<raw.length;i++){arr[i]=raw.charCodeAt(i);}'
                'var blob=new Blob([arr],{type:"application/msword"});'
                'var url=URL.createObjectURL(blob);'
                'var a=document.createElement("a");'
                'a.href=url;a.download="\u5b66\u4e60\u8bb0\u5f55.docx";'
                'document.body.appendChild(a);a.click();'
                'document.body.removeChild(a);'
                'setTimeout(function(){URL.revokeObjectURL(url);},3000);'
                'document.body.innerHTML+="<p>\u2705 \u4e0b\u8f7d\u5b8c\u6210</p>";'
                'document.body.innerHTML+="<p>\u5982\u679c\u672a\u81ea\u52a8\u4e0b\u8f7d\uff0c\u8bf7\u957f\u6309\u4e0b\u65b9\u94fe\u63a5\u9009\u62e9\u300c\u4e0b\u8f7d\u94fe\u63a5\u300d\uff1a</p>";'
                'document.body.innerHTML+="<a href=\'"+url+"\' download=\'\u5b66\u4e60\u8bb0\u5f55.docx\'>\ud83d\udcc4 \u5b66\u4e60\u8bb0\u5f55.docx</a>";'
                '</script>'
                '</body></html>'
            )
            self.page.launch_url("data:text/html," + urllib.parse.quote(html, safe=''))
            self.app.show_snackbar(f"\u5df2\u751f\u6210 {total} \u8bcd\uff0c\u6b63\u5728\u4e0b\u8f7d")
        except Exception as ex:
            self.app.show_snackbar(f"\u751f\u6210\u5931\u8d25\uff1a{ex}", ERROR)

    def _confirm_reset(self, e):
        dlg = ft.AlertDialog(
            title=ft.Text("\u786e\u8ba4\u91cd\u7f6e"),
            content=ft.Text("\u786e\u5b9a\u8981\u6e05\u9664\u6240\u6709\u5b66\u4e60\u8bb0\u5f55\u5417\uff1f"
                            "\u5355\u8bcd\u6570\u636e\u4e0d\u4f1a\u4e22\u5931\u3002"),
            actions=[
                ft.TextButton("\u53d6\u6d88",
                    on_click=lambda e: self.app.close_dialog(dlg)),
                ft.TextButton("\u786e\u5b9a\u91cd\u7f6e",
                    style=ft.ButtonStyle(color=ERROR),
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
            self.app.show_snackbar("\u5b66\u4e60\u8bb0\u5f55\u5df2\u6e05\u7a7a")
        else:
            self.app.show_snackbar("\u91cd\u7f6e\u5931\u8d25")
