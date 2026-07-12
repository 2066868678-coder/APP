#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 设置页面
==================
"""

import sys, os, threading, io, base64
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, PRIMARY_LIGHT, SECONDARY, SURFACE, SUCCESS, ERROR, BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, CARD_GAP, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL,
    RADIUS_MD, RADIUS_SM, RADIUS_XL,
    SHADOW_SM, SHADOW_MD,
    FONT_XS, FONT_SM, FONT_BODY, FONT_LG,
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
            result_icon = '✓' if w.get('result') == 'remember' else '✗'
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
            doc.add_paragraph(f"释义：{w.get('meaning', '')}", style='List Bullet')
            doc.add_paragraph(f"结果：{result_icon}", style='List Bullet')

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue(), total


def _format_date(d_str):
    """2026-07-12 → 7月12日"""
    try:
        dt = datetime.strptime(d_str, '%Y-%m-%d')
        return f"{dt.month}月{dt.day}日"
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
            border_color=PRIMARY,
            content_padding=ft.Padding(left=8, right=8, top=6, bottom=6),
        )
        # 日期选择状态
        self._date_checks = {}    # { date_str: Checkbox }
        self._preview_container = ft.Container(
            content=ft.Text("选择上方日期查看单词", size=FONT_SM, color=TEXT_HINT),
            padding=SPACING_MD,
        )
        self._download_btn = ft.Container(
            content=ft.Text("下载 Word 文档", color=ft.Colors.WHITE,
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
        for d in dates:
            cb = ft.Checkbox(
                label=f"{_format_date(d['date'])}（{d['count']}词）",
                value=False,
                on_change=self._on_date_toggle,
            )
            self._date_checks[d['date']] = cb
            date_rows.append(
                ft.Container(
                    content=cb,
                    padding=ft.Padding(left=4, top=6, right=4, bottom=6),
                )
            )

        if not date_rows:
            date_rows = [
                ft.Container(
                    content=ft.Text("暂无学习记录", size=FONT_SM, color=TEXT_HINT),
                    padding=SPACING_MD,
                )
            ]

        # 预览区域（初始空）
        self._preview_container.content = ft.Column([
            ft.Text("选择日期后预览单词", size=FONT_SM, color=TEXT_HINT),
        ], spacing=0)

        return ft.ListView([
            # === 每日学习目标 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.TRACK_CHANGES, color=PRIMARY, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("每日学习目标", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=SPACING_MD),
                    ft.Row([
                        ft.Text("每天新学单词", size=FONT_BODY, color=TEXT_SECONDARY),
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
                                ft.Text("保存目标", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                            ]),
                            padding=ft.Padding(20, 10, 20, 10),
                            bgcolor=PRIMARY,
                            border_radius=RADIUS_MD,
                            ink=True,
                            on_click=self._save_target,
                        ),
                    ]),
                    ft.Container(height=4),
                    ft.Text("建议：每天10-20个，有基础可30-50个",
                            size=FONT_SM, color=TEXT_HINT, italic=True),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # === 学习记录 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.DATE_RANGE, color=PRIMARY, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.10, PRIMARY),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("学习记录", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=SPACING_SM),
                    # 日期列表（可多选）
                    *([ft.Container(
                        content=ft.Column([
                            ft.Text("选择日期", size=FONT_SM, color=TEXT_SECONDARY,
                                    weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            *date_rows,
                        ], spacing=0),
                    )] if date_rows else [
                        ft.Container(
                            content=ft.Text("暂无学习记录", size=FONT_SM, color=TEXT_HINT),
                            padding=SPACING_MD,
                        )
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=SPACING_SM),
                    # 预览区域
                    ft.Container(
                        content=ft.Column([
                            ft.Text("单词预览", size=FONT_SM, color=TEXT_SECONDARY,
                                    weight=ft.FontWeight.W_500),
                            ft.Container(height=4),
                            self._preview_container,
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

            # === 数据管理 ===
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
                        ft.Text("数据管理", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=SPACING_MD),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DELETE_SWEEP, color=ERROR, size=18),
                            ft.Container(width=8),
                            ft.Text("重置学习记录", size=FONT_BODY,
                                    color=ERROR, expand=True),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_HINT, size=18),
                        ]),
                        padding=ft.Padding(12, 10, 12, 10),
                        bgcolor=ft.Colors.with_opacity(0.04, ERROR),
                        border_radius=RADIUS_SM,
                        ink=True,
                        on_click=self._confirm_reset,
                    ),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # === 启动帮助 ===
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
                        ft.Text("下次如何打开", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=8),
                    ft.Text("双击 start.bat 或在终端运行：", size=FONT_SM, color=TEXT_SECONDARY),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text("cd E:\\APP\npython run_app.py",
                                        size=13, color=PRIMARY, font_family="monospace"),
                        padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                        border_radius=RADIUS_SM,
                    ),
                    ft.Container(height=8),
                    ft.Text("浏览器打开 http://localhost:8551", size=FONT_SM, color=TEXT_SECONDARY),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=CARD_GAP),

            # === 关于 ===
            AppCard(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.INFO, color=TEXT_HINT, size=18),
                            padding=ft.Padding(6, 6, 6, 6),
                            bgcolor=ft.Colors.with_opacity(0.06, TEXT_HINT),
                            border_radius=8,
                        ),
                        ft.Container(width=8),
                        ft.Text("关于", size=FONT_LG,
                                weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Divider(height=1, color=ft.Colors.GREY_200),
                    ft.Container(height=8),
                    self._info_row("应用", "单词突围 (独立版)"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("版本", "2.1.0"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("数据来源", "《单词突围5200》上册"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("复习算法", "艾宾浩斯遗忘曲线"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("单词总数", "2281 个"),
                    ft.Divider(height=1, color=ft.Colors.GREY_100),
                    self._info_row("运行模式", "本地数据库 (无需后端)"),
                ], spacing=0),
                elevation="sm",
            ),

            ft.Container(height=SPACING_LG),
        ], padding=ft.Padding(left=PAGE_PADDING, top=PAGE_PADDING,
                               right=PAGE_PADDING, bottom=0), spacing=0)

    def _info_row(self, label, value):
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=FONT_BODY, color=TEXT_SECONDARY),
                ft.Container(expand=True),
                ft.Text(value, size=FONT_BODY, color=TEXT_PRIMARY,
                        weight=ft.FontWeight.W_500),
            ]),
            padding=ft.Padding(left=4, top=10, right=4, bottom=10),
        )

    def _save_target(self, e):
        try:
            val = int(self._target_value.value)
            if val < 1:
                self.app.show_snackbar("每日目标至少为1", ERROR)
                return
            if val > 200:
                self.app.show_snackbar("目标太高了，建议不超过50", ERROR)
                return
            ok = api_service.set_daily_target(val)
            if ok:
                self.app.show_snackbar(f"每日新词目标已设为 {val} 个")
            else:
                self.app.show_snackbar("保存失败", ERROR)
        except ValueError:
            self.app.show_snackbar("请输入有效数字", ERROR)

    def _on_date_toggle(self, e):
        """日期选择变化 → 刷新预览和下载按钮"""
        selected = [d for d, cb in self._date_checks.items() if cb.value]
        if not selected:
            self._preview_container.content = ft.Column([
                ft.Text("选择日期后预览单词", size=FONT_SM, color=TEXT_HINT),
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
                    content=ft.Text(f"{_format_date(date)}（{len(words)}词）",
                                   size=FONT_SM, weight=ft.FontWeight.BOLD,
                                   color=TEXT_PRIMARY),
                    padding=ft.Padding(top=4, bottom=2),
                )
            )
            for w in words[:5]:  # 最多显示5个
                preview_rows.append(
                    ft.Row([
                        ft.Container(width=4, height=4, bgcolor=PRIMARY_LIGHT,
                                    border_radius=2),
                        ft.Container(width=6),
                        ft.Text(w['word'], size=FONT_SM, color=TEXT_PRIMARY, expand=True),
                        ft.Text("✓" if w.get('result') == 'remember' else "✗",
                               size=FONT_XS, color=SUCCESS if w.get('result') == 'remember' else ERROR),
                    ], spacing=0)
                )
            if len(words) > 5:
                preview_rows.append(
                    ft.Text(f"... 还有{len(words)-5}词", size=FONT_XS, color=TEXT_HINT)
                )

        if not preview_rows:
            preview_rows = [ft.Text("暂无数据", size=FONT_SM, color=TEXT_HINT)]

        self._preview_container.content = ft.Column(
            preview_rows, spacing=2, scroll=ft.ScrollMode.AUTO
        )
        # 启用下载按钮
        self._download_btn.on_click = lambda e: self._do_download(selected)
        self._download_btn.bgcolor = PRIMARY
        self._download_btn.update()
        self._preview_container.update()

    def _do_download(self, selected):
        """生成并下载Word文档"""
        if not _DOCX_AVAILABLE:
            self.app.show_snackbar("缺少 python-docx 库，运行 pip install python-docx", ERROR)
            return
        try:
            words_by_date = api_service.get_words_by_dates(selected)
            if not words_by_date:
                self.app.show_snackbar("没有数据", ERROR)
                return

            docx_bytes, total = _generate_docx(words_by_date)
            b64 = base64.b64encode(docx_bytes).decode()

            # JS Blob下载（手机/电脑通用）
            self.page.run_script(f"""
                (function() {{
                    var b64 = `{b64}`;
                    var raw = atob(b64);
                    var arr = new Uint8Array(raw.length);
                    for (var i = 0; i < raw.length; i++) {{
                        arr[i] = raw.charCodeAt(i);
                    }}
                    var blob = new Blob([arr], {{type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = '学习记录.docx';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    setTimeout(function() {{ URL.revokeObjectURL(url); }}, 5000);
                }})();
            """)
            self.app.show_snackbar(f"已生成 {total} 词 Word 文档")
        except Exception as ex:
            self.app.show_snackbar(f"生成失败：{ex}", ERROR)

    def _confirm_reset(self, e):
        dlg = ft.AlertDialog(
            title=ft.Text("确认重置"),
            content=ft.Text("确定要清除所有学习记录吗？单词数据不会丢失。"),
            actions=[
                ft.TextButton("取消",
                    on_click=lambda e: self.app.close_dialog(dlg)),
                ft.TextButton("确定重置",
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
            self.app.show_snackbar("学习记录已清空")
        else:
            self.app.show_snackbar("重置失败")
