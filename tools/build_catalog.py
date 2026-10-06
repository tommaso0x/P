#!/usr/bin/env python3
"""Valida i metadati della libreria e genera ``CATALOG.md`` e ``catalog.json``.

Lo script scandisce le cartelle ``indicators/``, ``strategies/``, ``functions/`` e
``papers/`` alla ricerca di ``*/README.md`` (``templates/`` è ignorata), legge il
front matter YAML con un parser integrato (solo libreria standard, nessuna
dipendenza), controlla la coerenza dei metadati e genera il catalogo in Markdown
e in JSON.

Uso::

    python tools/build_catalog.py            # valida + scrive CATALOG.md e catalog.json; exit 0
    python tools/build_catalog.py --check    # valida + verifica che il catalogo sia aggiornato;
                                             # exit 1 con messaggi chiari se non valido o obsoleto
    python tools/build_catalog.py --root P   # radice del repository (default: cartella padre di tools/)
    python tools/build_catalog.py --quiet    # non stampa avvisi e messaggi informativi

Sottoinsieme YAML accettato nel front matter (fra le righe ``---``):

* ``chiave: valore`` con stringhe (anche fra virgolette ``'...'`` o ``"..."``),
  interi, decimali, ``true``/``false``;
* liste flow ``[a, b, "c d"]`` e lista vuota ``[]``;
* liste a blocchi (righe ``- voce`` sotto ``chiave:``);
* righe di commento che iniziano con ``#`` e commenti in linea ``# ...``
  preceduti da uno spazio;
* file con fine riga CRLF.

Nessuna mappa annidata, nessuna stringa multi-riga, nessun alias.

Oltre agli errori bloccanti (``ERRORE <percorso>: ...``, exit 1) lo script emette
avvisi non bloccanti (``AVVISO <percorso>: ...``) per: voci senza fonte, fonti senza
implementazioni, campi non previsti dallo schema, stato ``tested``/``stable`` senza
``multicharts_version``, ``version`` diversa dall'intestazione del sorgente o dalla
prima riga del Changelog, voci ``deprecated`` senza ``superseded_by`` e implementazioni
non elencate nella sezione "Implementazioni in questa libreria" della fonte.

Tutte le funzioni di parsing, validazione e rendering sono pure e importabili dai
test: :func:`parse_front_matter`, :func:`normalize_meta`, :func:`library_root_problem`,
:func:`load_library`, :func:`validate`, :func:`collect_warnings`,
:func:`render_catalog_md`, :func:`render_catalog_json`.
L'output è deterministico (voci ordinate per tipo e slug, fonti per anno e id,
nessun timestamp), così ``--check`` è stabile.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "CODE_TYPES",
    "TYPE_DIRS",
    "PAPERS_DIR",
    "PAPER_TYPES",
    "CODE_STATUSES",
    "PAPER_STATUSES",
    "LANGUAGES",
    "REQUIRED_CODE_FIELDS",
    "REQUIRED_PAPER_FIELDS",
    "OPTIONAL_CODE_FIELDS",
    "OPTIONAL_PAPER_FIELDS",
    "SLUG_RE",
    "SEMVER_RE",
    "FrontMatterError",
    "Entry",
    "Library",
    "split_front_matter",
    "parse_scalar",
    "parse_flow_list",
    "parse_simple_yaml",
    "parse_front_matter",
    "normalize_meta",
    "library_root_problem",
    "load_library",
    "validate",
    "collect_warnings",
    "source_header_version",
    "changelog_version",
    "implementations_section",
    "implementations_by_paper",
    "tags_index",
    "render_catalog_md",
    "render_catalog_json",
    "check_outputs",
    "write_outputs",
    "main",
]

# ---------------------------------------------------------------------------
# Costanti dello schema (vedi docs/CONVENZIONI.md)
# ---------------------------------------------------------------------------

#: Tipi di voce di codice, nell'ordine usato nel catalogo.
CODE_TYPES: tuple[str, ...] = ("indicator", "strategy", "function")
#: Cartella di primo livello per ogni tipo di codice.
TYPE_DIRS: dict[str, str] = {
    "indicator": "indicators",
    "strategy": "strategies",
    "function": "functions",
}
#: Mappa inversa: cartella -> tipo.
DIR_TYPES: dict[str, str] = {v: k for k, v in TYPE_DIRS.items()}
#: Etichette italiane (singolare) per i tipi di codice.
TYPE_LABELS: dict[str, str] = {
    "indicator": "indicatore",
    "strategy": "strategia",
    "function": "funzione",
}
#: Etichette italiane (plurale) per le sezioni del catalogo.
TYPE_LABELS_PLURAL: dict[str, str] = {
    "indicator": "Indicatori",
    "strategy": "Strategie",
    "function": "Funzioni",
}
PAPERS_DIR = "papers"
TEMPLATES_DIR = "templates"
#: Cartelle che identificano la radice della libreria (almeno una deve esistere).
LIBRARY_DIRS: tuple[str, ...] = (*TYPE_DIRS.values(), PAPERS_DIR, TEMPLATES_DIR)
PAPER_TYPES: tuple[str, ...] = ("paper", "book", "chapter", "article", "thesis", "web")
CODE_STATUSES: tuple[str, ...] = ("draft", "tested", "stable", "deprecated")
PAPER_STATUSES: tuple[str, ...] = ("to-read", "reading", "read", "extracted")
LANGUAGES: tuple[str, ...] = ("PowerLanguage", "PowerLanguage.NET")

REQUIRED_CODE_FIELDS: tuple[str, ...] = (
    "type",
    "name",
    "slug",
    "version",
    "status",
    "language",
    "source_file",
    "papers",
    "depends_on",
    "tags",
    "created",
    "updated",
)
REQUIRED_PAPER_FIELDS: tuple[str, ...] = (
    "type",
    "id",
    "title",
    "authors",
    "year",
    "status",
    "tags",
    "added",
)

#: Campi facoltativi ammessi dallo schema (docs/CONVENZIONI.md); ogni altro campo
#: produce un AVVISO "campo non previsto dallo schema" ma resta in catalog.json.
OPTIONAL_CODE_FIELDS: tuple[str, ...] = (
    "archive_file",
    "multicharts_version",
    "markets",
    "timeframes",
    "author",
    "summary",
    "superseded_by",
)
OPTIONAL_PAPER_FIELDS: tuple[str, ...] = (
    "journal",
    "volume",
    "issue",
    "pages",
    "publisher",
    "doi",
    "url",
    "pdf",
    "isbn",
    "summary",
)
#: Stati di codice per cui è attesa l'indicazione della versione di MultiCharts.
STATUSES_REQUIRING_MC: tuple[str, ...] = ("tested", "stable")
#: Intestazione della sezione della scheda fonte che elenca le implementazioni.
IMPLEMENTATIONS_HEADING = "## Implementazioni in questa libreria"
CHANGELOG_HEADING = "## Changelog"
SCHEMA_DOC = "docs/CONVENZIONI.md"

CATALOG_MD = "CATALOG.md"
CATALOG_JSON = "catalog.json"
GENERATED_BY = "tools/build_catalog.py"
REGENERATE_CMD = "python tools/build_catalog.py"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
#: Semver stretto MAJOR.MINOR.PATCH: niente suffissi di pre-release o build.
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
#: ``Versione: x.y.z`` nell'intestazione ``{ ... }`` di un sorgente PowerLanguage.
_HEADER_VERSION_RE = re.compile(r"Versione:\s*(\S+)")
#: Prima riga del Changelog: ``- AAAA-MM-GG — x.y.z: ...``.
_CHANGELOG_LINE_RE = re.compile(r"^\s*- \d{4}-\d{2}-\d{2} — (\d+\.\d+\.\d+)", re.MULTILINE)
#: Blocco di commento iniziale ``{ ... }`` di un sorgente PowerLanguage.
_LEADING_BLOCK_RE = re.compile(r"\A\s*\{(.*?)\}", re.DOTALL)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_RE = re.compile(r"^[-+]?\d+$")
_FLOAT_RE = re.compile(r"^[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?$")
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:(?:\s+(.*))?$")


# ---------------------------------------------------------------------------
# Parser del front matter (sottoinsieme YAML)
# ---------------------------------------------------------------------------


class FrontMatterError(ValueError):
    """Front matter assente o non conforme al sottoinsieme YAML supportato."""


def _normalize_newlines(text: str) -> str:
    """Converte CRLF e CR in LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_front_matter(text: str) -> tuple[str, str]:
    """Separa il blocco YAML iniziale dal corpo del documento.

    Ritorna la coppia ``(yaml, corpo)``. Il blocco deve iniziare con una riga
    ``---`` (eventualmente preceduta da righe vuote o BOM) e chiudersi con una
    riga ``---`` oppure ``...``.

    :raises FrontMatterError: se il front matter manca o non è chiuso.
    """
    lines = _normalize_newlines(text.lstrip("\ufeff")).split("\n")
    start = 0
    while start < len(lines) and lines[start].strip() == "":
        start += 1
    if start >= len(lines) or lines[start].rstrip() != "---":
        raise FrontMatterError("front matter assente: il file deve iniziare con una riga '---'")
    for end in range(start + 1, len(lines)):
        if lines[end].rstrip() in ("---", "..."):
            return "\n".join(lines[start + 1 : end]), "\n".join(lines[end + 1 :])
    raise FrontMatterError("front matter non chiuso: manca la riga '---' finale")


def _strip_inline_comment(value: str) -> str:
    """Rimuove un commento ``# ...`` in linea.

    Il commento è riconosciuto solo se il ``#`` è all'inizio del valore oppure
    preceduto da uno spazio, e solo fuori dalle virgolette (``url: https://x/#a``
    e ``tag: c#`` restano intatti).
    """
    quote: str | None = None
    token_start = True
    i = 0
    n = len(value)
    while i < n:
        ch = value[i]
        if quote is not None:
            if quote == '"' and ch == "\\":
                i += 2
                continue
            if quote == "'" and ch == "'" and i + 1 < n and value[i + 1] == "'":
                i += 2
                continue
            if ch == quote:
                quote = None
                token_start = False
            i += 1
            continue
        if ch == "#" and (i == 0 or value[i - 1] in " \t"):
            return value[:i].rstrip()
        if ch in "\"'" and token_start:
            quote = ch
        elif ch in "[,":
            token_start = True
        elif ch not in " \t":
            token_start = False
        i += 1
    return value.rstrip()


def _unquote_double(token: str) -> str:
    """Rimuove le virgolette doppie e risolve le sequenze di escape più comuni."""
    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/", "'": "'"}
    out: list[str] = []
    i = 1
    end = len(token) - 1
    while i < end:
        ch = token[i]
        if ch == "\\" and i + 1 < end:
            nxt = token[i + 1]
            hex_digits = token[i + 2 : i + 6]
            if nxt == "u" and len(hex_digits) == 4 and i + 6 <= end and all(c in "0123456789abcdefABCDEF" for c in hex_digits):
                out.append(chr(int(hex_digits, 16)))
                i += 6
                continue
            out.append(escapes.get(nxt, "\\" + nxt))
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_scalar(token: str) -> Any:
    """Interpreta un singolo valore scalare.

    Stringhe fra virgolette (singole o doppie) sono restituite senza virgolette;
    ``true``/``false`` diventano booleani; interi e decimali diventano numeri;
    ``null``, ``~`` e il valore vuoto diventano ``None``; tutto il resto resta
    una stringa (es. ``1.0.0``, ``2026-10-06``, ``10.1111/j.x``).
    """
    token = token.strip()
    if token == "" or token in ("~", "null", "Null", "NULL"):
        return None
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        return _unquote_double(token)
    if len(token) >= 2 and token[0] == "'" and token[-1] == "'":
        return token[1:-1].replace("''", "'")
    if token[0] in "\"'":
        raise FrontMatterError(f"virgolette non chiuse: {token}")
    if token in ("true", "True", "TRUE"):
        return True
    if token in ("false", "False", "FALSE"):
        return False
    if _INT_RE.match(token):
        return int(token)
    if _FLOAT_RE.match(token):
        return float(token)
    return token


def parse_flow_list(token: str) -> list[Any]:
    """Interpreta una lista in stile flow: ``[a, b, "c, d"]`` oppure ``[]``.

    Gli elementi sono separati da virgole fuori dalle virgolette e interpretati
    con :func:`parse_scalar`. Liste o mappe annidate non sono ammesse.
    """
    token = token.strip()
    if not (token.startswith("[") and token.endswith("]")):
        raise FrontMatterError(f"lista flow non valida (attesa fra parentesi quadre): {token}")
    inner = token[1:-1]
    items: list[Any] = []
    buf: list[str] = []
    quote: str | None = None
    token_start = True
    i = 0
    n = len(inner)

    def flush() -> None:
        text = "".join(buf).strip()
        if text:
            items.append(parse_scalar(text))
        buf.clear()

    while i < n:
        ch = inner[i]
        if quote is not None:
            buf.append(ch)
            if quote == '"' and ch == "\\" and i + 1 < n:
                buf.append(inner[i + 1])
                i += 2
                continue
            if quote == "'" and ch == "'" and i + 1 < n and inner[i + 1] == "'":
                buf.append("'")
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch == ",":
            flush()
            token_start = True
            i += 1
            continue
        if ch in "[{":
            raise FrontMatterError("liste o mappe annidate non supportate nel front matter")
        if ch in "\"'" and token_start:
            quote = ch
        if ch not in " \t":
            token_start = False
        buf.append(ch)
        i += 1
    if quote is not None:
        raise FrontMatterError(f"virgolette non chiuse nella lista: {token}")
    flush()
    return items


def parse_simple_yaml(yaml_text: str) -> dict[str, Any]:
    """Interpreta il blocco YAML del front matter (sottoinsieme semplice).

    :raises FrontMatterError: per righe non riconosciute, indentazione/mappe
        annidate, chiavi duplicate o elementi di lista senza chiave.
    """
    data: dict[str, Any] = {}
    pending_key: str | None = None  # chiave senza valore, in attesa di una lista a blocchi
    for lineno, raw in enumerate(_normalize_newlines(yaml_text).split("\n"), start=1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "-" or stripped.startswith("- "):
            if pending_key is None:
                raise FrontMatterError(f"riga {lineno}: elemento di lista '- ...' senza chiave")
            item = _strip_inline_comment(stripped[1:].strip())
            if item.startswith("[") or item.startswith("{") or _KEY_RE.match(item):
                raise FrontMatterError(
                    f"riga {lineno}: elementi di lista annidati o mappe non supportati"
                )
            if data[pending_key] is None:
                data[pending_key] = []
            data[pending_key].append(parse_scalar(item))
            continue
        if line[0] in " \t":
            raise FrontMatterError(
                f"riga {lineno}: indentazione non supportata (mappe annidate non ammesse)"
            )
        match = _KEY_RE.match(line)
        if not match:
            raise FrontMatterError(
                f"riga {lineno}: riga non riconosciuta, attesa 'chiave: valore': {stripped!r}"
            )
        key, raw_value = match.group(1), match.group(2) or ""
        if key in data:
            raise FrontMatterError(f"riga {lineno}: chiave duplicata '{key}'")
        value = _strip_inline_comment(raw_value)
        if value == "":
            data[key] = None
            pending_key = key
        else:
            data[key] = parse_flow_list(value) if value.startswith("[") else parse_scalar(value)
            pending_key = None
    return data


def parse_front_matter(text: str) -> dict[str, Any]:
    """Legge il front matter YAML di un ``README.md`` e lo restituisce come dizionario.

    Gestisce file con fine riga CRLF e BOM. Il corpo del documento è ignorato.

    :raises FrontMatterError: se il front matter manca o non è valido.
    """
    yaml_text, _body = split_front_matter(text)
    return parse_simple_yaml(yaml_text)


# ---------------------------------------------------------------------------
# Modello dati
# ---------------------------------------------------------------------------


@dataclass
class Entry:
    """Una voce della libreria (codice o fonte) letta da un ``README.md``.

    :param kind: ``"code"`` oppure ``"paper"``.
    :param dir_name: cartella di primo livello (``indicators``, ``strategies``,
        ``functions`` o ``papers``).
    :param folder: nome della cartella della voce (atteso uguale a slug/id).
    :param path: percorso POSIX del ``README.md`` relativo alla radice.
    :param meta: campi del front matter.
    :param body: corpo Markdown del ``README.md`` (dopo il front matter), usato dagli
        avvisi su Changelog e sezione "Implementazioni in questa libreria".
    """

    kind: str
    dir_name: str
    folder: str
    path: str
    meta: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    @property
    def folder_path(self) -> str:
        """Percorso POSIX della cartella della voce relativo alla radice."""
        return f"{self.dir_name}/{self.folder}"

    @property
    def entry_type(self) -> str:
        """Tipo canonico derivato dalla cartella (``indicator``, ``strategy``, ...)."""
        return DIR_TYPES.get(self.dir_name, "paper")

    @property
    def key(self) -> str:
        """Slug (codice) o id (fonte) dichiarato, altrimenti il nome della cartella."""
        declared = self.meta.get("id" if self.kind == "paper" else "slug")
        return str(declared) if isinstance(declared, (str, int)) and str(declared) else self.folder

    @property
    def display_name(self) -> str:
        """Nome (codice) o titolo (fonte) da mostrare, con ripiego sulla cartella."""
        declared = self.meta.get("title" if self.kind == "paper" else "name")
        return str(declared) if declared not in (None, "") else self.folder


@dataclass
class Library:
    """Contenuto della libreria: voci di codice, fonti ed errori di lettura."""

    root: Path
    entries: list[Entry] = field(default_factory=list)
    papers: list[Entry] = field(default_factory=list)
    load_errors: list[str] = field(default_factory=list)

    def entries_of_type(self, code_type: str) -> list[Entry]:
        """Voci di codice di un dato tipo (per cartella), già ordinate."""
        return [e for e in self.entries if e.dir_name == TYPE_DIRS[code_type]]


def _err(path: str, message: str) -> str:
    return f"ERRORE {path}: {message}"


def _warn(path: str, message: str) -> str:
    return f"AVVISO {path}: {message}"


def _is_missing(value: Any) -> bool:
    """Vero per ``None`` e stringhe vuote; una lista vuota NON è mancante."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def _as_str_list(value: Any) -> list[str]:
    """Normalizza un campo lista in lista di stringhe (robusto a valori errati)."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _year_key(value: Any) -> int:
    if isinstance(value, bool):
        return 9999
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 9999


def _entry_sort_key(entry: Entry) -> tuple[int, str]:
    order = CODE_TYPES.index(entry.entry_type) if entry.entry_type in CODE_TYPES else len(CODE_TYPES)
    return (order, entry.folder)


def _paper_sort_key(paper: Entry) -> tuple[int, str]:
    return (_year_key(paper.meta.get("year")), paper.folder)


#: Campi testuali per natura: un valore numerico (es. ``slug: 1992``) è riportato
#: a stringa, così catalog.json e i confronti con il nome della cartella restano coerenti.
_TEXT_FIELDS: dict[str, tuple[str, ...]] = {
    "code": ("name", "slug", "source_file", "archive_file", "summary", "superseded_by", "multicharts_version"),
    "paper": ("title", "id", "pdf", "summary"),
}


def normalize_meta(meta: dict[str, Any], kind: str) -> dict[str, Any]:
    """Normalizza i campi testuali letti dal front matter (funzione pura).

    Interi e decimali in campi che sono stringhe per natura (``name``, ``slug``,
    ``title``, ``id``, nomi di file, ``summary``) diventano stringhe; i booleani
    e gli altri tipi restano invariati così la validazione può segnalarli.
    """
    out = dict(meta)
    for name in _TEXT_FIELDS.get(kind, ()):
        value = out.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            out[name] = str(value)
    return out


def library_root_problem(root: str | Path) -> str | None:
    """Ritorna la descrizione del problema se ``root`` non sembra la radice della
    libreria (nessuna delle cartelle ``indicators/``, ``strategies/``, ``functions/``,
    ``papers/`` o ``templates/``), altrimenti ``None``."""
    root_path = Path(root)
    if not root_path.is_dir():
        return "cartella radice non trovata"
    if not any((root_path / name).is_dir() for name in LIBRARY_DIRS):
        expected = ", ".join(f"{name}/" for name in LIBRARY_DIRS)
        return f"non sembra la radice della libreria: nessuna delle cartelle {expected} è presente (indicare --root)"
    return None


def load_library(root: str | Path) -> Library:
    """Legge tutte le voci sotto ``root`` (``indicators/``, ``strategies/``,
    ``functions/``, ``papers/``) e ritorna una :class:`Library`.

    Gli errori di lettura (README mancante, front matter non valido) finiscono in
    ``Library.load_errors`` e sono riportati da :func:`validate`. Le voci sono
    ordinate per tipo e slug, le fonti per anno e id.
    """
    root_path = Path(root).resolve()
    lib = Library(root=root_path)
    for dir_name in (*TYPE_DIRS.values(), PAPERS_DIR):
        base = root_path / dir_name
        if not base.is_dir():
            continue
        kind = "paper" if dir_name == PAPERS_DIR else "code"
        folders = sorted(
            (p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")),
            key=lambda p: p.name,
        )
        for folder in folders:
            rel = f"{dir_name}/{folder.name}/README.md"
            readme = folder / "README.md"
            if not readme.is_file():
                lib.load_errors.append(_err(f"{dir_name}/{folder.name}", "manca il file README.md"))
                continue
            try:
                yaml_text, body = split_front_matter(readme.read_text(encoding="utf-8"))
                meta = parse_simple_yaml(yaml_text)
            except UnicodeDecodeError:
                lib.load_errors.append(_err(rel, "il file non è codificato in UTF-8"))
                continue
            except OSError as exc:
                lib.load_errors.append(_err(rel, f"impossibile leggere il file: {exc.strerror or exc}"))
                continue
            except FrontMatterError as exc:
                lib.load_errors.append(_err(rel, f"front matter non valido: {exc}"))
                continue
            meta = normalize_meta(meta, kind)
            entry = Entry(kind=kind, dir_name=dir_name, folder=folder.name, path=rel, meta=meta, body=body)
            (lib.papers if kind == "paper" else lib.entries).append(entry)
    lib.entries.sort(key=_entry_sort_key)
    lib.papers.sort(key=_paper_sort_key)
    return lib


# ---------------------------------------------------------------------------
# Validazione
# ---------------------------------------------------------------------------


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return False
    try:
        _dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _check_date(meta: dict[str, Any], field_name: str, path: str) -> list[str]:
    value = meta.get(field_name)
    if _is_missing(value) or _valid_date(value):
        return []
    return [_err(path, f"campo '{field_name}' deve essere una data ISO AAAA-MM-GG (trovato {value!r})")]


def _check_string_list(meta: dict[str, Any], field_name: str, path: str) -> list[str]:
    """Controlla che il campo sia una lista di stringhe non vuote (se presente)."""
    value = meta.get(field_name)
    if value is None:
        return []
    if not isinstance(value, list):
        return [
            _err(
                path,
                f"campo '{field_name}' deve essere una lista (es. [a, b] oppure righe '- voce'), "
                f"trovato {value!r}",
            )
        ]
    errors: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            errors.append(_err(path, f"elemento non valido in '{field_name}': {item!r} (attese stringhe)"))
    return errors


def _check_file_exists(lib: Library, entry: Entry, field_name: str) -> list[str]:
    value = entry.meta.get(field_name)
    if _is_missing(value):
        return []  # l'assenza di un campo obbligatorio è segnalata altrove
    if not isinstance(value, str):
        return [_err(entry.path, f"campo '{field_name}' deve essere un nome di file (trovato {value!r})")]
    if "/" in value or "\\" in value:
        return [_err(entry.path, f"campo '{field_name}': '{value}' deve essere un file nella stessa cartella")]
    target = lib.root / entry.dir_name / entry.folder / value
    if not target.is_file():
        what = "file sorgente" if field_name == "source_file" else "file"
        return [_err(entry.path, f"{field_name}: {what} '{value}' non trovato in {entry.folder_path}/")]
    return []


def _check_refs(
    entry: Entry, field_name: str, known: set[str], where: str, label: str
) -> list[str]:
    value = entry.meta.get(field_name)
    if not isinstance(value, list):
        return []  # tipo errato già segnalato da _check_string_list
    errors: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip() and item not in known:
            errors.append(_err(entry.path, f"{field_name}: {label} '{item}' non trovata in {where}/"))
    return errors


def _validate_code_entry(
    entry: Entry,
    lib: Library,
    paper_ids: set[str],
    function_slugs: set[str],
    code_slugs: set[str] | None = None,
) -> list[str]:
    if code_slugs is None:
        code_slugs = {e.folder for e in lib.entries}
    meta = entry.meta
    path = entry.path
    errors: list[str] = []
    for name in REQUIRED_CODE_FIELDS:
        if _is_missing(meta.get(name)):
            errors.append(_err(path, f"campo obbligatorio mancante o vuoto: '{name}'"))

    type_value = meta.get("type")
    if not _is_missing(type_value):
        expected = DIR_TYPES[entry.dir_name]
        if type_value not in CODE_TYPES:
            errors.append(_err(path, f"type '{type_value}' non valido (ammessi: {', '.join(CODE_TYPES)})"))
        elif type_value != expected:
            errors.append(
                _err(path, f"type '{type_value}' non coerente con la cartella '{entry.dir_name}/' (atteso '{expected}')")
            )

    slug = meta.get("slug")
    if not _is_missing(slug):
        slug_text = str(slug)
        if not SLUG_RE.match(slug_text):
            errors.append(_err(path, f"slug '{slug_text}' non valido: usare kebab-case [a-z0-9]+(-[a-z0-9]+)*"))
        if slug_text != entry.folder:
            errors.append(_err(path, f"slug '{slug_text}' diverso dal nome della cartella '{entry.folder}'"))

    version = meta.get("version")
    if not _is_missing(version) and not (isinstance(version, str) and SEMVER_RE.match(version)):
        errors.append(_err(path, f"version '{version}' non valida: usare semver MAJOR.MINOR.PATCH (es. 1.0.0)"))

    status = meta.get("status")
    if not _is_missing(status) and status not in CODE_STATUSES:
        errors.append(_err(path, f"status '{status}' non valido (ammessi: {', '.join(CODE_STATUSES)})"))

    language = meta.get("language")
    if not _is_missing(language) and language not in LANGUAGES:
        errors.append(_err(path, f"language '{language}' non valido (ammessi: {', '.join(LANGUAGES)})"))

    errors.extend(_check_file_exists(lib, entry, "source_file"))
    errors.extend(_check_file_exists(lib, entry, "archive_file"))
    source = meta.get("source_file")
    name = meta.get("name")
    if entry.dir_name == TYPE_DIRS["function"] and isinstance(source, str) and isinstance(name, str):
        stem = Path(source).stem
        if source.strip() and name.strip() and stem != name:
            errors.append(
                _err(
                    path,
                    f"per le funzioni source_file deve coincidere con name "
                    f"(trovato '{source}' per la funzione '{name}': MultiCharts richiede nome funzione = nome studio)",
                )
            )

    superseded = meta.get("superseded_by")
    if not _is_missing(superseded):
        if not isinstance(superseded, str):
            errors.append(_err(path, f"campo 'superseded_by' deve essere lo slug di una voce di codice (trovato {superseded!r})"))
        elif superseded == entry.folder:
            errors.append(_err(path, f"superseded_by: la voce '{superseded}' non può sostituire se stessa"))
        elif superseded not in code_slugs:
            errors.append(
                _err(
                    path,
                    f"superseded_by: voce '{superseded}' non trovata in "
                    f"{TYPE_DIRS['indicator']}/, {TYPE_DIRS['strategy']}/ o {TYPE_DIRS['function']}/",
                )
            )

    for list_field in ("papers", "depends_on", "tags", "markets", "timeframes"):
        errors.extend(_check_string_list(meta, list_field, path))
    errors.extend(_check_refs(entry, "papers", paper_ids, PAPERS_DIR, "fonte"))
    errors.extend(_check_refs(entry, "depends_on", function_slugs, TYPE_DIRS["function"], "funzione"))
    depends = meta.get("depends_on")
    if isinstance(depends, list) and entry.folder in depends:
        errors.append(_err(path, f"depends_on: la voce '{entry.folder}' non può dipendere da se stessa"))

    errors.extend(_check_date(meta, "created", path))
    errors.extend(_check_date(meta, "updated", path))
    return errors


def _validate_paper_entry(entry: Entry, lib: Library) -> list[str]:
    meta = entry.meta
    path = entry.path
    errors: list[str] = []
    for name in REQUIRED_PAPER_FIELDS:
        if _is_missing(meta.get(name)):
            errors.append(_err(path, f"campo obbligatorio mancante o vuoto: '{name}'"))

    type_value = meta.get("type")
    if not _is_missing(type_value) and type_value not in PAPER_TYPES:
        errors.append(_err(path, f"type '{type_value}' non valido (ammessi: {', '.join(PAPER_TYPES)})"))

    paper_id = meta.get("id")
    if not _is_missing(paper_id):
        id_text = str(paper_id)
        if not SLUG_RE.match(id_text):
            errors.append(_err(path, f"id '{id_text}' non valido: usare kebab-case [a-z0-9]+(-[a-z0-9]+)*"))
        if id_text != entry.folder:
            errors.append(_err(path, f"id '{id_text}' diverso dal nome della cartella '{entry.folder}'"))

    year = meta.get("year")
    if not _is_missing(year):
        valid_year = (isinstance(year, int) and not isinstance(year, bool) and 1000 <= year <= 2999) or (
            isinstance(year, str) and re.fullmatch(r"\d{4}", year.strip()) is not None
        )
        if not valid_year:
            errors.append(_err(path, f"year '{year}' non valido: atteso un anno a 4 cifre"))

    authors = meta.get("authors")
    errors.extend(_check_string_list(meta, "authors", path))
    if isinstance(authors, list) and not authors:
        errors.append(_err(path, "campo 'authors' non può essere una lista vuota"))

    status = meta.get("status")
    if not _is_missing(status) and status not in PAPER_STATUSES:
        errors.append(_err(path, f"status '{status}' non valido (ammessi: {', '.join(PAPER_STATUSES)})"))

    errors.extend(_check_string_list(meta, "tags", path))
    errors.extend(_check_date(meta, "added", path))
    errors.extend(_check_file_exists(lib, entry, "pdf"))
    return errors


def _validate_duplicates(items: Iterable[Entry], label: str) -> list[str]:
    groups: dict[str, list[Entry]] = {}
    for entry in items:
        groups.setdefault(entry.key, []).append(entry)
    errors: list[str] = []
    for key, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        for entry in group:
            others = ", ".join(o.path for o in group if o is not entry)
            errors.append(_err(entry.path, f"{label} '{key}' duplicato (presente anche in {others})"))
    return errors


def validate(lib: Library) -> list[str]:
    """Controlla tutti i metadati e ritorna la lista completa degli errori.

    Ogni errore ha la forma ``ERRORE <percorso>: <messaggio>``. Lista vuota =
    libreria valida. Non si ferma al primo errore.
    """
    errors: list[str] = list(lib.load_errors)
    paper_ids = {p.folder for p in lib.papers}
    function_slugs = {e.folder for e in lib.entries if e.dir_name == TYPE_DIRS["function"]}
    code_slugs = {e.folder for e in lib.entries}
    for entry in lib.entries:
        errors.extend(_validate_code_entry(entry, lib, paper_ids, function_slugs, code_slugs))
    for paper in lib.papers:
        errors.extend(_validate_paper_entry(paper, lib))
    errors.extend(_validate_duplicates(lib.entries, "slug"))
    errors.extend(_validate_duplicates(lib.papers, "id"))
    return errors


def implementations_by_paper(lib: Library) -> dict[str, list[Entry]]:
    """Mappa ``id fonte -> voci di codice che la citano`` (dal campo ``papers:``)."""
    result: dict[str, list[Entry]] = {p.folder: [] for p in lib.papers}
    for entry in lib.entries:
        for paper_id in _as_str_list(entry.meta.get("papers")):
            result.setdefault(paper_id, []).append(entry)
    return result


def source_header_version(text: str) -> str | None:
    """Versione dichiarata nell'intestazione ``{ ... }`` di un sorgente PowerLanguage.

    Cerca il primo ``Versione: <valore>`` nel blocco di commento iniziale; ``None``
    se il blocco o il campo mancano.
    """
    block = _LEADING_BLOCK_RE.match(_normalize_newlines(text))
    if not block:
        return None
    match = _HEADER_VERSION_RE.search(block.group(1))
    return match.group(1) if match else None


def _section(body: str, heading: str) -> str | None:
    """Testo della sezione ``heading`` del corpo Markdown, fino al prossimo ``## ``.

    ``None`` se l'intestazione non c'è. Il confronto ignora spazi finali e maiuscole.
    """
    lines = _normalize_newlines(body).split("\n")
    wanted = heading.strip().lower()
    for index, line in enumerate(lines):
        if line.strip().lower() == wanted:
            collected: list[str] = []
            for following in lines[index + 1 :]:
                if following.startswith("## "):
                    break
                collected.append(following)
            return "\n".join(collected)
    return None


def changelog_version(body: str) -> str | None:
    """Versione della prima riga ``- AAAA-MM-GG — x.y.z`` dopo ``## Changelog``.

    ``None`` se la sezione o una riga in quel formato mancano.
    """
    section = _section(body, CHANGELOG_HEADING)
    if section is None:
        return None
    match = _CHANGELOG_LINE_RE.search(section)
    return match.group(1) if match else None


def implementations_section(body: str) -> str:
    """Testo della sezione ``## Implementazioni in questa libreria`` di una scheda fonte
    (stringa vuota se la sezione manca)."""
    return _section(body, IMPLEMENTATIONS_HEADING) or ""


def _unknown_field_warnings(entry: Entry) -> list[str]:
    allowed = (
        set(REQUIRED_PAPER_FIELDS) | set(OPTIONAL_PAPER_FIELDS)
        if entry.kind == "paper"
        else set(REQUIRED_CODE_FIELDS) | set(OPTIONAL_CODE_FIELDS)
    )
    return [
        _warn(entry.path, f"campo '{key}' non previsto dallo schema (refuso?); i campi ammessi sono in {SCHEMA_DOC}")
        for key in entry.meta
        if key not in allowed
    ]


def _version_drift_warnings(lib: Library, entry: Entry) -> list[str]:
    """Confronta ``version`` con l'intestazione del sorgente e con il Changelog."""
    version = entry.meta.get("version")
    if not isinstance(version, str) or not version.strip():
        return []
    warnings: list[str] = []
    source = entry.meta.get("source_file")
    if isinstance(source, str) and source.strip() and "/" not in source and "\\" not in source:
        header_version: str | None = None
        try:
            header_version = source_header_version(
                (lib.root / entry.dir_name / entry.folder / source).read_text(encoding="utf-8", errors="replace")
            )
        except (OSError, ValueError):
            header_version = None  # file mancante o illeggibile: lo segnala già la validazione
        if header_version is not None and header_version != version:
            warnings.append(
                _warn(entry.path, f"version '{version}' diversa da quella nell'intestazione di {source} ('{header_version}')")
            )
    changelog = changelog_version(entry.body)
    if changelog is not None and changelog != version:
        warnings.append(_warn(entry.path, f"version '{version}' diversa dalla prima riga del Changelog ('{changelog}')"))
    return warnings


def collect_warnings(lib: Library) -> list[str]:
    """Avvisi non bloccanti, nella forma ``AVVISO <percorso>: <messaggio>``.

    * voce di codice senza fonte (``papers: []``);
    * campi del front matter non previsti dallo schema (possibili refusi);
    * stato ``tested``/``stable`` senza ``multicharts_version``;
    * ``version`` diversa dall'intestazione ``{ ... }`` del sorgente o dalla prima
      riga del Changelog;
    * stato ``deprecated`` senza ``superseded_by``;
    * fonte senza implementazioni in questa libreria;
    * implementazione non elencata nella sezione "Implementazioni in questa
      libreria" della scheda fonte.
    """
    warnings: list[str] = []
    impl = implementations_by_paper(lib)
    for entry in lib.entries:
        papers = entry.meta.get("papers")
        if isinstance(papers, list) and not papers:
            warnings.append(_warn(entry.path, "voce senza fonte (papers: [])"))
        warnings.extend(_unknown_field_warnings(entry))
        status = entry.meta.get("status")
        if status in STATUSES_REQUIRING_MC and _is_missing(entry.meta.get("multicharts_version")):
            warnings.append(
                _warn(
                    entry.path,
                    f"stato '{status}' senza 'multicharts_version' (indicare la versione di MultiCharts "
                    "su cui il codice è stato compilato/testato)",
                )
            )
        warnings.extend(_version_drift_warnings(lib, entry))
        if status == "deprecated" and _is_missing(entry.meta.get("superseded_by")):
            warnings.append(
                _warn(entry.path, "stato 'deprecated' senza 'superseded_by' (indicare lo slug della voce che la sostituisce)")
            )
    for paper in lib.papers:
        warnings.extend(_unknown_field_warnings(paper))
        derived = impl.get(paper.folder, [])
        if not derived:
            warnings.append(_warn(paper.path, "fonte senza implementazioni in questa libreria"))
            continue
        section = implementations_section(paper.body)
        for entry in derived:
            if f"/{entry.folder}/" not in section:
                warnings.append(
                    _warn(
                        paper.path,
                        f"la voce '{entry.folder}' cita questa fonte ma non è elencata in '{IMPLEMENTATIONS_HEADING}'",
                    )
                )
    return warnings


# ---------------------------------------------------------------------------
# Rendering del catalogo
# ---------------------------------------------------------------------------


def _cell(value: Any) -> str:
    """Testo sicuro per una cella di tabella Markdown."""
    if value is None or value == "" or value == []:
        return "—"
    if isinstance(value, list):
        text = ", ".join(str(v) for v in value)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _link(text: str, target: str) -> str:
    label = str(text).replace("|", "\\|").replace("]", "\\]").replace("\n", " ")
    return f"[{label}]({target})"


def _paper_links(entry: Entry, paper_paths: dict[str, str]) -> str:
    ids = _as_str_list(entry.meta.get("papers"))
    if not ids:
        return "—"
    parts = [_link(pid, paper_paths[pid]) if pid in paper_paths else _cell(pid) for pid in ids]
    return ", ".join(parts)


def _dependency_links(entry: Entry, function_paths: dict[str, str]) -> str:
    slugs = _as_str_list(entry.meta.get("depends_on"))
    if not slugs:
        return "—"
    parts = [_link(s, function_paths[s]) if s in function_paths else _cell(s) for s in slugs]
    return ", ".join(parts)


def _implementation_links(entries: list[Entry]) -> str:
    if not entries:
        return "—"
    return ", ".join(_link(e.display_name, e.path) for e in entries)


def _name_cell(entry: Entry) -> str:
    """Nome con link alla scheda; aggiunge `` (<language>)`` se non è PowerLanguage."""
    cell = _link(entry.display_name, entry.path)
    language = entry.meta.get("language")
    if not _is_missing(language) and str(language) != "PowerLanguage":
        cell += f" ({_cell(language)})"
    return cell


def _status_cell(entry: Entry, code_paths: dict[str, str]) -> str:
    """Stato; con ``superseded_by`` diventa ``deprecated → [slug](percorso)``."""
    status = _cell(entry.meta.get("status"))
    superseded = entry.meta.get("superseded_by")
    if _is_missing(superseded):
        return status
    slug = str(superseded)
    target = _link(slug, code_paths[slug]) if slug in code_paths else _cell(slug)
    return f"{status} → {target}"


def tags_index(lib: Library) -> dict[str, list[Entry]]:
    """Mappa ``tag -> voci di codice`` (ordinata per tag; voci per tipo e slug).

    I tag delle fonti non sono inclusi.
    """
    index: dict[str, list[Entry]] = {}
    for entry in lib.entries:  # già ordinate per (tipo, slug)
        for tag in _as_str_list(entry.meta.get("tags")):
            tag = tag.strip()
            if tag and entry not in index.setdefault(tag, []):
                index[tag].append(entry)
    return dict(sorted(index.items()))


def _summary_suffix(entry: Entry) -> str:
    summary = entry.meta.get("summary")
    return f" — {_cell(summary)}" if not _is_missing(summary) else ""


def render_catalog_md(lib: Library) -> str:
    """Genera il testo di ``CATALOG.md`` (italiano, deterministico, senza timestamp)."""
    impl = implementations_by_paper(lib)
    paper_paths = {p.folder: p.path for p in lib.papers}
    function_paths = {e.folder: e.path for e in lib.entries_of_type("function")}
    code_paths = {e.folder: e.path for e in lib.entries}
    lines: list[str] = []
    add = lines.append

    add("# Catalogo della libreria")
    add("")
    add(f"<!-- FILE GENERATO AUTOMATICAMENTE da {GENERATED_BY}: non modificare a mano. -->")
    add("")
    add(
        f"> **File generato automaticamente** da `{GENERATED_BY}` a partire dai front matter dei "
        "`README.md`: non modificarlo a mano, le modifiche andrebbero perse."
    )
    add(f"> Per rigenerarlo: `{REGENERATE_CMD}` — per verificarlo: `{REGENERATE_CMD} --check`.")
    add("")

    add("## Riepilogo")
    add("")
    add("| Tipo | Voci |")
    add("|---|---:|")
    for code_type in CODE_TYPES:
        add(f"| {TYPE_LABELS_PLURAL[code_type]} | {len(lib.entries_of_type(code_type))} |")
    add(f"| Fonti | {len(lib.papers)} |")
    add("")

    for code_type in CODE_TYPES:
        add(f"## {TYPE_LABELS_PLURAL[code_type]}")
        add("")
        rows = lib.entries_of_type(code_type)
        if not rows:
            add("_Nessuna voce._")
            add("")
            continue
        add("| Nome | Slug | Versione | Stato | MC | Fonti | Dipendenze | Tag |")
        add("|---|---|---|---|---|---|---|---|")
        for entry in rows:
            cells = [
                _name_cell(entry),
                f"`{entry.folder}`",
                _cell(entry.meta.get("version")),
                _status_cell(entry, code_paths),
                _cell(entry.meta.get("multicharts_version")),
                _paper_links(entry, paper_paths),
                _dependency_links(entry, function_paths),
                _cell(entry.meta.get("tags")),
            ]
            add("| " + " | ".join(cells) + " |")
        add("")

    add("## Fonti")
    add("")
    if not lib.papers:
        add("_Nessuna fonte._")
        add("")
    else:
        add("| Anno | Titolo | Autori | Tipo | Stato | Implementazioni |")
        add("|---|---|---|---|---|---|")
        for paper in lib.papers:
            cells = [
                _cell(paper.meta.get("year")),
                _link(paper.display_name, paper.path),
                _cell(paper.meta.get("authors")),
                _cell(paper.meta.get("type")),
                _cell(paper.meta.get("status")),
                _implementation_links(impl.get(paper.folder, [])),
            ]
            add("| " + " | ".join(cells) + " |")
        add("")

    add("## Mappa fonte → implementazioni")
    add("")
    if not lib.papers:
        add("_Nessuna fonte._")
        add("")
    for paper in lib.papers:
        year = paper.meta.get("year")
        title = paper.display_name.replace("\n", " ")
        add(f"### {title}" + (f" ({year})" if not _is_missing(year) else ""))
        add("")
        add(f"Id: `{paper.folder}` — [scheda]({paper.path})")
        add("")
        derived = impl.get(paper.folder, [])
        if derived:
            for entry in derived:
                add(f"- {TYPE_LABELS[entry.entry_type]}: {_link(entry.display_name, entry.path)}{_summary_suffix(entry)}")
        else:
            add("_Nessuna implementazione in questa libreria._")
        add("")

    add("## Indice per tag")
    add("")
    add("Solo le voci di codice (indicatori, strategie, funzioni): i tag delle fonti non sono inclusi.")
    add("")
    index = tags_index(lib)
    if index:
        for tag, tagged in index.items():
            links = ", ".join(_link(e.display_name, e.path) for e in tagged)
            add(f"- **{_cell(tag)}** ({len(tagged)}): {links}")
    else:
        add("_Nessun tag._")
    add("")

    add("## Voci senza fonte")
    add("")
    orphans = [e for e in lib.entries if not _as_str_list(e.meta.get("papers"))]
    if orphans:
        for entry in orphans:
            add(f"- {TYPE_LABELS[entry.entry_type]}: {_link(entry.display_name, entry.path)}{_summary_suffix(entry)}")
    else:
        add("_Nessuna: tutte le voci citano almeno una fonte._")
    add("")

    return "\n".join(lines).rstrip("\n") + "\n"


def render_catalog_json(lib: Library) -> str:
    """Genera il testo di ``catalog.json`` (chiavi ordinate, deterministico).

    Struttura: ``{"generated_by": ..., "entries": [...], "papers": [...]}`` con
    tutti i campi letti dal front matter più ``path``; per le fonti anche
    ``implementations`` (slug delle voci che le citano).
    """
    impl = implementations_by_paper(lib)
    entries = [{**e.meta, "path": e.path} for e in lib.entries]
    papers = [
        {**p.meta, "path": p.path, "implementations": [e.folder for e in impl.get(p.folder, [])]}
        for p in lib.papers
    ]
    data = {"generated_by": GENERATED_BY, "entries": entries, "papers": papers}
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# Scrittura / verifica dei file generati
# ---------------------------------------------------------------------------


def check_outputs(root: Path, catalog_md: str, catalog_json: str) -> list[str]:
    """Confronta i file su disco con il testo generato (fine riga normalizzati).

    Ritorna i problemi trovati; lista vuota se tutto è aggiornato.
    """
    problems: list[str] = []
    for name, expected in ((CATALOG_MD, catalog_md), (CATALOG_JSON, catalog_json)):
        target = root / name
        if target.exists() and not target.is_file():
            problems.append(f"{name} non è un file: rimuoverlo ed eseguire {REGENERATE_CMD}")
            continue
        if not target.is_file():
            problems.append(f"{name} mancante: esegui {REGENERATE_CMD}")
            continue
        try:
            actual = _normalize_newlines(target.read_text(encoding="utf-8").lstrip("\ufeff"))
        except (UnicodeDecodeError, OSError):
            actual = ""
        if actual != _normalize_newlines(expected):
            problems.append(f"{name} non aggiornato: esegui {REGENERATE_CMD}")
    return problems


def write_outputs(root: Path, catalog_md: str, catalog_json: str) -> list[Path]:
    """Scrive ``CATALOG.md`` e ``catalog.json`` nella radice (UTF-8, LF)."""
    written: list[Path] = []
    for name, text in ((CATALOG_MD, catalog_md), (CATALOG_JSON, catalog_json)):
        target = root / name
        target.write_text(text, encoding="utf-8", newline="\n")
        written.append(target)
    return written


def default_root() -> Path:
    """Radice del repository: la cartella padre di ``tools/``."""
    return Path(__file__).resolve().parent.parent


def build_arg_parser() -> argparse.ArgumentParser:
    """Costruisce il parser della riga di comando (testi in italiano)."""
    parser = argparse.ArgumentParser(
        prog="build_catalog.py",
        description=(
            "Valida i metadati delle voci (indicators/, strategies/, functions/, papers/) "
            "e genera CATALOG.md e catalog.json (tabelle per tipo con colonna MC = multicharts_version, "
            "fonti, mappa fonte → implementazioni, indice per tag, voci senza fonte)."
        ),
        epilog=(
            "Errori bloccanti (ERRORE <percorso>: ..., exit 1): campi obbligatori mancanti, slug/id diversi "
            "dalla cartella, version non semver stretto MAJOR.MINOR.PATCH (senza suffissi), file sorgente/"
            "archivio/PDF mancanti, riferimenti (papers, depends_on, superseded_by) inesistenti, funzioni il cui "
            "source_file non coincide con name.\n"
            "Avvisi non bloccanti (AVVISO <percorso>: ...): voci senza fonte, fonti senza implementazioni, campi "
            "non previsti dallo schema (docs/CONVENZIONI.md), stato tested/stable senza multicharts_version, "
            "version diversa dall'intestazione { ... } del sorgente o dalla prima riga del Changelog, stato "
            "deprecated senza superseded_by, implementazioni non elencate nella sezione "
            "'Implementazioni in questa libreria' della fonte.\n"
            "Codici di uscita: 0 = tutto valido (e catalogo scritto o aggiornato); "
            "1 = errori di validazione oppure, con --check, catalogo non aggiornato."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="mostra questo messaggio di aiuto ed esce")
    parser.add_argument(
        "--root",
        metavar="PERCORSO",
        help="radice del repository (default: cartella padre di tools/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="non scrive nulla: verifica che CATALOG.md e catalog.json siano aggiornati",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="non stampa avvisi e messaggi informativi (gli errori sono sempre stampati)",
    )
    return parser


def _console_utf8_safe() -> None:
    """Evita UnicodeEncodeError su console non UTF-8 (es. cp1252 su Windows):
    i caratteri non rappresentabili vengono sostituiti invece di interrompere lo script."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="backslashreplace")
            except (ValueError, OSError):
                pass

def main(argv: list[str] | None = None) -> int:
    """Punto di ingresso della riga di comando. Ritorna il codice di uscita."""
    _console_utf8_safe()
    args = build_arg_parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else default_root()
    problem = library_root_problem(root)
    if problem:
        print(_err(str(root), problem), file=sys.stderr)
        return 1

    lib = load_library(root)
    errors = validate(lib)
    if not args.quiet:
        for warning in collect_warnings(lib):
            print(warning, file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validazione fallita: {len(errors)} errori. Catalogo non generato.", file=sys.stderr)
        return 1

    catalog_md = render_catalog_md(lib)
    catalog_json = render_catalog_json(lib)
    summary = f"{len(lib.entries)} voci di codice, {len(lib.papers)} fonti"

    if args.check:
        problems = check_outputs(root, catalog_md, catalog_json)
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"Catalogo aggiornato ({summary}).")
        return 0

    try:
        write_outputs(root, catalog_md, catalog_json)
    except OSError as exc:
        name = Path(exc.filename).name if exc.filename else CATALOG_MD
        print(_err(name, f"impossibile scrivere il file: {exc.strerror or exc}"), file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"Scritti {CATALOG_MD} e {CATALOG_JSON} ({summary}).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # output in pipe chiusa in anticipo (es. `| head`): nessun traceback
        import os

        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
