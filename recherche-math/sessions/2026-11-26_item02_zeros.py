import numpy as np, math
from pathlib import Path
from mpmath import mp, zetazero
mp.dps = 30
work = Path(__file__).resolve().parent  # dossier recherche-math/sessions du dépôt Ipsy-Time
ck = work/'gammas_blocks.txt'
have = {}
if ck.exists():
    for line in ck.read_text().splitlines():
        if line.strip():
            n, g = line.split()
            have[int(n)] = float(g)

# blocs : indices de depart, taille
blocks = [(601, 300), (1901, 200), (3901, 200), (7901, 200), (9901, 200)]
with open(ck, 'a') as f:
    for start, size in blocks:
        for n in range(start, start + size):
            if n in have: continue
            g = float(zetazero(n).imag)
            f.write(f"{n} {g!r}\n"); f.flush()
print('zeros en base :', len(have) + sum(1 for _ in []) , '| fichier lignes :', len(ck.read_text().splitlines()) if ck.exists() else 0)
