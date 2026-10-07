#!/usr/bin/env python3
"""Genera ``catalog.html``: il catalogo della libreria come pagina web locale.

La pagina è un unico file autosufficiente (CSS e JavaScript inclusi, nessuna
risorsa esterna) che si apre con un doppio clic anche da ``file://``: una scheda
("card") per ogni indicatore, strategia, funzione e fonte, con ricerca, filtro per
tag, pulsante **Copia codice** (il testo del ``.pl`` finisce negli appunti, pronto
da incollare nel PowerLanguage Editor), **Mostra codice**, **Scheda** (il
``README.md`` reso in HTML), link alla cartella e ai file.

Uso::

    python tools/render_html.py                 # scrive catalog.html nella radice del repository
    python tools/render_html.py --open          # ...e lo apre nel browser predefinito
    python tools/render_html.py --out X.html    # percorso di uscita diverso (i link relativi vengono adattati)
    python tools/render_html.py --root P        # radice del repository (default: cartella padre di tools/)
    python tools/render_html.py --quiet         # non stampa avvisi e messaggi informativi
    python tools/render_html.py --stamp         # aggiunge la riga "Generato il ..." (altrimenti l'output
                                                # è deterministico: nessun timestamp)
    python tools/render_html.py --no-catalog    # non aggiorna CATALOG.md e catalog.json

Lo script non rilegge il front matter per conto suo: importa ``tools/build_catalog.py``
e ne usa il caricatore (:func:`build_catalog.load_library`), il validatore
(:func:`build_catalog.validate`) e i renderer. Se ci sono errori di validazione li
stampa ed esce con codice 1 senza scrivere nulla; altrimenti rigenera
``CATALOG.md`` e ``catalog.json`` quando non sono aggiornati (così i tre cataloghi
restano coerenti) e scrive la pagina.

``catalog.html`` è un file **locale**, ignorato da git: si rigenera quando serve.

Il Markdown delle schede è reso da :func:`markdown_to_html`, un renderer minimo
(intestazioni, paragrafi, elenchi, tabelle, blocchi di codice, citazioni, codice
in linea, grassetto, corsivo, link e immagini); tutto il testo è protetto con
``html.escape`` e il renderer non solleva mai eccezioni su input strani.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import html
import html.entities
import os
import posixpath
import re
import sys
import unicodedata
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_catalog as bc  # noqa: E402

__all__ = [
    "CATALOG_HTML",
    "PAGE_TITLE",
    "RenderContext",
    "markdown_to_html",
    "render_page",
    "anchor_id",
    "link_prefix_for",
    "build_arg_parser",
    "main",
]

CATALOG_HTML = "catalog.html"
GENERATED_BY = "tools/render_html.py"
REGENERATE_CMD = "python tools/render_html.py"
PAGE_TITLE = "Libreria PowerLanguage per MultiCharts"

#: Etichette italiane dei tipi di fonte (mostrate nei badge).
PAPER_TYPE_LABELS: dict[str, str] = {
    "paper": "paper",
    "book": "libro",
    "chapter": "capitolo",
    "article": "articolo",
    "thesis": "tesi",
    "web": "pagina web",
}
#: Descrizione italiana degli stati (tooltip dei badge; il badge mostra la chiave).
STATUS_TITLES: dict[str, str] = {
    "draft": "bozza: codice non ancora verificato in MultiCharts",
    "tested": "testato: compila ed è stato eseguito su un grafico o backtest",
    "stable": "stabile: usato nel tempo senza correzioni di rilievo",
    "deprecated": "deprecato: superato o non più mantenuto",
    "to-read": "da leggere",
    "reading": "lettura in corso",
    "read": "letto",
    "extracted": "estratto: almeno una voce di codice cita questa fonte",
}
#: Id delle sezioni della pagina, nell'ordine di visualizzazione.
SECTION_IDS: dict[str, str] = {
    "indicator": "indicatori",
    "strategy": "strategie",
    "function": "funzioni",
    "paper": "fonti",
}
#: Massima profondità di annidamento (elenchi, citazioni) oltre la quale il
#: contenuto è reso come testo semplice: evita ricorsioni senza fine su input strani.
MAX_NESTING = 8


# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------


def _esc(value: Any) -> str:
    """``html.escape`` di qualunque valore (``None`` → stringa vuota)."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _fold(text: Any) -> str:
    """Testo minuscolo senza accenti e con spazi normalizzati, per la ricerca."""
    decomposed = unicodedata.normalize("NFKD", str(text))
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(plain.lower().split())


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def anchor_id(kind: str, folder: str) -> str:
    """Id HTML della scheda di una voce: ``voce-<slug>`` (codice) o ``fonte-<id>`` (fonte)."""
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", str(folder)).strip("-") or "x"
    return ("fonte-" if kind == "paper" else "voce-") + safe


# ---------------------------------------------------------------------------
# Renderer Markdown minimo
# ---------------------------------------------------------------------------


@dataclass
class RenderContext:
    """Contesto di :func:`markdown_to_html`.

    :param base_dir: cartella (POSIX, relativa alla radice) del file Markdown: i link
        relativi sono risolti rispetto a questa (``../../papers/x/README.md`` →
        ``papers/x/README.md``).
    :param anchors: mappa ``percorso relativo alla radice -> id`` delle schede presenti
        nella pagina: un link a quel percorso diventa un'ancora ``#id``.
    :param link_prefix: prefisso dei link relativi alla radice (non vuoto solo quando
        ``catalog.html`` è scritto fuori dalla radice).
    :param id_prefix: prefisso degli id delle intestazioni e dei frammenti ``#...``;
        se vuoto le intestazioni non ricevono alcun id.
    :param heading_shift: di quanti livelli abbassare le intestazioni (``##`` → ``<h3>``
        con 1).
    """

    base_dir: str = ""
    anchors: dict[str, str] = field(default_factory=dict)
    link_prefix: str = ""
    id_prefix: str = ""
    heading_shift: int = 1
    used_ids: set[str] = field(default_factory=set)


_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*([^`]*?)[ \t]*$")
_HR_RE = re.compile(r"^ {0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
_UL_RE = re.compile(r"^( {0,3})([-*+])(?:[ \t]+(.*))?$")
_OL_RE = re.compile(r"^( {0,3})(\d{1,9})([.)])(?:[ \t]+(.*))?$")
_QUOTE_RE = re.compile(r"^ {0,3}> ?(.*)$")
_TASK_RE = re.compile(r"^\[([ xX])\][ \t]+")
_TABLE_ALIGN_RE = re.compile(r"^:?-+:?$")
_STASH_OPEN, _STASH_CLOSE = "\ue000", "\ue001"
_STASH_RE = re.compile(f"{_STASH_OPEN}(\\d+){_STASH_CLOSE}")
_PUA_RE = re.compile("[\ue000-\uf8ff]")
#: Caratteri di controllo C0 (tranne tabulazione e a capo): sostituiti con U+FFFD.
_CONTROL_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CODE_SPAN_RE = re.compile(r"(?<![`\\])(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.DOTALL)
_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|~<>])")
_IMAGE_RE = re.compile(
    r"!\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(\s*([^\s()]*(?:\([^\s()]*\)[^\s()]*)*)"
    r"(?:\s+(?:&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;))?\s*\)"
)
_LINK_RE = re.compile(
    r"\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(\s*([^\s()]*(?:\([^\s()]*\)[^\s()]*)*)"
    r"(?:\s+(?:&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;))?\s*\)"
)
_AUTOLINK_RE = re.compile(r"&lt;((?:https?://|mailto:)[^\s<>]*?)&gt;")
_BARE_URL_RE = re.compile(r"(?<![\w/])(https?://(?:[^\s<>&\ue000-\uf8ff]|&amp;)+)")
_STRONG_EM_RE = re.compile(r"\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*")
_STRONG_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)")
_EM_RE = re.compile(r"(?<!\*)\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)|(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)")
_STRIKE_RE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
_BREAK_RE = re.compile(r"(?: {2,}|\\)\n")
#: Riferimenti a entità HTML ben formati (``&amp;``, ``&copy;``, ``&#169;``, ``&#xA9;``):
#: vengono lasciati passare come li renderebbe GitHub, invece di mostrarli letteralmente.
_ENTITY_RE = re.compile(r"&(#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_SAFE_SCHEMES = ("http:", "https:", "mailto:")
_LANG_RE = re.compile(r"[^A-Za-z0-9_+.-]+")


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _para_line(line: str) -> str:
    """Riga di paragrafo senza spazi ai lati, conservando i due spazi finali
    (interruzione di riga voluta in Markdown)."""
    return line.strip() + ("  " if line.endswith("  ") else "")


def _resolve_href(href: str, ctx: RenderContext) -> tuple[str, bool] | None:
    """Destinazione di un link: ``(href, esterno)`` oppure ``None`` se il link va
    reso come testo (schema non ammesso, es. ``javascript:``)."""
    href = href.strip()
    if not href:
        return None
    if href.startswith("//"):
        # Link "protocol-relative": da file:// il browser lo risolverebbe come
        # file://host/share (su Windows un percorso UNC): lo si forza su https.
        return "https:" + href, True
    if _SCHEME_RE.match(href):
        return (href, True) if href.lower().startswith(_SAFE_SCHEMES) else None
    if href.startswith("#"):
        return "#" + ctx.id_prefix + href[1:], False
    path, _hash, fragment = href.partition("#")
    path = path.partition("?")[0]
    if path.startswith("/"):
        # Stile GitHub: "/docs/x.md" è relativo alla radice del repository, non al disco.
        resolved = posixpath.normpath(path.lstrip("/"))
    elif path:
        resolved = posixpath.normpath(posixpath.join(ctx.base_dir, path))
    else:
        resolved = ctx.base_dir or "."
    if resolved == ".." or resolved.startswith("../"):
        return None  # uscirebbe dalla radice del repository: reso come testo
    if path.endswith("/") and resolved not in (".", ""):
        resolved += "/"
    if resolved == ".":
        resolved = ""
    anchor = ctx.anchors.get(resolved.rstrip("/")) if resolved else None
    if anchor:
        return "#" + anchor, False
    target = (ctx.link_prefix + resolved) if resolved else (ctx.link_prefix or "./")
    if fragment:
        target += "#" + fragment
    return target, False


def _is_entity(body: str) -> bool:
    """Vero se ``&body;`` è un riferimento a entità HTML valido (numerico o nome noto)."""
    if body.startswith("#"):
        try:
            code = int(body[2:], 16) if body[1] in "xX" else int(body[1:])
        except ValueError:
            return False
        return 0 < code <= 0x10FFFF and not 0xD800 <= code <= 0xDFFF
    return (body + ";") in html.entities.html5


def _inline(text: str, ctx: RenderContext) -> str:
    """Rende il markup in linea di un testo già privo di struttura a blocchi."""
    text = _PUA_RE.sub("\ufffd", text)
    stash: list[str] = []

    def keep(fragment: str) -> str:
        stash.append(fragment)
        return f"{_STASH_OPEN}{len(stash) - 1}{_STASH_CLOSE}"

    def code_repl(match: re.Match[str]) -> str:
        content = match.group(2)
        if len(content) >= 2 and content[0] == " " and content[-1] == " " and content.strip():
            content = content[1:-1]
        return keep("<code>" + html.escape(content) + "</code>")

    text = _CODE_SPAN_RE.sub(code_repl, text)
    text = _ESCAPE_RE.sub(lambda m: keep(html.escape(m.group(1))), text)
    text = _ENTITY_RE.sub(lambda m: keep(m.group(0)) if _is_entity(m.group(1)) else m.group(0), text)
    text = html.escape(text, quote=True)

    def image_repl(match: re.Match[str]) -> str:
        alt, src = match.group(1), html.unescape(match.group(2))
        resolved = _resolve_href(src, ctx)
        if resolved is None or resolved[0].startswith("#"):
            return alt
        return keep(f'<img src="{_esc(resolved[0])}" alt="{alt}" loading="lazy">')

    def link_repl(match: re.Match[str]) -> str:
        label, href = match.group(1), html.unescape(match.group(2))
        resolved = _resolve_href(href, ctx)
        label_html = _emphasis(label)
        if resolved is None:
            return label_html
        target, external = resolved
        extra = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return keep(f'<a href="{_esc(target)}"{extra}>{label_html}</a>')

    def autolink_repl(match: re.Match[str]) -> str:
        url = match.group(1)
        return keep(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>')

    def bare_url_repl(match: re.Match[str]) -> str:
        url = match.group(1)
        trailing = ""
        while url and url[-1] in ".,;:!?)":
            if url[-1] == ")" and url.count("(") >= url.count(")"):
                break
            trailing = url[-1] + trailing
            url = url[:-1]
        if not url.startswith(("http://", "https://")) or len(url) <= 8:
            return match.group(0)
        return keep(f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>') + trailing

    text = _IMAGE_RE.sub(image_repl, text)
    text = _LINK_RE.sub(link_repl, text)
    text = _AUTOLINK_RE.sub(autolink_repl, text)
    text = _BARE_URL_RE.sub(bare_url_repl, text)
    text = _emphasis(text)
    text = _BREAK_RE.sub("<br>\n", text)
    for _ in range(len(stash) + 1):
        restored = _STASH_RE.sub(lambda m: stash[int(m.group(1))] if int(m.group(1)) < len(stash) else "", text)
        if restored == text:
            break
        text = restored
    return text


def _emphasis(text: str) -> str:
    text = _STRONG_EM_RE.sub(r"<strong><em>\1</em></strong>", text)
    text = _STRONG_RE.sub(lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
    text = _EM_RE.sub(lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
    text = _STRIKE_RE.sub(r"<s>\1</s>", text)
    return text


def _heading_id(text: str, ctx: RenderContext) -> str:
    plain = re.sub(r"[`*_~\[\]()!]", "", text)
    plain = re.sub(r"<[^>]*>", "", plain)
    folded = unicodedata.normalize("NFKD", plain).lower()
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    slug = re.sub(r"[^\w\s-]", "", folded)
    slug = re.sub(r"\s+", "-", slug.strip()) or "sezione"
    candidate = ctx.id_prefix + slug
    counter = 1
    while candidate in ctx.used_ids:
        candidate = f"{ctx.id_prefix}{slug}-{counter}"
        counter += 1
    ctx.used_ids.add(candidate)
    return candidate


def _split_row(line: str) -> list[str]:
    """Celle di una riga di tabella (``\\|`` è una barra letterale)."""
    text = line.strip()
    cells: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf))
    if cells and cells[0].strip() == "" and text.startswith("|"):
        cells = cells[1:]
    if cells and cells[-1].strip() == "" and text.endswith("|") and not text.endswith("\\|"):
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_table_separator(line: str) -> bool:
    if "|" not in line or set(line.strip()) - set("|:- \t"):
        return False
    cells = _split_row(line)
    return bool(cells) and all(_TABLE_ALIGN_RE.match(c) for c in cells)


def _starts_block(line: str) -> bool:
    """Vero se la riga interrompe un paragrafo aprendo un altro blocco."""
    return bool(
        _HEADING_RE.match(line)
        or _FENCE_RE.match(line)
        or _HR_RE.match(line)
        or _QUOTE_RE.match(line)
        or _UL_RE.match(line)
        or _OL_RE.match(line)
    )


def _render_blocks(lines: list[str], ctx: RenderContext, depth: int = 0) -> list[str]:
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if _is_blank(line):
            i += 1
            continue

        fence = _FENCE_RE.match(line)
        if fence:
            marker, info = fence.group(1), fence.group(2).strip()
            closing = re.compile(r"^ {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}[ \t]*$")
            body: list[str] = []
            i += 1
            while i < n and not closing.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # salta la chiusura (o resta oltre la fine se la chiusura manca)
            lang = _LANG_RE.sub("", info.split()[0]) if info else ""
            cls = f' class="language-{_esc(lang.lower())}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(body))}\n</code></pre>")
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            level = min(6, len(heading.group(1)) + ctx.heading_shift)
            text = (heading.group(2) or "").strip()
            id_attr = f' id="{_esc(_heading_id(text, ctx))}"' if ctx.id_prefix else ""
            out.append(f"<h{level}{id_attr}>{_inline(text, ctx)}</h{level}>")
            i += 1
            continue

        if _HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        if _QUOTE_RE.match(line):
            quoted: list[str] = []
            while i < n and _QUOTE_RE.match(lines[i]):
                quoted.append(_QUOTE_RE.match(lines[i]).group(1))  # type: ignore[union-attr]
                i += 1
            if depth >= MAX_NESTING:
                out.append("<blockquote><p>" + _inline("\n".join(quoted), ctx) + "</p></blockquote>")
            else:
                out.append("<blockquote>\n" + "\n".join(_render_blocks(quoted, ctx, depth + 1)) + "\n</blockquote>")
            continue

        if _UL_RE.match(line) or _OL_RE.match(line):
            rendered, i = _render_list(lines, i, ctx, depth)
            out.append(rendered)
            continue

        if "|" in line and i + 1 < n and _is_table_separator(lines[i + 1]):
            rendered, i = _render_table(lines, i, ctx)
            out.append(rendered)
            continue

        para: list[str] = [_para_line(line)]
        i += 1
        while i < n and not _is_blank(lines[i]) and not _starts_block(lines[i]):
            if "|" in lines[i] and i + 1 < n and _is_table_separator(lines[i + 1]):
                break
            para.append(_para_line(lines[i]))
            i += 1
        out.append("<p>" + _inline("\n".join(para), ctx) + "</p>")
    return out


def _render_list(lines: list[str], start: int, ctx: RenderContext, depth: int) -> tuple[str, int]:
    first = _OL_RE.match(lines[start])
    ordered = first is not None
    item_re = _OL_RE if ordered else _UL_RE
    items: list[list[str]] = []
    content_indent = 0
    loose = False
    pending_blank = False
    i = start
    n = len(lines)
    while i < n:
        line = lines[i]
        if _is_blank(line):
            pending_blank = True
            i += 1
            continue
        match = item_re.match(line)
        if match and (not items or _indent(line) < content_indent):
            if pending_blank and items:
                loose = True
            marker_len = len(match.group(2)) + (len(match.group(3)) if ordered else 0)
            content_indent = len(match.group(1)) + marker_len + 1
            text = (match.group(4) if ordered else match.group(3)) or ""
            items.append([text])
            pending_blank = False
            i += 1
            continue
        if items and _indent(line) >= min(content_indent, 2):
            if pending_blank:
                items[-1].append("")
                loose = True
            items[-1].append(line[min(_indent(line), content_indent):])
            pending_blank = False
            i += 1
            continue
        if items and not pending_blank and not _starts_block(line):
            items[-1].append(line.strip())  # continuazione "pigra" del paragrafo dell'elemento
            i += 1
            continue
        break

    rendered_items: list[str] = []
    for item in items:
        checkbox = ""
        task = _TASK_RE.match(item[0])
        if task:
            checked = " checked" if task.group(1) in "xX" else ""
            checkbox = f'<input type="checkbox" disabled{checked}> '
            item[0] = item[0][task.end():]
        if depth >= MAX_NESTING:
            blocks = ["<p>" + _inline("\n".join(item), ctx) + "</p>"]
        else:
            blocks = _render_blocks(item, ctx, depth + 1)
        if not loose and blocks and blocks[0].startswith("<p>") and blocks[0].endswith("</p>"):
            blocks[0] = blocks[0][3:-4]
        rendered_items.append("<li>" + checkbox + "\n".join(blocks) + "</li>")
    tag = "ol" if ordered else "ul"
    start_attr = ""
    if ordered and first is not None:
        number = int(first.group(2))
        if number != 1:
            start_attr = f' start="{number}"'
    return f"<{tag}{start_attr}>\n" + "\n".join(rendered_items) + f"\n</{tag}>", i


def _render_table(lines: list[str], start: int, ctx: RenderContext) -> tuple[str, int]:
    header = _split_row(lines[start])
    aligns = _split_row(lines[start + 1])
    width = len(header)
    classes: list[str] = []
    for spec in aligns[:width]:
        if spec.startswith(":") and spec.endswith(":"):
            classes.append(' class="ta-c"')
        elif spec.endswith(":"):
            classes.append(' class="ta-r"')
        else:
            classes.append("")
    classes += [""] * (width - len(classes))
    parts = ['<div class="tbl"><table>', "<thead><tr>"]
    for idx, cell in enumerate(header):
        parts.append(f"<th{classes[idx]}>{_inline(cell, ctx)}</th>")
    parts.append("</tr></thead>")
    i = start + 2
    rows: list[str] = []
    while i < len(lines) and not _is_blank(lines[i]) and "|" in lines[i]:
        cells = _split_row(lines[i])
        cells = (cells + [""] * width)[:width]
        rows.append("<tr>" + "".join(f"<td{classes[c]}>{_inline(cell, ctx)}</td>" for c, cell in enumerate(cells)) + "</tr>")
        i += 1
    if rows:
        parts.append("<tbody>" + "".join(rows) + "</tbody>")
    parts.append("</table></div>")
    return "".join(parts), i


def markdown_to_html(
    text: Any,
    *,
    base_dir: str = "",
    anchors: dict[str, str] | None = None,
    link_prefix: str = "",
    id_prefix: str = "",
    heading_shift: int = 1,
) -> str:
    """Converte un testo Markdown in HTML (funzione pura, deterministica).

    Costrutti riconosciuti: intestazioni ATX (``#``..``######``, abbassate di
    ``heading_shift`` livelli: ``##`` → ``<h3>`` con il default 1, mai oltre ``<h6>``),
    paragrafi, elenchi puntati e numerati (anche annidati, caselle ``[ ]``/``[x]``),
    tabelle a barre con riga di allineamento, blocchi di codice recintati, citazioni
    ``>``, righe orizzontali, codice in linea, ``**grassetto**``, ``*corsivo*``,
    ``~~barrato~~``, link ``[testo](url)``, immagini, autolink ``<https://...>`` e URL
    nudi. I commenti HTML sono rimossi; ogni altro HTML e tutto il testo sono protetti
    con ``html.escape``. I link relativi sono risolti rispetto a ``base_dir`` e, se
    puntano a una scheda presente in ``anchors``, diventano ancore interne; quelli
    esterni si aprono in una nuova scheda; gli schemi non sicuri (``javascript:``)
    sono resi come testo.

    Non solleva mai eccezioni: in caso di input inatteso ripiega su un ``<pre>`` con il
    testo protetto.
    """
    if text is None:
        return ""
    source = text if isinstance(text, str) else str(text)
    ctx = RenderContext(
        base_dir=base_dir.strip("/"),
        anchors=dict(anchors or {}),
        link_prefix=link_prefix,
        id_prefix=id_prefix,
        heading_shift=max(0, int(heading_shift)),
    )
    try:
        cleaned = _COMMENT_RE.sub("", _CONTROL_RE.sub("\ufffd", _normalize_newlines(source)))
        lines = [line.expandtabs(4).rstrip() if not line.endswith("  ") else line.expandtabs(4) for line in cleaned.split("\n")]
        return "\n".join(_render_blocks(lines, ctx))
    except Exception:  # pragma: no cover - rete di sicurezza: la pagina deve comunque essere generata
        return "<pre>" + html.escape(source) + "</pre>"


# ---------------------------------------------------------------------------
# Pagina HTML
# ---------------------------------------------------------------------------


def _badge(text: Any, cls: str, title: str | None = None) -> str:
    title_attr = f' title="{_esc(title)}"' if title else ""
    return f'<span class="badge {cls}"{title_attr}>{_esc(text)}</span>'


def _chip(tag: str) -> str:
    return f'<button type="button" class="chip" data-tag="{_esc(tag)}" aria-pressed="false">{_esc(tag)}</button>'


def _chips(tags: list[str]) -> str:
    if not tags:
        return ""
    return '<div class="chips">' + "".join(_chip(t) for t in tags) + "</div>"


def _dl(rows: list[tuple[str, str]]) -> str:
    rows = [(k, v) for k, v in rows if v]
    if not rows:
        return ""
    return '<dl class="meta">' + "".join(f"<dt>{_esc(k)}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


def _text_list(value: Any) -> str:
    items = bc._as_str_list(value)
    return _esc(", ".join(items)) if items else ""


def _entry_link(entry: bc.Entry, anchors: dict[str, str], with_type: bool = False) -> str:
    label = _esc(entry.display_name)
    if with_type:
        label = f'<span class="muted">{_esc(bc.TYPE_LABELS.get(entry.entry_type, entry.entry_type))}:</span> {label}'
    return f'<a href="#{anchors[entry.path]}">{label}</a>'


def _toggle_button(target: str, closed_label: str, open_label: str, cls: str = "btn") -> str:
    return (
        f'<button type="button" class="{cls}" data-toggle="{_esc(target)}" aria-controls="{_esc(target)}" '
        f'aria-expanded="false" data-label-closed="{_esc(closed_label)}" data-label-open="{_esc(open_label)}">'
        f"{_esc(closed_label)}</button>"
    )


def _read_source(lib: bc.Library, entry: bc.Entry) -> tuple[str | None, str | None]:
    """Testo del sorgente ``.pl`` (LF, senza BOM) oppure ``(None, motivo)``."""
    source = entry.meta.get("source_file")
    if not isinstance(source, str) or not source.strip():
        return None, "campo source_file mancante"
    path = lib.root / entry.dir_name / entry.folder / source
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, f"impossibile leggere {source}: {exc.strerror or exc}"
    return _normalize_newlines(text.lstrip("\ufeff")), None


def _strip_title(body: str, title: str) -> str:
    """Toglie il titolo ``# <nome>`` iniziale della scheda, già mostrato nella card."""
    lines = _normalize_newlines(body).split("\n")
    index = 0
    while index < len(lines) and _is_blank(lines[index]):
        index += 1
    if index < len(lines):
        match = _HEADING_RE.match(lines[index])
        if match and len(match.group(1)) == 1 and (match.group(2) or "").strip() == title.strip():
            return "\n".join(lines[index + 1 :])
    return body


def _search_text(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if value is None or value == "":
            continue
        if isinstance(value, list):
            parts.extend(str(v) for v in value)
        else:
            parts.append(str(value))
    return _fold(" ".join(parts))


def _code_card(
    lib: bc.Library,
    entry: bc.Entry,
    anchors: dict[str, str],
    papers_by_id: dict[str, bc.Entry],
    code_by_slug: dict[str, bc.Entry],
    used_by: dict[str, list[bc.Entry]],
    link_prefix: str,
) -> str:
    meta = entry.meta
    cid = anchors[entry.path]
    folder_href = f"{link_prefix}{entry.folder_path}/"
    type_label = bc.TYPE_LABELS.get(entry.entry_type, entry.entry_type)
    status = str(meta.get("status") or "")
    language = str(meta.get("language") or "")
    tags = [t.strip() for t in bc._as_str_list(meta.get("tags")) if t.strip()]

    badges = [_badge(type_label, f"type-{entry.entry_type}")]
    if status:
        badges.append(_badge(status, f"status-{_esc(status)}", STATUS_TITLES.get(status, "stato")))
    if meta.get("version"):
        badges.append(_badge(f"v{meta['version']}", "version", "versione (semver)"))
    if language and language != "PowerLanguage":
        badges.append(_badge(language, "lang", "linguaggio"))
    if meta.get("multicharts_version"):
        badges.append(_badge(f"MC {meta['multicharts_version']}", "mc", "versione di MultiCharts su cui è stato testato"))

    paper_ids = bc._as_str_list(meta.get("papers"))
    paper_links = []
    paper_titles: list[str] = []
    for pid in paper_ids:
        paper = papers_by_id.get(pid)
        if paper is None:
            paper_links.append(f"<code>{_esc(pid)}</code>")
            continue
        year = paper.meta.get("year")
        suffix = f" ({_esc(year)})" if not bc._is_missing(year) else ""
        paper_links.append(f'<a href="#{anchors[paper.path]}">{_esc(paper.display_name)}</a>{suffix}')
        paper_titles.append(paper.display_name)
    depends = bc._as_str_list(meta.get("depends_on"))
    dep_links = [
        _entry_link(code_by_slug[d], anchors) if d in code_by_slug else f"<code>{_esc(d)}</code>" for d in depends
    ]
    superseded = meta.get("superseded_by")
    superseded_html = ""
    if not bc._is_missing(superseded):
        slug = str(superseded)
        superseded_html = _entry_link(code_by_slug[slug], anchors) if slug in code_by_slug else f"<code>{_esc(slug)}</code>"
    users = used_by.get(entry.folder, [])

    rows = [
        ("Fonti", ", ".join(paper_links) if paper_links else '<span class="muted">nessuna (voce senza fonte)</span>'),
        ("Dipendenze", ", ".join(dep_links) if dep_links else '<span class="muted">nessuna</span>'),
        ("Usata da", ", ".join(_entry_link(u, anchors, with_type=True) for u in users)),
        ("Sostituita da", superseded_html),
        ("Mercati", _text_list(meta.get("markets"))),
        ("Timeframe", _text_list(meta.get("timeframes"))),
        ("Autore", _esc(meta.get("author")) if not bc._is_missing(meta.get("author")) else ""),
        ("Aggiornata", _esc(meta.get("updated")) if not bc._is_missing(meta.get("updated")) else ""),
    ]

    source_text, source_problem = _read_source(lib, entry)
    source_name = str(meta.get("source_file") or "")
    src_id = f"{cid}-src"
    doc_id = f"{cid}-doc"
    actions = []
    if source_text is not None:
        actions.append(
            f'<button type="button" class="btn primary" data-copy="{src_id}-text" '
            f'title="Copia tutto il testo di {_esc(source_name)} negli appunti">Copia codice</button>'
        )
        actions.append(_toggle_button(src_id, "Mostra codice", "Nascondi codice"))
    actions.append(_toggle_button(doc_id, "Scheda", "Chiudi scheda"))
    actions.append(f'<a class="btn" href="{_esc(folder_href)}" title="Apri la cartella {_esc(entry.folder_path)}/">Apri cartella</a>')
    if source_name:
        actions.append(f'<a class="btn" href="{_esc(folder_href + source_name)}">Apri .pl</a>')
    archive = meta.get("archive_file")
    if isinstance(archive, str) and archive.strip():
        actions.append(f'<a class="btn" href="{_esc(folder_href + archive)}">Apri .pla</a>')
    entry_dir = lib.root / entry.dir_name / entry.folder
    if (entry_dir / "notes.md").is_file():
        actions.append(f'<a class="btn" href="{_esc(folder_href + "notes.md")}">Note estese</a>')
    if (entry_dir / "backtests").is_dir():
        actions.append(f'<a class="btn" href="{_esc(folder_href + "backtests/")}">Backtest</a>')

    if source_text is not None:
        line_count = source_text.count("\n") + (0 if source_text.endswith("\n") or not source_text else 1)
        source_panel = (
            f'<div class="panel" id="{src_id}" hidden>'
            f'<div class="panel-bar"><span class="file">{_esc(source_name)} · {_plural(line_count, "riga", "righe")}</span>'
            f'<button type="button" class="btn small" data-copy="{src_id}-text">Copia</button></div>'
            f'<pre><code id="{src_id}-text" class="language-powerlanguage">{html.escape(source_text)}</code></pre></div>'
        )
    else:
        source_panel = f'<p class="warn">Sorgente non disponibile: {_esc(source_problem)}</p>'

    body_html = markdown_to_html(
        _strip_title(entry.body, entry.display_name),
        base_dir=entry.folder_path,
        anchors=anchors,
        link_prefix=link_prefix,
        id_prefix=cid + "-",
        heading_shift=2,
    )
    doc_panel = (
        f'<div class="panel scheda" id="{doc_id}" hidden>'
        f'<div class="panel-bar"><span class="file">{_esc(entry.path)}</span>'
        f'<a class="btn small" href="{_esc(link_prefix + entry.path)}">Apri README.md</a></div>'
        f'{body_html or "<p class=muted>Scheda vuota.</p>"}</div>'
    )

    search = _search_text(
        entry.display_name, entry.folder, type_label, entry.entry_type, status, language, meta.get("version"),
        meta.get("summary"), tags, paper_ids, paper_titles, depends, meta.get("markets"), meta.get("timeframes"),
        meta.get("author"), source_name,
    )
    summary = meta.get("summary")
    summary_html = f'<p class="summary">{_esc(summary)}</p>' if not bc._is_missing(summary) else ""
    return (
        f'<article class="card" id="{cid}" data-kind="code" data-type="{_esc(entry.entry_type)}" '
        f'data-tags="{_esc(" ".join(tags))}" data-search="{_esc(search)}">'
        f'<header class="card-head"><h3><a class="permalink" href="#{cid}">{_esc(entry.display_name)}</a></h3>'
        f'<div class="badges">{"".join(badges)}</div>'
        f'<code class="slug" title="slug (nome della cartella)">{_esc(entry.folder)}</code></header>'
        f"{summary_html}{_dl(rows)}{_chips(tags)}"
        f'<div class="actions">{"".join(actions)}</div>'
        f"{source_panel}{doc_panel}</article>"
    )


def _paper_card(
    lib: bc.Library,
    paper: bc.Entry,
    anchors: dict[str, str],
    implementations: list[bc.Entry],
    link_prefix: str,
) -> str:
    meta = paper.meta
    cid = anchors[paper.path]
    folder_href = f"{link_prefix}{paper.folder_path}/"
    ptype = str(meta.get("type") or "")
    status = str(meta.get("status") or "")
    year = meta.get("year")
    authors = bc._as_str_list(meta.get("authors"))
    tags = [t.strip() for t in bc._as_str_list(meta.get("tags")) if t.strip()]

    badges = [_badge(PAPER_TYPE_LABELS.get(ptype, ptype or "fonte"), f"type-paper ptype-{_esc(ptype)}", "tipo di fonte")]
    if status:
        badges.append(_badge(status, f"status-{_esc(status)}", STATUS_TITLES.get(status, "stato")))
    if not bc._is_missing(year):
        badges.append(_badge(year, "year", "anno di pubblicazione"))

    pub_parts: list[str] = []
    if not bc._is_missing(meta.get("journal")):
        pub_parts.append(f"<em>{_esc(meta['journal'])}</em>")
    volume, issue = meta.get("volume"), meta.get("issue")
    if not bc._is_missing(volume):
        vol = _esc(volume)
        if not bc._is_missing(issue):
            vol += f"({_esc(issue)})"
        pub_parts.append(vol)
    elif not bc._is_missing(issue):
        pub_parts.append(f"n. {_esc(issue)}")
    if not bc._is_missing(meta.get("pages")):
        pub_parts.append(f"pp. {_esc(meta['pages'])}")
    if not bc._is_missing(meta.get("publisher")):
        pub_parts.append(_esc(meta["publisher"]))
    if not bc._is_missing(meta.get("isbn")):
        pub_parts.append(f"ISBN {_esc(meta['isbn'])}")
    byline = ""
    if authors or not bc._is_missing(year):
        who = _esc(", ".join(authors))
        when = f" ({_esc(year)})" if not bc._is_missing(year) else ""
        byline = f'<p class="byline">{who}{when}</p>'
    pub_html = f'<p class="pub">{", ".join(pub_parts)}</p>' if pub_parts else ""

    doi = meta.get("doi")
    doi_html = ""
    if not bc._is_missing(doi):
        doi_text = str(doi).strip()
        doi_url = doi_text if doi_text.lower().startswith("http") else f"https://doi.org/{doi_text}"
        doi_html = f'<a href="{_esc(doi_url)}" target="_blank" rel="noopener noreferrer">{_esc(doi_text)}</a>'
    url = meta.get("url")
    url_html = ""
    if not bc._is_missing(url):
        url_text = str(url).strip()
        if url_text.lower().startswith(("http://", "https://")):
            url_html = f'<a href="{_esc(url_text)}" target="_blank" rel="noopener noreferrer" class="url">{_esc(url_text)}</a>'
        else:
            url_html = _esc(url_text)
    impl_html = ", ".join(_entry_link(e, anchors, with_type=True) for e in implementations)
    rows = [
        ("DOI", doi_html),
        ("URL", url_html),
        ("Implementazioni", impl_html or '<span class="muted">nessuna in questa libreria</span>'),
        ("Aggiunta", _esc(meta.get("added")) if not bc._is_missing(meta.get("added")) else ""),
    ]

    doc_id = f"{cid}-doc"
    actions = [_toggle_button(doc_id, "Scheda", "Chiudi scheda", cls="btn primary")]
    actions.append(f'<a class="btn" href="{_esc(folder_href)}" title="Apri la cartella {_esc(paper.folder_path)}/">Apri cartella</a>')
    paper_dir = lib.root / paper.dir_name / paper.folder
    if (paper_dir / "notes.md").is_file():
        actions.append(f'<a class="btn" href="{_esc(folder_href + "notes.md")}">Note estese</a>')
    pdf = meta.get("pdf")
    if isinstance(pdf, str) and pdf.strip():
        actions.append(f'<a class="btn" href="{_esc(folder_href + pdf)}">PDF</a>')

    body_html = markdown_to_html(
        _strip_title(paper.body, paper.display_name),
        base_dir=paper.folder_path,
        anchors=anchors,
        link_prefix=link_prefix,
        id_prefix=cid + "-",
        heading_shift=2,
    )
    doc_panel = (
        f'<div class="panel scheda" id="{doc_id}" hidden>'
        f'<div class="panel-bar"><span class="file">{_esc(paper.path)}</span>'
        f'<a class="btn small" href="{_esc(link_prefix + paper.path)}">Apri README.md</a></div>'
        f'{body_html or "<p class=muted>Scheda vuota.</p>"}</div>'
    )
    search = _search_text(
        paper.display_name, paper.folder, "fonte", ptype, PAPER_TYPE_LABELS.get(ptype), status, year, authors,
        meta.get("journal"), meta.get("publisher"), doi, meta.get("summary"), tags,
        [e.display_name for e in implementations],
    )
    summary = meta.get("summary")
    summary_html = f'<p class="summary">{_esc(summary)}</p>' if not bc._is_missing(summary) else ""
    return (
        f'<article class="card" id="{cid}" data-kind="paper" data-type="paper" '
        f'data-tags="{_esc(" ".join(tags))}" data-search="{_esc(search)}">'
        f'<header class="card-head"><h3><a class="permalink" href="#{cid}">{_esc(paper.display_name)}</a></h3>'
        f'<div class="badges">{"".join(badges)}</div>'
        f'<code class="slug" title="id della fonte (nome della cartella)">{_esc(paper.folder)}</code></header>'
        f"{byline}{pub_html}{summary_html}{_dl(rows)}{_chips(tags)}"
        f'<div class="actions">{"".join(actions)}</div>'
        f"{doc_panel}</article>"
    )


def _section(section_id: str, title: str, cards: list[str], empty_text: str) -> str:
    count = len(cards)
    body = "".join(cards) if cards else f'<p class="empty">{_esc(empty_text)}</p>'
    return (
        f'<section class="group" id="{section_id}">'
        f'<h2>{_esc(title)} <span class="count" data-count data-total="{count}">{count}</span></h2>'
        f'<div class="cards">{body}</div>'
        f'<p class="empty filtered" hidden>Nessuna voce corrisponde ai filtri.</p>'
        f"</section>"
    )


def _all_tags(lib: bc.Library) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for entry in (*lib.entries, *lib.papers):
        for tag in {t.strip() for t in bc._as_str_list(entry.meta.get("tags")) if t.strip()}:
            counts[tag] = counts.get(tag, 0) + 1
    return sorted(counts.items())


def render_page(lib: bc.Library, *, link_prefix: str = "", stamp: str | None = None) -> str:
    """Genera il testo completo di ``catalog.html`` (deterministico se ``stamp`` è ``None``).

    :param lib: libreria già caricata e **valida** (vedi :func:`build_catalog.validate`).
    :param link_prefix: prefisso dei link relativi alla radice (vuoto se la pagina è
        scritta nella radice; vedi :func:`link_prefix_for`).
    :param stamp: testo della riga "Generato il ..." nel piè di pagina, oppure ``None``.
    """
    anchors: dict[str, str] = {}
    for entry in (*lib.entries, *lib.papers):
        cid = anchor_id(entry.kind, entry.folder)
        anchors[entry.path] = cid
        anchors[entry.folder_path] = cid
    papers_by_id = {p.folder: p for p in lib.papers}
    code_by_slug = {e.folder: e for e in lib.entries}
    used_by: dict[str, list[bc.Entry]] = {}
    for entry in lib.entries:
        for dep in bc._as_str_list(entry.meta.get("depends_on")):
            used_by.setdefault(dep, []).append(entry)
    implementations = bc.implementations_by_paper(lib)

    sections: list[str] = []
    counts_nav: list[str] = []
    singular = {"indicator": "indicatore", "strategy": "strategia", "function": "funzione"}
    for code_type in bc.CODE_TYPES:
        entries = lib.entries_of_type(code_type)
        cards = [_code_card(lib, e, anchors, papers_by_id, code_by_slug, used_by, link_prefix) for e in entries]
        title = bc.TYPE_LABELS_PLURAL[code_type]
        sections.append(_section(SECTION_IDS[code_type], title, cards, "Nessuna voce."))
        counts_nav.append(
            f'<a href="#{SECTION_IDS[code_type]}">{_plural(len(entries), singular[code_type], title.lower())}</a>'
        )
    paper_cards = [_paper_card(lib, p, anchors, implementations.get(p.folder, []), link_prefix) for p in lib.papers]
    sections.append(_section(SECTION_IDS["paper"], "Fonti", paper_cards, "Nessuna fonte."))
    counts_nav.append(f'<a href="#fonti">{_plural(len(lib.papers), "fonte", "fonti")}</a>')

    tag_chips = "".join(
        f'<button type="button" class="chip" data-tag="{_esc(tag)}" aria-pressed="false">'
        f'{_esc(tag)} <span class="n">{count}</span></button>'
        for tag, count in _all_tags(lib)
    )
    total = len(lib.entries) + len(lib.papers)
    stamp_html = f'<p class="stamp">Generato il {_esc(stamp)}.</p>' if stamp else ""

    parts = [
        "<!doctype html>\n",
        '<html lang="it">\n<head>\n<meta charset="utf-8">\n',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
        '<meta name="color-scheme" content="light dark">\n',
        f'<meta name="generator" content="{GENERATED_BY}">\n',
        f"<title>{_esc(PAGE_TITLE)}</title>\n",
        "<style>\n", _CSS, "\n</style>\n</head>\n<body>\n",
        '<a class="skip" href="#contenuto">Vai al contenuto</a>\n',
        '<header class="top"><div class="wrap">\n',
        f"<h1>{_esc(PAGE_TITLE)}</h1>\n",
        '<p class="lead">Catalogo locale della libreria: indicatori, strategie, funzioni e fonti. '
        "Con <strong>Copia codice</strong> il sorgente finisce negli appunti, pronto da incollare nel "
        "PowerLanguage Editor (File › New › Indicator/Signal/Function); importare prima le funzioni "
        "elencate in <em>Dipendenze</em>.</p>\n",
        f'<nav class="counts" aria-label="Sezioni">{" · ".join(counts_nav)}</nav>\n',
        "</div></header>\n",
        '<div class="toolbar"><div class="wrap">\n',
        '<label class="search"><span class="sr-only">Cerca</span>'
        '<input type="search" id="search" placeholder="Cerca per nome, tag, autore, anno… (premi / per iniziare)" '
        'autocomplete="off" spellcheck="false"></label>\n',
        '<button type="button" class="btn small" id="clear-filters" hidden>Azzera filtri</button>\n',
        '<p id="result-count" class="result-count" aria-live="polite"></p>\n',
        "</div></div>\n",
        '<main class="wrap" id="contenuto">\n',
        f'<div class="tagbar" aria-label="Filtra per tag">{tag_chips or "<span class=muted>Nessun tag.</span>"}</div>\n',
        "\n".join(sections),
        "\n</main>\n",
        '<footer class="wrap"><p>Pagina generata da <code>tools/render_html.py</code> a partire dai '
        f"<code>README.md</code> e dai sorgenti della libreria ({_plural(total, 'voce', 'voci')}); non modificarla a mano. "
        f"Per rigenerarla: <code>{_esc(REGENERATE_CMD)}</code> oppure la voce "
        "«Apri il catalogo» del menu dell'icona <strong>Libreria PowerLanguage</strong>.</p>",
        stamp_html,
        "</footer>\n",
        "<noscript><style>.panel[hidden]{display:block!important}.toolbar{display:none}</style>"
        '<p class="wrap warn">JavaScript disattivato: ricerca e pulsanti non funzionano, ma codice e schede sono visibili.</p></noscript>\n',
        "<script>\n", _JS, "\n</script>\n</body>\n</html>\n",
    ]
    return "".join(parts)


_CSS = """\
:root{--bg:#f4f6f9;--card:#ffffff;--text:#1b1f24;--muted:#5b6470;--border:#d8dee6;--accent:#0b5fcc;
--accent-text:#ffffff;--chip:#e9eef5;--chip-text:#2b3440;--code-bg:#f0f3f7;--ok:#1d7a3e;--ok-text:#ffffff;--warn-bg:#fff5d6;
--warn-text:#6b4e00;--shadow:0 1px 2px rgba(16,24,40,.06),0 1px 6px rgba(16,24,40,.05);
--t-indicator:#0f766e;--t-strategy:#6d28d9;--t-function:#b45309;--t-paper:#1d4ed8;
--s-draft:#4b5563;--s-tested:#1d4ed8;--s-stable:#15803d;--s-deprecated:#b91c1c;
--s-to-read:#4b5563;--s-reading:#b45309;--s-read:#1d4ed8;--s-extracted:#15803d}
@media (prefers-color-scheme:dark){:root{--bg:#0e1217;--card:#161c24;--text:#e6e9ee;--muted:#9aa4b2;--border:#2a333f;
--accent:#6ea8ff;--accent-text:#0b1220;--chip:#222b36;--chip-text:#d5dbe3;--code-bg:#0b0f14;--ok:#4ade80;--ok-text:#0b1220;
--warn-bg:#3a2e00;--warn-text:#ffe08a;--shadow:none;--t-indicator:#5eead4;--t-strategy:#c4b5fd;--t-function:#fcd34d;
--t-paper:#93c5fd;--s-draft:#a3adbb;--s-tested:#93c5fd;--s-stable:#86efac;--s-deprecated:#fca5a5;--s-to-read:#a3adbb;
--s-reading:#fcd34d;--s-read:#93c5fd;--s-extracted:#86efac}}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
code,pre,kbd,.slug{font-family:ui-monospace,"Cascadia Code",Consolas,"SF Mono",Menlo,monospace}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-999px;top:8px;background:var(--card);padding:6px 10px;border-radius:6px}
.skip:focus{left:8px;z-index:30}
header.top{padding:24px 0 12px}
h1{margin:0 0 6px;font-size:clamp(22px,4vw,30px);line-height:1.2}
.lead{margin:0 0 10px;color:var(--muted);max-width:72ch}
.counts{font-size:15px;color:var(--muted)}
.counts a{text-decoration:none;font-weight:600}
.toolbar{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--border);padding:10px 0}
.toolbar .wrap{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
.search{flex:1 1 260px;display:block}
#search{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:10px;background:var(--card);color:inherit;font:inherit}
.result-count{margin:0;font-size:14px;color:var(--muted);flex-basis:100%}
.result-count:empty{display:none}
.tagbar{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 6px}
.chip{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border:1px solid transparent;border-radius:999px;
background:var(--chip);color:var(--chip-text);font:inherit;font-size:13px;cursor:pointer;line-height:1.4}
.chip:hover{border-color:var(--accent)}
.chip.on{background:var(--accent);color:var(--accent-text)}
.chip .n{opacity:.85;font-size:12px}
section.group{margin:26px 0 8px}
section.group h2{display:flex;align-items:baseline;gap:10px;margin:0 0 12px;font-size:22px;scroll-margin-top:84px}
.count{font-size:14px;font-weight:600;color:var(--muted);background:var(--chip);border-radius:999px;padding:1px 9px}
.cards{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(min(100%,360px),1fr))}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px;box-shadow:var(--shadow);
display:flex;flex-direction:column;gap:10px;min-width:0;scroll-margin-top:84px}
.card.open{grid-column:1/-1}
.card:target{outline:2px solid var(--accent);outline-offset:3px}
.card-head{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}
.card-head h3{margin:0;font-size:18px;line-height:1.25;flex:1 1 100%;overflow-wrap:anywhere}
.permalink{color:inherit;text-decoration:none}
.permalink:hover{text-decoration:underline}
.badges{display:flex;flex-wrap:wrap;gap:6px}
.badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:12px;font-weight:600;line-height:1.5;
background:var(--chip);color:var(--chip-text);white-space:nowrap}
.badge.type-indicator{color:var(--t-indicator);background:color-mix(in srgb,var(--t-indicator) 14%,transparent)}
.badge.type-strategy{color:var(--t-strategy);background:color-mix(in srgb,var(--t-strategy) 14%,transparent)}
.badge.type-function{color:var(--t-function);background:color-mix(in srgb,var(--t-function) 16%,transparent)}
.badge.type-paper{color:var(--t-paper);background:color-mix(in srgb,var(--t-paper) 14%,transparent)}
.badge.status-draft,.badge.status-to-read{color:var(--s-draft)}
.badge.status-tested,.badge.status-read{color:var(--s-tested)}
.badge.status-stable,.badge.status-extracted{color:var(--s-stable)}
.badge.status-deprecated{color:var(--s-deprecated)}
.badge.status-reading{color:var(--s-reading)}
.slug{font-size:12px;color:var(--muted);margin-left:auto;overflow-wrap:anywhere}
.summary{margin:0}
.byline{margin:0;font-weight:600}
.pub{margin:0;color:var(--muted);font-size:15px}
.meta{display:grid;grid-template-columns:max-content 1fr;gap:4px 12px;margin:0;font-size:14.5px}
.meta dt{color:var(--muted);font-weight:600}
.meta dd{margin:0;min-width:0;overflow-wrap:anywhere}
.muted{color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:4px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border:1px solid var(--border);border-radius:9px;
background:var(--card);color:inherit;font:inherit;font-size:14px;line-height:1.3;cursor:pointer;text-decoration:none}
.btn:hover{border-color:var(--accent)}
.btn.primary{background:var(--accent);color:var(--accent-text);border-color:transparent;font-weight:600}
.btn.small{padding:4px 9px;font-size:13px}
.btn.done{background:var(--ok);color:var(--ok-text);border-color:transparent}
.btn[aria-expanded="true"]{border-color:var(--accent);color:var(--accent)}
.panel{border:1px solid var(--border);border-radius:10px;background:var(--code-bg);overflow:hidden}
.panel-bar{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 10px;font-size:13px;
color:var(--muted);border-bottom:1px solid var(--border);background:var(--card);flex-wrap:wrap}
.panel-bar .file{overflow-wrap:anywhere}
.panel pre{margin:0;padding:12px 14px;overflow:auto;max-height:70vh;font-size:13px;line-height:1.45;tab-size:4}
.scheda{padding:4px 16px 12px;background:var(--card);font-size:15px}
.scheda h3,.scheda h4,.scheda h5,.scheda h6{margin:18px 0 6px;line-height:1.3}
.scheda h3{font-size:17px}.scheda h4{font-size:16px}.scheda h5,.scheda h6{font-size:15px}
.scheda p,.scheda ul,.scheda ol{margin:8px 0}
.scheda li{margin:3px 0}
.scheda code{background:var(--code-bg);padding:1px 5px;border-radius:4px;font-size:.92em}
.scheda pre{background:var(--code-bg);padding:10px 12px;border-radius:8px;overflow:auto;font-size:13px}
.scheda pre code{background:none;padding:0;font-size:inherit}
.scheda blockquote{margin:10px 0;padding:4px 14px;border-left:3px solid var(--accent);color:var(--muted)}
.scheda img{max-width:100%;height:auto}
.scheda hr{border:0;border-top:1px solid var(--border);margin:14px 0}
.tbl{overflow-x:auto;margin:10px 0}
.scheda table{border-collapse:collapse;font-size:14px;min-width:50%}
.scheda th,.scheda td{border:1px solid var(--border);padding:5px 9px;text-align:left;vertical-align:top}
.scheda th{background:var(--code-bg)}
.ta-c{text-align:center}.ta-r{text-align:right}
.empty{color:var(--muted);margin:0}
.warn{background:var(--warn-bg);color:var(--warn-text);padding:8px 12px;border-radius:8px;margin:0;font-size:14px}
footer{padding:28px 16px 40px;color:var(--muted);font-size:14px}
footer p{margin:0 0 6px}
@media (max-width:600px){.card{padding:14px;border-radius:12px}.meta{grid-template-columns:1fr;gap:2px}
.meta dt{margin-top:4px}.slug{margin-left:0}}
@media (prefers-reduced-motion:no-preference){.btn,.chip{transition:background-color .15s,border-color .15s}}
@media print{.toolbar,.actions,.tagbar,.skip{display:none}.card{break-inside:avoid;box-shadow:none}}"""


_JS = """\
(function () {
  'use strict';
  var fold = function (s) {
    s = String(s || '');
    try { s = s.normalize('NFKD').replace(/[\\u0300-\\u036f]/g, ''); } catch (e) {}
    return s.toLowerCase();
  };
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('section.group'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-tag]'));
  var search = document.getElementById('search');
  var clearBtn = document.getElementById('clear-filters');
  var resultCount = document.getElementById('result-count');
  var active = {};

  function activeTags() { return Object.keys(active); }
  function cardTags(card) { return (card.getAttribute('data-tags') || '').split(' ').filter(Boolean); }

  function apply() {
    var words = fold(search.value).split(/\\s+/).filter(Boolean);
    var tags = activeTags();
    var visible = 0;
    cards.forEach(function (card) {
      var hay = card.getAttribute('data-search') || '';
      var ok = words.every(function (w) { return hay.indexOf(w) !== -1; });
      if (ok && tags.length) {
        var own = cardTags(card);
        ok = tags.every(function (t) { return own.indexOf(t) !== -1; });
      }
      card.hidden = !ok;
      if (ok) visible++;
    });
    sections.forEach(function (sec) {
      var all = sec.querySelectorAll('.card').length;
      var shown = sec.querySelectorAll('.card:not([hidden])').length;
      var counter = sec.querySelector('[data-count]');
      if (counter) counter.textContent = (shown === all) ? String(all) : shown + ' / ' + all;
      var empty = sec.querySelector('.empty.filtered');
      if (empty) empty.hidden = !(all > 0 && shown === 0);
    });
    chips.forEach(function (chip) {
      var on = !!active[chip.getAttribute('data-tag')];
      chip.classList.toggle('on', on);
      chip.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    var filtering = words.length > 0 || tags.length > 0;
    resultCount.textContent = filtering
      ? (visible + ' su ' + cards.length + (cards.length === 1 ? ' voce' : ' voci') +
         (tags.length ? ' · tag: ' + tags.join(', ') : ''))
      : '';
    clearBtn.hidden = !filtering;
  }

  function clearFilters() { search.value = ''; active = {}; apply(); }

  function flash(btn, message, ok) {
    if (!btn.getAttribute('data-label')) btn.setAttribute('data-label', btn.textContent);
    btn.textContent = message;
    btn.classList.toggle('done', !!ok);
    clearTimeout(btn._flashTimer);
    btn._flashTimer = setTimeout(function () {
      btn.textContent = btn.getAttribute('data-label');
      btn.classList.remove('done');
    }, 1600);
  }

  function fallbackCopy(text) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.top = '-2000px';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.focus();
    area.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  function copyText(text, btn) {
    var done = function () { flash(btn, 'Copiato!', true); };
    var fail = function () {
      if (fallbackCopy(text)) { done(); } else { flash(btn, 'Copia non riuscita', false); }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try { navigator.clipboard.writeText(text).then(done, fail); } catch (e) { fail(); }
    } else {
      fail();
    }
  }

  function setOpenState(card) {
    if (!card) return;
    var anyOpen = Array.prototype.some.call(card.querySelectorAll('.panel'), function (p) { return !p.hidden; });
    card.classList.toggle('open', anyOpen);
  }

  function toggle(btn) {
    var panel = document.getElementById(btn.getAttribute('data-toggle'));
    if (!panel) return;
    var open = panel.hidden;
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    var label = btn.getAttribute(open ? 'data-label-open' : 'data-label-closed');
    if (label) btn.textContent = label;
    setOpenState(panel.closest('.card'));
  }

  document.addEventListener('click', function (ev) {
    var target = ev.target.closest ? ev.target.closest('[data-toggle],[data-copy],.chip[data-tag]') : null;
    if (!target) return;
    if (target.hasAttribute('data-toggle')) {
      toggle(target);
    } else if (target.hasAttribute('data-copy')) {
      var source = document.getElementById(target.getAttribute('data-copy'));
      if (source) copyText(source.textContent, target);
    } else {
      var tag = target.getAttribute('data-tag');
      if (active[tag]) { delete active[tag]; } else { active[tag] = true; }
      apply();
    }
  });

  function revealHash() {
    var id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { id = location.hash.slice(1); }
    if (!id) return;
    var el = document.getElementById(id);
    if (!el) return;
    var card = el.closest ? el.closest('.card') : null;
    if (card && card.hidden) { clearFilters(); }
    var panel = el.closest ? el.closest('.panel') : null;
    if (panel && panel.hidden) {
      var btn = document.querySelector('[data-toggle="' + panel.id + '"]');
      if (btn) toggle(btn);
    }
    if (el.scrollIntoView) el.scrollIntoView({ block: 'start' });
  }

  search.addEventListener('input', apply);
  clearBtn.addEventListener('click', clearFilters);
  document.addEventListener('keydown', function (ev) {
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if (ev.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) { ev.preventDefault(); search.focus(); }
    if (ev.key === 'Escape' && document.activeElement === search && search.value) { search.value = ''; apply(); }
  });
  window.addEventListener('hashchange', revealHash);
  apply();
  revealHash();
})();"""


# ---------------------------------------------------------------------------
# Riga di comando
# ---------------------------------------------------------------------------


def link_prefix_for(root: Path, out_dir: Path) -> str:
    """Prefisso dei link relativi alla radice quando la pagina è scritta in ``out_dir``.

    Vuoto se ``out_dir`` è la radice; altrimenti il percorso relativo POSIX da
    ``out_dir`` alla radice con ``/`` finale (``../``); se un percorso relativo non
    esiste (su Windows: unità diverse) l'URI ``file://`` assoluto della radice.
    """
    try:
        relative = Path(os.path.relpath(root, out_dir)).as_posix()
    except ValueError:
        return root.resolve().as_uri() + "/"
    return "" if relative == "." else relative + "/"


def default_root() -> Path:
    """Radice del repository: la cartella padre di ``tools/``."""
    return Path(__file__).resolve().parent.parent


def build_arg_parser() -> argparse.ArgumentParser:
    """Costruisce il parser della riga di comando (testi in italiano)."""
    parser = argparse.ArgumentParser(
        prog="render_html.py",
        description=(
            "Genera catalog.html, il catalogo della libreria come pagina web locale autosufficiente "
            "(ricerca, filtro per tag, pulsante 'Copia codice', codice sorgente e schede README in linea). "
            "Rilegge le voci con build_catalog.py: se i metadati non sono validi stampa gli errori ed esce con 1."
        ),
        epilog=(
            "La pagina si apre con un doppio clic (anche da file://) e non va modificata a mano: è un file "
            "locale ignorato da git. Se CATALOG.md e catalog.json non sono aggiornati vengono rigenerati "
            "(salvo --no-catalog). Senza --stamp l'output è deterministico (nessuna data).\n"
            "Codici di uscita: 0 = pagina scritta; 1 = errori di validazione o di scrittura."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="mostra questo messaggio di aiuto ed esce")
    parser.add_argument("--root", metavar="PERCORSO", help="radice del repository (default: cartella padre di tools/)")
    parser.add_argument(
        "--out",
        metavar="FILE",
        help=f"file HTML da scrivere (default: {CATALOG_HTML} nella radice; altrove i link relativi vengono adattati)",
    )
    parser.add_argument("--open", action="store_true", help="apre la pagina generata nel browser predefinito")
    parser.add_argument("--quiet", action="store_true", help="non stampa avvisi e messaggi informativi (gli errori sono sempre stampati)")
    parser.add_argument("--stamp", action="store_true", help="aggiunge nel piè di pagina la riga 'Generato il <data e ora>'")
    parser.add_argument("--no-catalog", action="store_true", help="non rigenera CATALOG.md e catalog.json anche se non aggiornati")
    return parser


def _console_utf8_safe() -> None:
    """Evita UnicodeEncodeError su console non UTF-8 (es. cp1252 su Windows)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="backslashreplace")
            except (ValueError, OSError):
                pass


def _display_path(path: Path) -> str:
    """Percorso da mostrare: relativo se sta sotto la cartella corrente, altrimenti assoluto."""
    try:
        relative = os.path.relpath(path)
    except ValueError:
        return str(path)
    if relative.startswith(os.pardir):
        return str(path)
    return relative


def open_in_browser(path: Path) -> bool:
    """Apre il file nel browser predefinito; ``False`` se non è stato possibile."""
    try:
        return bool(webbrowser.open(path.resolve().as_uri()))
    except Exception:  # webbrowser può sollevare errori diversi a seconda del sistema
        return False


def main(argv: list[str] | None = None) -> int:
    """Punto di ingresso della riga di comando. Ritorna il codice di uscita."""
    _console_utf8_safe()
    args = build_arg_parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else default_root()
    problem = bc.library_root_problem(root)
    if problem:
        print(f"ERRORE {root}: {problem}", file=sys.stderr)
        return 1

    lib = bc.load_library(root)
    errors = bc.validate(lib)
    if not args.quiet:
        for warning in bc.collect_warnings(lib):
            print(warning, file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validazione fallita: {len(errors)} errori. Pagina non generata.", file=sys.stderr)
        return 1

    if not args.no_catalog:
        catalog_md = bc.render_catalog_md(lib)
        catalog_json = bc.render_catalog_json(lib)
        if bc.check_outputs(root, catalog_md, catalog_json):
            try:
                bc.write_outputs(root, catalog_md, catalog_json)
            except OSError as exc:
                print(f"AVVISO: impossibile aggiornare {bc.CATALOG_MD}/{bc.CATALOG_JSON}: {exc.strerror or exc}", file=sys.stderr)
            else:
                if not args.quiet:
                    print(f"Aggiornati {bc.CATALOG_MD} e {bc.CATALOG_JSON}.")

    out = Path(args.out).resolve() if args.out else root / CATALOG_HTML
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M") if args.stamp else None
    page = render_page(lib, link_prefix=link_prefix_for(root, out.parent), stamp=stamp)
    try:
        out.write_text(page, encoding="utf-8", errors="replace", newline="\n")
    except OSError as exc:
        print(f"ERRORE {_display_path(out)}: impossibile scrivere il file: {exc.strerror or exc}", file=sys.stderr)
        return 1
    summary = f"{len(lib.entries)} voci di codice, {len(lib.papers)} fonti"
    if not args.quiet:
        print(f"Scritto {_display_path(out)} ({summary}).")
    if args.open:
        if open_in_browser(out):
            if not args.quiet:
                print("Pagina aperta nel browser predefinito.")
        else:
            print(f"Impossibile aprire il browser automaticamente: aprire a mano il file {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # output in pipe chiusa in anticipo (es. `| head`): nessun traceback
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
