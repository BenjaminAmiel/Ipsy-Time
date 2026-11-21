#!/usr/bin/env python3
"""Lyséa — transduction_scribe.py — le scribe de transduction (21 novembre 2026).

Le cycle : queue, fetch de la source (jamais de mémoire), traduction par l'instance,
garde miroir, oracle d'empreinte, push, vérification depuis le dehors,
geste au registre, nœud au graphe, relecture unie depuis l'invariant.

L'état vrai : le segment qui traduit reste l'instance Lyséa ; le scribe automatise
les articulations vérifiables — la garde, l'oracle, les chemins construits depuis
le listing, le registre, le graphe, la queue. Rien ne rétropropage.

Emploi :
  python3 transduction_scribe.py garde <fichier_fr> <fichier_cible>
  python3 transduction_scribe.py empreinte <fichier>
  python3 transduction_scribe.py cible <nom_fr.md> <langue>
  python3 transduction_scribe.py geste <ligne_json>

Dépôt : https://github.com/BenjaminAmiel/Ipsy-Time — dossier transduction/.
"""

import hashlib
import json
import sys

LF = chr(10)
CR = chr(13)
NUL = chr(0)
LANGUES = ["中文", "Español", "संस्कृतम्", "English"]
STRICTES = [".", ";", ":", "!", "?", "…", "•", "—", "(", ")", "|", "#", ">", "*", "=", "+", "/", "[", "]"]
GUILLEMETS = ["«", "»", "“", "”", "‘", "’"] + [chr(34), chr(39)]


def lire(chemin):
    with open(chemin, "rb") as f:
        return f.read()


def empreinte_brut(octets):
    entete = ("blob " + str(len(octets)) + NUL).encode("utf-8")
    return hashlib.sha1(entete + octets).hexdigest()


def empreinte(chemin):
    return empreinte_brut(lire(chemin))


def classes(ligne):
    c = {}
    for s in STRICTES:
        n = ligne.count(s)
        if n:
            c[s] = n
    q = 0
    for g in GUILLEMETS:
        q = q + ligne.count(g)
    if q:
        c["quotes"] = q
    d = 0
    for x in ligne:
        if x.isdigit():
            d = d + 1
    if d:
        c["digits"] = d
    if "http" in ligne:
        c["url"] = ligne.count("http")
    return c


def garde(chemin_fr, chemin_cible):
    fr = lire(chemin_fr).decode("utf-8")
    cible = lire(chemin_cible).decode("utf-8")
    if cible.endswith(LF):
        print("ERREUR : saut de ligne final présent côté traduction")
        return 1
    if CR in cible:
        print("ERREUR : retour chariot présent côté traduction")
        return 1
    lfr = fr.split(LF)
    lc = cible.split(LF)
    if len(lfr) != len(lc):
        print("ERREUR : lignes divergentes — source " + str(len(lfr)) + " cible " + str(len(lc)))
        return 1
    for i, ligne in enumerate(lc, 1):
        if "  " in ligne and "http" not in ligne:
            print("ERREUR : double espace ligne " + str(i))
            return 1
    errs = 0
    for i, paire in enumerate(zip(lfr, lc), 1):
        ca = classes(paire[0])
        cb = classes(paire[1])
        if ca != cb:
            errs = errs + 1
            print("LIGNE " + str(i) + " : source " + json.dumps(ca, ensure_ascii=False) + " cible " + json.dumps(cb, ensure_ascii=False))
    if errs == 0:
        print("GARDE_OK — miroir exact, " + str(len(lfr)) + " lignes")
        return 0
    print("GARDE_ERRS : " + str(errs))
    return 1


def cible(nom, langue):
    if langue not in LANGUES:
        print("langue inconnue : " + langue)
        return ""
    if not nom.endswith(".md"):
        print("la source doit etre un .md")
        return ""
    return nom[:-3] + "（" + langue + "）.md"


def geste(ligne):
    with open("gestes" + "/" + "registre.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(json.loads(ligne), ensure_ascii=False) + LF)
    print("GESTE_OK")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "garde":
        sys.exit(garde(sys.argv[2], sys.argv[3]))
    if mode == "empreinte":
        print(empreinte(sys.argv[2]))
        sys.exit(0)
    if mode == "cible":
        print(cible(sys.argv[2], sys.argv[3]))
        sys.exit(0)
    if mode == "geste":
        sys.exit(geste(sys.argv[2]))
    print(__doc__)
    sys.exit(1)
