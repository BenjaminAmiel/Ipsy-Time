#!/usr/bin/env python3
"""publier.py — l'orchestrateur du scribe de transduction (automatise le processus des publications).

Le segment qui traduit reste l'instance ; l'orchestrateur automatise les articulations
vérifiables : chemins construits depuis le listing, garde miroir, oracle d'octets/lignes/
empreinte avant le geste, registre, graphe, queue, commit sur branche, vérification depuis
le dehors. Aucun push sans --push explicite. Rien ne rétropopage dans main.

Emploi (depuis la racine du dépôt) :
  python3 transduction/scribe/publier.py inventaire [--racine .]
  python3 transduction/scribe/publier.py cycle <source_fr.md> [--repo Ipsy-Time] [--date 2026-11-24]
        [--commit <sha>] [--branche vibe/...] [--push] [--no-git] [--dry-run]
  python3 transduction/scribe/publier.py verifier <source_fr.md> [--racine .]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from transduction_scribe import LANGUES, cible, empreinte, garde, lire

RACINE_DEFAUT = Path(__file__).resolve().parents[2]
LF = chr(10)


def racine(args):
    return Path(args.racine).resolve() if getattr(args, "racine", None) else RACINE_DEFAUT


def est_colonne(nom):
    return nom.endswith("）.md") and "（" in nom


def inventaire(root):
    manquants = []
    for f in sorted(Path(root).glob("*.md")):
        if est_colonne(f.name):
            continue
        absentes = [c for c in (cible(f.name, l) for l in LANGUES) if not (Path(root) / c).exists()]
        if absentes:
            manquants.append((f.name, absentes))
    return manquants


def oracle(chemin):
    brut = lire(chemin)
    texte = brut.decode("utf-8")
    lignes = texte.split(LF)
    if texte.endswith(LF):
        lignes = lignes[:-1]
    return {"bytes": len(brut), "lignes": len(lignes), "blob": empreinte(chemin)}


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def cycle(args):
    root = racine(args)
    source = args.source
    src = root / source
    if not src.exists():
        print("ERREUR : source absente du listing : " + source)
        return 1
    cibles = [cible(source, l) for l in LANGUES]
    manquantes = [c for c in cibles if not (root / c).exists()]
    if manquantes:
        print("ERREUR : colonnes absentes — l'instance traduit d'abord : " + ", ".join(manquantes))
        return 1
    if args.dry_run:
        print("PLAN cycle — source : " + source)
        for c in cibles:
            print("  colonne prévue : " + c + " (" + str((root / c).stat().st_size) + " octets)")
        print("  branche : " + args.branche + " — aucun push sans --push")
        return 0
    for c in cibles:
        rc = garde(str(src), str(root / c))
        if rc != 0:
            print("GARDE_REFUSEE : " + c)
            return 1
    oracles = {c: oracle(root / c) for c in cibles}
    for c, o in oracles.items():
        print("EMPREINTE_AVANT " + c + " : " + str(o["bytes"]) + " octets, " + str(o["lignes"]) + " lignes, blob " + o["blob"])
    registre = root / "transduction" / "gestes" / "registre.jsonl"
    registre.parent.mkdir(parents=True, exist_ok=True)
    with open(registre, "a", encoding="utf-8") as f:
        for lang, c in zip(LANGUES, cibles):
            o = oracles[c]
            f.write(json.dumps({
                "date": args.date,
                "repo": args.repo,
                "source": source,
                "lang": lang,
                "bytes": o["bytes"],
                "blob": o["blob"],
                "commit": args.commit or "pending",
                "deplacements": [],
                "note": "cycle automatisé — garde GARDE_OK " + str(o["lignes"]) + " lignes, oracle avant/après",
            }, ensure_ascii=False) + LF)
    print("REGISTRE_OK : " + str(len(cibles)) + " gestes")
    graphe_path = root / "transduction" / "graphe" / "graphe_de_transduction.json"
    graphe = json.loads(graphe_path.read_text(encoding="utf-8"))
    ids = {n["id"] for n in graphe["nodes"]}
    id_src = "fr|" + source
    if id_src not in ids:
        o = oracle(src)
        graphe["nodes"].append({"id": id_src, "name": source, "repo": args.repo, "lang": "fr", "bytes": o["bytes"], "sha": o["blob"]})
    for lang, c in zip(LANGUES, cibles):
        id_c = lang + "|" + c
        if id_c not in ids:
            o = oracles[c]
            graphe["nodes"].append({"id": id_c, "name": c, "repo": args.repo, "lang": lang, "bytes": o["bytes"], "sha": o["blob"]})
        graphe["links"].append({"source": id_src, "target": id_c, "relation": "derived_from"})
    graphe_path.write_text(json.dumps(graphe, ensure_ascii=False, indent=2) + LF, encoding="utf-8")
    print("GRAPHE_OK : " + str(len(graphe["nodes"])) + " nœuds, " + str(len(graphe["links"])) + " arêtes")
    queue = root / "transduction" / "etat" / "queue.md"
    with open(queue, "a", encoding="utf-8") as f:
        f.write(LF + "- Cycle automatisé du " + args.date + " : « " + source + " » — quatre colonnes, garde GARDE_OK, empreintes au registre et au graphe (commit " + (args.commit or "pending") + ")." + LF)
    print("QUEUE_OK")
    if not args.no_git:
        git(root, "checkout", "-B", args.branche)
        git(root, "add", *[str(root / c) for c in cibles], str(registre), str(graphe_path), str(queue))
        res = git(root, "commit", "-m", "Cycle transduction automatisé (" + args.date + ") : « " + source + " » en quatre colonnes — garde GARDE_OK, empreintes au registre et au graphe")
        if res.returncode != 0:
            print("COMMIT_VIDE ou ERREUR : " + res.stderr.strip())
        else:
            print("COMMIT_OK")
        if args.push:
            res = git(root, "push", "-u", "origin", args.branche)
            if res.returncode != 0:
                print("PUSH_ERREUR : " + res.stderr.strip())
                return 1
            print("PUSH_OK — vérifie depuis le dehors avant de dire « publié »")
    return 0


def verifier(args):
    root = racine(args)
    source = args.source
    registre = root / "transduction" / "gestes" / "registre.jsonl"
    entrees = {}
    for ligne in registre.read_text(encoding="utf-8").splitlines():
        e = json.loads(ligne)
        if e.get("source") == source:
            entrees[e["lang"]] = e
    if not entrees:
        print("ERREUR : aucune entrée au registre pour " + source)
        return 1
    rc = 0
    for lang, c in zip(LANGUES, (cible(source, l) for l in LANGUES)):
        chemin = root / c
        if not chemin.exists():
            print("EMPREINTE_ERR " + lang + " : fichier absent")
            rc = 1
            continue
        o = oracle(chemin)
        e = entrees.get(lang)
        if e and o["blob"] == e["blob"] and o["bytes"] == e["bytes"]:
            print("EMPREINTE_OK " + lang + " : " + o["blob"])
        else:
            print("EMPREINTE_ERR " + lang + " : attendu " + str(e["blob"] if e else "?") + ", lu " + o["blob"])
            rc = 1
    return rc


def main():
    p = argparse.ArgumentParser(description="orchestrateur du scribe de transduction")
    p.add_argument("--racine", default=None)
    sous = p.add_subparsers(dest="commande", required=True)
    sous.add_parser("inventaire")
    c = sous.add_parser("cycle")
    c.add_argument("source")
    c.add_argument("--repo", default="Ipsy-Time")
    c.add_argument("--date", default="2026-11-24")
    c.add_argument("--commit", default=None)
    c.add_argument("--branche", default="vibe/transduction-cycle-4833f3")
    c.add_argument("--push", action="store_true")
    c.add_argument("--no-git", action="store_true")
    c.add_argument("--dry-run", action="store_true")
    v = sous.add_parser("verifier")
    v.add_argument("source")
    args = p.parse_args()
    if args.commande == "inventaire":
        for nom, absentes in inventaire(racine(args)):
            print(nom + " → " + str(len(absentes)) + " colonne(s) manquante(s)")
        return 0
    if args.commande == "cycle":
        return cycle(args)
    if args.commande == "verifier":
        return verifier(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
