"""Test (solo libreria standard) per ``tools/wizard.py``, la procedura guidata.

Ogni test lavora in una cartella temporanea che contiene una copia di ``templates/``
del repository e cartelle ``indicators/``, ``strategies/``, ``functions/``, ``papers/``
vuote (o con una fonte e una funzione di partenza create con ``new_entry.py``). Le
risposte dell'utente sono predefinite tramite il callable ``ask`` e l'output viene
raccolto tramite ``say``: nessun test tocca ``builtins.input`` né il repository reale.

Esecuzione dalla radice del repository::

    python -m unittest discover -s tools/tests -v
"""

from __future__ import annotations

import io
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
import wizard  # noqa: E402

REPO_ROOT = TOOLS_DIR.parent
FIXED_DATE = "2024-01-15"
PAPER_ID = "2001-rossi-bianchi-regole-trading-semplici"  # "di" è una parola vuota
FUNCTION_NAME = "MA_Signal"
FUNCTION_SLUG = "ma-signal"


# ---------------------------------------------------------------------------
# Utilità
# ---------------------------------------------------------------------------


class ScriptedIO:
    """Risposte predefinite per ``ask`` e trascrizione di tutto ciò che passa per ``say``."""

    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []
        self.lines: list[str] = []

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.answers:
            raise AssertionError(f"risposte predefinite esaurite al prompt: {prompt!r}\n" + self.transcript)
        return self.answers.pop(0)

    def say(self, text: str = "") -> None:
        self.lines.append(str(text))

    @property
    def transcript(self) -> str:
        return "\n".join(self.lines)

    @property
    def prompt_text(self) -> str:
        return "\n".join(self.prompts)


def front_matter_of(path: Path) -> dict[str, object]:
    return bc.parse_front_matter(path.read_text(encoding="utf-8"))


class TempRepoTestCase(unittest.TestCase):
    """Radice temporanea con i template reali e, a richiesta, una fonte e una funzione."""

    seed = True

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="wizard-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        shutil.copytree(REPO_ROOT / "templates", self.root / "templates")
        for name in ("indicators", "strategies", "functions", "papers"):
            (self.root / name).mkdir()
        if self.seed:
            self.new_entry(
                "paper", "Regole di trading semplici", "--authors", "Mario Rossi, Luca Bianchi",
                "--year", "2001", "--tags", "moving-average", "--doi", "10.1000/xyz",
            )
            self.new_entry("function", FUNCTION_NAME, "--tags", "trend-following", "--paper", PAPER_ID)

    def new_entry(self, *argv: str) -> None:
        out, err = io.StringIO(), io.StringIO()
        code = ne.main([*argv, "--root", str(self.root), "--date", FIXED_DATE], out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())

    def run_wizard(self, answers: list[str], **options: object) -> tuple[int, wizard.Wizard, ScriptedIO]:
        io_ = ScriptedIO(answers)
        options.setdefault("open_folder", None)
        options.setdefault("windows", False)
        options.setdefault("date", FIXED_DATE)
        w = wizard.Wizard(io_.ask, io_.say, root=self.root, **options)  # type: ignore[arg-type]
        code = w.run()
        return code, w, io_

    def assert_library_valid(self) -> None:
        lib = bc.load_library(self.root)
        self.assertEqual(bc.validate(lib), [])


# ---------------------------------------------------------------------------
# Funzioni pure
# ---------------------------------------------------------------------------


class TestPureFunctions(unittest.TestCase):
    def test_is_powerlanguage_identifier(self) -> None:
        for good in ("BLL_MA_Band_Signal", "_x", "a1", "Average2"):
            self.assertTrue(wizard.is_powerlanguage_identifier(good), good)
        for bad in ("", "3Bar", "MA Band", "ma-band", "Média", "a.b", "x!"):
            self.assertFalse(wizard.is_powerlanguage_identifier(bad), bad)

    def test_parse_choice(self) -> None:
        self.assertEqual(wizard.parse_choice("2", 4), 2)
        self.assertEqual(wizard.parse_choice(" 4 ", 4), 4)
        self.assertIsNone(wizard.parse_choice("5", 4))
        self.assertIsNone(wizard.parse_choice("0", 4))
        self.assertEqual(wizard.parse_choice("0", 4, allow_zero=True), 0)
        self.assertIsNone(wizard.parse_choice("-1", 4, allow_zero=True))
        self.assertIsNone(wizard.parse_choice("abc", 4))
        self.assertIsNone(wizard.parse_choice("", 4))

    def test_non_ascii_digits_are_not_numbers(self) -> None:
        # str.isdigit() è vero per "²" e per le cifre arabo-indiane, ma int() le rifiuta:
        # non devono mai arrivare a int() (traceback), ma essere scartate come scelta.
        for odd in ("²", "³", "٣", "1²"):
            self.assertIsNone(wizard.parse_choice(odd, 4), odd)
            self.assertIsNone(wizard.parse_multi_choice(odd, 3), odd)
        self.assertEqual(wizard.parse_choice("4", 4), 4)

    def test_parse_multi_choice(self) -> None:
        self.assertEqual(wizard.parse_multi_choice("1, 3,1", 3), [1, 3])
        self.assertEqual(wizard.parse_multi_choice("2 3", 3), [2, 3])
        self.assertEqual(wizard.parse_multi_choice("", 3), [])
        self.assertIsNone(wizard.parse_multi_choice("1,9", 3))
        self.assertIsNone(wizard.parse_multi_choice("uno", 3))

    def test_parse_yes_no(self) -> None:
        for yes in ("s", "S", "si", "sì", "y", "yes", " S "):
            self.assertIs(wizard.parse_yes_no(yes), True, yes)
        for no in ("n", "N", "no", "NO"):
            self.assertIs(wizard.parse_yes_no(no), False, no)
        self.assertIsNone(wizard.parse_yes_no(""))
        self.assertIs(wizard.parse_yes_no("", default=True), True)
        self.assertIsNone(wizard.parse_yes_no("forse"))

    def test_normalize_doi(self) -> None:
        self.assertEqual(wizard.normalize_doi("https://doi.org/10.1111/j.1540-6261.1992.tb04681.x"), "10.1111/j.1540-6261.1992.tb04681.x")
        self.assertEqual(wizard.normalize_doi("http://dx.doi.org/10.1/x"), "10.1/x")
        self.assertEqual(wizard.normalize_doi("doi:10.1/x"), "10.1/x")
        self.assertEqual(wizard.normalize_doi(" 10.1/x "), "10.1/x")
        self.assertEqual(wizard.normalize_doi(""), "")

    def test_normalize_tags(self) -> None:
        self.assertEqual(wizard.normalize_tags("Moving Average, trend-following,, moving-average"), ["moving-average", "trend-following"])
        self.assertEqual(wizard.normalize_tags("  "), [])
        self.assertEqual(wizard.normalize_tags("Volatilità; breakout"), ["volatilita", "breakout"])

    def test_format_command_posix_and_windows(self) -> None:
        argv = ["indicator", "MA Band", "--tags", "a,b", "--summary", 'Una "riga".']
        posix = wizard.format_command(argv, windows=False)
        self.assertTrue(posix.startswith("python3 tools/new_entry.py indicator 'MA Band' --tags a,b --summary "), posix)
        self.assertIn("riga", posix)
        win = wizard.format_command(argv, windows=True)
        self.assertEqual(win, 'py -3 tools\\new_entry.py indicator "MA Band" --tags a,b --summary "Una ""riga""."')
        self.assertEqual(wizard.format_command(["function", "X"], windows=False, python="python"), "python tools/new_entry.py function X")

    def test_doctests(self) -> None:
        import doctest

        failures, tests = doctest.testmod(wizard, verbose=False)
        self.assertEqual(failures, 0)
        self.assertGreater(tests, 0)


# ---------------------------------------------------------------------------
# Flussi completi per ogni tipo di voce
# ---------------------------------------------------------------------------


class TestIndicatorFlow(TempRepoTestCase):
    def test_indicator_end_to_end(self) -> None:
        code, w, io_ = self.run_wizard([
            "1",                                 # tipo: indicatore
            "BLL1992 MA Band",                   # nome
            "",                                  # slug: accetta quello derivato
            "1",                                 # fonte: la prima dell'elenco
            "1",                                 # dipendenza: la prima funzione
            "Moving Average, trend following",   # tag (normalizzati)
            "Media breve, media lunga e banda.", # sintesi
            "S",                                 # conferma
        ])
        self.assertEqual(code, 0, io_.transcript)
        expected_argv = [
            "indicator", "BLL1992 MA Band",
            "--paper", PAPER_ID,
            "--depends", FUNCTION_SLUG,
            "--tags", "moving-average,trend-following",
            "--summary", "Media breve, media lunga e banda.",
            "--root", str(self.root),
            "--date", FIXED_DATE,
        ]
        self.assertEqual(w.outcome.argv, expected_argv)
        self.assertEqual(w.outcome.relative_dir, "indicators/bll1992-ma-band")
        folder = self.root / "indicators" / "bll1992-ma-band"
        self.assertTrue((folder / "README.md").is_file())
        self.assertTrue((folder / "BLL1992_MA_Band.pl").is_file())
        meta = front_matter_of(folder / "README.md")
        self.assertEqual(meta["type"], "indicator")
        self.assertEqual(meta["name"], "BLL1992 MA Band")
        self.assertEqual(meta["slug"], "bll1992-ma-band")
        self.assertEqual(meta["papers"], [PAPER_ID])
        self.assertEqual(meta["depends_on"], [FUNCTION_SLUG])
        self.assertEqual(meta["tags"], ["moving-average", "trend-following"])
        self.assertEqual(meta["created"], FIXED_DATE)
        self.assertEqual(meta["summary"], "Media breve, media lunga e banda.")
        self.assertEqual(w.outcome.created, ["indicators/bll1992-ma-band/BLL1992_MA_Band.pl", "indicators/bll1992-ma-band/README.md"])
        self.assert_library_valid()

        # Il comando esatto è mostrato prima della conferma e corrisponde agli argomenti eseguiti.
        self.assertEqual(w.outcome.command, wizard.format_command(expected_argv, windows=False))
        self.assertIn(w.outcome.command, io_.transcript)
        self.assertLess(io_.transcript.index("Comando equivalente"), io_.transcript.index("Fatto. Prossimi passi"))
        self.assertIn("Procedere con la creazione? [S/N]", io_.prompt_text)
        # Elenchi numerati, suggerimenti e derivazioni mostrati all'utente.
        self.assertIn(f"1) {PAPER_ID} — Regole di trading semplici (2001)", io_.transcript)
        self.assertIn(f"1) {FUNCTION_SLUG} — {FUNCTION_NAME}", io_.transcript)
        self.assertIn("Tag già usati nella libreria: moving-average, trend-following", io_.transcript)
        self.assertIn("Tag normalizzati in kebab-case: moving-average, trend-following", io_.transcript)
        self.assertIn("Slug derivato: bll1992-ma-band   File sorgente: BLL1992_MA_Band.pl", io_.transcript)
        # Esito: file creati e prossimi passi (una sola volta), nessuna domanda sulla cartella (open_folder=None).
        self.assertIn("indicators/bll1992-ma-band/README.md", io_.transcript)
        self.assertEqual(io_.transcript.count("Prossimi passi"), 1)
        self.assertIn("Verifica", io_.transcript)
        self.assertNotIn("Aprire adesso la cartella", io_.prompt_text)

    def test_indicator_with_custom_slug_new_paper_id_and_no_dependencies(self) -> None:
        code, w, io_ = self.run_wizard([
            "1",
            "3 Bar Reversal",
            "tre-barre",                         # slug personalizzato
            "2020-nuovo-paper, 1",               # id nuovo + fonte esistente
            "",                                  # nessuna dipendenza
            "",                                  # nessun tag
            "",                                  # nessuna sintesi
            "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertEqual(w.outcome.argv[:6], ["indicator", "3 Bar Reversal", "--slug", "tre-barre", "--paper", "2020-nuovo-paper"])
        self.assertIn("--paper", w.outcome.argv[6:])
        self.assertNotIn("--depends", w.outcome.argv)
        self.assertNotIn("--tags", w.outcome.argv)
        self.assertNotIn("--summary", w.outcome.argv)
        folder = self.root / "indicators" / "tre-barre"
        self.assertTrue((folder / "_3_Bar_Reversal.pl").is_file(), "il file sorgente ha l'underscore iniziale")
        self.assertEqual(front_matter_of(folder / "README.md")["papers"], ["2020-nuovo-paper", PAPER_ID])
        self.assertIn("AVVISO: la fonte '2020-nuovo-paper' non esiste ancora", io_.transcript)


class TestStrategyFlow(TempRepoTestCase):
    def test_strategy_end_to_end(self) -> None:
        code, w, io_ = self.run_wizard([
            "2",
            "BLL1992 MA Crossover",
            "",
            PAPER_ID,                            # fonte scritta per intero (id esistente)
            FUNCTION_SLUG,                       # dipendenza scritta per intero
            "moving-average",
            "Crossover di medie con HoldDays.",
            "si",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertEqual(w.outcome.argv, [
            "strategy", "BLL1992 MA Crossover",
            "--paper", PAPER_ID, "--depends", FUNCTION_SLUG,
            "--tags", "moving-average", "--summary", "Crossover di medie con HoldDays.",
            "--root", str(self.root), "--date", FIXED_DATE,
        ])
        folder = self.root / "strategies" / "bll1992-ma-crossover"
        meta = front_matter_of(folder / "README.md")
        self.assertEqual(meta["type"], "strategy")
        self.assertEqual(meta["source_file"], "BLL1992_MA_Crossover.pl")
        self.assertTrue((folder / "BLL1992_MA_Crossover.pl").is_file())
        self.assert_library_valid()

    def test_unknown_dependency_is_rejected_and_reasked(self) -> None:
        code, w, io_ = self.run_wizard([
            "2", "Strat", "",
            "",                                  # nessuna fonte
            "9",                                 # numero fuori intervallo
            "non-esiste",                        # slug sconosciuto
            "1",                                 # ok
            "", "", "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertIn("Numero fuori intervallo: '9'", io_.transcript)
        self.assertIn("Valore non riconosciuto: 'non-esiste'", io_.transcript)
        self.assertEqual(w.outcome.argv[2:4], ["--depends", FUNCTION_SLUG])


class TestFunctionFlow(TempRepoTestCase):
    def test_function_end_to_end(self) -> None:
        code, w, io_ = self.run_wizard([
            "3",
            "BLL_MA_Band_Signal",
            "",
            "1",
            "1",                                 # dipende dalla funzione esistente
            "moving-average",
            "Segnale +1/-1/0 dalla banda.",
            "S",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertEqual(w.outcome.argv[:2], ["function", "BLL_MA_Band_Signal"])
        folder = self.root / "functions" / "bll-ma-band-signal"
        self.assertTrue((folder / "BLL_MA_Band_Signal.pl").is_file())
        meta = front_matter_of(folder / "README.md")
        self.assertEqual(meta["name"], "BLL_MA_Band_Signal")
        self.assertEqual(meta["source_file"], "BLL_MA_Band_Signal.pl")
        self.assertEqual(meta["depends_on"], [FUNCTION_SLUG])
        self.assertIn("identificatore PowerLanguage", io_.transcript)  # avvertenza iniziale
        self.assert_library_valid()

    def test_invalid_function_names_are_rejected(self) -> None:
        code, w, io_ = self.run_wizard([
            "3",
            "3 Bar",                             # spazio e cifra iniziale
            "Bad-Name",                          # trattino
            "_Leading",                          # underscore iniziale: il file sarebbe Leading.pl
            "Good_Name",                         # ok
            "", "", "", "", "", "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertEqual(io_.transcript.count("Nome non valido per una funzione"), 3)
        self.assertIn("non può iniziare con una cifra", io_.transcript)
        self.assertIn("il file sorgente sarebbe Leading.pl", io_.transcript)
        self.assertEqual(w.outcome.folder, "good-name")
        self.assertTrue((self.root / "functions" / "good-name" / "Good_Name.pl").is_file())
        self.assert_library_valid()


class TestPaperFlow(TempRepoTestCase):
    def test_paper_end_to_end_with_validation(self) -> None:
        code, w, io_ = self.run_wizard([
            "4",
            "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns",
            "",                                  # autori vuoti → richiesti
            ", ;",                               # solo separatori → nessun autore
            "William Brock, Josef Lakonishok, Blake LeBaron",
            "millenovecento",                    # anno non numerico
            "92",                                # anno non a 4 cifre
            "1992",
            "",                                  # tipo: default paper
            "https://doi.org/10.1111/j.1540-6261.1992.tb04681.x",
            "https://doi.org/10.1111/j.1540-6261.1992.tb04681.x",
            "technical-analysis, Moving Average",
            "Test di regole di media mobile sul Dow Jones.",
            "",                                  # id: accetta quello derivato
            "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        pid = "1992-brock-lakonishok-lebaron-simple-technical-trading-rules"
        self.assertEqual(w.outcome.argv, [
            "paper", "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns",
            "--authors", "William Brock, Josef Lakonishok, Blake LeBaron",
            "--year", "1992",
            "--doi", "10.1111/j.1540-6261.1992.tb04681.x",
            "--url", "https://doi.org/10.1111/j.1540-6261.1992.tb04681.x",
            "--tags", "technical-analysis,moving-average",
            "--summary", "Test di regole di media mobile sul Dow Jones.",
            "--root", str(self.root), "--date", FIXED_DATE,
        ])
        self.assertEqual(w.outcome.relative_dir, f"papers/{pid}")
        readme = self.root / "papers" / pid / "README.md"
        meta = front_matter_of(readme)
        self.assertEqual(meta["type"], "paper")
        self.assertEqual(meta["id"], pid)
        self.assertEqual(meta["year"], 1992)
        self.assertEqual(meta["authors"], ["William Brock", "Josef Lakonishok", "Blake LeBaron"])
        self.assertEqual(meta["doi"], "10.1111/j.1540-6261.1992.tb04681.x")
        self.assertEqual(meta["added"], FIXED_DATE)
        self.assertEqual(io_.transcript.count("Anno non valido"), 2)
        self.assertEqual(io_.transcript.count("Il valore non può essere vuoto"), 1)
        self.assertIn("Indicare almeno un autore come 'Nome Cognome'.", io_.transcript)
        self.assertIn(f"Id derivato: {pid}", io_.transcript)
        self.assert_library_valid()

    def test_book_with_custom_id_and_type_menu_validation(self) -> None:
        code, w, io_ = self.run_wizard([
            "4",
            "Trading Systems",
            "Emilio Tomasini, Urban Jaekle",
            "2009",
            "9",                                 # tipo fuori intervallo
            "2",                                 # book
            "",                                  # DOI
            "",                                  # URL
            "",                                  # tag
            "",                                  # sintesi
            "ID NON VALIDO",                     # id non kebab-case
            PAPER_ID,                            # id già esistente
            "2009-tomasini-jaekle-trading-systems-libro",
            "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertEqual(w.outcome.argv, [
            "paper", "Trading Systems", "--authors", "Emilio Tomasini, Urban Jaekle", "--year", "2009",
            "--id", "2009-tomasini-jaekle-trading-systems-libro", "--type", "book",
            "--root", str(self.root), "--date", FIXED_DATE,
        ])
        self.assertIn("Scelta non valida: inserire un numero da 1 a 6.", io_.transcript)
        self.assertIn("Id non valido: usare kebab-case", io_.transcript)
        self.assertNotIn("Slug non valido", io_.transcript)
        self.assertIn(f"Esiste già una fonte con id '{PAPER_ID}'", io_.transcript)
        meta = front_matter_of(self.root / "papers" / "2009-tomasini-jaekle-trading-systems-libro" / "README.md")
        self.assertEqual(meta["type"], "book")
        self.assertIsNone(meta.get("doi"), "nessun DOI: il campo del template resta vuoto")
        self.assertIsNone(meta.get("url"))
        self.assert_library_valid()


# ---------------------------------------------------------------------------
# Validazione dei singoli passi e annullamento
# ---------------------------------------------------------------------------


class TestValidationAndCancel(TempRepoTestCase):
    def test_type_choice_out_of_range_is_reasked(self) -> None:
        code, w, io_ = self.run_wizard(["7", "abc", "", "-1", "0"])
        self.assertEqual(code, 1)
        self.assertEqual(io_.transcript.count("Scelta non valida: inserire un numero da 0 a 4."), 4)
        self.assertTrue(io_.transcript.endswith(wizard.CANCELLED_MESSAGE))

    def test_superscript_digit_in_menus_is_reasked_not_a_traceback(self) -> None:
        code, _w, io_ = self.run_wizard(["²", "0"])
        self.assertEqual(code, 1)
        self.assertIn("Scelta non valida: inserire un numero da 0 a 4.", io_.transcript)
        # stessa risposta alle domande "Fonti" e "Dipendenze" (ask_multi) e all'id nuovo
        code, _w, io_ = self.run_wizard(["1", "Studio", "", "²", "", "٣", "", "", "", "n"])
        self.assertEqual(code, 1, io_.transcript)
        self.assertIn("'²' non è né un numero dell'elenco né un id valido", io_.transcript)
        self.assertIn("Valore non riconosciuto: '٣'", io_.transcript)

    def test_empty_name_is_reasked(self) -> None:
        code, w, io_ = self.run_wizard(["1", "", "   ", "Nome Valido", "", "", "", "", "", "n"])
        self.assertEqual(code, 1)
        self.assertEqual(io_.transcript.count("Il valore non può essere vuoto"), 2)
        self.assertEqual(w.outcome.folder, "nome-valido")

    def test_name_without_letters_is_reasked(self) -> None:
        code, w, io_ = self.run_wizard(["1", "!!!", "Ok", "", "", "", "", "", "n"])
        self.assertEqual(code, 1)
        self.assertIn("Il nome deve contenere almeno una lettera o una cifra.", io_.transcript)

    def test_existing_slug_is_rejected(self) -> None:
        code, w, io_ = self.run_wizard([
            "1", "MA Signal",                    # slug derivato ma-signal = funzione esistente
            "",                                  # accettarlo non è possibile
            "Not Valid",                         # slug non kebab-case
            "ma-signal-ind",                     # ok
            "", "", "", "", "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertIn("Esiste già una voce con slug 'ma-signal'", io_.transcript)
        self.assertIn("Slug non valido", io_.transcript)
        self.assertEqual(w.outcome.folder, "ma-signal-ind")
        self.assertEqual(w.outcome.argv[2:4], ["--slug", "ma-signal-ind"])

    def test_confirmation_requires_s_or_n(self) -> None:
        code, w, io_ = self.run_wizard(["1", "Studio", "", "", "", "", "", "forse", "", "N"])
        self.assertEqual(code, 1)
        self.assertEqual(io_.transcript.count("Rispondere S (sì) oppure N (no)."), 2)
        self.assertFalse((self.root / "indicators" / "studio").exists())
        self.assertTrue(io_.transcript.endswith(wizard.CANCELLED_MESSAGE))
        self.assertIn(w.outcome.command, io_.transcript, "il comando è mostrato prima della conferma")

    def test_zero_in_type_menu_cancels(self) -> None:
        code, _w, io_ = self.run_wizard(["0"])
        self.assertEqual(code, 1)
        self.assertEqual(io_.lines[-1], wizard.CANCELLED_MESSAGE)

    def test_keyboard_interrupt_is_handled(self) -> None:
        io_ = ScriptedIO(["1", "Studio"])

        def ask(prompt: str) -> str:
            if io_.answers:
                return io_.ask(prompt)
            raise KeyboardInterrupt

        w = wizard.Wizard(ask, io_.say, root=self.root, open_folder=None, windows=False)
        self.assertEqual(w.run(), 1)
        self.assertEqual(io_.lines[-1], wizard.CANCELLED_MESSAGE)
        self.assertFalse((self.root / "indicators" / "studio").exists())

    def test_end_of_input_is_handled_like_cancel(self) -> None:
        def ask(prompt: str) -> str:
            raise EOFError

        io_ = ScriptedIO([])
        w = wizard.Wizard(ask, io_.say, root=self.root, open_folder=None)
        self.assertEqual(w.run(), 1)
        self.assertEqual(io_.lines[-1], wizard.CANCELLED_MESSAGE)

    def test_root_that_is_not_a_library_fails_before_asking(self) -> None:
        io_ = ScriptedIO([])
        w = wizard.Wizard(io_.ask, io_.say, root=self.tmp / "vuota", open_folder=None)
        self.assertEqual(w.run(), 1)
        self.assertEqual(io_.prompts, [])
        self.assertTrue(io_.lines[0].startswith("ERRORE "), io_.transcript)


class TestEmptyLibrary(TempRepoTestCase):
    seed = False

    def test_lists_are_empty_but_new_paper_id_can_be_typed(self) -> None:
        code, w, io_ = self.run_wizard([
            "1", "Studio", "",
            "NON VALIDO",                        # né numero né id valido
            "2020-nuovo-paper",
            "qualcosa",                          # nessuna funzione: ogni testo è rifiutato
            "",
            "", "", "s",
        ])
        self.assertEqual(code, 0, io_.transcript)
        self.assertEqual(io_.transcript.count("(nessuna voce presente)"), 2)
        self.assertIn("'NON VALIDO' non è né un numero dell'elenco né un id valido", io_.transcript)
        self.assertIn("Valore non riconosciuto: 'qualcosa'", io_.transcript)
        self.assertNotIn("Tag già usati", io_.transcript)
        self.assertEqual(w.outcome.argv[2:4], ["--paper", "2020-nuovo-paper"])

    def test_number_with_empty_list_gets_a_sensible_message(self) -> None:
        code, _w, io_ = self.run_wizard(["1", "Studio", "", "1", "", "2", "", "", "", "n"])
        self.assertEqual(code, 1, io_.transcript)
        self.assertIn("Nessuna voce in elenco: premere Invio oppure scrivere l'id di una fonte nuova da creare in seguito.", io_.transcript)
        self.assertIn("Nessuna voce in elenco: premere Invio.", io_.transcript)
        self.assertNotIn("ammessi da 1 a 0", io_.transcript)


# ---------------------------------------------------------------------------
# Opzioni: dry-run, apertura cartella, stile Windows, riga di comando
# ---------------------------------------------------------------------------


class TestOptions(TempRepoTestCase):
    def test_dry_run_writes_nothing(self) -> None:
        code, w, io_ = self.run_wizard(["1", "Prova", "", "", "", "", "", "s"], dry_run=True)
        self.assertEqual(code, 0, io_.transcript)
        self.assertFalse((self.root / "indicators" / "prova").exists())
        self.assertEqual(w.outcome.argv[-1], "--dry-run")
        self.assertIn("[dry-run]", io_.transcript)
        self.assertNotIn("Fatto. Prossimi passi", io_.transcript)

    def test_open_folder_is_offered_and_called(self) -> None:
        opened: list[Path] = []
        code, w, io_ = self.run_wizard(["1", "Prova", "", "", "", "", "", "s", ""], open_folder=opened.append)
        self.assertEqual(code, 0, io_.transcript)
        self.assertIn("Aprire adesso la cartella della nuova voce? [S/n]", io_.prompt_text)
        self.assertEqual(opened, [self.root / "indicators" / "prova"])

    def test_cancel_at_open_folder_question_keeps_success(self) -> None:
        opened: list[Path] = []
        io_ = ScriptedIO(["1", "Prova", "", "", "", "", "", "s"])

        def ask(prompt: str) -> str:
            if io_.answers:
                return io_.ask(prompt)
            self.assertIn("Aprire adesso la cartella", prompt)
            raise KeyboardInterrupt

        w = wizard.Wizard(ask, io_.say, root=self.root, open_folder=opened.append, windows=False, date=FIXED_DATE)
        self.assertEqual(w.run(), 0, io_.transcript)
        self.assertTrue((self.root / "indicators" / "prova" / "README.md").exists())
        self.assertEqual(opened, [])
        self.assertIn("Fatto. Prossimi passi", io_.transcript)
        self.assertFalse(io_.transcript.rstrip().endswith(wizard.CANCELLED_MESSAGE))
        self.assertEqual(w.outcome.exit_code, 0)

    def test_tags_that_normalize_to_nothing_are_reported(self) -> None:
        code, w, io_ = self.run_wizard(["1", "Prova", "", "", "", "###, !!!", "", "n"])
        self.assertEqual(code, 1)
        self.assertIn("AVVISO: nessun tag valido ricavato da '###, !!!' (usare lettere o cifre): tags resta vuoto.", io_.transcript)
        self.assertNotIn("--tags", w.outcome.argv)
        self.assertNotIn("Tag normalizzati", io_.transcript)

    def test_load_errors_are_shown_once_before_the_menu(self) -> None:
        (self.root / "indicators" / "rotta").mkdir()  # cartella senza README.md
        code, _w, io_ = self.run_wizard(["0"])
        self.assertEqual(code, 1)
        self.assertIn("indicators/rotta", io_.transcript)
        self.assertIn("manca il file README.md", io_.transcript)
        self.assertIn("(queste voci non compaiono negli elenchi; correggerle prima di eseguire 'Verifica')", io_.transcript)
        self.assertLess(io_.transcript.index("manca il file README.md"), io_.transcript.index("Che cosa vuoi aggiungere?"))
        self.assertEqual(io_.transcript.count("correggerle prima di eseguire"), 1)
        # una libreria sana non mostra nulla
        shutil.rmtree(self.root / "indicators" / "rotta")
        code, _w, io_ = self.run_wizard(["1", "Sana", "", "", "", "", "", "n"])
        self.assertNotIn("non compaiono negli elenchi", io_.transcript)

    def test_open_folder_declined(self) -> None:
        opened: list[Path] = []
        code, _w, _io = self.run_wizard(["1", "Prova", "", "", "", "", "", "s", "n"], open_folder=opened.append)
        self.assertEqual(code, 0)
        self.assertEqual(opened, [])

    def test_open_folder_error_is_reported_not_raised(self) -> None:
        def broken(_path: Path) -> None:
            raise OSError("nessuna applicazione associata")

        code, _w, io_ = self.run_wizard(["1", "Prova", "", "", "", "", "", "s", "s"], open_folder=broken)
        self.assertEqual(code, 0)
        self.assertIn("Impossibile aprire la cartella: nessuna applicazione associata", io_.transcript)

    def test_windows_command_style(self) -> None:
        code, w, _io = self.run_wizard(["1", "MA Band", "", "", "", "", "", "n"], windows=True)
        self.assertEqual(code, 1)
        self.assertTrue(w.outcome.command.startswith('py -3 tools\\new_entry.py indicator "MA Band"'), w.outcome.command)

    def test_root_omitted_from_command_when_default(self) -> None:
        # Senza --root (radice = repository reale) il comando non contiene --root; niente viene scritto (si annulla).
        io_ = ScriptedIO(["1", "Voce Inesistente Di Prova", "", "", "", "", "", "n"])
        w = wizard.Wizard(io_.ask, io_.say, open_folder=None, windows=False)
        self.assertEqual(w.run(), 1)
        self.assertEqual(w.root, REPO_ROOT)
        self.assertNotIn("--root", w.outcome.argv)
        self.assertNotIn("--date", w.outcome.argv)
        self.assertFalse((REPO_ROOT / "indicators" / "voce-inesistente-di-prova").exists())
        real_papers = bc.load_library(REPO_ROOT).papers
        if real_papers:
            self.assertIn(f"1) {real_papers[0].key}", io_.transcript)

    def test_new_entry_failure_is_reported(self) -> None:
        # La cartella viene creata dopo che il wizard ha validato lo slug: new_entry.py fallisce.
        io_ = ScriptedIO(["1", "Prova", "", "", "", "", "", "s"])

        def ask(prompt: str) -> str:
            answer = io_.ask(prompt)
            if prompt.startswith("Procedere"):
                (self.root / "indicators" / "prova").mkdir(parents=True)
            return answer

        w = wizard.Wizard(ask, io_.say, root=self.root, open_folder=None, windows=False, date=FIXED_DATE)
        self.assertEqual(w.run(), 1)
        self.assertIn("ERRORE indicators/prova/: la cartella esiste già", io_.transcript)
        self.assertIn("La voce NON è stata creata", io_.transcript)

    def test_main_cli_with_injected_io(self) -> None:
        io_ = ScriptedIO(["3", "Fn_Nuova", "", "", "", "", "", "s"])
        code = wizard.main(["--root", str(self.root), "--date", FIXED_DATE], ask=io_.ask, say=io_.say, open_folder=None, windows=False)
        self.assertEqual(code, 0, io_.transcript)
        meta = front_matter_of(self.root / "functions" / "fn-nuova" / "README.md")
        self.assertEqual(meta["created"], FIXED_DATE)
        self.assertEqual(meta["name"], "Fn_Nuova")

    def test_main_rejects_bad_date(self) -> None:
        io_ = ScriptedIO([])
        self.assertEqual(wizard.main(["--root", str(self.root), "--date", "15/01/2024"], ask=io_.ask, say=io_.say), 2)
        self.assertEqual(wizard.main(["--root", str(self.root), "--date", "2024-02-30"], ask=io_.ask, say=io_.say), 2)
        self.assertEqual(io_.prompts, [])
        self.assertIn("non valida", io_.transcript)

    def test_main_reports_missing_root(self) -> None:
        io_ = ScriptedIO([])
        self.assertEqual(wizard.main(["--root", str(self.tmp / "manca")], ask=io_.ask, say=io_.say), 1)
        self.assertIn("ERRORE", io_.transcript)

    def test_help_is_italian(self) -> None:
        parser = wizard.build_arg_parser()
        text = parser.format_help()
        self.assertIn("--root", text)
        self.assertIn("--dry-run", text)
        self.assertIn("radice del repository", text)


if __name__ == "__main__":
    unittest.main()
