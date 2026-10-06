#!/usr/bin/env python3
"""Crea una nuova voce della libreria (indicatore, strategia, funzione o fonte) dai template.

Copia ``templates/<tipo>/`` nella cartella di destinazione sostituendo i placeholder
``{{...}}`` e rinominando il template del sorgente in ``<NomeFile>.pl``. Solo
libreria standard.

Uso::

    python tools/new_entry.py indicator "BLL1992 MA Band" [--slug bll1992-ma-band] [--paper <id> ...]
           [--depends <function-slug> ...] [--tags a,b] [--summary "..."]
    python tools/new_entry.py strategy "..." ...
    python tools/new_entry.py function "..." ...
    python tools/new_entry.py paper "Simple Technical Trading Rules..." \\
           --authors "William Brock, Josef Lakonishok" --year 1992 \\
           [--id <id>] [--type paper|book|chapter|article|thesis|web] [--doi ...] [--url ...] [--tags ...]

Opzioni comuni: ``--root <percorso>``, ``--date AAAA-MM-GG`` (default: oggi),
``--force`` (sovrascrive i file di una cartella esistente, salvando prima una copia
``<file>.bak`` di ogni file sovrascritto), ``--dry-run`` (non scrive nulla).

Derivazioni automatiche: lo slug è il nome in kebab-case; il file sorgente è il nome
con spazi → ``_`` e caratteri non alfanumerici rimossi, con ``_`` iniziale se
comincia con una cifra (``"3 Bar Reversal"`` → ``_3_Bar_Reversal.pl``, identificatore
PowerLanguage valido); l'id di una fonte è
``<anno>-<cognomi di al più 3 autori>-<prime 5 parole del titolo>`` dove, fra le
prime 5 parole, quelle vuote (``STOPWORDS``: articoli, preposizioni e congiunzioni
inglesi e italiane) sono scartate.

Placeholder sostituiti (vedi docs/CONVENZIONI.md): ``{{NAME}}``, ``{{SLUG}}``,
``{{SOURCE_FILE}}``, ``{{SOURCE_NAME}}``, ``{{PAPERS}}``, ``{{DEPENDS_ON}}``,
``{{TAGS}}``, ``{{DATE}}``, ``{{SUMMARY}}``, ``{{TYPE}}`` e, per le fonti,
``{{ID}}``, ``{{TITLE}}``, ``{{AUTHORS}}``, ``{{YEAR}}``, ``{{DOI}}``, ``{{URL}}``,
``{{PAPER_TYPE}}``, ``{{CITATION}}``. Un placeholder non previsto lasciato in un
template produce un errore esplicito.

Funzioni pure importabili dai test: :func:`slugify`, :func:`source_file_name`,
:func:`paper_id`, :func:`render_template`, :func:`render_entry_file`,
:func:`yaml_scalar`, :func:`yaml_flow_list`, :func:`apa_citation`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

__all__ = [
    "ENTRY_KINDS",
    "TYPE_DIRS",
    "PAPER_TYPES",
    "NewEntryError",
    "TemplateError",
    "ascii_fold",
    "clean_text",
    "slugify",
    "STOPWORDS",
    "title_words",
    "source_file_name",
    "split_authors",
    "author_surname",
    "paper_id",
    "yaml_scalar",
    "yaml_flow_list",
    "apa_citation",
    "render_template",
    "render_entry_file",
    "build_mapping",
    "ScaffoldResult",
    "scaffold",
    "scaffold_with_backups",
    "main",
]

#: Tipi di voce accettati dalla riga di comando.
ENTRY_KINDS: tuple[str, ...] = ("indicator", "strategy", "function", "paper")
#: Cartella di destinazione per ogni tipo di voce.
TYPE_DIRS: dict[str, str] = {
    "indicator": "indicators",
    "strategy": "strategies",
    "function": "functions",
    "paper": "papers",
}
#: Etichette italiane dei tipi, usate nei messaggi.
TYPE_LABELS: dict[str, str] = {
    "indicator": "indicatore",
    "strategy": "strategia",
    "function": "funzione",
    "paper": "fonte",
}
PAPER_TYPES: tuple[str, ...] = ("paper", "book", "chapter", "article", "thesis", "web")
TEMPLATES_DIR = "templates"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_NUMERIC_RE = re.compile(r"^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$")
_YAML_RESERVED = frozenset(
    {"true", "false", "null", "~", "yes", "no", "on", "off", "True", "False", "Null", "TRUE", "FALSE", "NULL"}
)
_YAML_SPECIAL_START = "[]{}\"'#&*!|>%@`,?:-"

#: Caratteri senza decomposizione Unicode, ridotti ad ASCII manualmente.
_ASCII_FOLD: dict[str, str] = {
    "ß": "ss", "æ": "ae", "Æ": "AE", "ø": "o", "Ø": "O", "œ": "oe", "Œ": "OE",
    "đ": "d", "Đ": "D", "ł": "l", "Ł": "L", "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D",
    "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
}


#: Parole vuote scartate dal titolo quando si deriva l'id di una fonte
#: (inglesi e italiane; confrontate dopo :func:`slugify`, quindi ``l`` copre ``l'``).
STOPWORDS: frozenset[str] = frozenset(
    {
        # inglese
        "a", "an", "and", "the", "of", "on", "in", "for", "to", "with", "by", "from", "at", "vs",
        # italiano
        "e", "ed", "il", "lo", "la", "i", "gli", "le", "l", "di", "del", "dello", "della", "dei",
        "degli", "delle", "un", "una", "uno", "per", "con", "su", "da", "dal", "dalla", "nel",
        "nella", "al", "alla",
    }
)
#: Numero massimo di parole del titolo nell'id di una fonte.
TITLE_WORDS_IN_ID = 5
#: Numero massimo di cognomi nell'id di una fonte.
AUTHORS_IN_ID = 3


class NewEntryError(Exception):
    """Errore d'uso o di ambiente che impedisce di creare la voce.

    :param message: descrizione in italiano.
    :param path: percorso (relativo alla radice) a cui si riferisce l'errore, se c'è.
    """

    def __init__(self, message: str, path: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.path = path

    def formatted(self) -> str:
        """Messaggio per l'utente: ``ERRORE <percorso>: ...`` oppure ``ERRORE: ...``."""
        return f"ERRORE {self.path}: {self.message}" if self.path else f"ERRORE: {self.message}"


class TemplateError(NewEntryError):
    """Un template contiene placeholder non previsti."""


# ---------------------------------------------------------------------------
# Funzioni pure
# ---------------------------------------------------------------------------


def ascii_fold(text: str) -> str:
    """Riduce il testo ad ASCII: rimuove accenti e sostituisce le lettere speciali."""
    replaced = "".join(_ASCII_FOLD.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFKD", replaced)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch) and ord(ch) < 128)


def clean_text(text: str) -> str:
    """Normalizza un testo da riga di comando: spazi, tabulazioni e a capo diventano
    un singolo spazio e gli spazi iniziali/finali sono rimossi.

    Un nome o una sintesi su più righe produrrebbe un front matter non valido:
    il sottoinsieme YAML letto da ``build_catalog.py`` non ammette stringhe multi-riga.

    >>> clean_text(" Multi\\nLine\\tName ".encode().decode("unicode_escape"))
    'Multi Line Name'
    """
    return " ".join(str(text).split())


def slugify(text: str) -> str:
    """Converte un testo in slug kebab-case ``[a-z0-9]+(-[a-z0-9]+)*``.

    >>> slugify("BLL1992 MA Band")
    'bll1992-ma-band'
    >>> slugify("Média Mòbile  Semplice!")
    'media-mobile-semplice'
    """
    folded = ascii_fold(text).lower()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def source_file_name(name: str) -> str:
    """Nome del file sorgente ``.pl`` a partire dal nome dello studio.

    Gli spazi diventano ``_`` e i caratteri non alfanumerici sono rimossi, così il
    nome resta uguale allo studio in MultiCharts. Se il risultato inizia con una
    cifra viene anteposto ``_``: un identificatore PowerLanguage non può iniziare
    con un numero.

    >>> source_file_name("BLL1992 MA Band")
    'BLL1992_MA_Band.pl'
    >>> source_file_name("3 Bar Reversal")
    '_3_Bar_Reversal.pl'

    :raises ValueError: se il nome non contiene caratteri utilizzabili.
    """
    base = re.sub(r"\s+", "_", ascii_fold(name).strip())
    base = re.sub(r"[^A-Za-z0-9_]", "", base)
    base = re.sub(r"_+", "_", base).strip("_")
    if not base:
        raise ValueError(f"nome dello studio senza caratteri alfanumerici: {name!r}")
    if base[0].isdigit():
        base = "_" + base
    return f"{base}.pl"


def split_authors(authors: str | Iterable[str]) -> list[str]:
    """Normalizza gli autori in lista: accetta una stringa ``"Nome Cognome, Nome Cognome"``
    (separatori ``,`` o ``;``) oppure una sequenza di stringhe (anch'esse separabili)."""
    raw: list[str] = []
    if isinstance(authors, str):
        raw.extend(re.split(r"[,;]", authors))
    else:
        for item in authors:
            raw.extend(re.split(r"[,;]", str(item)))
    return [clean_text(a) for a in raw if a.strip()]


def author_surname(author: str) -> str:
    """Cognome di un autore scritto come ``Nome [Secondo] Cognome`` (ultima parola)."""
    tokens = author.split()
    return tokens[-1] if tokens else ""


def title_words(title: str, limit: int = TITLE_WORDS_IN_ID) -> list[str]:
    """Parole del titolo usate nell'id di una fonte, in forma slug.

    Si prendono le prime ``limit`` parole del titolo e si scartano le parole vuote
    (:data:`STOPWORDS`), così l'id resta corto e senza articoli o preposizioni; se
    restano solo parole vuote si tengono tutte.

    >>> title_words("Simple Technical Trading Rules and the Stochastic Properties of Stock Returns")
    ['simple', 'technical', 'trading', 'rules']
    >>> title_words("Regole di trading semplici")
    ['regole', 'trading', 'semplici']
    """
    words = [w for w in slugify(title).split("-") if w][:limit]
    meaningful = [w for w in words if w not in STOPWORDS]
    return meaningful or words


def paper_id(year: int | str, authors: str | Iterable[str], title: str) -> str:
    """Id di una fonte: ``<anno>-<cognomi di al più 3 autori>-<prime 5 parole del titolo>``,
    scartando le parole vuote del titolo (:data:`STOPWORDS`).

    >>> paper_id(1992, "William Brock, Josef Lakonishok, Blake LeBaron",
    ...          "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns")
    '1992-brock-lakonishok-lebaron-simple-technical-trading-rules'
    """
    surnames = [slugify(author_surname(a)) for a in split_authors(authors)[:AUTHORS_IN_ID]]
    parts = [slugify(str(year))] + [s for s in surnames if s] + title_words(title)
    return "-".join(p for p in parts if p)


def _quote(text: str) -> str:
    """Virgolette doppie YAML con escape di ``\\``, ``"`` e dei caratteri di controllo."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    escaped = "".join(ch if ord(ch) >= 32 else f"\\u{ord(ch):04x}" for ch in escaped)
    return '"' + escaped + '"'


def yaml_scalar(value: Any) -> str:
    """Rappresenta un valore come scalare YAML del sottoinsieme letto da ``build_catalog.py``.

    Le virgolette sono aggiunte solo quando servono (valore vuoto, caratteri
    iniziali speciali, ``#`` di commento, ``: `` che in YAML aprirebbe una mappa
    annidata, parole riservate, valori numerici che devono restare stringhe,
    spazi iniziali/finali).
    """
    text = str(value)
    if text == "":
        return '""'
    needs_quotes = (
        text != text.strip()
        or text[0] in _YAML_SPECIAL_START
        or " #" in text
        or "\t#" in text
        or ": " in text
        or text.endswith(":")
        or text in _YAML_RESERVED
        or _NUMERIC_RE.match(text) is not None
        or any(ord(ch) < 32 for ch in text)
    )
    return _quote(text) if needs_quotes else text


def yaml_flow_list(items: Iterable[Any]) -> str:
    """Rappresenta una sequenza come lista YAML flow: ``[a, b, "c, d"]`` (``[]`` se vuota)."""
    rendered: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if (
            any(ch in text for ch in ",[]{}\"'#:")
            or text in _YAML_RESERVED
            or _NUMERIC_RE.match(text)
            or text[0] in _YAML_SPECIAL_START
            or any(ord(ch) < 32 for ch in text)
        ):
            text = _quote(text)
        rendered.append(text)
    return "[" + ", ".join(rendered) + "]"


def _apa_author(author: str) -> str:
    tokens = author.split()
    if len(tokens) <= 1:
        return author.strip()
    initials = " ".join(
        "-".join(part[0].upper() + "." for part in token.split("-") if part) for token in tokens[:-1]
    )
    return f"{tokens[-1]}, {initials}"


def apa_citation(
    authors: str | Iterable[str],
    year: int | str,
    title: str,
    doi: str = "",
    url: str = "",
) -> str:
    """Citazione in stile APA (da completare a mano con rivista, volume e pagine).

    >>> apa_citation("William Brock, Josef Lakonishok", 1992, "Simple Rules", doi="10.1/x")
    'Brock, W., & Lakonishok, J. (1992). Simple Rules. https://doi.org/10.1/x'
    """
    names = [_apa_author(a) for a in split_authors(authors)]
    if not names:
        who = ""
    elif len(names) == 1:
        who = names[0]
    else:
        who = ", ".join(names[:-1]) + ", & " + names[-1]
    clean_title = title.strip()
    if clean_title and clean_title[-1] not in ".?!":
        clean_title += "."
    parts = [f"{who} ({year})." if who else f"({year}).", clean_title]
    pointer = ""
    if doi:
        doi_text = doi.strip()
        pointer = doi_text if doi_text.lower().startswith("http") else f"https://doi.org/{doi_text}"
    elif url:
        pointer = url.strip()
    if pointer:
        parts.append(pointer)
    return " ".join(p for p in parts if p)


def render_template(text: str, mapping: Mapping[str, Any]) -> str:
    """Sostituisce i placeholder ``{{CHIAVE}}`` con i valori di ``mapping`` (una sola passata).

    :raises TemplateError: se il testo contiene placeholder non presenti in ``mapping``.
    """
    unknown: list[str] = []

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in mapping:
            return str(mapping[key])
        if key not in unknown:
            unknown.append(key)
        return match.group(0)

    rendered = PLACEHOLDER_RE.sub(replace, text)
    if unknown:
        listed = ", ".join("{{" + k + "}}" for k in unknown)
        raise TemplateError(
            f"placeholder sconosciuti nel template: {listed} "
            f"(ammessi: {', '.join('{{' + k + '}}' for k in sorted(mapping))})"
        )
    return rendered


_FRONT_MATTER_RE = re.compile(r"\A(\ufeff?---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z))", re.DOTALL)


def render_entry_file(text: str, yaml_mapping: Mapping[str, Any], body_mapping: Mapping[str, Any] | None = None) -> str:
    """Rende un file template distinguendo front matter e corpo.

    I placeholder dentro il front matter YAML (tra le righe ``---`` iniziali) sono
    sostituiti con ``yaml_mapping`` (valori già quotati dove serve); quelli nel resto
    del file — titolo ``# ...`` della scheda, commenti dei sorgenti ``.pl`` — con
    ``body_mapping`` (valori grezzi, senza virgolette). Senza front matter si usa
    solo ``body_mapping``; se ``body_mapping`` manca si usa ``yaml_mapping`` ovunque.

    :raises TemplateError: se il testo contiene placeholder non presenti nelle mappe.
    """
    if body_mapping is None:
        body_mapping = yaml_mapping
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return render_template(text, body_mapping)
    head = render_template(match.group(1), yaml_mapping)
    return head + render_template(text[match.end():], body_mapping)


def _split_csv(values: Iterable[str]) -> list[str]:
    """Unisce opzioni ripetibili e valori separati da virgola in una lista pulita, senza duplicati."""
    out: list[str] = []
    for value in values:
        for part in str(value).split(","):
            part = clean_text(part)
            if part and part not in out:
                out.append(part)
    return out


def _ref_slugs(values: Iterable[str], dir_name: str) -> list[str]:
    """Come :func:`_split_csv`, ma accetta anche la forma percorso ``<cartella>/<slug>[/README.md]``
    (es. da completamento automatico della shell) riducendola allo slug."""
    out: list[str] = []
    for part in _split_csv(values):
        part = part.replace("\\", "/").strip("/")
        if part.endswith("/README.md"):
            part = part[: -len("/README.md")]
        if part.startswith(dir_name + "/"):
            part = part[len(dir_name) + 1 :]
        part = part.strip("/")
        if part and part not in out:
            out.append(part)
    return out


# ---------------------------------------------------------------------------
# Costruzione della voce
# ---------------------------------------------------------------------------


@dataclass
class EntryPlan:
    """Cosa verrà creato: tipo, cartella e mappa dei placeholder."""

    kind: str
    folder: str
    mapping: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    #: Stessi placeholder di ``mapping`` ma con i valori grezzi (senza virgolette YAML):
    #: usati fuori dal front matter (titoli Markdown, commenti dei sorgenti ``.pl``).
    raw_mapping: dict[str, str] = field(default_factory=dict)

    @property
    def dir_name(self) -> str:
        return TYPE_DIRS[self.kind]

    @property
    def relative_dir(self) -> str:
        return f"{self.dir_name}/{self.folder}"


def _validate_date(value: str) -> str:
    if not DATE_RE.match(value):
        raise NewEntryError(f"--date '{value}' non valida: usare il formato AAAA-MM-GG")
    try:
        _dt.date.fromisoformat(value)
    except ValueError:
        raise NewEntryError(
            f"--date '{value}' non valida: non è una data di calendario esistente (formato AAAA-MM-GG)"
        ) from None
    return value


def build_mapping(args: argparse.Namespace, root: Path) -> EntryPlan:
    """Deriva slug/id, nome del file sorgente e mappa dei placeholder dagli argomenti.

    :raises NewEntryError: per argomenti mancanti o non validi.
    """
    kind: str = args.kind
    # Spazi multipli, tabulazioni e a capo sono ridotti a un solo spazio: il nome
    # deve stare su una riga del front matter e dello studio in MultiCharts.
    name: str = clean_text(args.name)
    if not name:
        raise NewEntryError("il nome (o titolo) non può essere vuoto")
    date = _validate_date(args.date or _dt.date.today().isoformat())
    tags = _split_csv(args.tags or [])
    summary = clean_text(args.summary or "")
    warnings: list[str] = []

    if kind == "paper":
        authors = split_authors(args.authors or [])
        if not authors:
            raise NewEntryError("per le fonti è obbligatorio --authors \"Nome Cognome, Nome Cognome\"")
        year = (args.year or "").strip()
        if not re.fullmatch(r"\d{4}", year):
            raise NewEntryError("per le fonti è obbligatorio --year con un anno a 4 cifre")
        folder = (args.paper_id or "").strip() or paper_id(year, authors, name)
        if not SLUG_RE.match(folder):
            raise NewEntryError(f"id '{folder}' non valido: usare kebab-case [a-z0-9]+(-[a-z0-9]+)*")
        doi = (args.doi or "").strip()
        url = (args.url or "").strip()
        mapping = {
            "TYPE": "paper",
            "PAPER_TYPE": args.paper_type or "paper",
            "ID": folder,
            "SLUG": folder,
            "TITLE": yaml_scalar(name),
            "NAME": yaml_scalar(name),
            "AUTHORS": yaml_flow_list(authors),
            "YEAR": year,
            "DOI": yaml_scalar(doi) if doi else "",
            "URL": yaml_scalar(url) if url else "",
            "CITATION": apa_citation(authors, year, name, doi=doi, url=url),
            "TAGS": yaml_flow_list(tags),
            "DATE": date,
            "SUMMARY": yaml_scalar(summary) if summary else "",
            "SOURCE_FILE": "",
            "SOURCE_NAME": "",
            "PAPERS": "[]",
            "DEPENDS_ON": "[]",
        }
        raw_mapping = {**mapping, "TITLE": name, "NAME": name, "DOI": doi, "URL": url, "SUMMARY": summary}
        return EntryPlan(kind=kind, folder=folder, mapping=mapping, warnings=warnings, raw_mapping=raw_mapping)

    folder = (args.slug or "").strip() or slugify(name)
    if not folder:
        raise NewEntryError(f"impossibile derivare uno slug dal nome {name!r}: indicare --slug")
    if not SLUG_RE.match(folder):
        raise NewEntryError(f"slug '{folder}' non valido: usare kebab-case [a-z0-9]+(-[a-z0-9]+)*")
    try:
        source_file = source_file_name(name)
    except ValueError as exc:
        raise NewEntryError(str(exc)) from None
    papers = _ref_slugs(args.paper or [], TYPE_DIRS["paper"])
    depends = _ref_slugs(args.depends or [], TYPE_DIRS["function"])
    for pid in papers:
        if not (root / TYPE_DIRS["paper"] / pid / "README.md").is_file():
            warnings.append(f"AVVISO: la fonte '{pid}' non esiste ancora in papers/ (crearla con: new_entry.py paper ...)")
    for dep in depends:
        if not (root / TYPE_DIRS["function"] / dep / "README.md").is_file():
            warnings.append(f"AVVISO: la funzione '{dep}' non esiste ancora in functions/")
    if kind == "function" and Path(source_file).stem != name:
        warnings.append(
            f"AVVISO: per le funzioni il nome dello studio deve coincidere con il nome del file "
            f"('{Path(source_file).stem}'): MultiCharts richiede nome funzione = nome studio e "
            f"build_catalog.py lo segnala come ERRORE; rinominare la funzione (es. --slug resta libero)"
        )
    mapping = {
        "TYPE": kind,
        "NAME": yaml_scalar(name),
        "SLUG": folder,
        "SOURCE_FILE": source_file,
        "SOURCE_NAME": Path(source_file).stem,
        "PAPERS": yaml_flow_list(papers),
        "DEPENDS_ON": yaml_flow_list(depends),
        "TAGS": yaml_flow_list(tags),
        "DATE": date,
        "SUMMARY": yaml_scalar(summary) if summary else "",
        # Alias dei placeholder delle fonti, così nessun template resta irrisolto.
        "ID": folder,
        "TITLE": yaml_scalar(name),
        "AUTHORS": "[]",
        "YEAR": "",
        "DOI": "",
        "URL": "",
        "PAPER_TYPE": "",
        "CITATION": "",
    }
    raw_mapping = {**mapping, "NAME": name, "TITLE": name, "SUMMARY": summary}
    return EntryPlan(kind=kind, folder=folder, mapping=mapping, warnings=warnings, raw_mapping=raw_mapping)


def _tidy(text: str) -> str:
    """Normalizza il testo generato: LF, niente spazi finali, una sola riga vuota finale."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).rstrip("\n") + "\n"


@dataclass
class ScaffoldResult:
    """Esito di :func:`scaffold_with_backups`.

    :param created: percorsi (assoluti) scritti, o che verrebbero scritti con ``dry_run``.
    :param backups: copie di sicurezza ``<file>.bak`` dei file preesistenti sovrascritti
        con ``force`` (o che verrebbero create con ``dry_run``).
    """

    created: list[Path] = field(default_factory=list)
    backups: list[Path] = field(default_factory=list)


def scaffold(root: Path, plan: EntryPlan, *, force: bool = False, dry_run: bool = False) -> list[Path]:
    """Come :func:`scaffold_with_backups`, ma ritorna solo i percorsi creati."""
    return scaffold_with_backups(root, plan, force=force, dry_run=dry_run).created


def scaffold_with_backups(root: Path, plan: EntryPlan, *, force: bool = False, dry_run: bool = False) -> ScaffoldResult:
    """Copia ``templates/<tipo>/`` in ``<cartella tipo>/<slug>/`` sostituendo i placeholder.

    Il file template con estensione ``.pl`` è rinominato in ``<SourceFile>.pl``.
    Con ``force`` ogni file già esistente che verrebbe sovrascritto è prima copiato in
    ``<file>.bak`` nella stessa cartella (una copia precedente ``.bak`` è sostituita).
    Con ``dry_run`` non scrive e non copia nulla.

    :raises NewEntryError: template mancanti, cartella già esistente senza ``force``,
        placeholder sconosciuti, copia di sicurezza non riuscita.
    """
    template_dir = root / TEMPLATES_DIR / plan.kind
    template_rel = f"{TEMPLATES_DIR}/{plan.kind}"
    if not template_dir.is_dir():
        raise NewEntryError("cartella dei template non trovata", path=f"{template_rel}/")
    template_files = sorted(p for p in template_dir.iterdir() if p.is_file() and not p.name.startswith("."))
    if not template_files:
        raise NewEntryError("nessun file template presente", path=f"{template_rel}/")

    target_dir = root / plan.dir_name / plan.folder
    if target_dir.exists() and not force:
        raise NewEntryError(
            "la cartella esiste già; usare --force per sovrascrivere i file del template",
            path=f"{plan.relative_dir}/",
        )

    outputs: list[tuple[Path, str]] = []
    for template in template_files:
        try:
            text = template.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise NewEntryError("il template non è codificato in UTF-8", path=f"{template_rel}/{template.name}") from None
        try:
            rendered = render_entry_file(text, plan.mapping, plan.raw_mapping or plan.mapping)
        except TemplateError as exc:
            raise TemplateError(exc.message, path=f"{template_rel}/{template.name}") from None
        target_name = template.name
        if template.suffix.lower() == ".pl" and plan.mapping.get("SOURCE_FILE"):
            target_name = plan.mapping["SOURCE_FILE"]
        outputs.append((target_dir / target_name, _tidy(rendered)))

    backups = [path.with_name(path.name + ".bak") for path, _ in outputs if path.is_file()]
    if not dry_run:
        for path in [p for p, _ in outputs if p.is_file()]:
            try:
                shutil.copy2(path, path.with_name(path.name + ".bak"))
            except OSError as exc:
                raise NewEntryError(
                    f"impossibile creare la copia di sicurezza {path.name}.bak: {exc.strerror or exc}",
                    path=f"{plan.relative_dir}/{path.name}",
                ) from None
        target_dir.mkdir(parents=True, exist_ok=True)
        for path, content in outputs:
            path.write_text(content, encoding="utf-8", newline="\n")
    return ScaffoldResult(created=[path for path, _ in outputs], backups=backups)


def _next_steps(plan: EntryPlan, created: list[Path], root: Path) -> list[str]:
    rel = [p.relative_to(root).as_posix() for p in created]
    readme = next((r for r in rel if r.endswith("README.md")), f"{plan.relative_dir}/README.md")
    source = next((r for r in rel if r.endswith(".pl")), None)
    steps: list[str] = []
    if plan.kind == "paper":
        steps.append(
            f"Compilare la scheda {readme}: riferimento completo, sintesi, regole/formule, parametri e note di estrazione."
        )
        steps.append(
            "Aggiornare `status` (to-read → reading → read → extracted) e, se distribuibile, aggiungere il PDF nel campo `pdf`."
        )
    else:
        steps.append(f"Compilare la scheda {readme}: descrizione, fonte, logica, input, output e note di implementazione.")
        if source:
            steps.append(
                f"Incollare il codice PowerLanguage in {source} (oppure scriverlo nel PowerLanguage Editor e salvarlo lì come testo)."
            )
    steps.append("Eseguire `python tools/build_catalog.py` per validare i metadati e rigenerare CATALOG.md e catalog.json.")
    return steps


def default_root() -> Path:
    """Radice del repository: la cartella padre di ``tools/``."""
    return Path(__file__).resolve().parent.parent


def build_arg_parser() -> argparse.ArgumentParser:
    """Costruisce il parser della riga di comando (testi in italiano)."""
    parser = argparse.ArgumentParser(
        prog="new_entry.py",
        description="Crea una nuova voce della libreria copiando templates/<tipo>/ e sostituendo i placeholder {{...}}.",
        epilog=(
            "Esempi:\n"
            '  python tools/new_entry.py paper "Simple Technical Trading Rules" --authors "William Brock, Josef Lakonishok" --year 1992\n'
            '  python tools/new_entry.py function "BLL_MA_Band_Signal" --slug bll-ma-band-signal --paper <id>\n'
            '  python tools/new_entry.py indicator "BLL1992 MA Band" --paper <id> --depends bll-ma-band-signal --tags moving-average,trend-following'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="mostra questo messaggio di aiuto ed esce")
    parser.add_argument("kind", metavar="tipo", choices=ENTRY_KINDS, help="tipo di voce: indicator, strategy, function o paper")
    parser.add_argument(
        "name",
        metavar="nome",
        help=(
            "nome dello studio come in MultiCharts, oppure titolo della fonte; il file sorgente deriva dal nome "
            "(spazi → _, caratteri non alfanumerici rimossi, _ iniziale se comincia con una cifra: "
            '"3 Bar Reversal" → _3_Bar_Reversal.pl)'
        ),
    )
    parser.add_argument("--slug", help="slug della cartella (default: derivato dal nome in kebab-case)")
    parser.add_argument("--paper", action="append", default=[], metavar="ID", help="id di una fonte in papers/ (ripetibile o separati da virgola)")
    parser.add_argument("--depends", action="append", default=[], metavar="SLUG", help="slug di una funzione in functions/ richiesta dallo studio (ripetibile)")
    parser.add_argument("--tags", action="append", default=[], help="tag separati da virgola (ripetibile)")
    parser.add_argument("--summary", default="", help="descrizione in una riga (campo summary, usato nel catalogo)")

    group = parser.add_argument_group("opzioni per le fonti (tipo paper)")
    group.add_argument("--authors", action="append", default=[], help='autori "Nome Cognome" separati da virgola (obbligatorio)')
    group.add_argument("--year", help="anno di pubblicazione a 4 cifre (obbligatorio)")
    group.add_argument(
        "--id",
        dest="paper_id",
        help=(
            "id della fonte (default: <anno>-<cognomi di al più 3 autori>-<prime 5 parole del titolo>, "
            "scartando fra queste le parole vuote inglesi e italiane come a, an, and, the, of, in, e, il, la, di, del, per, con...; "
            'es. "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns" → '
            "1992-brock-lakonishok-lebaron-simple-technical-trading-rules)"
        ),
    )
    group.add_argument("--type", dest="paper_type", choices=PAPER_TYPES, default="paper", help="tipo di fonte (default: paper)")
    group.add_argument("--doi", help="DOI (senza prefisso https://doi.org/)")
    group.add_argument("--url", help="URL della fonte")

    parser.add_argument("--root", metavar="PERCORSO", help="radice del repository (default: cartella padre di tools/)")
    parser.add_argument("--date", metavar="AAAA-MM-GG", help="data per created/updated/added (default: oggi)")
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "sovrascrive i file del template se la cartella esiste già; ogni file sovrascritto è prima copiato in "
            "<file>.bak nella stessa cartella (i percorsi delle copie sono stampati)"
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="mostra cosa verrebbe creato (e salvato in .bak) senza scrivere nulla")
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

def main(argv: list[str] | None = None, out: TextIO | None = None, err: TextIO | None = None) -> int:
    """Punto di ingresso della riga di comando. Ritorna il codice di uscita (0 = ok)."""
    _console_utf8_safe()
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_arg_parser().parse_args(argv)
    root = Path(args.root).resolve() if args.root else default_root()
    if not root.is_dir():
        print(NewEntryError("cartella radice non trovata", path=str(root)).formatted(), file=err)
        return 1
    try:
        plan = build_mapping(args, root)
        result = scaffold_with_backups(root, plan, force=args.force, dry_run=args.dry_run)
        created = result.created
    except NewEntryError as exc:
        print(exc.formatted(), file=err)
        return 1

    for warning in plan.warnings:
        print(warning, file=err)
    label = TYPE_LABELS[plan.kind]
    if args.dry_run:
        print(f"[dry-run] Nessun file scritto. Per la voce '{plan.folder}' ({label}) verrebbero creati:", file=out)
    else:
        print(f"Voce '{plan.folder}' ({label}) creata in {plan.relative_dir}/:", file=out)
    for path in created:
        print(f"  {path.relative_to(root).as_posix()}", file=out)
    if result.backups:
        if args.dry_run:
            print("[dry-run] I file già presenti verrebbero prima salvati in una copia di sicurezza:", file=out)
        else:
            print("File già presenti sovrascritti; copia di sicurezza salvata in:", file=out)
        for path in result.backups:
            print(f"  {path.relative_to(root).as_posix()}", file=out)
    print("", file=out)
    print("Prossimi passi:", file=out)
    for index, step in enumerate(_next_steps(plan, created, root), start=1):
        print(f"  {index}. {step}", file=out)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # output in pipe chiusa in anticipo (es. `| head`): nessun traceback
        import os

        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
