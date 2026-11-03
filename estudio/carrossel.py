"""Gera um carrossel do LocalPrice (1080x1350) a partir de um arquivo JSON de conteúdo.

Uso:
    python3 estudio/carrossel.py estudio/conteudo/<arquivo>.json [--short]

Saída em estudio/saida/<id>/: <id>-01.jpg ... , folha.png (conferência) e, com --short, <id>-short.mp4.
A conferência automática para com erro se algum texto sair da arte ou não couber.

Estilos: "encarte" (A, comparações e contas) e "print" (B, perguntas e opinião).
Marcação nos textos: **destaque** (vermelho no encarte, marca-texto no print), ==marca-texto==, quebra de linha com \n.
Veja estudio/LEIAME.md para todos os tipos de página.
"""
import html, json, os, re, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, "assets")

def md(t):
    t = html.escape(t or "")
    t = re.sub(r"\*\*(.+?)\*\*", r'<em class="d">\1</em>', t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    t = re.sub(r"\+\+(.+?)\+\+", r'<span class="ok">\1</span>', t)
    t = re.sub(r"R\$ (?=\d)", "R$&nbsp;", t)
    return t.replace("\n", "<br>")

def caixa(linhas, centro=False):
    """Caixa branca: cada linha numa só linha; a letra diminui para caber (72 a 50 px)."""
    maior = max(len(re.sub(r"\*\*|\+\+|==", "", l)) for l in linhas)
    tam = max(50, min(72, int(840 / (0.48 * maior))))
    corpo = "".join(f'<div class="l">{md(l)}</div>' for l in linhas)
    return f'<div class="caixa{" centro" if centro else ""}" style="font-size:{tam}px">{corpo}</div>'

CHECK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5' fill='none' stroke='white' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"

CSS_BASE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #222; font-family: "Inter", sans-serif; }
.post { width: 1080px; height: 1350px; position: relative; overflow: hidden; display: flex; flex-direction: column; }
"""

CSS_ENCARTE = """
.post { background: #FFD52E; color: #111; }
.faixa { height: 130px; flex: none; background: #E2231A; color: #fff; display: flex; align-items: center; justify-content: center;
  font: 900 50px Inter; text-transform: uppercase; padding: 0 40px; text-align: center; }
.meio { flex: 1; display: flex; flex-direction: column; justify-content: space-evenly; align-items: center; padding: 30px 60px; min-height: 0; }
.rod { flex: none; height: 120px; padding: 0 70px; display: flex; align-items: center; justify-content: space-between; font: 700 30px Inter; }
.rod img { height: 64px; }
.num { font: 900 34px Inter; background: #111; color: #FFD52E; border-radius: 40px; padding: 8px 22px; }
h1 { align-self: stretch; font: 900 108px/0.95 Inter; letter-spacing: -5px; text-transform: uppercase; }
h1.m { font-size: 82px; letter-spacing: -3px; line-height: 1; }
em.d { font-style: normal; color: #E2231A; }
.tags { display: flex; gap: 40px; justify-content: center; align-self: stretch; }
.tag { width: 460px; background: #fff; border: 8px solid #111; border-radius: 28px; padding: 30px 26px 26px; box-shadow: 14px 14px 0 #111; text-align: center; }
.tags .tag:nth-child(1) { transform: rotate(-4deg); } .tags .tag:nth-child(2) { transform: rotate(3deg); }
.tags.um .tag { transform: scale(1.3) rotate(-3deg); margin: 60px 0; }
.tag small { display: block; font: 800 42px Inter; text-transform: uppercase; }
.tag b { display: block; font: 900 112px/1 Inter; letter-spacing: -6px; margin-top: 10px; white-space: nowrap; }
.tag b span { font-size: 50px; letter-spacing: 0; vertical-align: 54px; margin-right: 6px; }
.tag i { display: block; font: 700 34px Inter; font-style: normal; margin-top: 10px; }
.tag.vermelho { background: #E2231A; color: #fff; } .tag.verde { background: #1E7A3C; color: #fff; }
.tag.riscado b { text-decoration: line-through 9px; }
.caixa { align-self: stretch; background: #fff; border: 8px solid #111; border-radius: 28px; box-shadow: 14px 14px 0 #111; padding: 40px 50px;
  font: 900 72px/1.2 Inter; letter-spacing: -2px; }
.caixa.centro { text-align: center; }
.caixa .l { white-space: nowrap; }
.ok { color: #1E7A3C; } .post.cta .ok { color: #FFD52E; } .caixa em.d { color: #E2231A; }
.selo { background: #111; color: #FFD52E; font: 900 60px Inter; padding: 22px 44px; border-radius: 18px; transform: rotate(-3deg); max-width: 960px; text-align: center; }
.selo.vermelho { background: #E2231A; color: #fff; }
.lista { list-style: none; align-self: stretch; }
.lista li { font: 800 62px/1.15 Inter; letter-spacing: -1px; padding: 26px 0 26px 100px; position: relative; border-bottom: 5px solid #111; }
.lista li::before { content: ""; position: absolute; left: 0; top: 30px; width: 64px; height: 64px; border-radius: 50%; background: #1E7A3C url("CHECK") center/70% no-repeat; }
.etq { width: 800px; background: #FFE14D; border: 8px solid #111; border-radius: 10px; box-shadow: 14px 14px 0 #111; overflow: hidden; transform: rotate(-2deg); }
.etq .t { background: #E2231A; color: #FFE14D; font: 900 56px Inter; text-align: center; padding: 14px; }
.etq .p { font: 900 170px/1 Inter; text-align: center; padding: 26px 0 6px; letter-spacing: -6px; }
.etq .p span { font-size: 60px; vertical-align: 80px; letter-spacing: 0; }
.etq .dd { display: flex; justify-content: space-between; align-items: center; padding: 10px 30px 26px; font: 800 34px Inter; gap: 20px; }
.etq .kg { border: 6px solid #E2231A; border-radius: 50%; padding: 10px 18px; white-space: nowrap; }
.post.cta { background: #1E7A3C; color: #fff; }
.post.cta .meio { align-items: flex-start; }
.post.cta h1 { font-size: 104px; }
.post.cta .texto { font: 700 58px/1.2 Inter; }
.post.cta .texto em.d { color: #FFD52E; }
.post.cta .selo { background: #FFD52E; color: #111; font-size: 52px; }
.post.cta .rod { color: #fff; } .post.cta .num { background: #FFD52E; color: #111; }
""".replace("CHECK", CHECK)

CSS_PRINT = """
.post { background: #EDEFEA; align-items: center; justify-content: center; }
.post.cta { background: #2F6B3A; }
.card { width: 940px; background: #fff; border-radius: 40px; padding: 56px 60px 44px; box-shadow: 0 30px 80px rgba(0,0,0,.12); max-height: 1250px; overflow: hidden; }
.perfil { display: flex; align-items: center; gap: 26px; }
.perfil img { width: 116px; height: 116px; border-radius: 50%; border: 3px solid #e3e3e3; }
.perfil b { display: block; font: 800 44px Inter; color: #111; }
.perfil span { font: 500 36px Inter; color: #7a7a7a; }
p { margin-top: 34px; font: 500 64px/1.2 Inter; color: #111; letter-spacing: -1px; }
p.g { font-size: 88px; font-weight: 800; letter-spacing: -3px; line-height: 1.05; }
p.s { font-size: 50px; color: #444; }
.ok { color: #2F6B3A; font-weight: 800; }
mark, em.d { background: #FFE14D; padding: 0 8px; border-radius: 8px; font-style: normal; }
.meta { margin-top: 34px; padding-top: 26px; border-top: 2px solid #eee; font: 500 32px Inter; color: #8a8a8a; display: flex; justify-content: space-between; }
.meta b { color: #2F6B3A; font-weight: 800; }
ul { list-style: none; margin-top: 30px; }
li { font: 700 54px/1.1 Inter; color: #111; padding: 22px 0 22px 84px; position: relative; border-bottom: 2px solid #f0f0f0; }
li::before { content: ""; position: absolute; left: 0; top: 22px; width: 56px; height: 56px; border-radius: 50%; background: #2F6B3A url("CHECK") center/70% no-repeat; }
li.falta { color: #999; } li.falta::before { background: #fff; border: 5px dashed #bbb; }
.campo { margin-top: 34px; border: 3px solid #e3e3e3; border-radius: 26px; padding: 28px 34px; font: 500 46px Inter; color: #999;
  display: flex; justify-content: space-between; align-items: center; gap: 20px; }
.campo b { color: #2F6B3A; font-weight: 800; white-space: nowrap; }
.cursor { display: inline-block; width: 5px; height: 52px; background: #2F6B3A; vertical-align: -10px; margin-left: 4px; }
.foto { margin-top: 34px; height: 380px; border-radius: 26px; background-size: cover; background-position: center 75%; }
.pag { position: absolute; bottom: 40px; right: 70px; font: 800 30px Inter; color: #999; }
.post.cta .pag { color: #cfe3d1; }
""".replace("CHECK", CHECK)

def img(nome):
    return "file://" + os.path.join(ASSETS, nome)

# ---------------- encarte ----------------
def tags_html(tags):
    out = []
    for t in tags:
        cls = " ".join(filter(None, ["tag", t.get("cor", "branco"), "riscado" if t.get("riscado") else ""]))
        p = html.escape(t["preco"]).replace("R$", "").strip()
        nota = f"<i>{md(t['nota'])}</i>" if t.get("nota") else ""
        out.append(f'<div class="{cls}"><small>{md(t.get("rotulo", ""))}</small><b><span>R$</span>{p}</b>{nota}</div>')
    return f'<div class="tags{" um" if len(tags) == 1 else ""}">{"".join(out)}</div>'

def encarte_slide(s, i, n, g):
    tipo = s["tipo"]; partes = []
    if s.get("titulo") and tipo != "cta":
        partes.append(f'<h1 class="{"m" if s.get("titulo_menor") or tipo in ("lista", "etiqueta", "conta") else ""}">{md(s["titulo"])}</h1>')
    if tipo in ("capa", "etiquetas"):
        partes.append(tags_html(s["tags"]))
    elif tipo == "conta":
        partes.append(caixa(s["linhas"], s.get("centro")))
    elif tipo == "lista":
        partes.append('<ul class="lista">' + "".join(f"<li>{md(x)}</li>" for x in s["itens"]) + "</ul>")
    elif tipo == "etiqueta":
        p = html.escape(s["preco"]).replace("R$", "").strip()
        partes.append(f'<div class="etq"><div class="t">{md(s.get("oferta", "OFERTA"))}</div><div class="p"><span>R$</span>{p}</div>'
                      f'<div class="dd"><span>{md(s.get("produto", ""))}</span>{f"<span class=kg>{md(s["destaque"])}</span>" if s.get("destaque") else ""}</div></div>')
    elif tipo == "cta":
        partes.append(f'<h1>{md(s["titulo"])}</h1>')
        if s.get("texto"): partes.append(f'<div class="texto">{md(s["texto"])}</div>')
    if s.get("linhas") and tipo != "conta":
        partes.append(caixa(s["linhas"]))
    if s.get("selo"):
        partes.append(f'<div class="selo{" vermelho" if s.get("selo_vermelho") else ""}">{md(s["selo"])}</div>')
    faixa = f'<div class="faixa">{md(s["faixa"])}</div>' if s.get("faixa") and tipo != "cta" else ""
    esq = "Arrasta pro lado &rarr;" if i == 1 else f'<span class="num">{i}/{n}</span>'
    aviso = "" if tipo == "cta" else md(s.get("aviso", g.get("aviso", "")))
    logo = img("logos/04-horizontal-branca.png" if tipo == "cta" else "logos/02-horizontal-colorida.png")
    return (f'<div class="post{" cta" if tipo == "cta" else ""}">{faixa}<div class="meio">{"".join(partes)}</div>'
            f'<div class="rod"><span>{esq}</span><span>{aviso}</span><img src="{logo}"></div></div>')

# ---------------- print nativo ----------------
def print_slide(s, i, n, g):
    tipo = s["tipo"]; perfil = g.get("perfil", {"nome": "LocalPrice Altamira", "usuario": "@localprice1"})
    c = [f'<div class="perfil"><img src="{img("logos/05-avatar-perfil.png")}"><div><b>{html.escape(perfil["nome"])}</b><span>{html.escape(perfil["usuario"])}</span></div></div>']
    if s.get("texto"): c.append(f'<p class="{"g" if s.get("grande", True) else ""}">{md(s["texto"])}</p>')
    if tipo == "lista":
        c.append("<ul>" + "".join(f"<li>{md(x)}</li>" for x in s["itens"]) +
                 (f'<li class="falta">{md(s["falta"])}</li>' if s.get("falta") else "") + "</ul>")
    if tipo == "campo":
        c.append(f'<div class="campo"><span>{md(s.get("placeholder", ""))}<span class="cursor"></span></span><b>{md(s.get("botao", "Publicar"))}</b></div>')
    if s.get("foto"):
        c.append(f'<div class="foto" style="background-image:url({img("fotos/" + s["foto"])})"></div>')
    if s.get("sub"): c.append(f'<p class="s">{md(s["sub"])}</p>')
    if s.get("meta"):
        a, b = (s["meta"] + ["", ""])[:2]
        c.append(f'<div class="meta"><span>{md(a)}</span><b>{md(b)}</b></div>')
    pag = "Arrasta &rarr;" if i == 1 else f"{i}/{n}"
    return f'<div class="post{" cta" if tipo == "cta" else ""}"><div class="card">{"".join(c)}</div><div class="pag">{pag}</div></div>'

def montar_html(g):
    est = g["estilo"]; n = len(g["paginas"])
    f = encarte_slide if est == "encarte" else print_slide
    css = CSS_BASE + (CSS_ENCARTE if est == "encarte" else CSS_PRINT)
    corpo = "\n".join(f(s, i + 1, n, g) for i, s in enumerate(g["paginas"]))
    return f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{css}</style></head><body>{corpo}</body></html>'

CONFERE = """() => {
  const erros = [];
  document.querySelectorAll('.post').forEach((p, i) => {
    const pr = p.getBoundingClientRect();
    p.querySelectorAll('*').forEach(e => {
      const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
      const txt = (e.innerText || '').trim().slice(0, 40);
      if (r.left < pr.left - 2 || r.right > pr.right + 2 || r.top < pr.top - 2 || r.bottom > pr.bottom + 2)
        erros.push(`página ${i + 1}: sai da arte -> ${e.tagName.toLowerCase()} "${txt}"`);
      const cs = getComputedStyle(e);
      if (e.scrollWidth > e.clientWidth + 3 && (cs.overflow !== 'visible' || cs.whiteSpace === 'nowrap' || e.children.length === 0 || e.tagName === 'B'))
        erros.push(`página ${i + 1}: texto cortado na largura -> "${txt}"`);
    });
    p.querySelectorAll('.meio, .card').forEach(m => {
      if (m.scrollHeight > m.clientHeight + 3) erros.push(`página ${i + 1}: conteúdo não cabe na altura (${m.scrollHeight} > ${m.clientHeight})`);
    });
  });
  return [...new Set(erros)];
}"""

def render(g, pasta):
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, "carrossel.html")
    open(caminho, "w").write(montar_html(g))
    js = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch(); const p = await b.newPage({{ viewport: {{ width: 1080, height: 1350 }} }});
  await p.goto('file://{caminho}'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(150);
  const erros = await p.evaluate({CONFERE});
  const els = await p.$$('.post'); let i = 1;
  for (const e of els) {{ await e.screenshot({{ path: '{pasta}/pg-' + String(i).padStart(2, '0') + '.png' }}); i++; }}
  await b.close(); console.log(JSON.stringify(erros));
}})();"""
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if r.returncode: sys.exit("Erro no Playwright:\n" + r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])

def finalizar(g, pasta):
    from PIL import Image
    import glob
    pgs = sorted(glob.glob(os.path.join(pasta, "pg-*.png"))); saidas = []
    for k, f in enumerate(pgs, 1):
        out = os.path.join(pasta, f"{g['id']}-{k:02d}.jpg")
        Image.open(f).convert("RGB").save(out, quality=93); saidas.append(out)
    ims = [Image.open(f).resize((270, 338)) for f in pgs]; cols = min(5, len(ims))
    folha = Image.new("RGB", (cols * 280, ((len(ims) + cols - 1) // cols) * 348), "#333")
    for k, im in enumerate(ims): folha.paste(im, ((k % cols) * 280, (k // cols) * 348))
    folha.save(os.path.join(pasta, "folha.png"))
    return pgs, saidas

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    g = json.load(open(sys.argv[1]))
    pasta = os.path.join(AQUI, "saida", g["id"])
    erros = render(g, pasta)
    pgs, saidas = finalizar(g, pasta)
    print(f"{len(saidas)} páginas em {pasta}")
    if erros:
        print("CONFERÊNCIA FALHOU:"); [print(" -", e) for e in erros]; sys.exit(2)
    print("Conferência ok: nenhum texto fora da arte ou cortado.")
    if "--short" in sys.argv:
        sys.path.insert(0, AQUI)
        from video import short_de_paginas
        short_de_paginas(pgs, os.path.join(pasta, f"{g['id']}-short.mp4"))

if __name__ == "__main__":
    main()
