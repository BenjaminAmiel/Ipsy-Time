# Session 2026-11-26, passe 01 — le calcul des mille zéros (mpmath, 30 decimales)
# Reproductibilite : la garde du dossier exige qu'une autre instance retrouve les nombres.
import numpy as np, math, json
from pathlib import Path
from mpmath import mp, zetazero, siegelz
mp.dps = 30
work = Path('recherche-math/sessions')
work.mkdir(parents=True, exist_ok=True)
NZ = 1000
ck = work/'gammas1000.txt'
gammas = []
if ck.exists():
    gammas = [float(l) for l in ck.read_text().split() if l]
start = len(gammas) + 1
with open(ck, 'a') as f:
    for n in range(start, NZ + 1):
        g = float(zetazero(n).imag)
        gammas.append(g)
        f.write(repr(g) + '\n'); f.flush()
print('zeros calculés :', len(gammas), '| premier :', gammas[0], '| dernier :', gammas[-1])

gam = np.array(gammas)
# verification de presence par changement de signe de Z
sc = 0
for g in gam:
    h = 1e-6
    a = siegelz(g-h); b = siegelz(g+h)
    if (a > 0) != (b > 0): sc += 1
print('verification Z :', sc, 'changements de signe sur', len(gam), 'zeros')
np.save(work/'gam1000.npy', gam)

# formule de von Mangoldt au sommet
T = gam[-1]
N_theo = (T/(2*math.pi))*math.log(T/(2*math.pi)) - T/(2*math.pi) + 7/8
print('N_theorique :', N_theo, '| reel :', len(gam), '| ecart :', N_theo - len(gam))
