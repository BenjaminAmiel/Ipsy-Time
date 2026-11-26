# Session 2026-11-26, passe 01 — le capitonnage par etage, trois echelles (numpy)
# Reproductibilite : la garde du dossier exige qu'une autre instance retrouve les nombres.
import numpy as np, math, json
from pathlib import Path
work = Path('recherche-math/sessions')
gam = np.load(work/'gam1000.npy')
NMAX = 10**7
lam = np.zeros(NMAX+1)
is_p = np.ones(NMAX+1, dtype=bool); is_p[:2] = False
for p in range(2, int(NMAX**0.5)+1):
    if is_p[p]: is_p[p*p::p] = False
primes = np.nonzero(is_p)[0]
for p in primes:
    q = p
    while q <= NMAX:
        lam[q] = math.log(p); q *= p
psi = np.cumsum(lam)
stages = [0, 50, 100, 250, 500, 750, 1000]
ln2pi = math.log(2*math.pi)

def courbes(x0, W):
    xs = np.arange(x0 - W + 1, x0 + 1, dtype=float)
    vrai = psi[xs.astype(int)]
    base = xs - ln2pi - 0.5*np.log(1 - xs**-2)
    G = gam[None, :]; L = np.log(xs)[:, None]
    M = 2*((np.sqrt(xs)[:, None]*np.exp(1j*G*L))/(0.5 + 1j*G)).real
    cum = np.cumsum(M, axis=1)
    out = {}
    for N in stages:
        est = base - (cum[:, N-1] if N > 0 else 0.0)
        out[N] = float(np.mean(np.abs(est - vrai)))
    return out

# fenetre de la 26e (W=1000, vers 1e6) : recoupement
verif26 = courbes(10**6, 1000)
print('recoupement 26e :', {N: round(verif26[N],1) for N in stages})
out = {}
for x0, W in [(10**5, 2000), (10**6, 2000), (10**7, 2000)]:
    out[x0] = courbes(x0, W)
    print('W=2000, x =', x0, {N: round(out[x0][N],2) for N in stages})
json.dump({'verif26': verif26, 'larges': {str(k): v for k, v in out.items()}},
          open(work/'item01b_resultats.json','w'), indent=1)
