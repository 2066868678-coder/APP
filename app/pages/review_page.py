#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 复习页面（翻卡模式 · 全新设计）
===============================
艾宾浩斯遗忘曲线复习
"""

import sys, os, threading, re, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from app.theme import (
    PRIMARY, SECONDARY, SURFACE, SUCCESS, ERROR, BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    PAGE_PADDING, SPACING_SM, SPACING_MD, SPACING_LG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL,
    SHADOW_SM, SHADOW_LG,
    FONT_SM, FONT_BODY, FONT_LG, FONT_XL, FONT_XXL, FONT_XXXL, FONT_DISPLAY,
)
from app.services import api_service


class ReviewPage:
    """复习页面 - 翻卡模式"""

    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.words = []
        self.word_index = 0
        self.remaining_queue = []
        self.review_done = 0
        self.review_total = 0
        self.flipped = False

        self.progress_text = ft.Text("加载中...", size=14, color=TEXT_SECONDARY)
        self.card_container = ft.Container(expand=True)
        self.action_buttons = ft.Container(visible=False)

    def build(self):
        header = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_STORIES, color=SECONDARY, size=20),
                    padding=ft.Padding(8, 8, 8, 8),
                    bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                    border_radius=10,
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text("复习单词", size=FONT_LG, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY),
                    self.progress_text,
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text("0/0", size=13, weight=ft.FontWeight.BOLD, color=SECONDARY),
                    padding=ft.Padding(10, 6, 10, 6),
                    bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                    border_radius=20,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(left=PAGE_PADDING, top=SPACING_LG,
                               right=PAGE_PADDING, bottom=SPACING_SM),
        )

        self.action_buttons = ft.Container(
            content=ft.Column([
                ft.Row([
                    # 熟悉
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.STAR, color=ft.Colors.WHITE, size=20),
                            ft.Text("熟悉", color=ft.Colors.WHITE, size=12,
                                    weight=ft.FontWeight.BOLD),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                        padding=ft.Padding(24, 10, 24, 10),
                        bgcolor="#43A047",
                        border_radius=RADIUS_LG,
                        ink=True,
                        shadow=SHADOW_SM,
                        expand=True,
                        tooltip="近期不再复习",
                        on_click=lambda e: self._handle_result('familiar'),
                    ),
                    # 模糊
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=20),
                            ft.Text("模糊", color=ft.Colors.WHITE, size=12,
                                    weight=ft.FontWeight.BOLD),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                        padding=ft.Padding(24, 10, 24, 10),
                        bgcolor=SECONDARY,
                        border_radius=RADIUS_LG,
                        ink=True,
                        shadow=SHADOW_SM,
                        expand=True,
                        tooltip="正常艾宾浩斯复习",
                        on_click=lambda e: self._handle_result('vague'),
                    ),
                    # 不记得
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.REPLAY, color=ft.Colors.WHITE, size=20),
                            ft.Text("不记得", color=ft.Colors.WHITE, size=12,
                                    weight=ft.FontWeight.BOLD),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                        padding=ft.Padding(24, 10, 24, 10),
                        bgcolor=ERROR,
                        border_radius=RADIUS_LG,
                        ink=True,
                        shadow=SHADOW_SM,
                        expand=True,
                        tooltip="今天多练几次",
                        on_click=lambda e: self._handle_result('forget'),
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(height=4),
                ft.Text("回顾单词和固定搭配，点击翻转查看答案", size=11, color=TEXT_HINT,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=PAGE_PADDING, right=PAGE_PADDING, bottom=16),
            visible=False,
        )

        # 加载数据
        try:
            today = api_service.get_today_words()
            words = []
            if today and today.get('review_words'):
                words = today['review_words']
        except Exception:
            words = []

        if not words:
            self.card_container.content = self._build_empty()
            self.progress_text.value = "今日复习: 0/0"
        else:
            self.words = words
            self.review_total = len(words)
            self.word_index = 0
            self.remaining_queue = []
            self._show_current_word(initial=True)

        return ft.Column([
            header,
            ft.Container(content=self.card_container, expand=True),
            self.action_buttons,
        ], spacing=0, tight=True)

    def _build_empty(self, msg=None):
        from app.services import api_service
        try:
            stats = api_service.get_study_stats()
            learned = stats.get('total_studied', 0) if stats else 0
        except:
            learned = 0
        if learned > 0:
            msg = msg or f"今日无需复习 ✓\n已学习 {learned} 个单词\n\n新学的单词将在1天后进入复习"
        else:
            msg = msg or "暂无需要复习的单词\n\n先去学习页面学单词\n学完的单词将在1天后进入复习"
        return ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=64, color=TEXT_HINT),
                    padding=ft.Padding(20, 20, 20, 20),
                    bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                    border_radius=40,
                ),
                ft.Container(height=16),
                ft.Text(msg, size=FONT_LG, color=TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=24),
                ft.Container(
                    content=ft.Text("去学新词", color=ft.Colors.WHITE, size=14,
                                   weight=ft.FontWeight.BOLD),
                    padding=ft.Padding(28, 12, 28, 12),
                    bgcolor=SECONDARY,
                    border_radius=RADIUS_XL,
                    ink=True,
                    on_click=lambda e: self.app.switch_to_page(1),
                ),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
        )

    def _load_data(self):
        try:
            today = api_service.get_today_words()
            words = []
            if today and today.get('review_words'):
                words = today['review_words']
        except Exception:
            words = []
        self._data_loaded(words)

    def _data_loaded(self, words):
        if not words:
            self.card_container.content = self._build_empty()
            self.progress_text.value = "今日复习: 0/0"
            self.action_buttons.visible = False
            return
        self.words = words
        self.review_total = len(words)
        self.review_done = 0
        self.word_index = 0
        self.remaining_queue = []
        self._show_current_word(initial=True)
        self.page.update()

    def _show_current_word(self, initial=False):
        wd = self._get_word()
        if not wd:
            self.card_container.content = self._build_empty("🎉 今日复习已完成！")
            self.action_buttons.visible = False
            if not initial:
                self.page.update()
            return
        self.flipped = False

        # 提取固定搭配（仅英文部分，用于反推练习）
        collocation_en = []
        if wd.get('collocations'):
            # 先按分号或竖线分割
            raw_items = [t.strip() for t in wd['collocations'].replace('；', '|').replace(';', '|').split('|') if t.strip()]
            for item in raw_items:
                # 拆出英文部分（中文前的内容）
                match = re.search(r'[一-鿿]', item)
                if match:
                    en_part = item[:match.start()].strip()
                    if en_part:
                        collocation_en.append(en_part)
                else:
                    collocation_en.append(item)

        front = ft.Container(
            content=ft.Column([
                ft.Container(height=4, bgcolor=SECONDARY,
                             border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0)),
                ft.Container(expand=True),
                # 单词
                ft.Text(wd['word'], size=32, weight=ft.FontWeight.BOLD,
                        color=TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=6),
                # 发音按钮
                ft.Row([
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.VOLUME_UP,
                        icon_size=24,
                        icon_color=SECONDARY,
                        tooltip="听发音",
                        on_click=lambda e: self._speak(wd['word']),
                    ),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=6),
                # 固定搭配（复习时展示）
                *([
                    ft.Container(height=4),
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.15, SECONDARY)),
                    ft.Container(height=4),
                    ft.Text("固定搭配（回想含义）", size=11, color=TEXT_HINT,
                            italic=True, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=4),
                ] + [
                    ft.Container(
                        content=ft.Text(item, size=13, color=TEXT_SECONDARY,
                                        text_align=ft.TextAlign.CENTER,
                                        weight=ft.FontWeight.W_500),
                        padding=ft.Padding(8, 4, 8, 4),
                        bgcolor=ft.Colors.with_opacity(0.06, SECONDARY),
                        border_radius=8,
                    ) for item in collocation_en
                ] if collocation_en else []),
                ft.Container(height=16),
                ft.Row([
                    ft.Icon(ft.Icons.TOUCH_APP, size=14, color=TEXT_HINT),
                    ft.Container(width=4),
                    ft.Text("回想意思和搭配，点击查看", size=13, color=TEXT_HINT),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(expand=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, tight=True),
            padding=ft.Padding(left=24, top=0, right=24, bottom=24),
            bgcolor=SURFACE,
            border_radius=RADIUS_LG,
            shadow=SHADOW_LG,
            margin=ft.Margin(left=20, right=20, top=12, bottom=12),
            ink=True,
            on_click=self._flip_card,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        self.action_buttons.visible = False
        self.card_container.content = ft.Column([front], spacing=0, tight=True)
        self._update_progress(initial=initial)
        if not initial:
            self.page.update()

    def _flip_card(self, e):
        if self.flipped:
            return
        self.flipped = True
        wd = self._get_word()
        if not wd:
            return

        sections = []
        # 基本信息区（带发音）
        sections.append(ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(wd['word'], size=FONT_XXXL, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.VOLUME_UP,
                        icon_size=22,
                        icon_color=SECONDARY,
                        tooltip="听发音",
                        on_click=lambda e: self._speak(wd['word']),
                    ),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=4),
                ft.Row([
                    ft.Text(wd.get('phonetic', ''), size=FONT_BODY,
                            color=TEXT_SECONDARY, italic=True),
                    ft.Container(width=8),
                    ft.Container(
                        content=ft.Text(wd.get('pos', ''), size=FONT_SM,
                                        color=ft.Colors.WHITE),
                        padding=ft.Padding(8, 3, 8, 3),
                        bgcolor=SECONDARY,
                        border_radius=4,
                    ) if wd.get('pos') else ft.Container(),
                ], spacing=4),
                ft.Container(height=8),
                ft.Text(wd.get('meaning', ''), size=FONT_XL, weight=ft.FontWeight.W_500,
                        color=TEXT_PRIMARY),
            ], spacing=0),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
            bgcolor=ft.Colors.with_opacity(0.06, SECONDARY),
            border_radius=RADIUS_SM,
            border=ft.Border(
                left=ft.BorderSide(3, SECONDARY),
                right=ft.BorderSide(0, None),
                top=ft.BorderSide(0, None),
                bottom=ft.BorderSide(0, None),
            ),
        ))

        # 记忆方法（高亮，放前面）
        if wd.get('memory_methods'):
            sections.append(self._section_with_audio(
                "💡 记忆方法", wd['memory_methods'],
                "#FFF8E1", "#FFB300", wd['word'],
            ))

        # 例句（点击显示翻译）
        if wd.get('examples'):
            sections.append(self._build_examples_section(wd['examples']))

        # 固定搭配（带发音 + 显示中文释义）
        if wd.get('collocations'):
            sections.append(self._section_with_audio(
                "📝 固定搭配", wd['collocations'],
                "#E3F2FD", "#64B5F6", wd['word'],
            ))

        # 派生词/扩展
        if wd.get('extensions'):
            sections.append(self._sec_plain("🔗 派生词/扩展", wd['extensions'],
                                            "#F1F8E9", "#81C784"))

        back = ft.Container(
            content=ft.Column(sections, spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            bgcolor=SURFACE,
            border_radius=RADIUS_LG,
            shadow=SHADOW_LG,
            margin=ft.Margin(left=16, right=16, top=12, bottom=12),
        )
        self.action_buttons.visible = True
        self.card_container.content = ft.Column([back], spacing=0, tight=True)
        self.page.update()

    def _sec_plain(self, title, content, bg_color, accent_color):
        """简单信息区（不带发音）"""
        items = [item.strip() for item in content.split('|') if item.strip()]
        content_parts = []
        for item in items:
            content_parts.append(
                ft.Row([
                    ft.Container(width=16, content=ft.Text("•", size=14, color=TEXT_HINT)),
                    ft.Text(item, size=FONT_BODY, color=TEXT_SECONDARY, expand=True),
                ], spacing=0)
            )
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)]),
                ft.Container(height=6),
                *content_parts,
            ], spacing=0),
            padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            bgcolor=bg_color, border_radius=RADIUS_SM,
            border=ft.Border(left=ft.BorderSide(3, accent_color),
                right=ft.BorderSide(0, None), top=ft.BorderSide(0, None), bottom=ft.BorderSide(0, None)),
        )

    def _section_with_audio(self, title, content, bg_color, accent_color, word):
        """信息区 — 每项带发音按钮"""
        items = [item.strip() for item in content.split('|') if item.strip()]
        content_parts = []
        for item in items[:5]:
            # 提取英文部分
            speak_text_match = re.search(r'[a-zA-Z].*?(?=[一-鿿]|$)', item)
            speak_text = speak_text_match.group(0).strip() if speak_text_match else item
            content_parts.append(
                ft.Row([
                    ft.Container(width=16, content=ft.Text("•", size=14, color=TEXT_HINT)),
                    ft.Text(item, size=FONT_BODY, color=TEXT_SECONDARY, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.VOLUME_UP, icon_size=16,
                        icon_color=accent_color, tooltip="听发音",
                        on_click=lambda e, t=speak_text: self._speak(t),
                    ),
                ], spacing=0)
            )
        if len(items) > 5:
            content_parts.append(
                ft.Text(f"... 还有 {len(items)-5} 条", size=11, color=TEXT_HINT)
            )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title, size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                *content_parts,
            ], spacing=0),
            padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            bgcolor=bg_color, border_radius=RADIUS_SM,
            border=ft.Border(left=ft.BorderSide(3, accent_color),
                right=ft.BorderSide(0, None), top=ft.BorderSide(0, None), bottom=ft.BorderSide(0, None)),
        )

    def _build_examples_section(self, examples_text):
        """例句区 — 默认隐藏翻译"""
        pairs = self._split_en_zh(examples_text)
        example_items = []
        for i, (en, zh) in enumerate(pairs):
            zh_row = ft.Container(
                content=ft.Column([
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, "#CE93D8")),
                    ft.Container(height=4),
                    ft.Row([
                        ft.Icon(ft.Icons.TRANSLATE, size=12, color="#CE93D8"),
                        ft.Container(width=4),
                        ft.Text(zh or "", size=FONT_BODY, color=TEXT_HINT, italic=True, expand=True),
                    ]),
                ], spacing=0), visible=False,
            )
            example_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{i+1}. ", size=FONT_BODY, color=TEXT_HINT, weight=ft.FontWeight.BOLD),
                            ft.Text(en, size=FONT_BODY, color=TEXT_SECONDARY, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.VOLUME_UP, icon_size=16, icon_color="#CE93D8",
                                tooltip="听发音",
                                on_click=lambda e, t=en[:100]: self._speak(t),
                            ),
                            ft.IconButton(icon=ft.Icons.EXPAND_MORE, icon_size=16, icon_color="#CE93D8", tooltip="显示/隐藏翻译"),
                        ], spacing=2, vertical_alignment=ft.CrossAxisAlignment.START),
                        ft.Container(height=2), zh_row,
                    ], spacing=0),
                    padding=ft.Padding(left=4, top=6, right=4, bottom=6), ink=True,
                    on_click=self._toggle_translation,
                )
            )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📖 例句", size=FONT_BODY, weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY, expand=True),
                    ft.Text("点击展开翻译", size=11, color=TEXT_HINT, italic=True),
                ]),
                ft.Container(height=4),
                *example_items,
            ], spacing=0),
            padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            bgcolor="#F3E5F5", border_radius=RADIUS_SM,
            border=ft.Border(left=ft.BorderSide(3, "#CE93D8"),
                right=ft.BorderSide(0, None), top=ft.BorderSide(0, None), bottom=ft.BorderSide(0, None)),
        )

    # ========== 发音 & 翻译辅助 ==========
    def _speak(self, text):
        """播放发音 - Audio元素播放有道词典发音"""
        try:
            audio_url = f"https://dict.youdao.com/dictvoice?audio={urllib.parse.quote(text)}&type=2"
            html = (
                '<html><body style="margin:0;background:#f5f5f5;display:flex;justify-content:center;align-items:center;height:100vh;">'
                '<div style="text-align:center;font-family:sans-serif;color:#999;">🔊 播放中...</div>'
                '<script>'
                'var a=new Audio("' + audio_url + '");'
                'a.play().then(function(){setTimeout(function(){window.close();},4000);});'
                '</script></body></html>'
            )
            self.page.launch_url("data:text/html," + urllib.parse.quote(html, safe=''))
        except Exception:
            pass

    def _split_en_zh(self, text):
        items = [t.strip() for t in text.split('|') if t.strip()]
        result = []
        for item in items:
            match = re.search(r'[一-鿿]', item)
            if match:
                result.append((item[:match.start()].strip(), item[match.start():].strip()))
            else:
                result.append((item, None))
        return result

    def _toggle_translation(self, e):
        col = e.control.content
        if col and isinstance(col, ft.Column) and len(col.controls) >= 3:
            zh_row = col.controls[2]
            if isinstance(zh_row, ft.Container):
                zh_row.visible = not zh_row.visible
                en_row = col.controls[0]
                if len(en_row.controls) >= 3:
                    en_row.controls[2].name = ft.Icons.EXPAND_LESS if zh_row.visible else ft.Icons.EXPAND_MORE
                    en_row.controls[2].update()
                zh_row.update()
                if hasattr(e.control, 'page') and e.control.page:
                    e.control.page.update()

    # ========== 三档熟悉程度 ==========
    def _handle_result(self, level):
        wd = self._get_word()
        if not wd:
            return
        word_id = wd.get('id', 0)

        if level == 'familiar':
            api_service.record_study(word_id, 'review', 'remember')
            from app.services.local_db import _get_session
            from backend.models import StudyRecord
            s = _get_session()
            try:
                last = s.query(StudyRecord).filter(StudyRecord.word_id == word_id
                    ).order_by(StudyRecord.id.desc()).first()
                if last:
                    last.review_interval = 60
                    s.commit()
            except: s.rollback()
            finally: s.close()
            self.review_done += 1
            self._next_word()
            self.app.show_snackbar("⭐ 已标记为熟悉", SUCCESS)
        elif level == 'vague':
            api_service.record_study(word_id, 'review', 'remember')
            self.review_done += 1
            self._next_word()
            self.app.show_snackbar("✅ 记得！下次复习间隔增加", SUCCESS)
        else:
            api_service.record_study(word_id, 'review', 'forget')
            if word_id not in self.remaining_queue:
                self.remaining_queue.append(word_id)
            self._next_word()
            self.app.show_snackbar("💪 忘了没关系，今天稍后重学", ERROR)

    def _next_word(self):
        self.word_index += 1
        if self.word_index >= len(self.words) and self.remaining_queue:
            self._reshuffle()
        if self.word_index >= len(self.words):
            self._show_completion()
        else:
            self._show_current_word()

    def _reshuffle(self):
        forgot = list(set(self.remaining_queue))
        fw = [w for w in self.words if w.get('id') in forgot]
        rest = [w for w in self.words[self.word_index:] if w.get('id') not in forgot]
        self.words = rest + fw
        self.word_index = 0
        self.remaining_queue = []

    def _get_word(self):
        if not self.words or self.word_index >= len(self.words):
            return None
        return self.words[self.word_index]

    def _update_progress(self, initial=False):
        self.progress_text.value = f"今日复习: {self.review_done}/{self.review_total}  |  当前 {min(self.word_index+1, self.review_total)}/{self.review_total}"
        if not initial:
            self.progress_text.update()

    def _show_completion(self):
        self.action_buttons.visible = False
        self.card_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CELEBRATION, size=72, color=SECONDARY),
                        padding=ft.Padding(20, 20, 20, 20),
                        bgcolor=ft.Colors.with_opacity(0.10, SECONDARY),
                        border_radius=40,
                    ),
                    ft.Container(height=20),
                    ft.Text("复习完成！", size=FONT_XXL, weight=ft.FontWeight.BOLD,
                            color=SECONDARY),
                    ft.Container(height=8),
                    ft.Text(f"今日复习 {self.review_done} 个单词",
                            size=FONT_BODY, color=TEXT_SECONDARY),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Text("返回首页", color=ft.Colors.WHITE,
                                        size=14, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(28, 12, 28, 12),
                        bgcolor=SECONDARY,
                        border_radius=RADIUS_XL,
                        ink=True,
                        on_click=lambda e: self.app.switch_to_page(0),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            ft.Container(expand=True),
        ])
        self.progress_text.value = f"今日复习: {self.review_done}/{self.review_total} ✅"
        self.page.update()
