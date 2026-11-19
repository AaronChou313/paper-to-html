#!/usr/bin/env python3
"""Render reviewed bilingual paper data into one standalone reading HTML file."""
import argparse
import base64
import json
import os
import re
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import quote, urlsplit

ASSETS = Path(__file__).resolve().parents[1] / "assets"
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
BLOCK_TYPES = {"section", "paragraph", "figure", "table", "equation", "references"}


def web_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError(f"Expected an HTTP(S) URL: {value}")
    return escape(value)


def local_url(path, output):
    return quote(Path(os.path.relpath(path.resolve(), output.parent.resolve())).as_posix(), safe="/")


def inline(text, highlights=(), links=None):
    """Escape source text, then wrap literal spans in links or highlights."""
    links = links or {}
    spans = set(highlights) | links.keys()
    if not spans:
        return escape(text).replace("\n", "<br>\n")
    pattern = re.compile("|".join(re.escape(span) for span in sorted(spans, key=lambda s: (-len(s), s))))
    pieces = []
    cursor = 0
    for match in pattern.finditer(text):
        pieces.append(escape(text[cursor:match.start()]))
        raw = match.group()
        if raw in links:
            pieces.append(f'<a href="#{escape(links[raw])}">{escape(raw)}</a>')
        else:
            pieces.append(f"<mark>{escape(raw)}</mark>")
        cursor = match.end()
    pieces.append(escape(text[cursor:]))
    return "".join(pieces).replace("\n", "<br>\n")


def note_html(notes):
    def emphasis(text):
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escape(text))
    if len(notes) == 1:
        return f"<p>{emphasis(notes[0])}</p>"
    return "<ul>" + "".join(f"<li>{emphasis(note)}</li>" for note in notes) + "</ul>"


def page_ref(block, source):
    if "pages" not in block:
        return ""
    first, last = block["pages"]
    label = f"PDF {first} 页" if first == last else f"PDF {first}–{last} 页"
    if source:
        return f'<a class="page-ref" href="{source}#page={first}">{label}</a>'
    return f'<span class="page-ref">{label}</span>'


def comparison(block, source, *, anchored=True):
    original = inline(block["en"], block.get("highlight_en", []), block.get("links_en"))
    chinese = inline(block["zh"], block.get("highlight_zh", []), block.get("links_zh"))
    anchor = f' id="{block["id"]}"' if anchored else ""
    lang = escape(block.get("source_lang", "en"))
    original_label = "英文原文" if lang == "en" else "原文"
    return f'''<div class="unit"{anchor}>
<div class="parallel">
<div class="origin"><div class="origin-top"><span class="label">{original_label}</span>{page_ref(block, source)}</div><p lang="{lang}">{original}</p></div>
<div class="translation"><span class="label">中文翻译</span><p>{chinese}</p></div>
</div>
<div class="reading-note"><span class="label">阅读笔记</span>{note_html(block["notes"])}</div>
</div>'''


def picture(path, label):
    mime = IMAGE_TYPES[path.suffix.lower()]
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f'<img src="data:{mime};base64,{data}" alt="{escape(label)}" loading="lazy">'


def table(rows, label, lang):
    def row(cells, heading=False):
        first = "col" if heading else "row"
        columns = [f'<th scope="{first}">{inline(cell)}</th>' if heading or i == 0
                   else f"<td>{inline(cell)}</td>" for i, cell in enumerate(cells)]
        return "<tr>" + "".join(columns) + "</tr>"
    body = "".join(row(cells) for cells in rows[1:])
    return (f'<div class="table-scroll" role="region" aria-label="{escape(label)}" tabindex="0">'
            f'<table lang="{escape(lang)}"><thead>{row(rows[0], True)}</thead><tbody>{body}</tbody></table></div>')


def check(data):
    blocks = data["blocks"]
    ids = [block["id"] for block in blocks]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key) for key in ids):
        raise ValueError("Block IDs must be unique and start with a letter, followed by letters, digits, _ or -.")
    if set(ids) & {"top", "reading", "notes-mode", "mark-mode"}:
        raise ValueError("Block IDs cannot use reserved reader IDs.")
    for block in blocks:
        key = block["id"]
        kind = block["type"]
        if kind not in BLOCK_TYPES:
            raise ValueError(f"{key}: unknown block type {kind}")
        required = ("title_zh", "title_en") if kind == "section" else (
            ("title",) if kind == "references" else ("en", "zh"))
        if any(not isinstance(block.get(field), str) or not block[field].strip() for field in required):
            raise ValueError(f"{key}: missing {', '.join(required)}")
        if kind not in {"section", "references"}:
            notes = block.get("notes")
            if not isinstance(notes, list) or not notes or any(not isinstance(n, str) or not n.strip() for n in notes):
                raise ValueError(f"{key}: provide a nonempty notes list")
        if "pages" in block:
            first, last = block["pages"]
            if not isinstance(first, int) or not isinstance(last, int) or not 0 < first <= last:
                raise ValueError(f"{key}: invalid physical PDF page range")
        for lang in ("en", "zh"):
            links = block.get(f"links_{lang}", {})
            highlights = block.get(f"highlight_{lang}", [])
            for label in [*links, *highlights]:
                if not label or label not in block.get(lang, ""):
                    raise ValueError(f"{key}: inline label must match {lang} text: {label!r}")
            if any(target not in ids for target in links.values()):
                raise ValueError(f"{key}: unknown link target")
        if kind == "table":
            if not (block.get("image") or block.get("rows_en")):
                raise ValueError(f"{key}: a table requires the original rows or an image of the original")
            for field in ("rows_zh", "rows_en"):
                if field not in block and field == "rows_en":
                    continue
                rows = block.get(field)
                if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
                    raise ValueError(f"{key}: expected a rectangular {field} table")
    if not any(block["type"] == "section" for block in blocks):
        raise ValueError("Include at least one section.")
    if not any(block["type"] == "paragraph" for block in blocks):
        raise ValueError("Include the paper's paragraphs.")


def render(data, data_dir, output, source_pdf=None):
    check(data)
    source = local_url(source_pdf, output) if source_pdf else ""
    paper = data["paper"]
    lang = paper.get("source_lang", "en")
    sections = [b for b in data["blocks"] if b["type"] == "section"]
    nav = "<ul>" + "".join(
        f'<li><a href="#{b["id"]}" class="{"" if b.get("level", 2) == 2 else "sub"}">{escape(b["title_zh"])}</a></li>'
        for b in sections) + "</ul>"
    fragments = []
    for block in data["blocks"]:
        block = {"source_lang": lang, **block}
        kind, key = block["type"], block["id"]
        if kind == "section":
            level = 2 if block.get("level", 2) == 2 else 3
            style = "major" if level == 2 else "minor"
            fragments.append(
                f'<header class="section-heading {style}" id="{key}">'
                f'<h{level}>{escape(block["title_zh"])}</h{level}>'
                f'<p lang="{escape(lang)}">{escape(block["title_en"])}</p></header>')
        elif kind == "paragraph":
            fragments.append(comparison(block, source))
        elif kind == "references":
            items = []
            for item in block["entries"]:
                url = f' <a href="{web_url(item["url"])}">来源</a>' if item.get("url") else ""
                items.append(f'<li lang="{escape(lang)}">{escape(item["text"])}{url}</li>')
            fragments.append(f'<details class="references" id="{key}"><summary>{escape(block["title"])}</summary>'
                             f'<ol>{"".join(items)}</ol></details>')
        else:
            label = block.get("title", block["zh"])
            original = picture(data_dir / block["image"], label) if block.get("image") else ""
            body = comparison(block, source, anchored=False)
            if kind == "figure":
                if not original:
                    raise ValueError(f"{key}: a figure requires an image")
            elif kind == "equation":
                if not original:
                    original = f'<div class="equation">{escape(block["formula"])}</div>'
            else:
                if not original:
                    original = table(block["rows_en"], label, lang)
                body += table(block["rows_zh"], label, "zh-CN")
                body += f"<details><summary>展开原表</summary>{original}</details>"
                original = ""
            fragments.append(f'<section class="visual" id="{key}"><h4 class="table-heading">{escape(label)}</h4>'
                             f'{original}{body}</section>')
    if paper.get("keywords_zh"):
        keywords = " · ".join(paper["keywords_zh"])
        keywords_en = " · ".join(paper.get("keywords_en", []))
        byline_keywords = f'<p class="item-note"><strong>关键词</strong>　{escape(keywords)}'
        if keywords_en:
            byline_keywords += f'<br><span lang="{escape(lang)}">{escape(keywords_en)}</span>'
        byline_keywords += "</p>"
    else:
        byline_keywords = ""
    links = [f'<a href="{web_url(item["url"])}">{escape(item["label"])}</a>' for item in paper.get("links", [])]
    route = [f'<a href="#{b["id"]}">{escape(b.get("route_label", b["title_zh"]))}</a>'
             for b in sections if b.get("route_label")]
    byline = [escape(paper[field]) for field in ("authors", "publication") if paper.get(field)]
    return Template((ASSETS / "reader.html").read_text(encoding="utf-8")).substitute(
        title=escape(paper["title_zh"]), title_short=escape(paper.get("short_title", paper["title_zh"])),
        title_en=escape(paper["title_en"]), byline=f'<p class="byline">{"<br>".join(byline)}</p>' if byline else "",
        sources=f'<div class="sources">{"".join(links)}</div>' if links else "",
        route=f'<div class="route"><span>阅读主线</span>{"".join(route)}</div>' if route else "",
        pdf_link=f'<a href="{source}">原版 PDF</a>' if source else "",
        nav=nav, content=byline_keywords + "".join(fragments),
        style=(ASSETS / "reader.css").read_text(encoding="utf-8"),
        script=(ASSETS / "reader.js").read_text(encoding="utf-8"),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path, help="Reviewed paper JSON")
    parser.add_argument("output", type=Path, help="Destination HTML")
    parser.add_argument("--source-pdf", type=Path, help="Original PDF, for relative page links")
    args = parser.parse_args()
    try:
        if args.source_pdf and not args.source_pdf.is_file():
            raise ValueError("The original PDF does not exist.")
        data = json.loads(args.data.read_text(encoding="utf-8"))
        document = render(data, args.data.parent, args.output, args.source_pdf)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Could not render the paper: {error}\n")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
