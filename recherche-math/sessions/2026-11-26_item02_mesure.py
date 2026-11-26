import numpy as np, math, json
from pathlib import Path
work = Path(__file__).resolve().parent  # dossier recherche-math/sessions du dépôt Ipsy-Time
gammas_blocks = {}
for line in (work/'gammas_blocks.txt').read_text().splitlines():
    n, g = line.split(); gammas_blocks[int(n)] = float(g)
# les mille premiers zéros (passe 01, fichier gam1000.npy du dossier de session)
gam1000 = np.load(work/'gam1000.npy')
blocks_file = gammas_blocks

def gamme(n_de, n_a):
    """retourne les hauteurs gamma_n pour n dans [n_de, n_a] (indices inclusifs)"""
    gam = {}
    for n in range(n_de, n_a + 1):
        if n <= 1000: gam[n] = float(gam1000[n-1])
        elif n in blocks_file: gam[n] = blocks_file[n]
    ns = sorted(gam)
    return np.array([gam[n] for n in ns])

def stats_normalisees(gam):
    d = np.diff(gam)
    w = d * np.log(gam[:-1]/(2*np.pi)) / (2*np.pi)   # espacement normalise local
    return w

# Wigner surmise (GUE 2x2) : P(s) = 32/pi^2 * s^2 * exp(-4 s^2/pi)
def wigner_cdf_bins(bins):
    s = np.linspace(0, 8, 200001)
    P = 32/np.pi**2 * s**2 * np.exp(-4*s**2/np.pi)
    cdf = np.cumsum(P)*(s[1]-s[0])
    out = []
    for a, b in bins:
        i0 = np.searchsorted(s, a); i1 = np.searchsorted(s, b)
        out.append(float(cdf[min(i1, len(cdf)-1)] - cdf[max(i0-1,0)]))
    return out

bins = [(0, 0.3), (0.3, 0.7), (0.7, 1.3), (1.3, 2.0), (2.0, 8.0)]
theo = wigner_cdf_bins(bins)

blocs = {
 'B0 (n=1-500)': (1, 500),
 'B1 (n=501-1000)': (501, 1000),
 'B2 (n=1901-2100)': (1901, 2100),
 'B3 (n=3901-4100)': (3901, 4100),
 'B4 (n=7901-8100)': (7901, 8100),
 'B5 (n=9901-10100)': (9901, 10100),
}
res = {}
for nom, (a, b) in blocs.items():
    gam = gamme(a, b)
    w = stats_normalisees(gam)
    prop = [float(np.mean((w >= x) & (w < y))) for x, y in bins]
    res[nom] = {
        'gamma_de': round(float(gam[0]), 2), 'gamma_a': round(float(gam[-1]), 2),
        'taille': len(gam), 'espacements': len(w),
        'moyenne': round(float(w.mean()), 4),
        'ecart_type': round(float(w.std()), 4),
        'sous_0_1': round(float(np.mean(w < 0.1)), 4),
        'bins': [round(p, 4) for p in prop]
    }
    print(nom, 'hauteur', round(gam[0]), '->', round(gam[-1]), '| moyenne', round(float(w.mean()),4), '| ecart-type', round(float(w.std()),4))

print('Wigner (GUE) : moyenne 1, ecart-type ~0.411')
print('probabilites theoriques des bins (surmisse de Wigner) :', [round(t,4) for t in theo])
json.dump({'blocs': res, 'bins_theoriques': [round(t,4) for t in theo],
           'wigner_ecart_type': 0.411}, open(work/'item02_resultats.json','w'), indent=1)
print('sauvegarde ok')
