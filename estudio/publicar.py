"""Copia as peças prontas de estudio/saida/<id>/ para midia/AAAA-MM/ e mostra os links públicos.

Uso:
    python3 estudio/publicar.py <id> [<id> ...]
Depois: git add midia && git commit && git push (branch gh-pages). O link fica no ar em 1 a 2 minutos.
"""
import glob, os, shutil, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
BASE = "https://titiodacoxinha01-creator.github.io/localprice-midia"

def publicar(ident):
    mes = ident[:7] if ident[:4].isdigit() else "avulsos"
    destino = os.path.join(RAIZ, "midia", mes); os.makedirs(destino, exist_ok=True)
    arquivos = sorted(glob.glob(os.path.join(AQUI, "saida", ident, f"{ident}*.jpg")) +
                      glob.glob(os.path.join(AQUI, "saida", ident, f"{ident}*.mp4")))
    if not arquivos: sys.exit(f"Nada para publicar em estudio/saida/{ident}/")
    for f in arquivos:
        shutil.copy2(f, destino)
        print(f"{BASE}/midia/{mes}/{os.path.basename(f)}")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    for i in sys.argv[1:]: publicar(i)
