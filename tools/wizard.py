#!/usr/bin/env python3
"""Procedura guidata (in italiano) per aggiungere una voce alla libreria.

Fa una domanda alla volta — tipo di voce, nome, fonti, dipendenze, tag, sintesi
(o, per le fonti, autori, anno, tipo, DOI, URL) — mostra lo slug/id derivato e
il comando ``new_entry.py`` equivalente, chiede conferma e crea la voce
chiamando :func:`new_entry.main` nello stesso processo. Solo libreria standard.

Uso::

    python tools/wizard.py                       # procedura guidata interattiva
    python tools/wizard.py --root <percorso>     # radice del repository (default: cartella padre di tools/)
    python tools/wizard.py --date AAAA-MM-GG     # data per created/updated/added (default: oggi)
    python tools/wizard.py --dry-run             # mostra cosa verrebbe creato senza scrivere nulla

Ctrl+C (o fine dell'input) in qualunque momento: ``Operazione annullata.`` e codice
di uscita 1. Rispondere ``N`` alla conferma finale ha lo stesso effetto.

Progettato per essere verificabile: :class:`Wizard` riceve due callable, ``ask``
(``prompt -> str``, default :func:`input`) e ``say`` (``str -> None``, default
:func:`print`), così i test forniscono risposte predefinite e leggono l'output.
Funzioni pure importabili: :func:`is_powerlanguage_identifier`, :func:`parse_choice`,
:func:`parse_multi_choice`, :func:`parse_yes_no`, :func:`normalize_doi`,
:func:`normalize_tags`, :func:`format_command`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import io
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_catalog as bc  # noqa: E402
import new_entry as ne  # noqa: E402

__all__ = [
    "CANCELLED_MESSAGE",
    "KIND_MENU",
    "PAPER_TYPE_LABELS",
    "WizardCancelled",
    "WizardOutcome",
    "Wizard",
    "is_powerlanguage_identifier",
    "parse_choice",
    "parse_multi_choice",
    "parse_yes_no",
    "normalize_doi",
    "normalize_tags",
    "format_command",
    "main",
]

#: Messaggio stampato quando la procedura viene interrotta (Ctrl+C, fine input, risposta N).
CANCELLED_MESSAGE = "Operazione annullata."

#: Voci del menu iniziale, nell'ordine mostrato: (tipo per new_entry.py, etichetta).
KIND_MENU: tuple[tuple[str, str], ...] = (
    ("indicator", "Indicatore (studio che disegna plot sul grafico)"),
    ("strategy", "Strategia (in MultiCharts: signal)"),
    ("function", "Funzione (richiamata da indicatori e strategie)"),
    ("paper", "Fonte (paper, libro, capitolo, articolo, tesi, pagina web)"),
)

#: Etichette italiane dei tipi di fonte, nell'ordine di ``new_entry.PAPER_TYPES``.
PAPER_TYPE_LABELS: dict[str, str] = {
    "paper": "paper (articolo accademico)",
    "book": "book (libro)",
    "chapter": "chapter (capitolo di libro)",
    "article": "article (articolo divulgativo o di rivista di settore)",
    "thesis": "thesis (tesi)",
    "web": "web (pagina web, post)",
}

#: Identificatore PowerLanguage: lettere, cifre e underscore, non inizia con una cifra.
PL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_YEAR_RE = re.compile(r"^[0-9]{4}$")
#: Solo cifre ASCII: str.isdigit() accetta anche "²" o cifre arabo-indiane, che int() rifiuta.
_DIGITS_RE = re.compile(r"^[0-9]+$")
_DOI_PREFIX_RE = re.compile(r"^(?:https?://)?(?:dx\.)?doi\.org/", re.IGNORECASE)
_YES = frozenset({"s", "si", "sì", "y", "yes"})
_NO = frozenset({"n", "no"})


class WizardCancelled(Exception):
    """L'utente ha interrotto la procedura (Ctrl+C, fine input o risposta N)."""


# ---------------------------------------------------------------------------
# Funzioni pure
# ---------------------------------------------------------------------------


def is_powerlanguage_identifier(name: str) -> bool:
    """Vero se ``name`` è un identificatore PowerLanguage valido: solo lettere ASCII,
    cifre e ``_``, non inizia con una cifra.

    >>> is_powerlanguage_identifier("BLL_MA_Band_Signal")
    True
    >>> is_powerlanguage_identifier("3Bar"), is_powerlanguage_identifier("MA Band")
    (False, False)
    """
    return PL_IDENTIFIER_RE.match(name) is not None


def parse_choice(text: str, count: int, *, allow_zero: bool = False) -> int | None:
    """Interpreta la risposta a un menu numerato ``1..count``.

    Ritorna il numero scelto, oppure ``None`` se la risposta non è un intero
    nell'intervallo (``0`` è ammesso solo con ``allow_zero``).

    >>> parse_choice(" 2 ", 4), parse_choice("5", 4), parse_choice("x", 4)
    (2, None, None)
    """
    token = text.strip()
    if not _DIGITS_RE.match(token):
        return None
    value = int(token)
    if value == 0:
        return 0 if allow_zero else None
    return value if 1 <= value <= count else None


def parse_multi_choice(text: str, count: int) -> list[int] | None:
    """Interpreta una scelta multipla ``"1, 3"`` su un menu numerato ``1..count``.

    Separatori ammessi: virgola, punto e virgola, spazi. Ritorna la lista dei
    numeri (senza duplicati, nell'ordine dato); lista vuota per risposta vuota;
    ``None`` se un elemento non è un intero nell'intervallo.

    >>> parse_multi_choice("1, 3,1", 3), parse_multi_choice("", 3), parse_multi_choice("1,9", 3)
    ([1, 3], [], None)
    """
    chosen: list[int] = []
    for token in re.split(r"[,;\s]+", text.strip()):
        if not token:
            continue
        value = parse_choice(token, count)
        if value is None:
            return None
        if value not in chosen:
            chosen.append(value)
    return chosen


def parse_yes_no(text: str, default: bool | None = None) -> bool | None:
    """Interpreta una risposta S/N (accetta anche ``si``, ``sì``, ``y``, ``yes``, ``no``).

    Risposta vuota → ``default``; risposta non riconosciuta → ``None``.
    """
    token = text.strip().lower()
    if not token:
        return default
    if token in _YES:
        return True
    if token in _NO:
        return False
    return None


def normalize_doi(text: str) -> str:
    """Riduce un DOI alla sola parte ``10.xxxx/...`` togliendo ``https://doi.org/`` e simili.

    >>> normalize_doi("https://doi.org/10.1111/j.1540-6261.1992.tb04681.x")
    '10.1111/j.1540-6261.1992.tb04681.x'
    >>> normalize_doi(" doi:10.1/x ")
    '10.1/x'
    """
    doi = text.strip()
    doi = _DOI_PREFIX_RE.sub("", doi)
    if doi.lower().startswith("doi:"):
        doi = doi[4:].strip()
    return doi


def normalize_tags(text: str) -> list[str]:
    """Trasforma ``"Moving Average, trend-following"`` nella lista di tag kebab-case
    ``['moving-average', 'trend-following']`` (senza duplicati né vuoti).

    >>> normalize_tags("Moving Average, trend-following,, moving-average")
    ['moving-average', 'trend-following']
    """
    tags: list[str] = []
    for part in re.split(r"[,;]", text):
        tag = ne.slugify(part)
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _quote_windows(arg: str) -> str:
    """Quoting per ``cmd.exe``: virgolette doppie solo se servono, con ``"`` raddoppiate."""
    if arg and not re.search(r'[\s"&|<>^()%!]', arg):
        return arg
    return '"' + arg.replace('"', '""') + '"'


def format_command(argv: Sequence[str], *, windows: bool | None = None, python: str | None = None) -> str:
    """Comando ``new_entry.py`` equivalente agli argomenti, pronto da incollare nel terminale.

    Su Windows (``windows=True``, default: ``os.name == "nt"``) usa ``py -3`` e
    virgolette doppie in stile ``cmd.exe``; altrove ``python3`` e il quoting POSIX
    di :func:`shlex.quote`.

    >>> format_command(["indicator", "MA Band", "--tags", "a,b"], windows=False)
    "python3 tools/new_entry.py indicator 'MA Band' --tags a,b"
    >>> format_command(["indicator", "MA Band"], windows=True)
    'py -3 tools\\\\new_entry.py indicator "MA Band"'
    """
    if windows is None:
        windows = os.name == "nt"
    if windows:
        interpreter = python or "py -3"
        parts = [interpreter, "tools\\new_entry.py", *(_quote_windows(a) for a in argv)]
    else:
        interpreter = python or "python3"
        parts = [interpreter, "tools/new_entry.py", *(shlex.quote(a) for a in argv)]
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Procedura guidata
# ---------------------------------------------------------------------------


@dataclass
class WizardOutcome:
    """Cosa ha deciso e fatto la procedura guidata (usato dai test e dal chiamante).

    :param kind: tipo di voce (``indicator``, ``strategy``, ``function``, ``paper``).
    :param folder: slug o id della cartella creata.
    :param argv: argomenti passati a :func:`new_entry.main`.
    :param command: comando equivalente mostrato all'utente.
    :param exit_code: codice di uscita della procedura (0 = voce creata).
    :param created: percorsi (relativi alla radice) scritti da ``new_entry.py``.
    """

    kind: str = ""
    folder: str = ""
    argv: list[str] = field(default_factory=list)
    command: str = ""
    exit_code: int = 1
    created: list[str] = field(default_factory=list)

    @property
    def relative_dir(self) -> str:
        return f"{ne.TYPE_DIRS[self.kind]}/{self.folder}" if self.kind else ""


class Wizard:
    """Procedura guidata interattiva.

    :param ask: funzione ``prompt -> str`` (default :func:`input`).
    :param say: funzione ``str -> None`` (default :func:`print`).
    :param root: radice del repository (default: cartella padre di ``tools/``).
    :param date: data ``AAAA-MM-GG`` da passare a ``new_entry.py`` (default: oggi).
    :param dry_run: passa ``--dry-run`` a ``new_entry.py`` (non scrive nulla).
    :param open_folder: funzione ``Path -> None`` usata per aprire la cartella della
        nuova voce; default :func:`os.startfile` dove esiste (Windows), altrimenti
        la domanda non viene posta. Passare ``None`` esplicito per disattivarla.
    :param windows: stile del comando mostrato (default: in base al sistema).
    """

    def __init__(
        self,
        ask: Callable[[str], str] = input,
        say: Callable[[str], None] = print,
        *,
        root: str | Path | None = None,
        date: str | None = None,
        dry_run: bool = False,
        open_folder: Callable[[Path], None] | None | bool = True,
        windows: bool | None = None,
    ) -> None:
        self.ask = ask
        self.say = say
        self.root = Path(root).resolve() if root else ne.default_root()
        self.date = date
        self.dry_run = dry_run
        if open_folder is True:
            startfile = getattr(os, "startfile", None)  # solo Windows
            self.open_folder: Callable[[Path], None] | None = (
                (lambda path: startfile(str(path))) if callable(startfile) else None
            )
        elif open_folder is False:
            self.open_folder = None
        else:
            self.open_folder = open_folder
        self.windows = os.name == "nt" if windows is None else windows
        self.outcome = WizardOutcome()
        self._lib: bc.Library | None = None

    # -- accesso alla libreria esistente -------------------------------------

    @property
    def lib(self) -> bc.Library:
        """Libreria caricata da ``root`` (lettura pigra, una sola volta)."""
        if self._lib is None:
            self._lib = bc.load_library(self.root)
        return self._lib

    def existing_papers(self) -> list[bc.Entry]:
        return list(self.lib.papers)

    def existing_functions(self) -> list[bc.Entry]:
        return self.lib.entries_of_type("function")

    def existing_tags(self) -> list[str]:
        """Tag già usati nella libreria (codice e fonti), ordinati."""
        tags: set[str] = set(bc.tags_index(self.lib))
        for paper in self.lib.papers:
            tags.update(t.strip() for t in bc._as_str_list(paper.meta.get("tags")) if t.strip())
        return sorted(tags)

    def existing_code_slugs(self) -> set[str]:
        return {e.folder for e in self.lib.entries} | {e.key for e in self.lib.entries}

    def existing_paper_ids(self) -> set[str]:
        return {p.folder for p in self.lib.papers} | {p.key for p in self.lib.papers}

    # -- domande elementari --------------------------------------------------

    def _ask(self, prompt: str) -> str:
        """Pone una domanda; Ctrl+C o fine input diventano :class:`WizardCancelled`."""
        try:
            answer = self.ask(prompt)
        except (KeyboardInterrupt, EOFError):
            raise WizardCancelled() from None
        return "" if answer is None else str(answer)

    def ask_text(
        self,
        prompt: str,
        *,
        default: str = "",
        required: bool = True,
        validator: Callable[[str], str | None] | None = None,
    ) -> str:
        """Chiede un testo su una riga finché non è valido.

        ``validator`` riceve il testo normalizzato e ritorna un messaggio d'errore
        (in italiano) oppure ``None`` se va bene. Con ``default`` la risposta vuota
        vale il default; con ``required`` una risposta vuota viene rifiutata.
        """
        suffix = f" [{default}]" if default else ""
        while True:
            answer = ne.clean_text(self._ask(f"{prompt}{suffix}: "))
            if not answer and default:
                answer = default
            if not answer:
                if not required:
                    return ""
                self.say("  Il valore non può essere vuoto: riprovare.")
                continue
            if validator is not None:
                problem = validator(answer)
                if problem:
                    self.say(f"  {problem}")
                    continue
            return answer

    def ask_choice(self, prompt: str, options: Sequence[str], *, default: int | None = None, zero_label: str | None = None) -> int:
        """Mostra un menu numerato e ritorna il numero scelto (1-based; 0 se ``zero_label``)."""
        count = len(options)
        for index, label in enumerate(options, start=1):
            self.say(f"  {index}) {label}")
        if zero_label:
            self.say(f"  0) {zero_label}")
        suffix = f" [{default}]" if default is not None else ""
        while True:
            answer = self._ask(f"{prompt}{suffix}: ").strip()
            if not answer and default is not None:
                return default
            choice = parse_choice(answer, count, allow_zero=zero_label is not None)
            if choice is not None:
                return choice
            low = "0" if zero_label else "1"
            self.say(f"  Scelta non valida: inserire un numero da {low} a {count}.")

    def ask_yes_no(self, prompt: str, *, default: bool | None = None) -> bool:
        """Domanda S/N; con ``default`` la risposta vuota vale il default."""
        hint = "S/n" if default is True else "s/N" if default is False else "S/N"
        while True:
            answer = parse_yes_no(self._ask(f"{prompt} [{hint}] "), default)
            if answer is not None:
                return answer
            self.say("  Rispondere S (sì) oppure N (no).")

    def ask_multi(
        self,
        prompt: str,
        options: Sequence[bc.Entry],
        *,
        describe: Callable[[bc.Entry], str],
        extra: Callable[[str], str | None] | None = None,
        extra_hint: str = "",
    ) -> list[str]:
        """Scelta multipla da un elenco numerato di voci; Invio per nessuna.

        Ritorna le chiavi (slug/id) scelte. Oltre ai numeri accetta una chiave
        scritta per intero se corrisponde a una voce; con ``extra`` anche valori
        nuovi: ``extra(token)`` ritorna un messaggio d'errore oppure ``None`` per
        accettarlo.
        """
        keys = [e.key for e in options]
        if options:
            for index, entry in enumerate(options, start=1):
                self.say(f"  {index}) {describe(entry)}")
            hint = "numeri separati da virgola" + (f", oppure {extra_hint}" if extra_hint else "") + "; Invio per nessuna"
        else:
            self.say("  (nessuna voce presente)")
            hint = (f"scrivere {extra_hint}; " if extra_hint else "") + "Invio per nessuna"
        while True:
            answer = self._ask(f"{prompt} ({hint}): ").strip()
            chosen: list[str] = []
            problem: str | None = None
            for token in re.split(r"[,;]", answer):
                token = token.strip()
                if not token:
                    continue
                if _DIGITS_RE.match(token):
                    index = parse_choice(token, len(options))
                    if index is None:
                        if not options:
                            problem = "Nessuna voce in elenco: premere Invio" + (f" oppure scrivere {extra_hint}" if extra_hint else "") + "."
                        else:
                            problem = f"Numero fuori intervallo: '{token}' (ammessi da 1 a {len(options)})."
                        break
                    value = keys[index - 1]
                elif token in keys:
                    value = token
                elif extra is not None:
                    problem = extra(token)
                    if problem:
                        break
                    value = token
                else:
                    problem = f"Valore non riconosciuto: '{token}'. Usare i numeri dell'elenco."
                    break
                if value not in chosen:
                    chosen.append(value)
            if problem:
                self.say(f"  {problem}")
                continue
            return chosen

    # -- validatori -----------------------------------------------------------

    def _validate_code_name(self, kind: str) -> Callable[[str], str | None]:
        def validate(name: str) -> str | None:
            if kind == "function":
                if not is_powerlanguage_identifier(name):
                    return (
                        "Nome non valido per una funzione: deve essere un identificatore PowerLanguage "
                        "(solo lettere, cifre e underscore, senza spazi, non può iniziare con una cifra), "
                        "es. BLL_MA_Band_Signal."
                    )
                stem = Path(ne.source_file_name(name)).stem
                if stem != name:
                    return (
                        f"Nome non valido per una funzione: il file sorgente sarebbe {stem}.pl e deve "
                        f"coincidere con il nome; evitare underscore iniziali, finali o doppi."
                    )
                return None
            try:
                ne.source_file_name(name)
            except ValueError:
                return "Il nome deve contenere almeno una lettera o una cifra."
            if not ne.slugify(name):
                return "Impossibile derivare uno slug dal nome: usare lettere o cifre."
            return None

        return validate

    def _validate_slug(self, kind: str) -> Callable[[str], str | None]:
        def validate(slug: str) -> str | None:
            if not ne.SLUG_RE.match(slug):
                what, example = ("Id", "1992-brock-simple-trading-rules") if kind == "paper" else ("Slug", "bll1992-ma-band")
                return f"{what} non valido: usare kebab-case [a-z0-9]+(-[a-z0-9]+)* (es. {example})."
            if kind == "paper":
                exists = slug in self.existing_paper_ids() or (self.root / ne.TYPE_DIRS["paper"] / slug).exists()
                return f"Esiste già una fonte con id '{slug}': scegliere un altro id." if exists else None
            exists = slug in self.existing_code_slugs() or any(
                (self.root / d / slug).exists() for d in (ne.TYPE_DIRS[k] for k in ("indicator", "strategy", "function"))
            )
            return f"Esiste già una voce con slug '{slug}': scegliere un altro slug." if exists else None

        return validate

    @staticmethod
    def _validate_year(year: str) -> str | None:
        return None if _YEAR_RE.match(year) else "Anno non valido: inserire quattro cifre (es. 1992)."

    @staticmethod
    def _validate_authors(authors: str) -> str | None:
        return None if ne.split_authors(authors) else "Indicare almeno un autore come 'Nome Cognome'."

    @staticmethod
    def _validate_new_paper_id(token: str) -> str | None:
        if ne.SLUG_RE.match(token):
            return None
        return (
            f"'{token}' non è né un numero dell'elenco né un id valido "
            f"(kebab-case, es. 1992-brock-lakonishok-lebaron-simple-technical-trading-rules)."
        )

    # -- raccolta dati -------------------------------------------------------

    def ask_tags(self) -> list[str]:
        suggestions = self.existing_tags()
        if suggestions:
            self.say("  Tag già usati nella libreria: " + ", ".join(suggestions))
        answer = self._ask("Tag (separati da virgola, in inglese; Invio per nessuno): ")
        tags = normalize_tags(answer)
        typed = [t.strip() for t in re.split(r"[,;]", answer) if t.strip()]
        if answer.strip() and not tags:
            self.say(f"  AVVISO: nessun tag valido ricavato da '{answer.strip()}' (usare lettere o cifre): tags resta vuoto.")
        elif tags and tags != typed:
            self.say("  Tag normalizzati in kebab-case: " + ", ".join(tags))
        return tags

    def collect_code_entry(self, kind: str) -> list[str]:
        """Domande per indicatori, strategie e funzioni; ritorna gli argomenti per ``new_entry.py``."""
        label = ne.TYPE_LABELS[kind]
        self.say("")
        if kind == "function":
            self.say(
                "Il nome di una funzione deve essere un identificatore PowerLanguage valido (lettere, cifre e "
                "underscore, non inizia con una cifra) e coincide con il nome del file .pl e dello studio in MultiCharts."
            )
        name = self.ask_text(f"Nome dello studio ({label}), come apparirà in MultiCharts", validator=self._validate_code_name(kind))
        derived_slug = ne.slugify(name)
        source_file = ne.source_file_name(name)
        self.say(f"  Slug derivato: {derived_slug}   File sorgente: {source_file}")
        slug = self.ask_text("Slug della cartella (Invio per accettare)", default=derived_slug, validator=self._validate_slug(kind))

        self.say("")
        self.say("Fonti da cui deriva il codice (schede in papers/):")
        papers = self.ask_multi(
            "Fonti",
            self.existing_papers(),
            describe=lambda p: f"{p.key} — {p.display_name} ({p.meta.get('year', '?')})",
            extra=self._validate_new_paper_id,
            extra_hint="l'id di una fonte nuova da creare in seguito",
        )
        for pid in papers:
            if pid not in self.existing_paper_ids():
                self.say(f"  AVVISO: la fonte '{pid}' non esiste ancora: crearla con la procedura guidata (tipo Fonte) prima di eseguire 'Verifica'.")

        self.say("")
        self.say("Funzioni della libreria richieste dallo studio (campo depends_on):")
        depends = self.ask_multi(
            "Dipendenze",
            self.existing_functions(),
            describe=lambda f: f"{f.key} — {f.display_name}",
        )

        self.say("")
        tags = self.ask_tags()
        summary = self.ask_text("Sintesi in una riga (Invio per saltare)", required=False)

        argv = [kind, name]
        if slug != derived_slug:
            argv += ["--slug", slug]
        for pid in papers:
            argv += ["--paper", pid]
        for dep in depends:
            argv += ["--depends", dep]
        if tags:
            argv += ["--tags", ",".join(tags)]
        if summary:
            argv += ["--summary", summary]
        self.outcome.kind = kind
        self.outcome.folder = slug
        return argv

    def collect_paper(self) -> list[str]:
        """Domande per una fonte; ritorna gli argomenti per ``new_entry.py``."""
        self.say("")
        title = self.ask_text("Titolo originale della fonte (non tradotto)")
        authors_text = self.ask_text("Autori, come 'Nome Cognome' separati da virgola", validator=self._validate_authors)
        authors = ne.split_authors(authors_text)
        year = self.ask_text("Anno di pubblicazione (4 cifre)", validator=self._validate_year)
        self.say("Tipo di fonte:")
        type_index = self.ask_choice("Tipo", [PAPER_TYPE_LABELS[t] for t in ne.PAPER_TYPES], default=1)
        paper_type = ne.PAPER_TYPES[type_index - 1]
        doi = normalize_doi(self.ask_text("DOI (senza https://doi.org/; Invio per nessuno)", required=False))
        url = self.ask_text("URL della fonte (Invio per nessuno)", required=False)
        self.say("")
        tags = self.ask_tags()
        summary = self.ask_text("Sintesi in una riga (Invio per saltare)", required=False)

        derived_id = ne.paper_id(year, authors, title)
        self.say(f"  Id derivato: {derived_id}")
        pid = self.ask_text("Id della fonte (Invio per accettare)", default=derived_id, validator=self._validate_slug("paper"))

        argv = ["paper", title, "--authors", ", ".join(authors), "--year", year]
        if pid != derived_id:
            argv += ["--id", pid]
        if paper_type != "paper":
            argv += ["--type", paper_type]
        if doi:
            argv += ["--doi", doi]
        if url:
            argv += ["--url", url]
        if tags:
            argv += ["--tags", ",".join(tags)]
        if summary:
            argv += ["--summary", summary]
        self.outcome.kind = "paper"
        self.outcome.folder = pid
        return argv

    # -- esecuzione ----------------------------------------------------------

    def _common_options(self) -> list[str]:
        options: list[str] = []
        if self.root != ne.default_root():
            options += ["--root", str(self.root)]
        if self.date:
            options += ["--date", self.date]
        if self.dry_run:
            options.append("--dry-run")
        return options

    def _run_new_entry(self, argv: list[str]) -> int:
        """Chiama :func:`new_entry.main` nello stesso processo e riporta il suo output tramite ``say``."""
        out, err = io.StringIO(), io.StringIO()
        try:
            code = ne.main(argv, out=out, err=err)
        except SystemExit as exc:  # argparse: argomenti non validi (non dovrebbe succedere)
            code = exc.code if isinstance(exc.code, int) else 1
        errors = err.getvalue().rstrip("\n")
        if errors:
            self.say(errors)
        # new_entry.py stampa anche i suoi "Prossimi passi": qui si mostra solo l'elenco dei
        # file creati, i passi successivi li elenca la procedura guidata (vedi _next_steps).
        report = out.getvalue().split("\nProssimi passi:", 1)[0].rstrip("\n")
        if report:
            self.say(report)
        created = re.findall(r"^  (\S+)$", report, flags=re.MULTILINE)
        self.outcome.created = [p for p in created if "/" in p and not p.endswith(".bak")]
        return code

    def _next_steps(self) -> list[str]:
        rel = self.outcome.relative_dir
        steps = [f"Aprire la scheda {rel}/README.md e compilare le sezioni."]
        if self.outcome.kind != "paper":
            source = next((p for p in self.outcome.created if p.endswith(".pl")), f"{rel}/<NomeFile>.pl")
            steps.append(f"Incollare il codice PowerLanguage in {source} (dal PowerLanguage Editor: seleziona tutto, copia, incolla).")
        steps.append("Dal menu di avvia.bat eseguire 'Verifica' (test + catalogo), poi 'Salva su GitHub'.")
        steps.append("Da terminale, in alternativa: python tools/build_catalog.py")
        return steps

    def run(self) -> int:
        """Esegue la procedura completa. Ritorna il codice di uscita (0 = voce creata)."""
        try:
            return self._run()
        except (WizardCancelled, KeyboardInterrupt, EOFError):
            self.say("")
            self.say(CANCELLED_MESSAGE)
            self.outcome.exit_code = 1
            return 1

    def _run(self) -> int:
        problem = bc.library_root_problem(self.root)
        if problem:
            self.say(f"ERRORE {self.root}: {problem}")
            return 1
        self.say("=== Nuova voce della libreria PowerLanguage ===")
        self.say(f"Repository: {self.root}")
        self.say("Ctrl+C in qualunque momento per annullare.")
        if self.lib.load_errors:
            self.say("")
            for problem in self.lib.load_errors:
                self.say(problem)
            self.say("  (queste voci non compaiono negli elenchi; correggerle prima di eseguire 'Verifica')")
        self.say("")
        self.say("Che cosa vuoi aggiungere?")
        choice = self.ask_choice("Tipo di voce", [label for _, label in KIND_MENU], zero_label="Annulla")
        if choice == 0:
            raise WizardCancelled()
        kind = KIND_MENU[choice - 1][0]

        argv = self.collect_paper() if kind == "paper" else self.collect_code_entry(kind)
        argv += self._common_options()
        command = format_command(argv, windows=self.windows)
        self.outcome.argv = argv
        self.outcome.command = command

        self.say("")
        self.say("Riepilogo:")
        self.say(f"  Tipo:     {ne.TYPE_LABELS[kind]}")
        self.say(f"  Cartella: {self.outcome.relative_dir}/")
        self.say("Comando equivalente (da terminale, nella cartella della libreria):")
        self.say(f"  {command}")
        self.say("")
        if not self.ask_yes_no("Procedere con la creazione?" if not self.dry_run else "Procedere (prova, nessun file scritto)?"):
            raise WizardCancelled()

        self.say("")
        code = self._run_new_entry(argv)
        self.outcome.exit_code = code
        if code != 0:
            self.say("")
            self.say("La voce NON è stata creata. Correggere quanto segnalato sopra e riprovare.")
            return code
        if self.dry_run:
            return 0

        self.say("")
        self.say("Fatto. Prossimi passi:")
        for index, step in enumerate(self._next_steps(), start=1):
            self.say(f"  {index}. {step}")
        if self.open_folder is not None:
            folder = self.root / self.outcome.relative_dir
            # La voce esiste già: Ctrl+C a questa domanda facoltativa non è un annullamento.
            try:
                wants_open = self.ask_yes_no("Aprire adesso la cartella della nuova voce?", default=True)
            except WizardCancelled:
                wants_open = False
                self.say("")
            if wants_open:
                try:
                    self.open_folder(folder)
                except OSError as exc:
                    self.say(f"  Impossibile aprire la cartella: {exc}")
        return 0


# ---------------------------------------------------------------------------
# Riga di comando
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wizard.py",
        description="Procedura guidata per aggiungere una voce alla libreria (chiama tools/new_entry.py).",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="mostra questo messaggio di aiuto ed esce")
    parser.add_argument("--root", metavar="PERCORSO", help="radice del repository (default: cartella padre di tools/)")
    parser.add_argument("--date", metavar="AAAA-MM-GG", help="data per created/updated/added (default: oggi)")
    parser.add_argument("--dry-run", action="store_true", help="mostra cosa verrebbe creato senza scrivere nulla")
    return parser


def _console_utf8_safe() -> None:
    """Evita UnicodeEncodeError/UnicodeDecodeError su console non UTF-8 (es. cp1252 su
    Windows, o input ridiretto con PYTHONIOENCODING=ascii): i byte non decodificabili
    letti da ``input()`` diventano U+FFFD, quelli non codificabili in uscita ``\\xNN``."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="replace" if stream is sys.stdin else "backslashreplace")
            except (ValueError, OSError):
                pass


def main(
    argv: list[str] | None = None,
    ask: Callable[[str], str] = input,
    say: Callable[[str], None] = print,
    **wizard_options: object,
) -> int:
    """Punto di ingresso della riga di comando. Ritorna il codice di uscita (0 = voce creata, 1 = annullata/errore)."""
    _console_utf8_safe()
    args = build_arg_parser().parse_args(argv)
    if args.date:
        try:
            if not ne.DATE_RE.match(args.date):
                raise ValueError
            _dt.date.fromisoformat(args.date)
        except ValueError:
            say(f"ERRORE: --date '{args.date}' non valida: usare il formato AAAA-MM-GG")
            return 2
    wizard = Wizard(ask, say, root=args.root, date=args.date, dry_run=args.dry_run, **wizard_options)  # type: ignore[arg-type]
    return wizard.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print(CANCELLED_MESSAGE)
        sys.exit(1)
