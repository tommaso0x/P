"""Test (solo libreria standard) per ``tools/render_html.py``.

Coprono il renderer Markdown (:func:`render_html.markdown_to_html`), la pagina
generata su una libreria sintetica in una cartella temporanea, la riga di comando
(``--out``, ``--quiet``, ``--stamp``, ``--open`` con ``webbrowser`` sostituito) e una
generazione completa su una copia della libreria reale del repository. In coda un
test facoltativo sull'icona ``tools/windows/libreria.ico`` (saltato se il file manca).

Esecuzione dalla radice del repository::

    python -m unittest discover -s tools/tests -v
"""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_catalog as bc  # noqa: E402
import render_html as rh  # noqa: E402

REPO_ROOT = TOOLS_DIR.parent
PAPER_ID = "2001-rossi-bianchi-regole-trading"
FIXED_DATE = "2024-01-15"
DOI = "10.1000/xyz.2001.123"
SCRIPT = "<script>alert(1)</script>"


# ---------------------------------------------------------------------------
# Utilità per costruire una libreria sintetica
# ---------------------------------------------------------------------------


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def yaml_value(value: object) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


def front_matter(fields: dict[str, object], body: str) -> str:
    lines = ["---"] + [f"{k}: {yaml_value(v)}" for k, v in fields.items()] + ["---", "", body, ""]
    return "\n".join(lines)


def code_fields(entry_type: str, name: str, slug: str, source_file: str, **overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "type": entry_type,
        "name": name,
        "slug": slug,
        "version": "1.0.0",
        "status": "draft",
        "language": "PowerLanguage",
        "source_file": source_file,
        "papers": [PAPER_ID],
        "depends_on": [],
        "tags": ["moving-average"],
        "created": FIXED_DATE,
        "updated": FIXED_DATE,
    }
    fields.update(overrides)
    return fields


def source_text(name: str, extra: str = "") -> str:
    return (
        f"{{\n  Nome:        {name}\n  Versione:    1.0.0\n}}\n\n"
        f"inputs: Length(20);\nif Close > Average(Close, Length) and Length <> 0 then\n"
        f'    Plot1(Average(Close, Length), "{name}");\n{extra}'
    )


def code_body(name: str, extra: str = "") -> str:
    return (
        f"# {name}\n\n"
        f"## Descrizione\n\nTesto con **grassetto** e `codice`. {SCRIPT}\n\n"
        f"## Fonte\n\n- [Rossi & Bianchi (2001)](../../papers/{PAPER_ID}/README.md) — sezione 2.\n\n"
        f"## Changelog\n\n- {FIXED_DATE} — 1.0.0: prima bozza.\n{extra}"
    )


def add_code_entry(root: Path, entry_type: str, slug: str, name: str, source_file: str, **overrides: object) -> Path:
    folder = root / bc.TYPE_DIRS[entry_type] / slug
    body_extra = str(overrides.pop("body_extra", ""))
    source_extra = str(overrides.pop("source_extra", ""))
    write(folder / "README.md", front_matter(code_fields(entry_type, name, slug, source_file, **overrides), code_body(name, body_extra)))
    write(folder / source_file, source_text(name, source_extra))
    return folder


def paper_body(*slugs: str) -> str:
    lines = [
        "# Regole di trading semplici",
        "",
        "<!-- commento da togliere -->",
        "",
        "## Riferimento",
        "",
        f"Rossi, M., & Bianchi, L. (2001). Regole di trading semplici. https://doi.org/{DOI}",
        "",
        "## Sintesi",
        "",
        f"Sintesi con {SCRIPT} e una tabella:",
        "",
        "| Parametro | Valore |",
        "|---|---:|",
        "| `n` | 50 |",
        "",
        "Note estese: [notes.md](notes.md)",
        "",
        bc.IMPLEMENTATIONS_HEADING,
        "",
    ]
    lines += [f"- [{slug}](../../indicators/{slug}/README.md)" for slug in slugs]
    return "\n".join(lines) + "\n"


def add_paper(root: Path, pid: str = PAPER_ID, implementations: tuple[str, ...] = (), **overrides: object) -> Path:
    fields: dict[str, object] = {
        "type": "paper",
        "id": pid,
        "title": "Regole di trading semplici",
        "authors": ["Mario Rossi", "Luca Bianchi"],
        "year": 2001,
        "status": "extracted",
        "tags": ["technical-analysis"],
        "added": FIXED_DATE,
        "journal": "Rivista di Finanza",
        "volume": 47,
        "issue": 5,
        "pages": "1-20",
        "doi": DOI,
        "url": f"https://doi.org/{DOI}",
    }
    fields.update(overrides)
    folder = root / bc.PAPERS_DIR / pid
    write(folder / "README.md", front_matter(fields, paper_body(*implementations)))
    write(folder / "notes.md", "# Note\n\nTesto.\n")
    return folder


def make_repo(root: Path) -> None:
    """Una fonte, una funzione, un indicatore e una strategia coerenti fra loro."""
    add_paper(root, implementations=("ma-band",))
    add_code_entry(root, "function", "ma-band-signal", "MA_Band_Signal", "MA_Band_Signal.pl", tags=["signal"])
    add_code_entry(
        root, "indicator", "ma-band", 'MA Band "beta" <b>', "MA_Band.pl",
        depends_on=["ma-band-signal"], summary=f"Bande attorno alla media mobile. {SCRIPT}",
        tags=["moving-average", "band"], source_extra=f"{{ {SCRIPT} & commento }}\n",
    )
    add_code_entry(
        root, "strategy", "ma-crossover", "MA Crossover", "MA_Crossover.pl",
        depends_on=["ma-band-signal"], tags=["trend-following", "moving-average"],
        language="PowerLanguage.NET", status="tested", multicharts_version='"14"',
    )
    (root / bc.TEMPLATES_DIR).mkdir(exist_ok=True)


class TempRepoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def library(self) -> bc.Library:
        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])
        return lib


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = rh.main(argv)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Renderer Markdown
# ---------------------------------------------------------------------------


class TestMarkdownToHtml(unittest.TestCase):
    def test_headings_are_shifted_and_clamped(self) -> None:
        out = rh.markdown_to_html("# Uno\n## Due\n### Tre\n#### Quattro\n##### Cinque\n###### Sei\n## Chiuso ##")
        self.assertEqual(
            out.split("\n"),
            ["<h2>Uno</h2>", "<h3>Due</h3>", "<h4>Tre</h4>", "<h5>Quattro</h5>", "<h6>Cinque</h6>", "<h6>Sei</h6>", "<h3>Chiuso</h3>"],
        )
        self.assertEqual(rh.markdown_to_html("## Due", heading_shift=2), "<h4>Due</h4>")
        self.assertEqual(rh.markdown_to_html("#NoSpazio"), "<p>#NoSpazio</p>")

    def test_heading_ids_only_with_prefix_and_deduplicated(self) -> None:
        self.assertNotIn("id=", rh.markdown_to_html("## Regole / Formule"))
        out = rh.markdown_to_html("## Regole / Formule\n## Regole / Formule\n### Idee chiave", id_prefix="voce-x-")
        self.assertIn('<h3 id="voce-x-regole-formule">', out)
        self.assertIn('<h3 id="voce-x-regole-formule-1">', out)
        self.assertIn('<h4 id="voce-x-idee-chiave">', out)
        self.assertIn('href="#voce-x-sintesi"', rh.markdown_to_html("[s](#sintesi)", id_prefix="voce-x-"))

    def test_paragraphs_and_inline_markup(self) -> None:
        out = rh.markdown_to_html("Riga uno\nriga due.\n\nCon **forte**, *corsivo*, __forte__, _corsivo_, ~~barrato~~, ***entrambi*** e `cod<e>`.")
        self.assertIn("<p>Riga uno\nriga due.</p>", out)
        self.assertIn("<strong>forte</strong>, <em>corsivo</em>, <strong>forte</strong>, <em>corsivo</em>, <s>barrato</s>", out)
        self.assertIn("<strong><em>entrambi</em></strong>", out)
        self.assertIn("<code>cod&lt;e&gt;</code>", out)
        self.assertEqual(rh.markdown_to_html("a  \nb\\\nc"), "<p>a<br>\nb<br>\nc</p>")
        self.assertEqual(rh.markdown_to_html("`` a ` b `` e ` c `"), "<p><code>a ` b</code> e <code>c</code></p>")

    def test_underscores_inside_identifiers_are_not_emphasis(self) -> None:
        out = rh.markdown_to_html("BLL_MA_Band_Signal e snake_case_name, ma _questo_ sì e 2*3*4.")
        self.assertIn("BLL_MA_Band_Signal e snake_case_name", out)
        self.assertIn("<em>questo</em>", out)
        self.assertIn("2<em>3</em>4", out)  # come CommonMark: * funziona anche dentro le parole

    def test_backslash_escapes(self) -> None:
        self.assertEqual(rh.markdown_to_html("\\*non forte\\* e \\[no link\\](x) e \\`no codice\\`"), "<p>*non forte* e [no link](x) e `no codice`</p>")

    def test_lists_nested_ordered_and_tasks(self) -> None:
        out = rh.markdown_to_html("- a\n- b **x**\n  continua\n  - annidato\n- c\n\n3. tre\n4. quattro\n   segue\n\n- [ ] da fare\n- [x] fatto")
        self.assertIn("<ul>\n<li>a</li>\n<li>b <strong>x</strong>\ncontinua\n<ul>\n<li>annidato</li>\n</ul></li>\n<li>c</li>\n</ul>", out)
        self.assertIn('<ol start="3">\n<li>tre</li>\n<li>quattro\nsegue</li>\n</ol>', out)
        self.assertIn('<li><input type="checkbox" disabled> da fare</li>', out)
        self.assertIn('<li><input type="checkbox" disabled checked> fatto</li>', out)
        loose = rh.markdown_to_html("- uno\n\n- due")
        self.assertIn("<li><p>uno</p></li>", loose)
        self.assertIn("<p>intro:</p>\n<ul>\n<li>a</li>", rh.markdown_to_html("intro:\n- a"))

    def test_pipe_tables_with_alignment_and_escaped_pipes(self) -> None:
        out = rh.markdown_to_html("| A | B | C |\n|:--|:-:|--:|\n| 1 | 2 \\| x | <s> |\n| solo |\n\ndopo")
        self.assertIn('<thead><tr><th>A</th><th class="ta-c">B</th><th class="ta-r">C</th></tr></thead>', out)
        self.assertIn('<td>1</td><td class="ta-c">2 | x</td><td class="ta-r">&lt;s&gt;</td>', out)
        self.assertIn('<tr><td>solo</td><td class="ta-c"></td><td class="ta-r"></td></tr>', out)
        self.assertTrue(out.startswith('<div class="tbl"><table>'))
        self.assertTrue(out.endswith("</table></div>\n<p>dopo</p>"))
        self.assertIn("<th>x</th><th>y</th>", rh.markdown_to_html("x | y\n--|--\n1|2"))
        self.assertEqual(rh.markdown_to_html("a | b\nc | d"), "<p>a | b\nc | d</p>")  # senza riga di allineamento

    def test_fenced_code_blocks_are_escaped_and_tolerate_missing_closer(self) -> None:
        out = rh.markdown_to_html("```powerlanguage\nif a < b then\n    Plot1(x, \"<p>\");\n```\ntesto\n~~~\nsenza chiusura\n**no**")
        self.assertIn('<pre><code class="language-powerlanguage">if a &lt; b then\n    Plot1(x, &quot;&lt;p&gt;&quot;);\n</code></pre>', out)
        self.assertIn("<p>testo</p>", out)
        self.assertIn("<pre><code>senza chiusura\n**no**\n</code></pre>", out)

    def test_blockquotes_and_rules(self) -> None:
        out = rh.markdown_to_html("> citazione\n> con **forte**\n\n> > doppia\n\n---\n***")
        self.assertIn("<blockquote>\n<p>citazione\ncon <strong>forte</strong></p>\n</blockquote>", out)
        self.assertIn("<blockquote>\n<blockquote>\n<p>doppia</p>\n</blockquote>\n</blockquote>", out)
        self.assertEqual(out.count("<hr>"), 2)

    def test_links_are_resolved_relative_to_the_entry_folder(self) -> None:
        anchors = {f"papers/{PAPER_ID}/README.md": f"fonte-{PAPER_ID}", f"papers/{PAPER_ID}": f"fonte-{PAPER_ID}", "functions/f/README.md": "voce-f"}
        kwargs = dict(base_dir="indicators/i1", anchors=anchors)
        self.assertEqual(
            rh.markdown_to_html(f"[t](../../papers/{PAPER_ID}/README.md)", **kwargs),
            f'<p><a href="#fonte-{PAPER_ID}">t</a></p>',
        )
        self.assertIn('href="#fonte-', rh.markdown_to_html(f"[t](../../papers/{PAPER_ID}/)", **kwargs))
        self.assertIn('href="#voce-f"', rh.markdown_to_html("[t](../../functions/f/README.md#input)", **kwargs))
        self.assertEqual(rh.markdown_to_html("[n](notes.md)", **kwargs), '<p><a href="indicators/i1/notes.md">n</a></p>')
        self.assertEqual(rh.markdown_to_html("[c](../../CATALOG.md)", **kwargs), '<p><a href="CATALOG.md">c</a></p>')
        self.assertEqual(rh.markdown_to_html("[n](notes.md)", link_prefix="../P/", **kwargs), '<p><a href="../P/indicators/i1/notes.md">n</a></p>')
        self.assertIn('<a href="indicators/i1/backtests/a.png">', rh.markdown_to_html("[i](backtests/a.png \"titolo\")", **kwargs))
        self.assertEqual(rh.markdown_to_html("[n](notes.md)"), '<p><a href="notes.md">n</a></p>')

    def test_links_never_leave_the_repository_and_root_links_are_repo_relative(self) -> None:
        kwargs = dict(base_dir="indicators/i1", anchors={"docs/A.md": "doc-a"})
        # stile GitHub: "/docs/x" è la radice del repository, non quella del disco
        self.assertEqual(rh.markdown_to_html("[d](/docs/B.md)", **kwargs), '<p><a href="docs/B.md">d</a></p>')
        self.assertEqual(rh.markdown_to_html("[d](/docs/A.md)", **kwargs), '<p><a href="#doc-a">d</a></p>')
        self.assertEqual(rh.markdown_to_html("[d](/docs/)", link_prefix="../P/", **kwargs), '<p><a href="../P/docs/">d</a></p>')
        self.assertEqual(rh.markdown_to_html("[r](/)", **kwargs), '<p><a href="./">r</a></p>')
        # link che uscirebbero dal repository: resi come testo
        self.assertEqual(rh.markdown_to_html("[x](../../../../etc/passwd)", **kwargs), "<p>x</p>")
        self.assertEqual(rh.markdown_to_html("[x](../../..)", **kwargs), "<p>x</p>")
        self.assertEqual(rh.markdown_to_html("[x](/../x.md)", **kwargs), "<p>x</p>")
        self.assertEqual(rh.markdown_to_html("![x](../../../i.png)", **kwargs), "<p>x</p>")
        self.assertNotIn("..", rh.markdown_to_html("[x](../a.md)"))
        # protocol-relative: da file:// diventerebbe file://host/share (UNC su Windows)
        out = rh.markdown_to_html("[h](//evil.example/x)")
        self.assertIn('href="https://evil.example/x" target="_blank"', out)
        self.assertNotIn('href="//', out)

    def test_entity_references_are_kept_like_github(self) -> None:
        out = rh.markdown_to_html("a &amp; b &copy; &#169; &#xA9; &bogus; &#xD800; & c &lt;b&gt;")
        self.assertIn("a &amp; b &copy; &#169; &#xA9; &amp;bogus; &amp;#xD800; &amp; c &lt;b&gt;", out)
        self.assertNotIn("&amp;amp;", out)
        self.assertNotIn("<b>", out)
        self.assertEqual(rh.markdown_to_html("`&amp;`"), "<p><code>&amp;amp;</code></p>")

    def test_external_links_autolinks_and_bare_urls(self) -> None:
        out = rh.markdown_to_html("[e](https://e.com/a_b*c?x=1&y=2) e <https://auto.link/?a=1&b=2> e nudo https://nudo.it/p. Fine (https://par.it/x).")
        self.assertIn('<a href="https://e.com/a_b*c?x=1&amp;y=2" target="_blank" rel="noopener noreferrer">e</a>', out)
        self.assertIn('<a href="https://auto.link/?a=1&amp;b=2" target="_blank" rel="noopener noreferrer">https://auto.link/?a=1&amp;b=2</a>', out)
        self.assertIn('<a href="https://nudo.it/p" target="_blank" rel="noopener noreferrer">https://nudo.it/p</a>. Fine', out)
        self.assertIn('<a href="https://par.it/x" target="_blank" rel="noopener noreferrer">https://par.it/x</a>).', out)
        self.assertIn("<strong>", rh.markdown_to_html("[**f**](https://x.y)"))
        self.assertIn('href="mailto:a@b.it"', rh.markdown_to_html("[m](mailto:a@b.it)"))

    def test_unsafe_schemes_become_plain_text(self) -> None:
        self.assertEqual(rh.markdown_to_html("[js](javascript:alert(1))"), "<p>js</p>")
        self.assertEqual(rh.markdown_to_html("[d](data:text/html,x)"), "<p>d</p>")
        self.assertEqual(rh.markdown_to_html("![bad](javascript:x)"), "<p>bad</p>")
        self.assertNotIn("javascript:", rh.markdown_to_html("[j](JAVASCRIPT:alert(1))"))

    def test_images(self) -> None:
        out = rh.markdown_to_html("![grafico \"a\"](backtests/img.png) e ![e](https://x.y/i.png)", base_dir="indicators/i1")
        self.assertIn('<img src="indicators/i1/backtests/img.png" alt="grafico &quot;a&quot;" loading="lazy">', out)
        self.assertIn('<img src="https://x.y/i.png" alt="e" loading="lazy">', out)

    def test_html_is_escaped_and_comments_are_stripped(self) -> None:
        out = rh.markdown_to_html(f"<!-- via --> testo {SCRIPT} & <b onclick=x>b</b> <!-- multi\nriga -->\n\n## Dopo")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; &amp; &lt;b onclick=x&gt;b&lt;/b&gt;", out)
        self.assertNotIn("via", out)
        self.assertIn("<h3>Dopo</h3>", out)
        self.assertNotIn("<script>", rh.markdown_to_html(f"```\n{SCRIPT}\n```"))
        self.assertNotIn("<script>", rh.markdown_to_html(f"| {SCRIPT} |\n|---|\n| `{SCRIPT}` |"))
        self.assertNotIn("<script>", rh.markdown_to_html(f"[{SCRIPT}](x) ![{SCRIPT}](y.png) # {SCRIPT}"))
        self.assertNotIn('"><', rh.markdown_to_html('[x]("><script>alert(1)</script>)'))

    def test_never_raises_on_odd_input(self) -> None:
        odd = [
            "", " ", "\n\n\n", None, 42, 3.5, ["a"], "\ufeff# bom", "\r\n- crlf\r\n\r\n1. x\r\n",
            ">" * 60 + " profondo", " " * 500 + "- elenco", "- " * 300, "1. " * 200, "```", "~~~\n```", "`",
            "``` ```", "[", "](", "[]()", "![", "**", "*", "_", "__", "~~", "| | |", "|---|", "||\n||", "\\",
            "\\\\" * 50, "#" * 40, "#\n#\n#", "- [ ]", "- [x]", "> ", ">", "\t\t- tab", "a\tb\t|\tc\n--|--",
            "\x00\x01\x1f\x7f", "\ue000 0 \ue001 \ue0ff", "x" * 20000, ("abc " * 50 + "\n") * 200,
            "[a](" + "(" * 50 + ")" * 50 + ")", "<" * 100, "&" * 100, "<!--", "-->", "<!-- -->" * 100,
            "![](x)", "[](x)", "[x]( )", "[x](#)", "[x](//cdn.x/y)", "[x](../../../../../..)", "[x](/assoluto)",
            "1) uno\n2) due", "*  *  *", "- - -", "---\n---", "a\n---", "| a |\n| --- |\n| b |\nc",
        ]
        for text in odd:
            with self.subTest(text=repr(text)[:40]):
                out = rh.markdown_to_html(text)  # type: ignore[arg-type]
                self.assertIsInstance(out, str)
                self.assertNotIn("<script>", out)

    def test_output_is_deterministic(self) -> None:
        text = (REPO_ROOT / "templates" / "indicator" / "README.md").read_text(encoding="utf-8") if (REPO_ROOT / "templates" / "indicator" / "README.md").is_file() else "# T\n\n- a\n- b"
        body = bc.split_front_matter(text)[1] if text.lstrip().startswith("---") else text
        self.assertEqual(rh.markdown_to_html(body), rh.markdown_to_html(body))


# ---------------------------------------------------------------------------
# Pagina HTML su una libreria sintetica
# ---------------------------------------------------------------------------


class TestRenderPage(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_repo(self.root)
        self.lib = self.library()
        self.page = rh.render_page(self.lib)

    def test_entries_sources_and_internal_links(self) -> None:
        page = self.page
        for name in ("MA_Band_Signal", "MA Crossover", "Regole di trading semplici"):
            self.assertIn(name, page)
        self.assertIn("MA Band &quot;beta&quot; &lt;b&gt;", page)
        # sorgente .pl dentro <pre><code>, protetto
        self.assertIn('<pre><code id="voce-ma-band-src-text" class="language-powerlanguage">', page)
        self.assertIn('Plot1(Average(Close, Length), &quot;MA_Band_Signal&quot;);', page)
        self.assertIn("if Close &gt; Average(Close, Length) and Length &lt;&gt; 0 then", page)
        self.assertIn("MA_Band_Signal.pl · 8 righe", page)
        # ancore interne: fonte ↔ voci, dipendenze, sezioni
        self.assertIn(f'id="fonte-{PAPER_ID}"', page)
        self.assertIn(f'<a href="#fonte-{PAPER_ID}">Regole di trading semplici</a> (2001)', page)
        self.assertIn('<a href="#voce-ma-band-signal">MA_Band_Signal</a>', page)
        self.assertIn('<span class="muted">indicatore:</span> MA Band', page)
        for section in ("indicatori", "strategie", "funzioni", "fonti"):
            self.assertIn(f'<section class="group" id="{section}">', page)
            self.assertIn(f'href="#{section}"', page)
        self.assertIn("1 indicatore", page)
        self.assertIn("1 strategia", page)
        self.assertIn("1 fonte", page)
        # DOI e URL esterni in nuova scheda
        self.assertIn(f'<a href="https://doi.org/{DOI}" target="_blank" rel="noopener noreferrer">{DOI}</a>', page)
        self.assertIn("<em>Rivista di Finanza</em>, 47(5), pp. 1-20", page)
        self.assertIn("Mario Rossi, Luca Bianchi (2001)", page)
        # badge e metadati
        self.assertIn('<span class="badge type-indicator">indicatore</span>', page)
        self.assertIn('class="badge lang"', page)
        self.assertIn("PowerLanguage.NET", page)
        self.assertIn("MC 14", page)
        self.assertIn('class="badge status-tested"', page)
        self.assertIn("<dt>Usata da</dt>", page)

    def test_buttons_links_and_panels(self) -> None:
        page = self.page
        self.assertIn('data-copy="voce-ma-band-src-text"', page)
        self.assertIn(">Copia codice</button>", page)
        self.assertIn('data-toggle="voce-ma-band-src"', page)
        self.assertIn('data-label-open="Nascondi codice"', page)
        self.assertIn('data-toggle="voce-ma-band-doc"', page)
        self.assertIn('<a class="btn" href="indicators/ma-band/" title="Apri la cartella indicators/ma-band/">Apri cartella</a>', page)
        self.assertIn('<a class="btn" href="indicators/ma-band/MA_Band.pl">Apri .pl</a>', page)
        self.assertIn(f'<a class="btn" href="papers/{PAPER_ID}/notes.md">Note estese</a>', page)
        self.assertNotIn(">PDF</a>", page)
        self.assertNotIn("Apri .pla", page)
        self.assertIn("Copiato!", page)  # testo del riscontro nel JavaScript
        self.assertIn("execCommand('copy')", page)
        self.assertIn("navigator.clipboard", page)
        self.assertIn('<input type="search" id="search"', page)
        self.assertIn('class="chip" data-tag="moving-average"', page)
        self.assertIn('data-tags="moving-average band"', page)
        self.assertIn("prefers-color-scheme:dark", page)
        self.assertIn('<meta name="viewport"', page)
        self.assertIn('<html lang="it">', page)

    def test_optional_files_pdf_archive_and_backtests(self) -> None:
        write(self.root / "papers" / PAPER_ID / "paper.pdf", "%PDF-1.4 finto")
        write(self.root / "indicators" / "ma-band" / "MA_Band.pla", "binario finto")
        write(self.root / "indicators" / "ma-band" / "notes.md", "# Note\n")
        (self.root / "indicators" / "ma-band" / "backtests").mkdir()
        lib = bc.load_library(self.root)
        lib.papers[0].meta["pdf"] = "paper.pdf"
        lib.entries_of_type("indicator")[0].meta["archive_file"] = "MA_Band.pla"
        page = rh.render_page(lib)
        self.assertIn(f'<a class="btn" href="papers/{PAPER_ID}/paper.pdf">PDF</a>', page)
        self.assertIn('<a class="btn" href="indicators/ma-band/MA_Band.pla">Apri .pla</a>', page)
        self.assertIn('<a class="btn" href="indicators/ma-band/notes.md">Note estese</a>', page)
        self.assertIn('<a class="btn" href="indicators/ma-band/backtests/">Backtest</a>', page)

    def test_content_is_escaped_everywhere(self) -> None:
        page = self.page
        self.assertNotIn(SCRIPT, page)
        self.assertEqual(page.count("<script"), 1, "l'unico <script> è quello della pagina")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        # il nome con virgolette non rompe gli attributi
        self.assertIn('data-search="', page)
        self.assertNotIn('"beta"', page)
        self.assertIn("ma band &quot;beta&quot; &lt;b&gt;", page)  # testo di ricerca minuscolo e protetto

    def test_hidden_attribute_wins_over_display_rules(self) -> None:
        # `.card{display:flex}` e `.btn{display:inline-flex}` sono regole d'autore e batterebbero
        # lo stile predefinito del browser per [hidden]: senza questa regola le schede filtrate
        # e il pulsante «Azzera filtri» resterebbero visibili.
        page = self.page
        self.assertIn("[hidden]{display:none!important}", page)
        self.assertIn("<noscript><style>.panel[hidden]{display:block!important}", page)

    def test_readme_body_is_rendered_with_internal_anchor_and_heading_ids(self) -> None:
        page = self.page
        self.assertIn(f'<a href="#fonte-{PAPER_ID}">Rossi &amp; Bianchi (2001)</a>', page)
        self.assertIn('<h4 id="voce-ma-band-descrizione">Descrizione</h4>', page)
        self.assertIn("Testo con <strong>grassetto</strong> e <code>codice</code>.", page)
        self.assertNotIn("commento da togliere", page)
        self.assertIn('<a href="papers/' + PAPER_ID + '/notes.md">notes.md</a>', page)
        self.assertIn('<td class="ta-r">50</td>', page)
        # il titolo "# Nome" della scheda non è ripetuto dentro il pannello
        self.assertNotIn("<h3>MA_Band_Signal</h3>", page)
        self.assertIn('<a href="#voce-ma-band">ma-band</a>', page)  # link dalla fonte alla voce

    def test_deterministic_and_without_timestamp_unless_stamp(self) -> None:
        self.assertEqual(self.page, rh.render_page(self.lib))
        self.assertNotIn("Generato il", self.page)
        stamped = rh.render_page(self.lib, stamp="2026-10-06 12:00")
        self.assertIn('<p class="stamp">Generato il 2026-10-06 12:00.</p>', stamped)

    def test_link_prefix(self) -> None:
        page = rh.render_page(self.lib, link_prefix="../P/")
        self.assertIn('href="../P/indicators/ma-band/"', page)
        self.assertIn('href="../P/indicators/ma-band/MA_Band.pl"', page)
        self.assertIn(f'href="../P/papers/{PAPER_ID}/notes.md"', page)
        self.assertIn(f'href="#fonte-{PAPER_ID}"', page)  # le ancore interne restano tali
        self.assertEqual(rh.link_prefix_for(self.root, self.root), "")
        self.assertEqual(rh.link_prefix_for(self.root, self.root / "sub" / "dir"), "../../")
        self.assertEqual(rh.link_prefix_for(self.root / "indicators", self.root), "indicators/")

    def test_empty_library_renders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / bc.TEMPLATES_DIR).mkdir()
            lib = bc.load_library(root)
            page = rh.render_page(lib)
            self.assertIn("Nessuna voce.", page)
            self.assertIn("Nessuna fonte.", page)
            self.assertIn("Nessun tag.", page)
            self.assertIn("0 indicatori", page)

    def test_unreadable_source_is_reported_not_fatal(self) -> None:
        lib = self.library()
        entry = lib.entries_of_type("indicator")[0]
        (self.root / entry.dir_name / entry.folder / "MA_Band.pl").unlink()
        page = rh.render_page(lib)
        self.assertIn("Sorgente non disponibile", page)
        self.assertNotIn('data-copy="voce-ma-band-src-text"', page)
        self.assertIn('data-copy="voce-ma-crossover-src-text"', page)

    def test_anchor_id(self) -> None:
        self.assertEqual(rh.anchor_id("code", "bll1992-ma-band"), "voce-bll1992-ma-band")
        self.assertEqual(rh.anchor_id("paper", "1992-brock"), "fonte-1992-brock")
        self.assertEqual(rh.anchor_id("code", "a b/c"), "voce-a-b-c")


# ---------------------------------------------------------------------------
# Riga di comando
# ---------------------------------------------------------------------------


class TestMain(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_repo(self.root)

    def test_writes_html_and_refreshes_catalog(self) -> None:
        code, out, err = run_main(["--root", str(self.root)])
        self.assertEqual(code, 0, err)
        target = self.root / rh.CATALOG_HTML
        self.assertTrue(target.is_file())
        self.assertIn("MA Crossover", target.read_text(encoding="utf-8"))
        self.assertIn("Scritto", out)
        self.assertIn("3 voci di codice, 1 fonti", out)
        self.assertIn("Aggiornati CATALOG.md e catalog.json.", out)
        self.assertTrue((self.root / bc.CATALOG_MD).is_file())
        self.assertTrue((self.root / bc.CATALOG_JSON).is_file())
        self.assertEqual(bc.main(["--root", str(self.root), "--check", "--quiet"]), 0)
        # seconda esecuzione: catalogo già aggiornato, non viene riscritto
        code, out, _ = run_main(["--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertNotIn("Aggiornati", out)

    def test_no_catalog_flag(self) -> None:
        code, _, _ = run_main(["--root", str(self.root), "--no-catalog", "--quiet"])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / rh.CATALOG_HTML).is_file())
        self.assertFalse((self.root / bc.CATALOG_MD).exists())
        self.assertFalse((self.root / bc.CATALOG_JSON).exists())

    def test_out_elsewhere_adapts_relative_links(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            target = Path(other) / "sotto" / "pagina.html"
            target.parent.mkdir()
            code, out, err = run_main(["--root", str(self.root), "--out", str(target), "--quiet"])
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")
            page = target.read_text(encoding="utf-8")
            prefix = Path(os.path.relpath(self.root, target.parent)).as_posix() + "/"
            self.assertIn(f'href="{prefix}indicators/ma-band/MA_Band.pl"', page)
            self.assertFalse((self.root / rh.CATALOG_HTML).exists())

    def test_stamp_adds_date_and_default_is_deterministic(self) -> None:
        code, _, _ = run_main(["--root", str(self.root), "--quiet"])
        first = (self.root / rh.CATALOG_HTML).read_text(encoding="utf-8")
        code, _, _ = run_main(["--root", str(self.root), "--quiet"])
        self.assertEqual(code, 0)
        self.assertEqual(first, (self.root / rh.CATALOG_HTML).read_text(encoding="utf-8"))
        self.assertNotIn("Generato il", first)
        code, _, _ = run_main(["--root", str(self.root), "--quiet", "--stamp"])
        self.assertEqual(code, 0)
        self.assertRegex((self.root / rh.CATALOG_HTML).read_text(encoding="utf-8"), r"Generato il \d{4}-\d{2}-\d{2} \d{2}:\d{2}\.")

    def test_validation_errors_exit_1_and_write_nothing(self) -> None:
        readme = self.root / "indicators" / "ma-band" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("depends_on: [ma-band-signal]", "depends_on: [inesistente]"), encoding="utf-8")
        code, out, err = run_main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("ERRORE indicators/ma-band/README.md", err)
        self.assertIn("Validazione fallita: 1 errori. Pagina non generata.", err)
        self.assertFalse((self.root / rh.CATALOG_HTML).exists())
        self.assertFalse((self.root / bc.CATALOG_MD).exists())
        self.assertEqual(out, "")

    def test_quiet_hides_warnings_but_not_errors(self) -> None:
        add_paper(self.root, "1999-verdi-filtri", implementations=())  # fonte senza implementazioni → AVVISO
        code, _, err = run_main(["--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("AVVISO papers/1999-verdi-filtri/README.md", err)
        code, out, err = run_main(["--root", str(self.root), "--quiet"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(out, "")

    def test_open_uses_webbrowser(self) -> None:
        calls: list[str] = []
        original = rh.webbrowser.open
        rh.webbrowser.open = lambda url, *a, **k: calls.append(url) or True  # type: ignore[assignment]
        try:
            code, out, err = run_main(["--root", str(self.root), "--open"])
        finally:
            rh.webbrowser.open = original  # type: ignore[assignment]
        self.assertEqual(code, 0, err)
        self.assertEqual(calls, [(self.root / rh.CATALOG_HTML).resolve().as_uri()])
        self.assertIn("Pagina aperta nel browser predefinito.", out)

    def test_open_failure_prints_hint(self) -> None:
        original = rh.webbrowser.open
        rh.webbrowser.open = lambda url, *a, **k: False  # type: ignore[assignment]
        try:
            code, _, err = run_main(["--root", str(self.root), "--open", "--quiet"])
        finally:
            rh.webbrowser.open = original  # type: ignore[assignment]
        self.assertEqual(code, 0)
        self.assertIn("Impossibile aprire il browser automaticamente", err)
        self.assertIn(str(self.root / rh.CATALOG_HTML), err)

    def test_root_problems(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            code, _, err = run_main(["--root", empty])
            self.assertEqual(code, 1)
            self.assertIn("non sembra la radice della libreria", err)
        code, _, err = run_main(["--root", str(self.root / "non-esiste")])
        self.assertEqual(code, 1)
        self.assertIn("cartella radice non trovata", err)

    def test_unwritable_output_is_a_clear_error(self) -> None:
        target = self.root / "cartella"
        target.mkdir()
        code, _, err = run_main(["--root", str(self.root), "--out", str(target), "--quiet"])
        self.assertEqual(code, 1)
        self.assertIn("impossibile scrivere il file", err)

    def test_help_is_in_italian(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            rh.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        text = out.getvalue()
        for fragment in ("catalog.html", "--open", "--out", "--quiet", "--stamp", "--no-catalog", "Copia codice", "browser predefinito", "deterministico"):
            self.assertIn(fragment, text)


# ---------------------------------------------------------------------------
# Libreria reale del repository (copiata in una cartella temporanea)
# ---------------------------------------------------------------------------


class TestRealRepository(unittest.TestCase):
    def test_render_real_library_copy(self) -> None:
        if not any((REPO_ROOT / d).is_dir() for d in bc.LIBRARY_DIRS):
            self.skipTest("libreria reale non trovata accanto a tools/")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "P"
            root.mkdir()
            for name in bc.LIBRARY_DIRS:
                if (REPO_ROOT / name).is_dir():
                    shutil.copytree(REPO_ROOT / name, root / name)
            out = Path(tmp) / "out" / "catalog.html"
            out.parent.mkdir()
            code, stdout, stderr = run_main(["--root", str(root), "--out", str(out), "--no-catalog"])
            self.assertEqual(code, 0, stderr)
            self.assertNotIn("ERRORE", stderr)
            page = out.read_text(encoding="utf-8")
            lib = bc.load_library(root)
            self.assertEqual(bc.validate(lib), [])
            for entry in (*lib.entries, *lib.papers):
                self.assertIn(f'id="{rh.anchor_id(entry.kind, entry.folder)}"', page)
                self.assertIn(rh._esc(entry.display_name), page)
            for entry in lib.entries:
                source = (root / entry.dir_name / entry.folder / str(entry.meta["source_file"])).read_text(encoding="utf-8")
                normalized = source.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
                self.assertIn(rh._esc(normalized), page, f"sorgente di {entry.folder} non presente integralmente nel <pre>")
            for paper in lib.papers:
                doi = paper.meta.get("doi")
                if doi:
                    self.assertIn(f'href="https://doi.org/{rh._esc(doi)}"', page)
            self.assertNotIn("<script>alert", page)
            self.assertEqual(page.count("<script"), 1)
            self.assertFalse((root / rh.CATALOG_HTML).exists())
            # deterministico anche sulla libreria reale
            code, _, _ = run_main(["--root", str(root), "--out", str(out.with_name("bis.html")), "--no-catalog", "--quiet"])
            self.assertEqual(code, 0)
            self.assertEqual(page, out.with_name("bis.html").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Icona di Windows (facoltativa: il file è prodotto da tools/windows/make_icon.py)
# ---------------------------------------------------------------------------


class TestWindowsIcon(unittest.TestCase):
    ICO_PATH = TOOLS_DIR / "windows" / "libreria.ico"
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

    def test_icon_is_a_valid_ico_with_png_entries(self) -> None:
        if not self.ICO_PATH.is_file():
            self.skipTest("tools/windows/libreria.ico non presente")
        data = self.ICO_PATH.read_bytes()
        self.assertGreaterEqual(len(data), 6 + 16, "intestazione ICO troppo corta")
        reserved, image_type, count = struct.unpack_from("<HHH", data, 0)
        self.assertEqual(reserved, 0)
        self.assertEqual(image_type, 1, "tipo 1 = icona (2 = cursore)")
        self.assertGreaterEqual(count, 1)
        self.assertGreaterEqual(len(data), 6 + 16 * count)
        png_entries = 0
        sizes: set[int] = set()
        for index in range(count):
            width, height, _colors, _reserved, _planes, _bpp, size, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * index)
            self.assertLessEqual(offset + size, len(data), f"voce {index} oltre la fine del file")
            blob = data[offset : offset + size]
            if blob.startswith(self.PNG_SIGNATURE):
                png_entries += 1
                self.assertEqual(blob[12:16], b"IHDR")
                png_width, png_height = struct.unpack_from(">II", blob, 16)
                self.assertEqual(png_width, width or 256)
                self.assertEqual(png_height, height or 256)
                sizes.add(png_width)
        self.assertGreaterEqual(png_entries, 1, "nessuna voce PNG nell'icona")
        if png_entries >= 4:
            self.assertTrue({16, 32, 48, 256} <= sizes, f"attese le misure 16/32/48/256, trovate {sorted(sizes)}")


if __name__ == "__main__":
    unittest.main()
