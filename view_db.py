# -*- coding: utf-8 -*-
"""单词库查看器：双击 查看单词库.bat 运行，浏览器打开可搜索的完整词库表格"""
import sqlite3, os, webbrowser, tempfile, json

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'words.db')

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT word, phonetic, pos, meaning, examples, memory_methods, chapter, source_page, source_book FROM words ORDER BY id')
rows = cur.fetchall()
conn.close()

rows_html = []
for w, ph, pos, me, ex, mm, ch, sp, sb in rows:
    esc = lambda s: (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    mm_short = esc(mm)[:500] + ('…' if len(mm or '') > 500 else '')
    rows_html.append(
        f'<tr><td class="w">{esc(w)}</td><td>{esc(ph)}</td><td>{esc(pos)}</td>'
        f'<td>{esc(me)}</td><td>{esc(ex)}</td><td class="mm">{mm_short}</td>'
        f'<td>{esc(ch)}</td><td>P{sp}</td></tr>'
    )

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>单词突围 · 单词库查看器（{len(rows)}词）</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; margin: 20px; background: #f6f7fb; color: #1f2430; }}
h1 {{ font-size: 20px; }}
#search {{ width: 400px; padding: 8px 12px; font-size: 14px; border: 1px solid #c9cede; border-radius: 8px; }}
table {{ border-collapse: collapse; width: 100%; background: #fff; margin-top: 12px; }}
th, td {{ border: 1px solid #e3e6ee; padding: 6px 8px; font-size: 13px; vertical-align: top; text-align: left; }}
th {{ background: #4F46E5; color: #fff; position: sticky; top: 0; }}
td.w {{ font-weight: bold; color: #4F46E5; white-space: nowrap; }}
td.mm {{ color: #555; }}
tr:hover {{ background: #eef1ff; }}
.count {{ color: #888; font-size: 13px; }}
</style>
</head>
<body>
<h1>📖 单词突围 · 单词库查看器 <span class="count">共 {len(rows)} 个单词</span></h1>
<input id="search" placeholder="输入单词/释义/记忆方法 搜索…" oninput="filterRows(this.value)">
<table>
<thead><tr><th>单词</th><th>音标</th><th>词性</th><th>释义</th><th>例句</th><th>记忆方法</th><th>章节</th><th>页码</th></tr></thead>
<tbody id="tbody">
{''.join(rows_html)}
</tbody>
</table>
<script>
function filterRows(v) {{
  v = v.toLowerCase();
  document.querySelectorAll('#tbody tr').forEach(tr => {{
    tr.style.display = tr.textContent.toLowerCase().includes(v) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""

out = os.path.join(tempfile.gettempdir(), 'words_viewer.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
webbrowser.open('file:///' + out.replace('\\', '/'))
print(f'已生成并打开词库页面（{len(rows)}词），文件: {out}')
