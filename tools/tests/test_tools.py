"""Test unitari (solo libreria standard) per ``tools/build_catalog.py`` e ``tools/new_entry.py``.

I test non dipendono dal contenuto reale di ``templates/`` né dalle voci del
repository: costruiscono cartelle temporanee con template e voci sintetiche.

Esecuzione dalla radice del repository::

    python -m unittest discover -s tools/tests -v
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_catalog as bc  # noqa: E402
import new_entry as ne  # noqa: E402

PAPER_ID = "2001-rossi-bianchi-regole-trading-semplici"  # "di" è una parola vuota
PAPER_ID_2 = "1999-verdi-filtri-volatilita"
FIXED_DATE = "2024-01-15"


# ---------------------------------------------------------------------------
# Utilità per costruire repository sintetici
# ---------------------------------------------------------------------------


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def yaml_value(value: object) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


def front_matter(fields: dict[str, object], body: str = "") -> str:
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


def paper_fields(pid: str = PAPER_ID, **overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "type": "paper",
        "id": pid,
        "title": "Regole di trading semplici",
        "authors": ["Mario Rossi", "Luca Bianchi"],
        "year": 2001,
        "status": "extracted",
        "tags": ["technical-analysis"],
        "added": FIXED_DATE,
    }
    fields.update(overrides)
    return fields


def code_body(name: str, version: str = "1.0.0") -> str:
    return f"# {name}\n\n## Descrizione\n\nTesto.\n\n## Changelog\n\n- {FIXED_DATE} — {version}: prima bozza.\n"


def source_text(name: str, version: str = "1.0.0") -> str:
    return (
        f"{{\n  Nome:        {name}\n  Versione:    {version}\n  Data:        {FIXED_DATE}\n}}\n\n"
        f'inputs: Length(20);\nPlot1(Average(Close, Length), "{name}");\n'
    )


def add_code_entry(root: Path, entry_type: str, slug: str, name: str, source_file: str, **overrides: object) -> Path:
    folder = root / bc.TYPE_DIRS[entry_type] / slug
    version = str(overrides.get("version", "1.0.0")).strip("'\"")
    write(folder / "README.md", front_matter(code_fields(entry_type, name, slug, source_file, **overrides), code_body(name, version)))
    write(folder / source_file, source_text(name, version))
    return folder


def implementations_body(*slugs: str) -> str:
    lines = ["# Titolo", "", "## Sintesi", "", "Testo.", "", bc.IMPLEMENTATIONS_HEADING, ""]
    lines += [f"- [{slug}](../../indicators/{slug}/README.md)" for slug in slugs]
    lines += ["", "## Riferimenti correlati", "", "- nessuno"]
    return "\n".join(lines) + "\n"


def add_paper(root: Path, pid: str = PAPER_ID, implementations: tuple[str, ...] | None = None, **overrides: object) -> Path:
    folder = root / bc.PAPERS_DIR / pid
    body = implementations_body(*implementations) if implementations is not None else "# Titolo"
    write(folder / "README.md", front_matter(paper_fields(pid, **overrides), body))
    return folder


def make_valid_repo(root: Path) -> None:
    """Una fonte, una funzione, un indicatore e una strategia, tutti coerenti (nessun avviso)."""
    add_paper(root, implementations=("ma-band-signal", "ma-band", "ma-crossover"))
    add_code_entry(root, "function", "ma-band-signal", "MA_Band_Signal", "MA_Band_Signal.pl", tags=["signal"])
    add_code_entry(
        root, "indicator", "ma-band", "MA Band", "MA_Band.pl",
        depends_on=["ma-band-signal"], summary="Bande attorno alla media mobile.",
    )
    add_code_entry(
        root, "strategy", "ma-crossover", "MA Crossover", "MA_Crossover.pl",
        depends_on=["ma-band-signal"], tags=["trend-following", "moving-average"],
    )


class TempRepoTestCase(unittest.TestCase):
    """Caso di test con una radice temporanea pulita per ogni test."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def errors(self) -> list[str]:
        return bc.validate(bc.load_library(self.root))

    def assertAnyError(self, errors: list[str], *fragments: str) -> None:
        matching = [e for e in errors if all(f in e for f in fragments)]
        self.assertTrue(matching, f"nessun errore contiene {fragments!r}; errori: {errors!r}")

    def rewrite_readme(self, rel_dir: str, fields: dict[str, object], drop: tuple[str, ...] = ()) -> None:
        folder = self.root / rel_dir
        text = (folder / "README.md").read_text(encoding="utf-8")
        _yaml, body = bc.split_front_matter(text)
        current = bc.parse_front_matter(text)
        current.update(fields)
        for key in drop:
            current.pop(key, None)
        write(folder / "README.md", front_matter(current, body.strip("\n")))

    def warnings(self) -> list[str]:
        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])
        return bc.collect_warnings(lib)

    def assertAnyWarning(self, warnings: list[str], *fragments: str) -> None:
        matching = [w for w in warnings if all(f in w for f in fragments)]
        self.assertTrue(matching, f"nessun avviso contiene {fragments!r}; avvisi: {warnings!r}")


def run_main(func, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = func(argv)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Parser del front matter
# ---------------------------------------------------------------------------


class TestFrontMatterParser(unittest.TestCase):
    def test_scalars_quotes_numbers_and_booleans(self) -> None:
        text = (
            "---\n"
            "name: BLL1992 MA Band\n"
            "single: 'con ''apice'' interno'\n"
            'double: "virgolette \\"interne\\" ok"\n'
            "count: 47\n"
            "band: 0.01\n"
            "negative: -3\n"
            "flag_on: true\n"
            "flag_off: False\n"
            "version: 1.0.0\n"
            "created: 2026-10-06\n"
            'mc: "14"\n'
            "doi: 10.1111/j.1540-6261.1992.tb04681.x\n"
            "pages: 1731-1764\n"
            "url: https://doi.org/10.1111/j.1540-6261.1992.tb04681.x\n"
            "title: Regole: con due punti nel valore\n"
            "---\n"
            "# Corpo\n"
        )
        data = bc.parse_front_matter(text)
        self.assertEqual(data["name"], "BLL1992 MA Band")
        self.assertEqual(data["single"], "con 'apice' interno")
        self.assertEqual(data["double"], 'virgolette "interne" ok')
        self.assertEqual(data["count"], 47)
        self.assertIsInstance(data["count"], int)
        self.assertEqual(data["band"], 0.01)
        self.assertIsInstance(data["band"], float)
        self.assertEqual(data["negative"], -3)
        self.assertIs(data["flag_on"], True)
        self.assertIs(data["flag_off"], False)
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["created"], "2026-10-06")
        self.assertEqual(data["mc"], "14")
        self.assertEqual(data["doi"], "10.1111/j.1540-6261.1992.tb04681.x")
        self.assertEqual(data["pages"], "1731-1764")
        self.assertEqual(data["url"], "https://doi.org/10.1111/j.1540-6261.1992.tb04681.x")
        self.assertEqual(data["title"], "Regole: con due punti nel valore")

    def test_flow_lists(self) -> None:
        text = (
            "---\n"
            'tags: [a, b, "c d"]\n'
            "empty: []\n"
            "spaced: [  ]\n"
            "numbers: [1, 2, 3]\n"
            "quoted_comma: ['x, y', z]\n"
            "trailing: [a, b, ]\n"
            "---\n"
        )
        data = bc.parse_front_matter(text)
        self.assertEqual(data["tags"], ["a", "b", "c d"])
        self.assertEqual(data["empty"], [])
        self.assertEqual(data["spaced"], [])
        self.assertEqual(data["numbers"], [1, 2, 3])
        self.assertEqual(data["quoted_comma"], ["x, y", "z"])
        self.assertEqual(data["trailing"], ["a", "b"])

    def test_block_lists(self) -> None:
        text = (
            "---\n"
            "authors:\n"
            "  - William Brock\n"
            "  - Josef Lakonishok\n"
            "- Blake LeBaron\n"
            "tags:\n"
            "  - 'quoted item'\n"
            "  - 7\n"
            "year: 1992\n"
            "---\n"
        )
        data = bc.parse_front_matter(text)
        self.assertEqual(data["authors"], ["William Brock", "Josef Lakonishok", "Blake LeBaron"])
        self.assertEqual(data["tags"], ["quoted item", 7])
        self.assertEqual(data["year"], 1992)

    def test_comments(self) -> None:
        text = (
            "---\n"
            "# commento su una riga intera\n"
            "name: Studio # commento in linea\n"
            "   # commento indentato\n"
            "url: https://example.org/pagina#frammento\n"
            "tag: c#\n"
            'quoted: "a # non è un commento"\n'
            "tags: [a, b] # commento dopo la lista\n"
            "items:\n"
            "  - primo # commento\n"
            "  - secondo\n"
            "only_comment: # solo commento\n"
            "# archive_file: Nome.pla\n"
            "---\n"
        )
        data = bc.parse_front_matter(text)
        self.assertEqual(data["name"], "Studio")
        self.assertEqual(data["url"], "https://example.org/pagina#frammento")
        self.assertEqual(data["tag"], "c#")
        self.assertEqual(data["quoted"], "a # non è un commento")
        self.assertEqual(data["tags"], ["a", "b"])
        self.assertEqual(data["items"], ["primo", "secondo"])
        self.assertIsNone(data["only_comment"])
        self.assertNotIn("archive_file", data)

    def test_empty_values_are_none(self) -> None:
        data = bc.parse_front_matter("---\nsummary:\ndoi: \nnullo: null\ntilde: ~\n---\n")
        self.assertIsNone(data["summary"])
        self.assertIsNone(data["doi"])
        self.assertIsNone(data["nullo"])
        self.assertIsNone(data["tilde"])

    def test_crlf_and_bom(self) -> None:
        text = "﻿---\r\nname: Studio\r\ntags: [a, b]\r\nitems:\r\n  - uno\r\n  - due\r\n---\r\n\r\n# Corpo\r\n"
        data = bc.parse_front_matter(text)
        self.assertEqual(data, {"name": "Studio", "tags": ["a", "b"], "items": ["uno", "due"]})

    def test_body_is_ignored_and_split(self) -> None:
        yaml_text, body = bc.split_front_matter("---\nname: X\n---\n# Titolo\n\nname: non è metadato\n")
        self.assertEqual(yaml_text, "name: X")
        self.assertIn("# Titolo", body)
        self.assertEqual(bc.parse_front_matter("---\nname: X\n---\nname: Y\n"), {"name": "X"})

    def test_errors(self) -> None:
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("# Nessun front matter\nname: X\n")
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("---\nname: X\n")  # non chiuso
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("---\nouter:\n  inner: 1\n---\n")  # mappa annidata
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("---\nname: A\nname: B\n---\n")  # chiave duplicata
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("---\n- orfano\n---\n")  # elemento senza chiave
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("---\nriga senza due punti\n---\n")
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter("---\ntags: [a, [b, c]]\n---\n")  # lista annidata
        with self.assertRaises(bc.FrontMatterError):
            bc.parse_front_matter('---\nname: "non chiusa\n---\n')

    def test_parse_scalar_directly(self) -> None:
        self.assertEqual(bc.parse_scalar(" 12 "), 12)
        self.assertEqual(bc.parse_scalar("1e3"), 1000.0)
        self.assertEqual(bc.parse_scalar("TRUE"), True)
        self.assertEqual(bc.parse_scalar("'a''b'"), "a'b")
        self.assertEqual(bc.parse_scalar('"tab\\tok"'), "tab\tok")
        self.assertEqual(bc.parse_flow_list('["a,b", c]'), ["a,b", "c"])


# ---------------------------------------------------------------------------
# Caricamento e validazione
# ---------------------------------------------------------------------------


class TestValidation(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_valid_repo(self.root)

    def test_valid_repo_has_no_errors(self) -> None:
        lib = bc.load_library(self.root)
        self.assertEqual(self.errors(), [])
        self.assertEqual([e.folder for e in lib.entries], ["ma-band", "ma-crossover", "ma-band-signal"])
        self.assertEqual([p.folder for p in lib.papers], [PAPER_ID])
        self.assertEqual(lib.entries[0].path, "indicators/ma-band/README.md")

    def test_templates_dir_is_ignored(self) -> None:
        write(self.root / "templates" / "indicator" / "README.md", "---\ntype: indicator\n---\n")
        self.assertEqual(self.errors(), [])

    def test_missing_required_field(self) -> None:
        self.rewrite_readme("indicators/ma-band", {}, drop=("version",))
        errors = self.errors()
        self.assertAnyError(errors, "ERRORE indicators/ma-band/README.md:", "campo obbligatorio", "'version'")

    def test_empty_required_field(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"name": ""})
        self.assertAnyError(self.errors(), "campo obbligatorio", "'name'")

    def test_bad_slug(self) -> None:
        folder = self.root / "indicators" / "ma-band"
        self.rewrite_readme("indicators/ma-band", {"slug": "MA_Band"})
        shutil.move(str(folder), str(self.root / "indicators" / "MA_Band"))
        errors = self.errors()
        self.assertAnyError(errors, "indicators/MA_Band/README.md", "slug 'MA_Band' non valido")

    def test_slug_differs_from_folder(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"slug": "altro-slug"})
        self.assertAnyError(self.errors(), "slug 'altro-slug' diverso dal nome della cartella 'ma-band'")

    def test_type_mismatch_with_folder(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"type": "strategy"})
        self.assertAnyError(self.errors(), "type 'strategy' non coerente con la cartella 'indicators/'")
        self.rewrite_readme("indicators/ma-band", {"type": "sconosciuto"})
        self.assertAnyError(self.errors(), "type 'sconosciuto' non valido")

    def test_unknown_paper_id(self) -> None:
        self.rewrite_readme("strategies/ma-crossover", {"papers": [PAPER_ID, "2020-nessuno-titolo"]})
        self.assertAnyError(self.errors(), "strategies/ma-crossover/README.md", "papers:", "'2020-nessuno-titolo' non trovata in papers/")

    def test_unknown_depends_on(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"depends_on": ["funzione-inesistente"]})
        self.assertAnyError(self.errors(), "depends_on:", "'funzione-inesistente' non trovata in functions/")

    def test_missing_source_file(self) -> None:
        (self.root / "indicators" / "ma-band" / "MA_Band.pl").unlink()
        self.assertAnyError(self.errors(), "source_file:", "'MA_Band.pl' non trovato")

    def test_missing_archive_and_pdf_files(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"archive_file": "MA_Band.pla"})
        self.rewrite_readme(f"papers/{PAPER_ID}", {"pdf": "paper.pdf"})
        errors = self.errors()
        self.assertAnyError(errors, "archive_file:", "'MA_Band.pla' non trovato")
        self.assertAnyError(errors, f"papers/{PAPER_ID}/README.md", "pdf:", "'paper.pdf' non trovato")
        write(self.root / "indicators" / "ma-band" / "MA_Band.pla", "bin")
        write(self.root / "papers" / PAPER_ID / "paper.pdf", "%PDF")
        self.assertEqual(self.errors(), [])

    def test_bad_status(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"status": "finito"})
        self.assertAnyError(self.errors(), "status 'finito' non valido", "draft, tested, stable, deprecated")
        self.rewrite_readme(f"papers/{PAPER_ID}", {"status": "letto"})
        self.assertAnyError(self.errors(), "status 'letto' non valido", "to-read, reading, read, extracted")

    def test_bad_version(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"version": "v1"})
        self.assertAnyError(self.errors(), "version 'v1' non valida")

    def test_bad_language(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"language": "EasyLanguage"})
        self.assertAnyError(self.errors(), "language 'EasyLanguage' non valido")

    def test_bad_date(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"created": "15/01/2024"})
        self.assertAnyError(self.errors(), "campo 'created' deve essere una data ISO")
        self.rewrite_readme("indicators/ma-band", {"created": FIXED_DATE, "updated": "2024-13-45"})
        self.assertAnyError(self.errors(), "campo 'updated' deve essere una data ISO")
        self.rewrite_readme(f"papers/{PAPER_ID}", {"added": "ieri"})
        self.assertAnyError(self.errors(), "campo 'added' deve essere una data ISO")

    def test_duplicate_slug(self) -> None:
        add_code_entry(self.root, "strategy", "ma-band", "MA Band bis", "MA_Band_bis.pl")
        errors = self.errors()
        self.assertAnyError(errors, "indicators/ma-band/README.md", "slug 'ma-band' duplicato", "strategies/ma-band/README.md")
        self.assertAnyError(errors, "strategies/ma-band/README.md", "slug 'ma-band' duplicato", "indicators/ma-band/README.md")

    def test_duplicate_paper_id(self) -> None:
        add_paper(self.root, PAPER_ID_2, title="Filtri di volatilità", authors=["Anna Verdi"], year=1999)
        self.rewrite_readme(f"papers/{PAPER_ID_2}", {"id": PAPER_ID})
        errors = self.errors()
        self.assertAnyError(errors, f"id '{PAPER_ID}' duplicato")
        self.assertAnyError(errors, f"id '{PAPER_ID}' diverso dal nome della cartella '{PAPER_ID_2}'")

    def test_paper_errors(self) -> None:
        self.rewrite_readme(f"papers/{PAPER_ID}", {"year": "millenovecento", "type": "rivista", "authors": []}, drop=("title",))
        errors = self.errors()
        self.assertAnyError(errors, "year 'millenovecento' non valido")
        self.assertAnyError(errors, "type 'rivista' non valido")
        self.assertAnyError(errors, "'authors' non può essere una lista vuota")
        self.assertAnyError(errors, "campo obbligatorio", "'title'")

    def test_list_fields_must_be_lists(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"tags": "moving-average"})
        self.assertAnyError(self.errors(), "campo 'tags' deve essere una lista")

    def test_missing_readme_and_bad_front_matter(self) -> None:
        (self.root / "functions" / "vuota").mkdir()
        write(self.root / "strategies" / "rotta" / "README.md", "# Senza front matter\n")
        errors = self.errors()
        self.assertAnyError(errors, "ERRORE functions/vuota:", "manca il file README.md")
        self.assertAnyError(errors, "ERRORE strategies/rotta/README.md:", "front matter non valido")

    def test_all_errors_are_collected_and_prefixed(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"status": "x", "version": "y", "created": "z"})
        errors = self.errors()
        self.assertGreaterEqual(len(errors), 3)
        for error in errors:
            self.assertTrue(error.startswith("ERRORE indicators/ma-band/README.md: "), error)

    def test_valid_repo_has_no_warnings(self) -> None:
        self.assertEqual(self.warnings(), [])

    def test_warnings(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"papers": []})
        add_paper(self.root, PAPER_ID_2, title="Filtri di volatilità", authors=["Anna Verdi"], year=1999)
        warnings = self.warnings()
        self.assertIn("AVVISO indicators/ma-band/README.md: voce senza fonte (papers: [])", warnings)
        self.assertIn(f"AVVISO papers/{PAPER_ID_2}/README.md: fonte senza implementazioni in questa libreria", warnings)

    def test_function_source_file_must_equal_name_is_an_error(self) -> None:
        self.rewrite_readme("functions/ma-band-signal", {"name": "Nome Diverso"})
        errors = self.errors()
        self.assertIn(
            "ERRORE functions/ma-band-signal/README.md: per le funzioni source_file deve coincidere con name "
            "(trovato 'MA_Band_Signal.pl' per la funzione 'Nome Diverso': MultiCharts richiede nome funzione = nome studio)",
            errors,
        )
        self.assertFalse(any("nome del file sorgente" in w for w in bc.collect_warnings(bc.load_library(self.root))))
        # per indicatori e strategie il nome del file è libero
        self.rewrite_readme("functions/ma-band-signal", {"name": "MA_Band_Signal"})
        self.rewrite_readme("indicators/ma-band", {"name": "Nome Diverso"})
        self.assertEqual(self.errors(), [])

    def test_semver_is_strict(self) -> None:
        for version in ("1.0.0-beta.1", "1.0.0+build.5", "1.0.0-rc1", "01.0", "1.0"):
            self.rewrite_readme("indicators/ma-band", {"version": f"'{version}'"})
            self.assertAnyError(self.errors(), f"version '{version}' non valida", "semver MAJOR.MINOR.PATCH")
        self.assertIsNotNone(bc.SEMVER_RE.match("10.20.30"))
        self.assertIsNone(bc.SEMVER_RE.match("1.0.0-beta"))

    def test_multicharts_version_warning_for_tested_and_stable(self) -> None:
        for status in ("tested", "stable"):
            self.rewrite_readme("indicators/ma-band", {"status": status}, drop=("multicharts_version",))
            self.assertIn(
                f"AVVISO indicators/ma-band/README.md: stato '{status}' senza 'multicharts_version' "
                "(indicare la versione di MultiCharts su cui il codice è stato compilato/testato)",
                self.warnings(),
            )
            self.rewrite_readme("indicators/ma-band", {"status": status, "multicharts_version": '"14"'})
            self.assertFalse(any("multicharts_version" in w for w in self.warnings()))
        self.rewrite_readme("indicators/ma-band", {"status": "draft"}, drop=("multicharts_version",))
        self.assertFalse(any("multicharts_version" in w for w in self.warnings()))

    def test_version_drift_warnings(self) -> None:
        folder = self.root / "indicators" / "ma-band"
        # intestazione del sorgente diversa
        write(folder / "MA_Band.pl", source_text("MA Band", "0.9.0"))
        self.assertIn(
            "AVVISO indicators/ma-band/README.md: version '1.0.0' diversa da quella nell'intestazione di MA_Band.pl ('0.9.0')",
            self.warnings(),
        )
        # prima riga del Changelog diversa
        write(folder / "MA_Band.pl", source_text("MA Band", "1.0.0"))
        write(folder / "README.md", front_matter(code_fields("indicator", "MA Band", "ma-band", "MA_Band.pl", depends_on=["ma-band-signal"]), code_body("MA Band", "1.1.0")))
        self.assertIn(
            "AVVISO indicators/ma-band/README.md: version '1.0.0' diversa dalla prima riga del Changelog ('1.1.0')",
            self.warnings(),
        )
        # sorgente senza intestazione, Changelog assente o senza righe nel formato: nessun avviso
        write(folder / "MA_Band.pl", "inputs: Length(20);\nPlot1(Close, \"x\");\n")
        write(folder / "README.md", front_matter(code_fields("indicator", "MA Band", "ma-band", "MA_Band.pl", depends_on=["ma-band-signal"]), "# MA Band\n\n## Changelog\n\n- prima bozza senza versione\n"))
        self.assertFalse(any("version '1.0.0' diversa" in w for w in self.warnings()))
        # sorgente mancante: nessun crash, l'errore è della validazione
        (folder / "MA_Band.pl").unlink()
        lib = bc.load_library(self.root)
        self.assertAnyError(bc.validate(lib), "source_file:", "'MA_Band.pl' non trovato")
        self.assertFalse(any("intestazione" in w for w in bc.collect_warnings(lib)))
        # funzioni pure
        self.assertEqual(bc.source_header_version("{\n Nome: X\n Versione: 2.3.4\n}\ncodice"), "2.3.4")
        self.assertIsNone(bc.source_header_version("codice senza intestazione { Versione: 1.0.0 }"))
        self.assertIsNone(bc.source_header_version("{ Nome: X }"))
        self.assertEqual(bc.changelog_version("## Changelog\n\n- 2024-01-15 — 1.2.3: note\n- 2024-01-01 — 1.0.0: prima"), "1.2.3")
        self.assertIsNone(bc.changelog_version("## Changelog\n\n- senza data\n\n## Altro\n\n- 2024-01-15 — 9.9.9: fuori sezione"))
        self.assertIsNone(bc.changelog_version("# Solo titolo"))

    def test_unknown_field_warning(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"sumary": "refuso", "multicharts_version": '"14"', "markets": ["azioni"]})
        self.rewrite_readme(f"papers/{PAPER_ID}", {"jurnal": "refuso", "journal": "Rivista", "doi": "10.1/x"})
        warnings = self.warnings()
        self.assertIn(
            "AVVISO indicators/ma-band/README.md: campo 'sumary' non previsto dallo schema (refuso?); "
            "i campi ammessi sono in docs/CONVENZIONI.md",
            warnings,
        )
        self.assertIn(
            f"AVVISO papers/{PAPER_ID}/README.md: campo 'jurnal' non previsto dallo schema (refuso?); "
            "i campi ammessi sono in docs/CONVENZIONI.md",
            warnings,
        )
        self.assertEqual(len([w for w in warnings if "non previsto dallo schema" in w]), 2)
        for name in bc.OPTIONAL_CODE_FIELDS + bc.REQUIRED_CODE_FIELDS + bc.OPTIONAL_PAPER_FIELDS + bc.REQUIRED_PAPER_FIELDS:
            self.assertNotIn(f"'{name}'", " ".join(w for w in warnings if "non previsto" in w))
        self.assertEqual(bc.OPTIONAL_CODE_FIELDS, ("archive_file", "multicharts_version", "markets", "timeframes", "author", "summary", "superseded_by"))
        self.assertEqual(bc.OPTIONAL_PAPER_FIELDS, ("journal", "volume", "issue", "pages", "publisher", "doi", "url", "pdf", "isbn", "summary"))
        # i campi sconosciuti restano in catalog.json
        data = json.loads(bc.render_catalog_json(bc.load_library(self.root)))
        self.assertEqual(next(e for e in data["entries"] if e["slug"] == "ma-band")["sumary"], "refuso")

    def test_paper_implementations_section_warning(self) -> None:
        add_paper(self.root, implementations=("ma-band", "ma-crossover"))  # manca ma-band-signal
        self.assertEqual(
            self.warnings(),
            [f"AVVISO papers/{PAPER_ID}/README.md: la voce 'ma-band-signal' cita questa fonte ma non è elencata in "
             "'## Implementazioni in questa libreria'"],
        )
        add_paper(self.root)  # sezione assente: tutte le voci derivate sono segnalate, in ordine (tipo, slug)
        warnings = self.warnings()
        self.assertEqual(
            [w.split("la voce '")[1].split("'")[0] for w in warnings if "non è elencata" in w],
            ["ma-band", "ma-crossover", "ma-band-signal"],
        )
        self.assertEqual(bc.implementations_section("# T\n\n## Implementazioni in questa libreria\n\n- [x](../../a/x/README.md)\n\n## Dopo\n\n- [y](../../a/y/README.md)\n"), "\n- [x](../../a/x/README.md)\n")
        self.assertEqual(bc.implementations_section("# T\n\n## Sintesi\n"), "")

    def test_superseded_by(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"superseded_by": "ma-band-signal"})
        self.assertEqual(self.errors(), [])
        self.rewrite_readme("indicators/ma-band", {"superseded_by": "ma-crossover"})  # anche una strategia va bene
        self.assertEqual(self.errors(), [])
        self.rewrite_readme("indicators/ma-band", {"superseded_by": "inesistente"})
        self.assertIn(
            "ERRORE indicators/ma-band/README.md: superseded_by: voce 'inesistente' non trovata in indicators/, strategies/ o functions/",
            self.errors(),
        )
        self.rewrite_readme("indicators/ma-band", {"superseded_by": "ma-band"})
        self.assertIn("ERRORE indicators/ma-band/README.md: superseded_by: la voce 'ma-band' non può sostituire se stessa", self.errors())
        self.rewrite_readme("indicators/ma-band", {"superseded_by": [PAPER_ID]})
        self.assertAnyError(self.errors(), "campo 'superseded_by' deve essere lo slug")
        # deprecated senza superseded_by: avviso
        self.rewrite_readme("indicators/ma-band", {"status": "deprecated"}, drop=("superseded_by",))
        self.assertIn(
            "AVVISO indicators/ma-band/README.md: stato 'deprecated' senza 'superseded_by' (indicare lo slug della voce che la sostituisce)",
            self.warnings(),
        )
        self.rewrite_readme("indicators/ma-band", {"status": "deprecated", "superseded_by": "ma-crossover"})
        self.assertEqual(self.warnings(), [])
        data = json.loads(bc.render_catalog_json(bc.load_library(self.root)))
        self.assertEqual(next(e for e in data["entries"] if e["slug"] == "ma-band")["superseded_by"], "ma-crossover")


# ---------------------------------------------------------------------------
# Rendering del catalogo
# ---------------------------------------------------------------------------


class TestCatalogRendering(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_valid_repo(self.root)
        add_paper(self.root, PAPER_ID_2, title="Filtri di volatilità | con pipe", authors=["Anna Verdi"], year=1999, status="read")
        add_code_entry(self.root, "indicator", "aaa-primo", "AAA Primo", "AAA_Primo.pl", papers=[])

    def test_markdown_content(self) -> None:
        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])
        md = bc.render_catalog_md(lib)
        self.assertTrue(md.startswith("# Catalogo della libreria\n"))
        self.assertIn("tools/build_catalog.py", md)
        self.assertIn("python tools/build_catalog.py", md)
        for heading in ("## Riepilogo", "## Indicatori", "## Strategie", "## Funzioni", "## Fonti",
                        "## Mappa fonte → implementazioni", "## Indice per tag", "## Voci senza fonte"):
            self.assertIn(f"\n{heading}\n", md)
        self.assertIn("| Nome | Slug | Versione | Stato | MC | Fonti | Dipendenze | Tag |", md)
        self.assertIn("|---|---|---|---|---|---|---|---|", md)
        self.assertIn("| Anno | Titolo | Autori | Tipo | Stato | Implementazioni |", md)
        self.assertIn("[MA Band](indicators/ma-band/README.md)", md)
        self.assertIn("[ma-band-signal](functions/ma-band-signal/README.md)", md)
        self.assertIn(f"[{PAPER_ID}](papers/{PAPER_ID}/README.md)", md)
        self.assertIn("| Indicatori | 2 |", md)
        self.assertIn("| Fonti | 2 |", md)
        self.assertIn("Filtri di volatilità \\| con pipe", md)  # pipe nelle celle è protetta
        self.assertIn("- indicatore: [AAA Primo](indicators/aaa-primo/README.md)", md)  # voce senza fonte
        self.assertIn("Bande attorno alla media mobile.", md)  # summary usato nel catalogo
        self.assertIn("_Nessuna implementazione in questa libreria._", md)
        # ordinamento: per tipo (indicatori prima) e slug; fonti per anno
        self.assertLess(md.index("indicators/aaa-primo/"), md.index("indicators/ma-band/"))
        self.assertLess(md.index("## Indicatori"), md.index("## Strategie"))
        self.assertLess(md.index("## Strategie"), md.index("## Funzioni"))
        self.assertLess(md.index(f"| 1999 | [Filtri"), md.index(f"| 2001 | [Regole"))
        self.assertTrue(md.endswith("\n"))
        self.assertNotIn("\r", md)

    def test_tag_index_section(self) -> None:
        md = bc.render_catalog_md(bc.load_library(self.root))
        start = md.index("## Indice per tag")
        end = md.index("## Voci senza fonte")
        self.assertLess(md.index("## Mappa fonte → implementazioni"), start)
        section = md[start:end]
        self.assertIn("Solo le voci di codice (indicatori, strategie, funzioni): i tag delle fonti non sono inclusi.", section)
        self.assertNotIn("technical-analysis", section)  # tag della fonte, non incluso
        lines = [line for line in section.splitlines() if line.startswith("- **")]
        self.assertEqual(
            lines,
            [
                "- **moving-average** (3): [AAA Primo](indicators/aaa-primo/README.md), [MA Band](indicators/ma-band/README.md), "
                "[MA Crossover](strategies/ma-crossover/README.md)",
                "- **signal** (1): [MA_Band_Signal](functions/ma-band-signal/README.md)",
                "- **trend-following** (1): [MA Crossover](strategies/ma-crossover/README.md)",
            ],
        )
        self.assertEqual(list(bc.tags_index(bc.load_library(self.root))), ["moving-average", "signal", "trend-following"])

    def test_mc_column_status_with_superseded_by_and_language_suffix(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"multicharts_version": '"14"', "status": "deprecated", "superseded_by": "aaa-primo"})
        self.rewrite_readme("strategies/ma-crossover", {"language": "PowerLanguage.NET"})
        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])
        md = bc.render_catalog_md(lib)
        self.assertIn(
            "| [MA Band](indicators/ma-band/README.md) | `ma-band` | 1.0.0 | deprecated → [aaa-primo](indicators/aaa-primo/README.md) | 14 | ",
            md,
        )
        self.assertIn("| [AAA Primo](indicators/aaa-primo/README.md) | `aaa-primo` | 1.0.0 | draft | — | — | — | moving-average |", md)
        self.assertIn("| [MA Crossover](strategies/ma-crossover/README.md) (PowerLanguage.NET) | `ma-crossover` |", md)
        self.assertNotIn("[MA Band](indicators/ma-band/README.md) (PowerLanguage)", md)

    def test_json_content(self) -> None:
        lib = bc.load_library(self.root)
        data = json.loads(bc.render_catalog_json(lib))
        self.assertEqual(data["generated_by"], "tools/build_catalog.py")
        self.assertEqual(sorted(data), ["entries", "generated_by", "papers"])
        self.assertEqual(len(data["entries"]), 4)
        self.assertEqual(len(data["papers"]), 2)
        self.assertEqual([e["slug"] for e in data["entries"]], ["aaa-primo", "ma-band", "ma-crossover", "ma-band-signal"])
        self.assertEqual([p["id"] for p in data["papers"]], [PAPER_ID_2, PAPER_ID])
        entry = data["entries"][1]
        self.assertEqual(entry["path"], "indicators/ma-band/README.md")
        self.assertEqual(entry["depends_on"], ["ma-band-signal"])
        self.assertEqual(entry["version"], "1.0.0")
        paper = data["papers"][1]
        self.assertEqual(paper["path"], f"papers/{PAPER_ID}/README.md")
        self.assertEqual(paper["year"], 2001)
        self.assertEqual(paper["implementations"], ["ma-band", "ma-crossover", "ma-band-signal"])
        self.assertEqual(data["papers"][0]["implementations"], [])

    def test_rendering_is_deterministic_and_has_no_timestamps(self) -> None:
        first_md = bc.render_catalog_md(bc.load_library(self.root))
        first_json = bc.render_catalog_json(bc.load_library(self.root))
        # Stesso contenuto ricreato in ordine inverso, in un'altra radice: output identico.
        with tempfile.TemporaryDirectory() as other:
            other_root = Path(other).resolve()
            add_code_entry(other_root, "indicator", "aaa-primo", "AAA Primo", "AAA_Primo.pl", papers=[])
            add_paper(other_root, PAPER_ID_2, title="Filtri di volatilità | con pipe", authors=["Anna Verdi"], year=1999, status="read")
            add_code_entry(other_root, "strategy", "ma-crossover", "MA Crossover", "MA_Crossover.pl",
                           depends_on=["ma-band-signal"], tags=["trend-following", "moving-average"])
            add_code_entry(other_root, "indicator", "ma-band", "MA Band", "MA_Band.pl",
                           depends_on=["ma-band-signal"], summary="Bande attorno alla media mobile.")
            add_code_entry(other_root, "function", "ma-band-signal", "MA_Band_Signal", "MA_Band_Signal.pl", tags=["signal"])
            add_paper(other_root)
            self.assertEqual(bc.render_catalog_md(bc.load_library(other_root)), first_md)
            self.assertEqual(bc.render_catalog_json(bc.load_library(other_root)), first_json)
        today = _dt.date.today().isoformat()
        self.assertNotIn(today, first_md)
        self.assertNotIn(today, first_json)
        self.assertNotIn(str(self.root), first_md)
        self.assertNotIn(str(self.root), first_json)

    def test_empty_library_renders(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            lib = bc.load_library(empty)
            self.assertEqual(bc.validate(lib), [])
            md = bc.render_catalog_md(lib)
            self.assertIn("_Nessuna voce._", md)
            self.assertIn("_Nessuna fonte._", md)
            self.assertEqual(json.loads(bc.render_catalog_json(lib))["entries"], [])


# ---------------------------------------------------------------------------
# Riga di comando di build_catalog.py e --check
# ---------------------------------------------------------------------------


class TestBuildCatalogMain(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_valid_repo(self.root)

    def test_write_then_check_is_stable(self) -> None:
        code, out, err = run_main(bc.main, ["--root", str(self.root)])
        self.assertEqual(code, 0, err)
        self.assertIn("CATALOG.md", out)
        self.assertTrue((self.root / "CATALOG.md").is_file())
        self.assertTrue((self.root / "catalog.json").is_file())
        self.assertEqual(err, "")  # repository coerente: nessun avviso
        code, out, err = run_main(bc.main, ["--root", str(self.root), "--check"])
        self.assertEqual(code, 0, err)
        self.assertIn("Catalogo aggiornato", out)
        code, out, err = run_main(bc.main, ["--root", str(self.root), "--check", "--quiet"])
        self.assertEqual((code, out), (0, ""))

    def test_check_detects_stale_catalog(self) -> None:
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--quiet"])[0], 0)
        self.rewrite_readme("indicators/ma-band", {"version": "1.1.0"})
        code, _out, err = run_main(bc.main, ["--root", str(self.root), "--check"])
        self.assertEqual(code, 1)
        self.assertIn("CATALOG.md non aggiornato: esegui python tools/build_catalog.py", err)
        self.assertIn("catalog.json non aggiornato: esegui python tools/build_catalog.py", err)
        # Dopo la rigenerazione --check torna a 0.
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--quiet"])[0], 0)
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--check", "--quiet"])[0], 0)

    def test_check_reports_missing_files(self) -> None:
        code, _out, err = run_main(bc.main, ["--root", str(self.root), "--check"])
        self.assertEqual(code, 1)
        self.assertIn("CATALOG.md mancante: esegui python tools/build_catalog.py", err)
        self.assertIn("catalog.json mancante", err)

    def test_check_normalises_line_endings(self) -> None:
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--quiet"])[0], 0)
        for name in ("CATALOG.md", "catalog.json"):
            path = self.root / name
            crlf = path.read_text(encoding="utf-8").replace("\n", "\r\n")
            path.write_bytes(crlf.encode("utf-8"))
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--check", "--quiet"])[0], 0)

    def test_validation_errors_fail_and_do_not_write(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"status": "finito"})
        code, _out, err = run_main(bc.main, ["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("ERRORE indicators/ma-band/README.md: status 'finito' non valido", err)
        self.assertIn("Validazione fallita", err)
        self.assertFalse((self.root / "CATALOG.md").exists())

    def test_warnings_go_to_stderr_unless_quiet(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"papers": []})
        code, _out, err = run_main(bc.main, ["--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertIn("AVVISO indicators/ma-band/README.md: voce senza fonte", err)
        code, _out, err = run_main(bc.main, ["--root", str(self.root), "--quiet"])
        self.assertEqual((code, err), (0, ""))

    def test_missing_root(self) -> None:
        code, _out, err = run_main(bc.main, ["--root", str(self.root / "non-esiste")])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("ERRORE "))


# ---------------------------------------------------------------------------
# new_entry.py: funzioni pure
# ---------------------------------------------------------------------------


class TestNewEntryHelpers(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(ne.slugify("BLL1992 MA Band"), "bll1992-ma-band")
        self.assertEqual(ne.slugify("Média Mòbile  Semplice!"), "media-mobile-semplice")
        self.assertEqual(ne.slugify("  --Trading Range (Breakout)--  "), "trading-range-breakout")
        self.assertEqual(ne.slugify("Straße & Øl"), "strasse-ol")
        self.assertEqual(ne.slugify(""), "")
        self.assertRegex(ne.slugify("Qualcosa di Nuovo 2.0"), bc.SLUG_RE)

    def test_source_file_name(self) -> None:
        self.assertEqual(ne.source_file_name("BLL1992 MA Band"), "BLL1992_MA_Band.pl")
        self.assertEqual(ne.source_file_name("BLL_MA_Band_Signal"), "BLL_MA_Band_Signal.pl")
        self.assertEqual(ne.source_file_name("MA-Band (v2)"), "MABand_v2.pl")
        self.assertEqual(ne.source_file_name("  Média   Mobile "), "Media_Mobile.pl")
        # un identificatore PowerLanguage non può iniziare con una cifra
        self.assertEqual(ne.source_file_name("3 Bar Reversal"), "_3_Bar_Reversal.pl")
        self.assertEqual(ne.source_file_name("2x ATR Stop"), "_2x_ATR_Stop.pl")
        self.assertEqual(ne.source_file_name("_3 Bar"), "_3_Bar.pl")
        with self.assertRaises(ValueError):
            ne.source_file_name("!!!")

    def test_paper_id(self) -> None:
        title = "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns"
        self.assertEqual(
            ne.paper_id(1992, "William Brock, Josef Lakonishok, Blake LeBaron", title),
            "1992-brock-lakonishok-lebaron-simple-technical-trading-rules",
        )
        # al più 3 cognomi, al più 5 parole; accetta anche una lista di autori e l'anno come stringa
        self.assertEqual(
            ne.paper_id("2001", ["Mario Rossi", "Luca Bianchi", "Anna Verdi", "Quarto Autore"], "Primo Secondo Terzo Quarto Quinto Sesto"),
            "2001-rossi-bianchi-verdi-primo-secondo-terzo-quarto-quinto",
        )
        self.assertEqual(ne.paper_id(2001, "Mario Rossi, Luca Bianchi", "Regole di trading semplici"), PAPER_ID)
        self.assertRegex(ne.paper_id(2020, "Jean-Luc Côté", "Étude: les règles!"), bc.SLUG_RE)

    def test_paper_id_drops_stopwords(self) -> None:
        # fra le prime 5 parole del titolo, articoli/preposizioni/congiunzioni (EN e IT) sono scartate
        self.assertEqual(ne.title_words("The Use of Moving Averages in Trading"), ["use", "moving", "averages"])
        self.assertEqual(ne.title_words("L'analisi tecnica: un'introduzione à la carte"), ["analisi", "tecnica", "introduzione"])
        self.assertEqual(ne.paper_id(2010, "Anna Verdi", "Il momentum e la volatilità nei mercati"), "2010-verdi-momentum-volatilita")
        self.assertEqual(ne.paper_id(2010, "Anna Verdi", "Trend vs Mean Reversion"), "2010-verdi-trend-mean-reversion")
        # titolo fatto solo di parole vuote: si tengono le parole originali
        self.assertEqual(ne.title_words("On and On"), ["on", "and", "on"])
        for word in ("a", "an", "and", "the", "of", "on", "in", "for", "to", "with", "by", "from", "at", "vs",
                     "e", "ed", "il", "lo", "la", "i", "gli", "le", "l", "di", "del", "dello", "della", "dei", "degli",
                     "delle", "un", "una", "uno", "per", "con", "su", "da", "dal", "dalla", "nel", "nella", "al", "alla"):
            self.assertIn(word, ne.STOPWORDS)
        self.assertNotIn("trading", ne.STOPWORDS)

    def test_render_template(self) -> None:
        text = "name: {{NAME}}\nslug: {{ SLUG }}\nagain: {{NAME}}\n"
        rendered = ne.render_template(text, {"NAME": "Studio", "SLUG": "studio"})
        self.assertEqual(rendered, "name: Studio\nslug: studio\nagain: Studio\n")
        # nessuna sostituzione ricorsiva
        self.assertEqual(ne.render_template("{{A}}", {"A": "{{B}}", "B": "x"}), "{{B}}")
        with self.assertRaises(ne.TemplateError) as ctx:
            ne.render_template("{{NAME}} {{IGNOTO}} {{ALTRO}}", {"NAME": "x"})
        self.assertIn("{{IGNOTO}}", str(ctx.exception))
        self.assertIn("{{ALTRO}}", str(ctx.exception))
        self.assertIn("placeholder sconosciuti", str(ctx.exception))

    def test_yaml_helpers_round_trip_through_parser(self) -> None:
        self.assertEqual(ne.yaml_flow_list([]), "[]")
        self.assertEqual(ne.yaml_flow_list(["a", "b c"]), "[a, b c]")
        flow = ne.yaml_flow_list(["Brock, W.", "x#y", "2020", "true", "semplice"])
        self.assertEqual(bc.parse_flow_list(flow), ["Brock, W.", "x#y", "2020", "true", "semplice"])
        for value in ("BLL1992 MA Band", "", "14", "true", "[non lista]", "a # b", "#hash", " spazi ", 'con "virgolette"'):
            self.assertEqual(bc.parse_scalar(ne.yaml_scalar(value)), value, value)
        self.assertEqual(ne.yaml_scalar("BLL1992 MA Band"), "BLL1992 MA Band")  # senza virgolette inutili

    def test_apa_citation(self) -> None:
        self.assertEqual(
            ne.apa_citation("William Brock, Josef Lakonishok, Blake LeBaron", 1992, "Simple Rules", doi="10.1/x"),
            "Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple Rules. https://doi.org/10.1/x",
        )
        self.assertEqual(ne.apa_citation(["Anna Verdi"], 1999, "Filtri?", url="https://e.org"), "Verdi, A. (1999). Filtri? https://e.org")
        self.assertEqual(ne.apa_citation("Jean-Luc Côté", 2020, "Titolo."), "Côté, J.-L. (2020). Titolo.")


# ---------------------------------------------------------------------------
# new_entry.py: scaffold completo e validazione con build_catalog
# ---------------------------------------------------------------------------

CODE_README_TEMPLATE = """---
type: {{TYPE}}
name: {{NAME}}
slug: {{SLUG}}
version: 1.0.0
status: draft
language: PowerLanguage
source_file: {{SOURCE_FILE}}
papers: {{PAPERS}}
depends_on: {{DEPENDS_ON}}
tags: {{TAGS}}
created: {{DATE}}
updated: {{DATE}}
summary: {{SUMMARY}}
# archive_file: {{SOURCE_NAME}}.pla
---

# {{NAME}}

## Descrizione

## Fonte

## Changelog

- {{DATE}} — 1.0.0: prima bozza.
"""

CODE_SOURCE_TEMPLATE = """{
  Nome: {{NAME}}  Tipo: {{TYPE}}  Fonte: {{PAPERS}}  Dipendenze: {{DEPENDS_ON}}  Data: {{DATE}}
}
inputs: Length(20);
variables: v(0);
v = Average(Close, Length);
Plot1(v, "{{NAME}}");
"""

PAPER_README_TEMPLATE = """---
type: {{PAPER_TYPE}}
id: {{ID}}
title: {{TITLE}}
authors: {{AUTHORS}}
year: {{YEAR}}
status: to-read
tags: {{TAGS}}
added: {{DATE}}
doi: {{DOI}}
url: {{URL}}
summary: {{SUMMARY}}
---

# {{TITLE}}

## Riferimento

{{CITATION}}
"""


def make_templates(root: Path) -> None:
    for kind, source_name in (("indicator", "Indicator.pl"), ("strategy", "Strategy.pl"), ("function", "Function.pl")):
        write(root / "templates" / kind / "README.md", CODE_README_TEMPLATE)
        write(root / "templates" / kind / source_name, CODE_SOURCE_TEMPLATE)
    write(root / "templates" / "paper" / "README.md", PAPER_README_TEMPLATE)


class TestNewEntryScaffold(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_templates(self.root)

    def new(self, *argv: str) -> tuple[int, str, str]:
        return run_main(ne.main, [*argv, "--root", str(self.root), "--date", FIXED_DATE])

    def test_full_round_trip_validates_with_build_catalog(self) -> None:
        code, out, err = self.new(
            "paper", "Regole di trading semplici", "--authors", "Mario Rossi, Luca Bianchi", "--year", "2001",
            "--doi", "10.1000/xyz123", "--tags", "technical-analysis", "--summary", "Una riga.",
        )
        self.assertEqual(code, 0, err)
        paper_dir = self.root / "papers" / PAPER_ID  # id derivato: anno-cognomi-prime 5 parole
        self.assertTrue((paper_dir / "README.md").is_file())
        self.assertIn(f"papers/{PAPER_ID}/README.md", out)
        self.assertIn("Prossimi passi", out)
        meta = bc.parse_front_matter((paper_dir / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(meta["id"], PAPER_ID)
        self.assertEqual(meta["type"], "paper")
        self.assertEqual(meta["title"], "Regole di trading semplici")
        self.assertEqual(meta["authors"], ["Mario Rossi", "Luca Bianchi"])
        self.assertEqual(meta["year"], 2001)
        self.assertEqual(meta["tags"], ["technical-analysis"])
        self.assertEqual(meta["added"], FIXED_DATE)
        self.assertEqual(meta["doi"], "10.1000/xyz123")
        self.assertIsNone(meta["url"])
        self.assertEqual(meta["summary"], "Una riga.")
        self.assertIn("Rossi, M., & Bianchi, L. (2001). Regole di trading semplici. https://doi.org/10.1000/xyz123",
                      (paper_dir / "README.md").read_text(encoding="utf-8"))

        code, out, err = self.new("function", "MA_Band_Signal", "--slug", "ma-band-signal", "--paper", PAPER_ID)
        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")  # la fonte esiste: nessun avviso
        self.assertTrue((self.root / "functions" / "ma-band-signal" / "MA_Band_Signal.pl").is_file())

        code, out, err = self.new(
            "indicator", "MA Band", "--paper", PAPER_ID, "--depends", "ma-band-signal",
            "--tags", "moving-average,trend-following", "--tags", "bande", "--summary", "Bande attorno alla media.",
        )
        self.assertEqual(code, 0, err)
        ind_dir = self.root / "indicators" / "ma-band"  # slug derivato dal nome
        self.assertEqual(sorted(p.name for p in ind_dir.iterdir()), ["MA_Band.pl", "README.md"])
        readme = (ind_dir / "README.md").read_text(encoding="utf-8")
        meta = bc.parse_front_matter(readme)
        self.assertEqual(meta["type"], "indicator")
        self.assertEqual(meta["name"], "MA Band")
        self.assertEqual(meta["slug"], "ma-band")
        self.assertEqual(meta["source_file"], "MA_Band.pl")
        self.assertEqual(meta["papers"], [PAPER_ID])
        self.assertEqual(meta["depends_on"], ["ma-band-signal"])
        self.assertEqual(meta["tags"], ["moving-average", "trend-following", "bande"])
        self.assertEqual(meta["created"], FIXED_DATE)
        self.assertEqual(meta["summary"], "Bande attorno alla media.")
        self.assertNotIn("{{", readme)
        source = (ind_dir / "MA_Band.pl").read_text(encoding="utf-8")
        self.assertIn('Plot1(v, "MA Band");', source)
        self.assertIn(f"Fonte: [{PAPER_ID}]", source)
        self.assertNotIn("{{", source)

        code, _out, err = self.new("strategy", "MA Crossover", "--paper", PAPER_ID, "--depends", "ma-band-signal")
        self.assertEqual(code, 0, err)

        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])
        self.assertEqual(len(lib.entries), 3)
        self.assertEqual(len(lib.papers), 1)
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--quiet"])[0], 0)
        self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--check", "--quiet"])[0], 0)
        catalog = (self.root / "CATALOG.md").read_text(encoding="utf-8")
        self.assertIn("[MA Band](indicators/ma-band/README.md)", catalog)
        self.assertIn("Bande attorno alla media.", catalog)

    def test_empty_optional_values_and_warnings(self) -> None:
        code, _out, err = self.new("indicator", "Senza Fonte", "--paper", "2020-ignoto-titolo", "--depends", "funzione-ignota")
        self.assertEqual(code, 0, err)
        self.assertIn("AVVISO: la fonte '2020-ignoto-titolo' non esiste ancora in papers/", err)
        self.assertIn("AVVISO: la funzione 'funzione-ignota' non esiste ancora in functions/", err)
        readme = (self.root / "indicators" / "senza-fonte" / "README.md").read_text(encoding="utf-8")
        self.assertIn("\nsummary:\n", readme)  # valore vuoto, senza spazi finali
        self.assertFalse(any(line != line.rstrip() for line in readme.split("\n")))
        meta = bc.parse_front_matter(readme)
        self.assertIsNone(meta["summary"])
        self.assertEqual(meta["tags"], [])

    def test_refuses_existing_folder_unless_force(self) -> None:
        self.assertEqual(self.new("indicator", "MA Band")[0], 0)
        marker = self.root / "indicators" / "ma-band" / "notes.md"
        write(marker, "appunti")
        code, _out, err = self.new("indicator", "MA Band")
        self.assertEqual(code, 1)
        self.assertIn("ERRORE indicators/ma-band/: la cartella esiste già", err)
        self.assertIn("--force", err)
        folder = self.root / "indicators" / "ma-band"
        (folder / "MA_Band.pl").write_text("codice utente", encoding="utf-8")
        code, out, err = self.new("indicator", "MA Band", "--force", "--summary", "Riscritto.")
        self.assertEqual(code, 0, err)
        self.assertTrue(marker.is_file())  # i file estranei al template restano
        self.assertFalse((folder / "notes.md.bak").exists())  # e non vengono copiati
        self.assertIn("summary: Riscritto.", (folder / "README.md").read_text(encoding="utf-8"))
        # i file sovrascritti sono prima copiati in <file>.bak nella stessa cartella
        self.assertEqual((folder / "MA_Band.pl.bak").read_text(encoding="utf-8"), "codice utente")
        self.assertIn("name: MA Band", (folder / "README.md.bak").read_text(encoding="utf-8"))
        self.assertNotIn("Riscritto", (folder / "README.md.bak").read_text(encoding="utf-8"))
        self.assertIn("copia di sicurezza", out)
        self.assertIn("indicators/ma-band/MA_Band.pl.bak", out)
        self.assertIn("indicators/ma-band/README.md.bak", out)
        self.assertEqual(
            sorted(p.name for p in folder.iterdir()),
            ["MA_Band.pl", "MA_Band.pl.bak", "README.md", "README.md.bak", "notes.md"],
        )
        # una seconda sovrascrittura aggiorna la copia .bak
        code, _out, err = self.new("indicator", "MA Band", "--force", "--summary", "Terza.")
        self.assertEqual(code, 0, err)
        self.assertIn("Riscritto", (folder / "README.md.bak").read_text(encoding="utf-8"))
        # prima creazione: nessuna copia e nessuna menzione
        code, out, _err = self.new("indicator", "Nuova Voce")
        self.assertEqual(code, 0)
        self.assertNotIn(".bak", out)
        self.assertEqual(sorted(p.name for p in (self.root / "indicators" / "nuova-voce").iterdir()), ["Nuova_Voce.pl", "README.md"])

    def test_dry_run_writes_nothing(self) -> None:
        code, out, err = self.new("strategy", "Prova Dry Run", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertIn("[dry-run]", out)
        self.assertIn("strategies/prova-dry-run/README.md", out)
        self.assertIn("strategies/prova-dry-run/Prova_Dry_Run.pl", out)
        self.assertFalse((self.root / "strategies").exists())

    def test_unknown_placeholder_in_template_is_an_error(self) -> None:
        write(self.root / "templates" / "function" / "README.md", CODE_README_TEMPLATE + "\n{{PLACEHOLDER_IGNOTO}}\n")
        code, _out, err = self.new("function", "Func_X")
        self.assertEqual(code, 1)
        self.assertIn("ERRORE templates/function/README.md:", err)
        self.assertIn("{{PLACEHOLDER_IGNOTO}}", err)
        self.assertFalse((self.root / "functions").exists())

    def test_argument_errors(self) -> None:
        code, _out, err = self.new("paper", "Titolo senza autori", "--year", "2001")
        self.assertEqual(code, 1)
        self.assertIn("ERRORE: per le fonti è obbligatorio --authors", err)
        code, _out, err = self.new("paper", "Titolo", "--authors", "Mario Rossi", "--year", "duemila")
        self.assertEqual(code, 1)
        self.assertIn("--year", err)
        code, _out, err = self.new("indicator", "Nome", "--slug", "Slug_Non_Valido")
        self.assertEqual(code, 1)
        self.assertIn("ERRORE: slug 'Slug_Non_Valido' non valido", err)
        code, _out, err = run_main(ne.main, ["indicator", "Nome", "--root", str(self.root), "--date", "15/01/2024"])
        self.assertEqual(code, 1)
        self.assertIn("--date", err)
        shutil.rmtree(self.root / "templates" / "strategy")
        code, _out, err = self.new("strategy", "Nome")
        self.assertEqual(code, 1)
        self.assertIn("ERRORE templates/strategy/: cartella dei template non trovata", err)

    def test_paper_with_explicit_id_type_and_url(self) -> None:
        code, _out, err = self.new(
            "paper", "Un libro: con due punti", "--authors", "Anna Verdi", "--year", "1999",
            "--id", "1999-verdi-libro", "--type", "book", "--url", "https://example.org/libro",
        )
        self.assertEqual(code, 0, err)
        meta = bc.parse_front_matter((self.root / "papers" / "1999-verdi-libro" / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(meta["type"], "book")
        self.assertEqual(meta["id"], "1999-verdi-libro")
        self.assertEqual(meta["title"], "Un libro: con due punti")
        self.assertEqual(meta["url"], "https://example.org/libro")
        self.assertIsNone(meta["doi"])
        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])

    def test_values_needing_quotes_are_quoted_only_in_front_matter(self) -> None:
        # Front matter: ": " e " #" richiedono le virgolette YAML; corpo Markdown e sorgente .pl: valori grezzi.
        code, _out, err = self.new(
            "paper", "Un libro: con due punti", "--authors", "Anna Verdi", "--year", "1999", "--id", "1999-verdi-libro",
            "--summary", "Sintesi: breve",
        )
        self.assertEqual(code, 0, err)
        readme = (self.root / "papers" / "1999-verdi-libro" / "README.md").read_text(encoding="utf-8")
        self.assertIn('\ntitle: "Un libro: con due punti"\n', readme)
        self.assertIn('\nsummary: "Sintesi: breve"\n', readme)
        self.assertIn("\n# Un libro: con due punti\n", readme)
        self.assertIn("Verdi, A. (1999). Un libro: con due punti.", readme)
        meta = bc.parse_front_matter(readme)
        self.assertEqual(meta["title"], "Un libro: con due punti")
        self.assertEqual(meta["summary"], "Sintesi: breve")

        code, _out, err = self.new("indicator", "Filtro #1: prova", "--summary", "Nota #1")
        self.assertEqual(code, 0, err)
        ind_dir = self.root / "indicators" / "filtro-1-prova"
        readme = (ind_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn('\nname: "Filtro #1: prova"\n', readme)
        self.assertIn('\nsummary: "Nota #1"\n', readme)
        self.assertIn("\n# Filtro #1: prova\n", readme)
        meta = bc.parse_front_matter(readme)
        self.assertEqual(meta["name"], "Filtro #1: prova")
        self.assertEqual(meta["summary"], "Nota #1")
        self.assertEqual(meta["source_file"], "Filtro_1_prova.pl")
        source = (ind_dir / "Filtro_1_prova.pl").read_text(encoding="utf-8")
        self.assertIn("Nome: Filtro #1: prova  Tipo: indicator", source)
        self.assertIn('Plot1(v, "Filtro #1: prova");', source)
        self.assertEqual(bc.validate(bc.load_library(self.root)), [])

    def test_render_entry_file_splits_front_matter(self) -> None:
        text = "---\nname: {{NAME}}\n---\n\n# {{NAME}}\n"
        rendered = ne.render_entry_file(text, {"NAME": '"A: b"'}, {"NAME": "A: b"})
        self.assertEqual(rendered, '---\nname: "A: b"\n---\n\n# A: b\n')
        # Senza front matter si usa la mappa del corpo; senza mappa del corpo quella YAML ovunque.
        self.assertEqual(ne.render_entry_file("{ {{NAME}} }", {"NAME": '"x"'}, {"NAME": "x"}), "{ x }")
        self.assertEqual(ne.render_entry_file("# {{NAME}}", {"NAME": '"x"'}), '# "x"')
        with self.assertRaises(ne.TemplateError):
            ne.render_entry_file("---\na: {{A}}\n---\n{{B}}", {"A": "1"}, {"A": "1"})


# ---------------------------------------------------------------------------
# Test di regressione "avversari": casi limite trovati collaudando gli strumenti
# ---------------------------------------------------------------------------


class TestAdversarialFrontMatter(unittest.TestCase):
    """Input ostili al parser del front matter."""

    def test_quoted_values_with_colon_and_hash(self) -> None:
        meta = bc.parse_front_matter('---\ntitle: "A: B # non commento"\nname: \'x: y\'\nurl: https://doi.org/10.1/x#frag\n---\n')
        self.assertEqual(meta, {"title": "A: B # non commento", "name": "x: y", "url": "https://doi.org/10.1/x#frag"})

    def test_tabs_and_inline_comments(self) -> None:
        meta = bc.parse_front_matter("---\nname:\tx\t# commento\ntags:\t[a,\tb] # c\nversion: 1.0.0 #semver\n---\n")
        self.assertEqual(meta, {"name": "x", "tags": ["a", "b"], "version": "1.0.0"})

    def test_flow_and_block_lists_with_quoted_commas(self) -> None:
        text = "---\nauthors: [\"Brock, W.\", 'Lakonishok, J.', Blake LeBaron]\ntags:\n  - a\n  - \"b, c\" # commento\n  # riga di commento\n- d\nvuota: []\nspazi: [ ]\n---\n"
        meta = bc.parse_front_matter(text)
        self.assertEqual(meta["authors"], ["Brock, W.", "Lakonishok, J.", "Blake LeBaron"])
        self.assertEqual(meta["tags"], ["a", "b, c", "d"])
        self.assertEqual((meta["vuota"], meta["spazi"]), ([], []))

    def test_alternative_closers_and_trailing_spaces(self) -> None:
        self.assertEqual(bc.parse_front_matter("---  \nname: x\n...\ncorpo\n"), {"name": "x"})
        self.assertEqual(bc.parse_front_matter("---\nname: x   \n---   \n---\naltro: y\n---\n"), {"name": "x"})
        self.assertEqual(bc.parse_front_matter("\ufeff---\r\nname: x\r\n---\r\n"), {"name": "x"})

    def test_unknown_fields_and_numeric_looking_strings(self) -> None:
        meta = bc.parse_front_matter("---\nfoo_bar: \"x: y\"\nmc: \"14\"\nversion: 1.0\npages: 1731-1764\nhex: 0x10\n---\n")
        self.assertEqual(meta["foo_bar"], "x: y")
        self.assertEqual(meta["mc"], "14")
        self.assertEqual(meta["version"], 1.0)  # senza virgolette è un decimale: la validazione lo rifiuta
        self.assertEqual(meta["pages"], "1731-1764")
        self.assertEqual(meta["hex"], "0x10")

    def test_unicode_escape_in_double_quotes(self) -> None:
        self.assertEqual(bc.parse_scalar('"caf\\u00e9 \\u0001 \\uzzzz"'), "café \x01 \\uzzzz")

    def test_clear_errors_for_broken_front_matter(self) -> None:
        for text, fragment in (
            ("---\nname: x\ncorpo senza chiusura", "non chiuso"),
            ("# Titolo\n\ncorpo", "front matter assente"),
            ("", "front matter assente"),
            ("---\n\tname: x\n---\n", "indentazione"),
            ("---\nname:x\n---\n", "attesa 'chiave: valore'"),
            ("---\nname: \"aperta\n---\n", "virgolette non chiuse"),
            ("---\ntags: [a, [b]]\n---\n", "annidate"),
        ):
            with self.assertRaises(bc.FrontMatterError, msg=repr(text)) as ctx:
                bc.parse_front_matter(text)
            self.assertIn(fragment, str(ctx.exception))


class TestAdversarialValidation(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_valid_repo(self.root)

    def test_numeric_slug_and_name_become_strings(self) -> None:
        add_code_entry(self.root, "indicator", "1992", "1992", "I1992.pl")  # name e slug scritti come numeri
        meta = bc.parse_front_matter((self.root / "indicators" / "1992" / "README.md").read_text(encoding="utf-8"))
        self.assertEqual((meta["slug"], meta["name"]), (1992, 1992))
        self.assertEqual(self.errors(), [])
        data = json.loads(bc.render_catalog_json(bc.load_library(self.root)))
        entry = next(e for e in data["entries"] if e["path"] == "indicators/1992/README.md")
        self.assertEqual((entry["slug"], entry["name"]), ("1992", "1992"))
        self.assertEqual(bc.normalize_meta({"id": 2001, "title": 3.5, "year": 2001}, "paper"), {"id": "2001", "title": "3.5", "year": 2001})
        self.assertEqual(bc.normalize_meta({"slug": True}, "code"), {"slug": True})

    def test_depends_on_must_point_to_a_function(self) -> None:
        self.rewrite_readme("strategies/ma-crossover", {"depends_on": ["ma-band"]})  # ma-band è un indicatore
        self.assertAnyError(self.errors(), "strategies/ma-crossover/README.md", "depends_on: funzione 'ma-band' non trovata in functions/")

    def test_version_must_be_full_semver(self) -> None:
        for version in ("1.0", "'1.0'", "v1.0.0", "1", "1.0.0.0", "2.10.3-beta.1", "1.0.0+build.5"):
            self.rewrite_readme("indicators/ma-band", {"version": version})
            self.assertAnyError(self.errors(), "indicators/ma-band/README.md", "version", "semver MAJOR.MINOR.PATCH")
        for version in ("1.0.0", "2.10.3", "0.0.1"):
            self.rewrite_readme("indicators/ma-band", {"version": version})
            self.assertEqual(self.errors(), [], version)

    def test_impossible_calendar_dates(self) -> None:
        for value, shown in (("2026-13-40", "'2026-13-40'"), ("2026-02-30", "'2026-02-30'"), ("2026-10-06T10:00:00", "'2026-10-06T10:00:00'"), ("20261006", "20261006")):
            self.rewrite_readme("indicators/ma-band", {"created": value})
            self.assertAnyError(self.errors(), "campo 'created' deve essere una data ISO AAAA-MM-GG", f"(trovato {shown})")

    def test_crlf_and_bom_readme_is_accepted(self) -> None:
        path = self.root / "indicators" / "ma-band" / "README.md"
        path.write_bytes(("\ufeff" + path.read_text(encoding="utf-8")).replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(self.errors(), [])

    def test_extra_fields_are_allowed_and_preserved(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"campo_extra": "\"x: y # z\"", "multicharts_version": "\"14\"", "lista_extra": [1, 2]})
        self.assertEqual(self.errors(), [])  # solo avvisi, nessun errore
        extra = [w for w in bc.collect_warnings(bc.load_library(self.root)) if "non previsto dallo schema" in w]
        self.assertEqual(len(extra), 2)
        data = json.loads(bc.render_catalog_json(bc.load_library(self.root)))
        entry = next(e for e in data["entries"] if e["path"] == "indicators/ma-band/README.md")
        self.assertEqual((entry["campo_extra"], entry["multicharts_version"], entry["lista_extra"]), ("x: y # z", "14", [1, 2]))

    def test_folder_without_readme_and_template_like_folder(self) -> None:
        (self.root / "indicators" / "senza-scheda").mkdir()
        shutil.copytree(self.root / "indicators" / "ma-band", self.root / "strategies" / "templates")
        errors = self.errors()
        self.assertIn("ERRORE indicators/senza-scheda: manca il file README.md", errors)
        self.assertAnyError(errors, "strategies/templates/README.md", "type 'indicator' non coerente con la cartella 'strategies/'")
        self.assertAnyError(errors, "strategies/templates/README.md", "slug 'ma-band' diverso dal nome della cartella 'templates'")
        self.assertAnyError(errors, "slug 'ma-band' duplicato")
        # un file sparso nella cartella di tipo e una cartella nascosta sono ignorati
        write(self.root / "indicators" / "sparso.md", "x")
        (self.root / "indicators" / ".nascosta").mkdir()
        self.assertEqual(len([e for e in self.errors() if "sparso" in e or "nascosta" in e]), 0)

    def test_source_file_must_be_a_plain_file_in_the_folder(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"source_file": "../../README.md"})
        self.assertAnyError(self.errors(), "deve essere un file nella stessa cartella")
        (self.root / "indicators" / "ma-band" / "cartella.pl").mkdir()
        self.rewrite_readme("indicators/ma-band", {"source_file": "cartella.pl"})
        self.assertAnyError(self.errors(), "source_file: file sorgente 'cartella.pl' non trovato")

    def test_markdown_cells_escape_pipes_and_brackets(self) -> None:
        self.rewrite_readme("indicators/ma-band", {"name": '"A | B ] C"'})
        self.rewrite_readme(f"papers/{PAPER_ID}", {"title": '"T | con barra"'})
        self.assertEqual(self.errors(), [])
        md = bc.render_catalog_md(bc.load_library(self.root))
        self.assertIn("[A \\| B \\] C](indicators/ma-band/README.md)", md)
        self.assertIn("[T \\| con barra](papers/", md)
        for line in md.splitlines():
            if line.startswith("| [") or line.startswith("| 2001"):
                self.assertEqual(line.replace("\\|", "").count("|"), line.count("|") - line.count("\\|"))


class TestHelpTexts(unittest.TestCase):
    def test_build_catalog_help_describes_checks_in_italian(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            run_main(bc.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)
        text = " ".join(bc.build_arg_parser().format_help().split())
        for fragment in ("MC", "multicharts_version", "superseded_by", "Changelog", "Implementazioni in questa libreria",
                         "indice per tag", "MAJOR.MINOR.PATCH", "source_file non coincide con name", "AVVISO", "ERRORE"):
            self.assertIn(fragment, text)

    def test_new_entry_help_describes_derivations_in_italian(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            run_main(ne.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)
        # argparse spezza le righe lunghe: si confrontano i testi con gli spazi normalizzati
        # (l'id di esempio può essere spezzato su un trattino, quindi se ne controlla la parte finale)
        text = " ".join(ne.build_arg_parser().format_help().split())
        for fragment in ("_3_Bar_Reversal.pl", "parole vuote", "simple-technical-trading-rules", "<file>.bak", "senza scrivere nulla"):
            self.assertIn(fragment, text)


class TestAdversarialMain(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_valid_repo(self.root)

    def test_root_without_library_folders_is_rejected_and_nothing_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            code, _out, err = run_main(bc.main, ["--root", other])
            self.assertEqual(code, 1)
            self.assertIn("ERRORE ", err)
            self.assertIn("non sembra la radice della libreria", err)
            self.assertEqual(sorted(Path(other).iterdir()), [])
            # con la sola cartella templates/ (repository appena creato) si procede
            (Path(other) / "templates").mkdir()
            self.assertEqual(run_main(bc.main, ["--root", other, "--quiet"])[0], 0)
            self.assertTrue((Path(other) / "CATALOG.md").is_file())
        self.assertIsNone(bc.library_root_problem(self.root))
        self.assertIn("non trovata", bc.library_root_problem(self.root / "manca") or "")

    def test_output_path_that_is_a_directory_is_a_clear_error(self) -> None:
        (self.root / "CATALOG.md").mkdir()
        code, _out, err = run_main(bc.main, ["--root", str(self.root), "--check"])
        self.assertEqual(code, 1)
        self.assertIn("CATALOG.md non è un file", err)
        code, _out, err = run_main(bc.main, ["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("ERRORE CATALOG.md: impossibile scrivere il file", err)
        self.assertNotIn("Traceback", err)

    def test_relative_root_from_another_cwd(self) -> None:
        previous = Path.cwd()
        try:
            os.chdir(self.root.parent)
            code, _out, err = run_main(bc.main, ["--root", self.root.name, "--quiet"])
            self.assertEqual(code, 0, err)
            os.chdir(self.root / "tools" if (self.root / "tools").is_dir() else self.root.parent)
            self.assertEqual(run_main(bc.main, ["--root", str(self.root), "--check", "--quiet"])[0], 0)
        finally:
            os.chdir(previous)
        self.assertTrue((self.root / "catalog.json").is_file())
        self.assertFalse((self.root.parent / "catalog.json").exists())


class TestAdversarialNewEntry(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        make_templates(self.root)

    def new(self, *argv: str) -> tuple[int, str, str]:
        return run_main(ne.main, [*argv, "--root", str(self.root), "--date", FIXED_DATE])

    def test_slugify_ascii_folds_accents(self) -> None:
        self.assertEqual(ne.slugify("Bande di Bollinger à la Ehlers"), "bande-di-bollinger-a-la-ehlers")
        self.assertEqual(ne.slugify("Ünïcödé Straße Ø — test’s"), "unicode-strasse-o-test-s")
        self.assertEqual(ne.source_file_name("Bande di Bollinger à la Ehlers"), "Bande_di_Bollinger_a_la_Ehlers.pl")
        self.assertEqual(ne.slugify("!!! ***"), "")
        self.assertEqual(ne.slugify("日本語"), "")

    def test_name_without_usable_characters_is_a_clear_error(self) -> None:
        for name in ("!!! ***", "日本語", "   "):
            code, _out, err = self.new("indicator", name)
            self.assertEqual(code, 1, name)
            self.assertTrue(err.startswith("ERRORE: "), err)
            self.assertNotIn("Traceback", err)
        self.assertIn("indicare --slug", self.new("indicator", "!!!")[2])
        # con --slug esplicito il nome resta inutilizzabile per il file sorgente
        code, _out, err = self.new("indicator", "!!!", "--slug", "punti")
        self.assertEqual(code, 1)
        self.assertIn("senza caratteri alfanumerici", err)
        self.assertFalse((self.root / "indicators").exists())

    def test_multiline_name_and_summary_are_normalised(self) -> None:
        code, _out, err = self.new("indicator", "Multi\nLine  Name\t!", "--summary", "riga1\nriga2")
        self.assertEqual(code, 0, err)
        readme = (self.root / "indicators" / "multi-line-name" / "README.md").read_text(encoding="utf-8")
        meta = bc.parse_front_matter(readme)
        self.assertEqual(meta["name"], "Multi Line Name !")
        self.assertEqual(meta["summary"], "riga1 riga2")
        self.assertEqual(meta["source_file"], "Multi_Line_Name.pl")
        self.assertIn("\n# Multi Line Name !\n", readme)
        self.assertEqual(bc.validate(bc.load_library(self.root)), [])
        self.assertEqual(ne.clean_text(" a \r\n b\t\tc "), "a b c")

    def test_yaml_helpers_escape_control_characters(self) -> None:
        for value in ("a\nb", "tab\there", "x\x01y", 'q"uote\\back', " spazi ", "# cancelletto", "- trattino", "1.0"):
            self.assertEqual(bc.parse_scalar(ne.yaml_scalar(value)), value, repr(value))
        self.assertEqual(bc.parse_flow_list(ne.yaml_flow_list(["a\nb", "ok", "c, d"])), ["a\nb", "ok", "c, d"])

    def test_date_errors_are_in_italian(self) -> None:
        for value in ("2026-13-40", "2026-02-30"):
            code, _out, err = run_main(ne.main, ["indicator", "Nome", "--root", str(self.root), "--date", value])
            self.assertEqual(code, 1)
            self.assertIn(f"ERRORE: --date '{value}' non valida: non è una data di calendario esistente", err)
        code, _out, err = run_main(ne.main, ["indicator", "Nome", "--root", str(self.root), "--date", "2026-1-1"])
        self.assertEqual(code, 1)
        self.assertIn("usare il formato AAAA-MM-GG", err)

    def test_reference_path_forms_are_reduced_to_slugs(self) -> None:
        add_paper(self.root)
        add_code_entry(self.root, "function", "ma-band-signal", "MA_Band_Signal", "MA_Band_Signal.pl")
        code, _out, err = self.new(
            "indicator", "Con Percorsi",
            "--paper", f"papers/{PAPER_ID}/", "--paper", f"papers/{PAPER_ID}/README.md",
            "--depends", "functions/ma-band-signal", "--depends", "ma-band-signal",
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(err, "")  # i riferimenti esistono: nessun avviso
        meta = bc.parse_front_matter((self.root / "indicators" / "con-percorsi" / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(meta["papers"], [PAPER_ID])
        self.assertEqual(meta["depends_on"], ["ma-band-signal"])
        self.assertEqual(bc.validate(bc.load_library(self.root)), [])

    def test_paper_id_with_one_to_four_authors(self) -> None:
        title = "Simple Technical Trading Rules and the Stochastic Properties"
        authors = ["William Brock", "Josef Lakonishok", "Blake LeBaron", "John Doe"]
        expected = [
            "1992-brock-simple-technical-trading-rules",
            "1992-brock-lakonishok-simple-technical-trading-rules",
            "1992-brock-lakonishok-lebaron-simple-technical-trading-rules",
            "1992-brock-lakonishok-lebaron-simple-technical-trading-rules",
        ]
        for count, pid in enumerate(expected, start=1):
            self.assertEqual(ne.paper_id(1992, ", ".join(authors[:count]), title), pid)
            code, out, err = self.new("paper", title, "--authors", ", ".join(authors[:count]), "--year", "1992", "--dry-run")
            self.assertEqual(code, 0, err)
            self.assertIn(f"papers/{pid}/README.md", out)
        self.assertFalse((self.root / "papers").exists())
        # autori con accenti e separatore ';'
        code, _out, err = self.new("paper", "L'analisi tecnica: un'introduzione à la carte", "--authors", "José Ñandú; Zoë Straße", "--year", "2001")
        self.assertEqual(code, 0, err)
        folder = self.root / "papers" / "2001-nandu-strasse-analisi-tecnica-introduzione"
        meta = bc.parse_front_matter((folder / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(meta["authors"], ["José Ñandú", "Zoë Straße"])
        self.assertEqual(meta["title"], "L'analisi tecnica: un'introduzione à la carte")
        self.assertEqual(bc.validate(bc.load_library(self.root)), [])

    def test_dry_run_with_force_on_existing_folder_writes_nothing(self) -> None:
        self.assertEqual(self.new("indicator", "MA Band")[0], 0)
        source = self.root / "indicators" / "ma-band" / "MA_Band.pl"
        source.write_text("codice utente", encoding="utf-8")
        code, out, _err = self.new("indicator", "MA Band", "--force", "--dry-run", "--summary", "Nuova")
        self.assertEqual(code, 0)
        self.assertIn("[dry-run]", out)
        self.assertIn("indicators/ma-band/MA_Band.pl.bak", out)  # annuncia le copie di sicurezza...
        self.assertFalse((self.root / "indicators" / "ma-band" / "MA_Band.pl.bak").exists())  # ...senza crearle
        self.assertEqual(sorted(p.name for p in (self.root / "indicators" / "ma-band").iterdir()), ["MA_Band.pl", "README.md"])
        self.assertEqual(source.read_text(encoding="utf-8"), "codice utente")
        self.assertNotIn("Nuova", (self.root / "indicators" / "ma-band" / "README.md").read_text(encoding="utf-8"))
        # senza --force il dry-run segnala comunque la cartella esistente
        code, _out, err = self.new("indicator", "MA Band", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("la cartella esiste già", err)

    def test_placeholder_like_name_is_not_expanded(self) -> None:
        code, _out, err = self.new("indicator", "{{TAGS}} injection", "--tags", "a")
        self.assertEqual(code, 0, err)
        readme = (self.root / "indicators" / "tags-injection" / "README.md").read_text(encoding="utf-8")
        meta = bc.parse_front_matter(readme)
        self.assertEqual(meta["name"], "{{TAGS}} injection")
        self.assertIn("\n# {{TAGS}} injection\n", readme)
        self.assertEqual(bc.validate(bc.load_library(self.root)), [])

    def test_unknown_placeholder_lists_allowed_ones(self) -> None:
        write(self.root / "templates" / "strategy" / "README.md", CODE_README_TEMPLATE + "\n{{FOO}} e {{ BAR }}\n")
        code, _out, err = self.new("strategy", "Zed", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("ERRORE templates/strategy/README.md: placeholder sconosciuti nel template: {{FOO}}, {{BAR}}", err)
        self.assertIn("ammessi:", err)
        self.assertIn("{{NAME}}", err)


if __name__ == "__main__":
    unittest.main()
