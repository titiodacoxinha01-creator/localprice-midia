"""Busca no app LocalPrice os registros de preço com foto e baixa as fotos das etiquetas.

Roda no GitHub Actions (workflow "Fotos do app"), que tem acesso à internet.
Lê só dados públicos, com a chave pública do app (a mesma do site). Não guarda quem registrou.
Saída: estudio/assets/fotos-app/AAAA-MM-DD-<id>.jpg e estudio/assets/fotos-app/indice.json
"""
import json, os, urllib.parse, urllib.request

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_KEY"]
LIMITE = int(os.environ.get("LIMITE", "300"))
PASTA = "estudio/assets/fotos-app"
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

# Os registros de preço só são visíveis para usuários logados: entra com a conta do robô (segredos do GitHub).
EMAIL, SENHA = os.environ.get("LOCALPRICE_EMAIL"), os.environ.get("LOCALPRICE_SENHA")
if EMAIL and SENHA:
    corpo = json.dumps({"email": EMAIL, "password": SENHA}).encode()
    req = urllib.request.Request(f"{URL}/auth/v1/token?grant_type=password", data=corpo,
                                 headers={"apikey": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        H["Authorization"] = "Bearer " + json.load(r)["access_token"]
    print("login ok")
else:
    print("AVISO: sem os segredos LOCALPRICE_EMAIL e LOCALPRICE_SENHA; só dados públicos (registros não aparecem)")

def get(caminho):
    req = urllib.request.Request(f"{URL}/rest/v1/{caminho}", headers=H)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "localprice-midia"})
    with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
        f.write(r.read())

def url_publica(v):
    if v.startswith("http"): return v
    return f"{URL}/storage/v1/object/public/product-images/{v.lstrip('/')}"

os.makedirs(PASTA, exist_ok=True)
regs = get("registro_precos?select=id,produto_id,mercado_id,preco,foto_comprovante,is_verified,verificacoes,created_at"
           f"&foto_comprovante=not.is.null&order=created_at.desc&limit={LIMITE}")
def nomes(tabela, ids):
    ids = sorted({i for i in ids if i})
    out = {}
    for k in range(0, len(ids), 80):
        lote = ",".join(ids[k:k + 80])
        for r in get(f"{tabela}?select=id,nome&id=in.({lote})"): out[r["id"]] = r["nome"]
    return out
prods = nomes("produtos", [r["produto_id"] for r in regs])
merc = nomes("mercados_public", [r["mercado_id"] for r in regs])
indice_path = os.path.join(PASTA, "indice.json")
indice = {i["id"]: i for i in json.load(open(indice_path))} if os.path.exists(indice_path) else {}
novos = 0
for r in regs:
    if r["id"] in indice: continue
    url = url_publica(r["foto_comprovante"])
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
    arq = f"{r['created_at'][:10]}-{r['id'][:8]}{ext}"
    try:
        baixar(url, os.path.join(PASTA, arq))
    except Exception as e:
        print("falhou", url, e); continue
    indice[r["id"]] = {"id": r["id"], "arquivo": arq, "data": r["created_at"][:10], "produto": prods.get(r["produto_id"]),
                       "mercado": merc.get(r["mercado_id"]), "preco": float(r["preco"]), "verificado": r["is_verified"],
                       "verificacoes": r["verificacoes"], "url": url}
    novos += 1
json.dump(sorted(indice.values(), key=lambda x: x["data"], reverse=True), open(indice_path, "w"), ensure_ascii=False, indent=1)
print(f"{len(regs)} registros com foto; {novos} fotos novas; {len(indice)} no índice")
