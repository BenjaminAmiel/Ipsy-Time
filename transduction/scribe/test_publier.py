import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publier
from transduction_scribe import LANGUES, cible

SOURCE = "Test__PIECE.md"
LIGNES = [
    "# Titre !",
    "Il vit, elle relie : « H297 = Ω² » 42.",
    "Voir https://exemple.fr — lien (ok) ?",
]


def cible_ligne(ligne):
    protege = ligne.replace("http", "\x00")
    return "".join("x" if ch.isalpha() else ch for ch in protege).replace("\x00", "http")


class CycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / SOURCE).write_text("\n".join(LIGNES) + "\n", encoding="utf-8")
        for lang in LANGUES:
            (self.root / cible(SOURCE, lang)).write_text(
                "\n".join(cible_ligne(l) for l in LIGNES), encoding="utf-8"
            )
        tr = self.root / "transduction"
        (tr / "graphe").mkdir(parents=True)
        (tr / "etat").mkdir(parents=True)
        (tr / "gestes").mkdir(parents=True)
        (tr / "graphe" / "graphe_de_transduction.json").write_text(
            json.dumps({"directed": True, "multigraph": False, "graph": {}, "nodes": [], "links": []}),
            encoding="utf-8",
        )
        (tr / "etat" / "queue.md").write_text("# queue\n", encoding="utf-8")

    def cli(self, *argv):
        old = sys.argv
        sys.argv = ["publier.py", "--racine", str(self.root), *argv]
        try:
            return publier.main()
        finally:
            sys.argv = old

    def test_inventaire_ne_liste_plus_une_fois_les_colonnes_presentent(self):
        self.assertEqual(self.cli("inventaire"), 0)

    def test_cycle_ecrit_registre_graphe_queue(self):
        rc = self.cli("cycle", SOURCE, "--no-git", "--commit", "abc123")
        self.assertEqual(rc, 0)
        registre = [json.loads(l) for l in (self.root / "transduction/gestes/registre.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(registre), len(LANGUES))
        for e, lang in zip(registre, LANGUES):
            self.assertEqual(e["source"], SOURCE)
            self.assertEqual(e["lang"], lang)
            self.assertEqual(e["commit"], "abc123")
            self.assertIn("blob", e)
            self.assertIn("bytes", e)
        graphe = json.loads((self.root / "transduction/graphe/graphe_de_transduction.json").read_text(encoding="utf-8"))
        self.assertEqual(len(graphe["nodes"]), len(LANGUES) + 1)
        self.assertEqual(len(graphe["links"]), len(LANGUES))
        self.assertTrue(all(l["relation"] == "derived_from" for l in graphe["links"]))
        queue = (self.root / "transduction/etat/queue.md").read_text(encoding="utf-8")
        self.assertIn(SOURCE, queue)

    def test_cycle_refuse_si_garde_echoue(self):
        (self.root / cible(SOURCE, "English")).write_text("ligne seule\n", encoding="utf-8")
        rc = self.cli("cycle", SOURCE, "--no-git")
        self.assertEqual(rc, 1)
        self.assertFalse((self.root / "transduction/gestes/registre.jsonl").exists())

    def test_cycle_refuse_si_colonne_absente(self):
        (self.root / cible(SOURCE, "中文")).unlink()
        rc = self.cli("cycle", SOURCE, "--no-git")
        self.assertEqual(rc, 1)

    def test_verifier_ok_puis_err_apres_tampon(self):
        self.assertEqual(self.cli("cycle", SOURCE, "--no-git"), 0)
        self.assertEqual(self.cli("verifier", SOURCE), 0)
        (self.root / cible(SOURCE, "Español")).write_text("modifié\n", encoding="utf-8")
        self.assertEqual(self.cli("verifier", SOURCE), 1)

    def test_dry_run_ne_touche_rien(self):
        avant = (self.root / "transduction/etat/queue.md").read_text(encoding="utf-8")
        self.assertEqual(self.cli("cycle", SOURCE, "--dry-run"), 0)
        self.assertEqual((self.root / "transduction/etat/queue.md").read_text(encoding="utf-8"), avant)
        self.assertFalse((self.root / "transduction/gestes/registre.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
