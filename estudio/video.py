"""Vídeos do LocalPrice (1080x1920): reels a partir de JSON e Shorts a partir das páginas de um carrossel.

Uso:
    python3 estudio/video.py estudio/conteudo/<reel>.json

Saída: estudio/saida/<id>/<id>.mp4 e quadros de conferência (quadros.png).
Tipos de cena, trechos de voz e telas do app prontas: veja estudio/LEIAME.md.
"""
import glob, json, os, random, re, shutil, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, "assets")
GRAVACAO = os.path.join(ASSETS, "gravacoes", "tela-registrar-preco.mp4")
W, H, FPS, SR = 1080, 1920, 30, 44100
VERDE = "0x568F60"  # verde economia do app
FONTES = os.path.join(ASSETS, "fontes")  # Nunito (títulos do app); Inter vem do sistema

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit("ERRO: " + " ".join(map(str, cmd))[:300] + "\n" + r.stderr[-2500:])

def enc(out):
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), out]

def ease(t0, t1, a, b, var):
    p = f"clip(({var}-{t0})/{t1 - t0},0,1)"
    return f"({a}+({b}-{a})*({p})*({p})*(3-2*({p})))"

# ---------------------------------------------------------------- áudio
def note(f): return 440 * 2 ** ((f - 69) / 12)

def music_bed(total):
    """Trilha original gerada por código (sem direitos autorais): Am F C G a 116 bpm."""
    t_all = np.arange(int(total * SR)) / SR; music = np.zeros_like(t_all)
    beat = 60 / 116; prog = [(57, 60, 64), (53, 57, 60), (60, 64, 67), (55, 59, 62)]
    nb = int(total / beat) + 1; rng = np.random.default_rng(3)
    for i in range(nb * 2):
        n0 = int(i * beat / 2 * SR)
        if n0 >= len(music): break
        ch = prog[(i // 8) % 4]; f = note(ch[i % 3] + 12 * (i % 4 == 3))
        seg = np.arange(int(0.4 * SR)) / SR
        music[n0:n0 + len(seg)] += 0.15 * ((np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(4 * np.pi * f * seg)) * np.exp(-seg * 8))[: len(music) - n0]
    for i in range(nb):
        n0 = int(i * beat * SR)
        if n0 >= len(music): break
        ch = prog[(i // 4) % 4]; L = int(0.5 * SR); seg = np.arange(L) / SR
        bass = np.sin(2 * np.pi * note(ch[0] - 24) * seg) * np.exp(-seg * 4)
        kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-seg * 30)) * seg) * np.exp(-seg * 14) if i % 2 == 0 else 0
        hat = np.zeros(L); hl = int(0.05 * SR); hat[:hl] = rng.standard_normal(hl) * np.exp(-np.arange(hl) / SR * 80)
        music[n0:n0 + L] += (0.22 * bass + 0.35 * kick + (0.05 * hat if i % 2 else 0))[: len(music) - n0]
    return music * np.clip(t_all / 0.4, 0, 1) * np.clip((total - t_all) / 1.0, 0, 1)

def ler_voz(caminho):
    with wave.open(caminho) as wf:
        sr = wf.getframerate(); ch = wf.getnchannels()
        v = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(float) / 32768
    if ch > 1: v = v.reshape(-1, ch).mean(1)
    if sr != SR: v = np.interp(np.arange(int(len(v) * SR / sr)) / SR, np.arange(len(v)) / sr, v)
    return v

def mixar(total, voz_arq, partes, pops, whooshes, dings, out):
    t_all = np.arange(int(total * SR)) / SR
    music = music_bed(total); sfx = np.zeros_like(t_all); voice = np.zeros_like(t_all)
    if partes:
        v = ler_voz(voz_arq)
        for a, b, at in partes:
            seg = v[int(a * SR):int(b * SR)].copy(); fl = int(0.03 * SR)
            seg[:fl] *= np.linspace(0, 1, fl); seg[-fl:] *= np.linspace(1, 0, fl)
            n0 = int(at * SR); voice[n0:n0 + len(seg)] += seg[: len(voice) - n0]
    rng = np.random.default_rng(1)
    def put(sig, at, gain):
        n0 = int(at * SR)
        if 0 <= n0 < len(sfx): sfx[n0:n0 + len(sig)] += gain * sig[: len(sfx) - n0]
    for at in whooshes:
        n = rng.standard_normal(int(0.35 * SR)); env = np.sin(np.linspace(0, np.pi, len(n))) ** 2
        put(np.convolve(n, np.ones(12) / 12, "same") * env, at - 0.18, 0.2)
    for at in pops:
        seg = np.arange(int(0.14 * SR)) / SR
        put(np.sin(2 * np.pi * (500 + 900 * np.exp(-seg * 35)) * seg) * np.exp(-seg * 28), at, 0.45)
    for at in dings:
        seg = np.arange(int(0.9 * SR)) / SR
        put((np.sin(2 * np.pi * 1046.5 * seg) + 0.6 * np.sin(2 * np.pi * 1568 * seg)) * np.exp(-seg * 5), at, 0.35)
    if voice.any():
        env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
        duck = 1 - 0.7 * np.clip(env / (env.max() * 0.15 + 1e-9), 0, 1)
    else:
        duck = 1
    mix = music * duck * 0.85 + sfx * 0.8 + voice * 0.95
    mix = mix / max(1e-9, np.abs(mix).max()) * 0.89
    with wave.open(out, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---------------------------------------------------------------- recursos visuais
PW, PH, PX, PY = 776, 1440, 152, 400   # celular
CW, CH, CX, CY = 900, 1424, 90, 400    # cartão de resultado

def preparar(trab, foto):
    def rounded(w, h, r, path):
        img = Image.new("L", (w, h), 0); ImageDraw.Draw(img).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); img.save(path)
    rounded(PW, PH, 44, f"{trab}/mask_phone.png"); rounded(CW, CH, 44, f"{trab}/mask_card.png")
    for name, w, h in [("shadow_phone.png", PW, PH), ("shadow_card.png", CW, CH)]:
        a = Image.new("L", (w + 120, h + 120), 0)
        ImageDraw.Draw(a).rounded_rectangle([60, 70, 60 + w, 70 + h], 44, fill=150)
        s = Image.new("RGBA", a.size, (0, 0, 0, 0)); s.putalpha(a.filter(ImageFilter.GaussianBlur(28))); s.save(f"{trab}/{name}")
    g = np.interp(np.linspace(0, 1, H), [0, .45, .62, 1], [.80, .38, .25, .85])
    gi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gi.putalpha(Image.fromarray((np.repeat(g[:, None], W, 1) * 255).astype(np.uint8), "L")); gi.save(f"{trab}/grad.png")
    im = Image.open(foto).convert("RGB")
    r = im.resize((max(W, int(im.width * H / im.height)), H), Image.LANCZOS) if im.width * H / im.height >= W else im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    x, y = (r.width - W) // 2, (r.height - H) // 2
    r = r.crop((x, y, x + W, y + H)); r.save(f"{trab}/foto.jpg", quality=92)
    r.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.5)).save(f"{trab}/fundo_blur.png")
    logo = Image.open(os.path.join(ASSETS, "logos/04-horizontal-branca.png")).convert("RGBA")
    logo.resize((700, int(logo.height * 700 / logo.width)), Image.LANCZOS).save(f"{trab}/plate.png")
    selo = Image.open(os.path.join(ASSETS, "logos/03-simbolo-branco.png")).convert("RGBA")
    selo = selo.resize((74, int(selo.height * 74 / selo.width)), Image.LANCZOS)
    selo.putalpha(selo.split()[3].point(lambda v: int(v * 0.9))); selo.save(f"{trab}/selo.png")

def cena_foto(trab, nome, dur, z0=1.0, z1=1.1, cx=566, cy=1100, escura=False):
    n = int(round(dur * FPS)); z = ease(0, dur, z0, z1, f"(on/{FPS})")
    src = f"{trab}/fundo_blur.png" if escura else f"{trab}/foto.jpg"
    vf = (f"[0:v]scale={W}:{H},zoompan=z='{z}':x='clip({cx}-iw/zoom/2,0,iw-iw/zoom)':y='clip({cy}-ih/zoom/2,0,ih-ih/zoom)'"
          f":d=1:s={W}x{H}:fps={FPS}[b];[b][1:v]overlay=0:0,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", src, "-loop", "1", "-i", f"{trab}/grad.png",
         "-filter_complex", vf, "-map", "[v]", "-frames:v", str(n), *enc(f"{trab}/{nome}.mp4")])
    return n / FPS

TELAS = {  # trechos prontos da gravação de tela (início, fim, velocidade) + zoom (t0, t1, z0, z1, cx, cy)
    "abrir":   {"clipes": [(0.8, 3.85, 1)], "zoom": None},
    "menu":    {"clipes": [(3.8, 6.0, 2.2 / 2.7)], "zoom": (0.2, 1.2, 1.0, 1.55, 400, 1124)},
    "foto":    {"clipes": [(7.5, 15.0, 7.5 / 1.75)], "zoom": (0.2, 1.3, 1.0, 1.5, 560, 1074)},
    "leitura": {"clipes": [(15.0, 27.0, 12 / 1.75), (29.5, 30.5, 1)], "zoom": (1.8, 2.2, 1.0, 1.9, 260, 330)},
    "mercado": {"clipes": [(41.1, 43.0, 1)], "zoom": (0.9, 1.4, 1.0, 1.7, 336, 174)},
}

def cena_tela(trab, nome, preset):
    clips, zoom = TELAS[preset]["clipes"], TELAS[preset]["zoom"]
    parts, labels, dur = [], [], 0.0
    for i, (a, b, sp) in enumerate(clips):
        parts.append(f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},fps={FPS}[c{i}]"); labels.append(f"[c{i}]"); dur += (b - a) / sp
    chain = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(clips)}:v=1:a=0[raw];[raw]crop=396:735:0:115,scale=792:1470:flags=lanczos,unsharp=5:5:0.5"
    if zoom:
        t0, t1, z0, z1, cx, cy = zoom
        chain += (f",zoompan=z='{ease(t0, t1, z0, z1, f'(on/{FPS})')}':x='clip({cx}-iw/zoom/2,0,iw-iw/zoom)':"
                  f"y='clip({cy}-ih/zoom/2,0,ih-ih/zoom)':d=1:s={PW}x{PH}:fps={FPS}")
    else:
        chain += f",scale={PW}:{PH}"
    chain += (f",format=rgba[p];[1:v]format=gray[m];[p][m]alphamerge[pm];[3:v]fps={FPS},format=yuv420p[bg];"
              f"[bg][2:v]overlay=x={PX - 60}:y={PY - 60}:shortest=1[bs];[bs][pm]overlay=x={PX}:y={PY}:shortest=1,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", GRAVACAO, "-loop", "1", "-i", f"{trab}/mask_phone.png", "-loop", "1", "-i", f"{trab}/shadow_phone.png",
         "-loop", "1", "-i", f"{trab}/fundo_blur.png", "-filter_complex", chain, "-map", "[v]", "-t", f"{dur:.3f}", *enc(f"{trab}/{nome}.mp4")])
    return dur

def cena_resultado(trab, nome, dur):
    vf = (f"[0:v]trim=78.3:82.3,setpts=PTS-STARTPTS,fps={FPS},tpad=stop_mode=clone:stop_duration={max(0.1, dur - 4):.2f},"
          f"crop=376:595:10:130,scale={int(CW*1.1)}:{int(CH*1.1)}:flags=lanczos,unsharp=5:5:0.5,"
          f"zoompan=z='{ease(0, 4.5, 1.0, 1.06, '(on/30)')}':x='iw/2-iw/zoom/2':y='ih*0.42-ih/zoom*0.42':d=1:s={CW}x{CH}:fps={FPS},"
          f"format=rgba[p];[1:v]format=gray[m];[p][m]alphamerge[pm];[3:v]fps={FPS},format=yuv420p[bg];"
          f"[bg][2:v]overlay=x={CX - 60}:y='{CY}+900*pow(max(0,1-t/0.35),3)-60':shortest=1[bs];"
          f"[bs][pm]overlay=x={CX}:y='{CY}+900*pow(max(0,1-t/0.35),3)':shortest=1,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", GRAVACAO, "-loop", "1", "-i", f"{trab}/mask_card.png", "-loop", "1", "-i", f"{trab}/shadow_card.png",
         "-loop", "1", "-i", f"{trab}/fundo_blur.png", "-filter_complex", vf, "-map", "[v]", "-t", f"{dur}", *enc(f"{trab}/{nome}.mp4")])
    return dur

def cena_fim(trab, nome, dur):
    pw = Image.open(f"{trab}/plate.png").width
    vf = (f"color=c={VERDE}:s={W}x{H}:r={FPS}:d={dur}[bg];[1:v]format=rgba,fade=in:st=0.1:d=0.25:alpha=1[pl];"
          f"[bg][pl]overlay=x={(W - pw) // 2}:y='300+260*pow(max(0,1-t/0.5),3)':shortest=1,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "nullsrc", "-loop", "1", "-i", f"{trab}/plate.png",
         "-filter_complex", vf, "-map", "[v]", "-t", f"{dur}", *enc(f"{trab}/{nome}.mp4")])
    return dur

# ---------------------------------------------------------------- textos (ASS)
AM, BR = "&H0069D2FC&", "&H00FFFFFF&"  # amarelo oferta #FCD269 (ASS usa BGR) e branco
POP = "\\fscx0\\fscy0\\t(0,170,\\fscx110\\fscy110)\\t(170,280,\\fscx100\\fscy100)"
ESTILOS = {"giga": ("Nunito Black", 200, 6), "grande": ("Nunito Black", 116, 5), "medio": ("Nunito Black", 80, 4),
           "sub": ("Inter SemiBold", 54, 3), "pequeno": ("Inter Medium", 36, 2), "forma": ("Inter", 40, 0),
           "etiqueta": ("Nunito Black", 60, 0), "num": ("Nunito Black", 70, 0)}
LARG = {"giga": 0.50, "grande": 0.50, "medio": 0.50, "sub": 0.50, "pequeno": 0.50, "etiqueta": 0.52}  # largura média por caractere / tamanho

def ts(t): t = max(0, t); return f"0:{int(t // 60):02d}:{t % 60:05.2f}"

def rrect(w, h, r):
    k = 0.55 * r
    return (f"m {r} 0 l {w-r} 0 b {w-r+k} 0 {w} {r-k} {w} {r} l {w} {h-r} b {w} {h-r+k} {w-r+k} {h} {w-r} {h} "
            f"l {r} {h} b {r-k} {h} 0 {h-r+k} 0 {h-r} l 0 {r} b 0 {r-k} {r-k} 0 {r} 0")

def ellipse(w, h):
    k = 0.55
    return (f"m {w/2} 0 b {w/2 + k*w/2} 0 {w} {h/2 - k*h/2} {w} {h/2} b {w} {h/2 + k*h/2} {w/2 + k*w/2} {h} {w/2} {h} "
            f"b {w/2 - k*w/2} {h} 0 {h/2 + k*h/2} 0 {h/2} b 0 {h/2 - k*h/2} {w/2 - k*w/2} 0 {w/2} 0")

def marcar(t):
    t = t.replace("{", "(").replace("}", ")")
    return re.sub(r"\*\*(.+?)\*\*", lambda m: f"{{\\c{AM}}}{m.group(1)}{{\\c{BR}}}", t)

def escrever_ass(path, ev):
    with open(path, "w") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
                "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        for n, (fn, sz, sh) in ESTILOS.items():
            f.write(f"Style: {n},{fn},{sz},{BR},{BR},&H00000000,&H70000000,0,0,0,0,100,100,-1,0,1,0,{sh},5,40,40,0,1\n")
        f.write("\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(ev) + "\n")

# ---------------------------------------------------------------- reel a partir de JSON
def reel(cfg):
    pasta = os.path.join(AQUI, "saida", cfg["id"]); trab = os.path.join(pasta, "trab"); os.makedirs(trab, exist_ok=True)
    preparar(trab, os.path.join(ASSETS, "fotos", cfg.get("foto", "detergente-limpol-599.jpg")))
    voz = os.path.join(ASSETS, "vozes", cfg.get("voz", "narracao-tutorial.wav"))
    d, avisos = [], []
    for i, c in enumerate(cfg["cenas"]):
        nome = f"c{i}"; tipo = c["tipo"]
        if tipo == "foto":
            z = c.get("zoom", [1.0, 1.1]); f = c.get("foco", [566, 1500])
            d.append(cena_foto(trab, nome, c["dur"], z[0], z[1], f[0], f[1]))
        elif tipo == "fundo":
            d.append(cena_foto(trab, nome, c["dur"], 1.05, 1.0, 540, 960, escura=True))
        elif tipo == "tela":
            d.append(cena_tela(trab, nome, c["tela"]))
        elif tipo == "resultado":
            d.append(cena_resultado(trab, nome, c["dur"]))
        elif tipo == "fim":
            d.append(cena_fim(trab, nome, c.get("dur", 5.75)))
        else:
            sys.exit(f"Tipo de cena desconhecido: {tipo}")
    st = [sum(d[:i]) for i in range(len(d))]; total = sum(d)
    ev, pops, whoosh, dings, partes = [], [], st[1:], [], []
    def dlg(a, b, style, text, layer=1): ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{style},,0,0,0,,{text}")
    for i, c in enumerate(cfg["cenas"]):
        s, e = st[i], st[i] + d[i]
        if c.get("voz"): partes.append((c["voz"][0], c["voz"][1], s))
        for tx in c.get("textos", []):
            est = tx.get("estilo", "grande"); a = s + tx.get("t", 0.1)
            x, y = tx.get("pos", [540, 900]); al = "\\an4" if tx.get("alinhar") == "esq" else ""
            fs = f"\\fs{tx['tam']}" if tx.get("tam") else ""
            cor = f"\\c{AM}" if tx.get("amarelo") else ""
            anim = POP if tx.get("efeito", "pop") == "pop" else "\\fad(120,0)"
            dlg(a, e, est, f"{{{al}\\pos({x},{y}){fs}{cor}{anim}}}{marcar(tx['texto'])}")
            if anim == POP: pops.append(a)
            tam = tx.get("tam", ESTILOS[est][1]); larg = len(re.sub(r"\*\*", "", tx["texto"])) * tam * LARG.get(est, 0.6)
            borda = x + larg if al else x + larg / 2
            if borda > W - 30 or (not al and x - larg / 2 < 30):
                avisos.append(f"cena {i + 1}: texto pode não caber na largura: \"{tx['texto']}\" (diminua 'tam' ou quebre em duas linhas)")
        if c.get("circulo"):
            ci = c["circulo"]; a = s + ci.get("t", 0.8); cx, cy = ci.get("pos", [566, 1690]); w, h = ci.get("tam", [640, 330])
            dlg(a, e, "forma", f"{{\\an5\\pos({cx},{cy})\\p1\\1a&HFF&\\3c{AM}\\bord14\\shad0\\frz-4{POP}}}{ellipse(w, h)}{{\\p0}}", 2); pops.append(a)
        if c.get("passo"):
            p = c["passo"]
            dlg(s, e, "forma", f"{{\\an5\\pos(150,220)\\p1\\c{AM}\\bord0\\shad0{POP}}}{ellipse(124, 124)}{{\\p0}}", 2)
            dlg(s, e, "num", f"{{\\pos(150,224)\\c&H212121&{POP}}}{p['n']}", 3)
            dlg(s, e, "medio", f"{{\\an4\\pos(245,185)\\fs64\\fad(100,80)\\move(215,185,245,185,0,180)}}{marcar(p['l1'])}", 3)
            dlg(s, e, "medio", f"{{\\an4\\pos(245,262)\\fs64\\c{AM}\\fad(100,80)\\move(215,262,245,262,60,240)}}{marcar(p['l2'])}", 3)
            pops.append(s + 0.02)
            if c.get("tela") == "leitura":
                dlg(s + 0.05, s + 1.75, "forma", f"{{\\an7\\p1\\c{AM}\\bord0\\shad0\\1a&H40&\\move(170,740,170,1540)}}{rrect(740, 10, 5)}{{\\p0}}", 4)
        if c.get("selo"):
            se = c["selo"]; a = s + se.get("t", 1.0); cx, cy = se.get("pos", [820, 470])
            dlg(a, e, "forma", f"{{\\an5\\pos({cx},{cy})\\frz8\\p1\\c{AM}\\bord0\\shad10\\4c&H60000000&{POP}}}{rrect(420, 160, 30)}{{\\p0}}", 5)
            dlg(a, e, "pequeno", f"{{\\pos({cx},{cy - 32})\\frz8\\c&H212121&\\shad0{POP}}}{se['linha1']}", 6)
            dlg(a, e, "etiqueta", f"{{\\pos({cx},{cy + 30})\\frz8\\fs80\\c&H212121&{POP}}}{se['linha2']}", 6)
            dings.append(a)
        if c.get("caixa"):
            cx_ = c["caixa"]; a = s + cx_.get("t", 1.5); y = cx_.get("y", 1100); l = cx_["linhas"]
            hh = 80 + 75 * len(l)
            dlg(a, e, "forma", f"{{\\an5\\pos(540,{y})\\p1\\c{AM}\\bord0\\shad8\\4c&H50000000&\\frz-2{POP}}}{rrect(900, hh, 40)}{{\\p0}}", 2)
            for k, linha in enumerate(l):
                dlg(a, e, "etiqueta", f"{{\\pos(540,{y - (len(l) - 1) * 37 + k * 75})\\frz-2\\c&H212121&{POP}}}{linha}", 3)
            dings.append(a)
        if c["tipo"] == "fim":
            t = c.get("titulo", ["Manda pra quem", "faz as compras", "**aí em casa.**"])
            for k, linha in enumerate(t):
                y = 800 + 120 * k
                dlg(s + 0.35 + 0.15 * k, e, "grande", f"{{\\pos(540,{y})\\fs100\\fad(150,0)\\move(540,{y + 40},540,{y},0,250)}}{marcar(linha)}")
            dlg(s + 1.6, e, "forma", f"{{\\an5\\pos(540,{800 + 120 * len(t) + 140})\\p1\\c{AM}\\bord0\\shad8\\4c&H50000000&{POP}}}{rrect(760, 130, 65)}{{\\p0}}", 2)
            dlg(s + 1.6, e, "etiqueta", f"{{\\pos(540,{800 + 120 * len(t) + 140})\\c&H212121&{POP}}}localprice.com.br", 3)
            dlg(s + 2.1, e, "pequeno", f"{{\\pos(540,{800 + 120 * len(t) + 280})\\fad(200,0)}}cadastro grátis · link na bio", 3)
            if c.get("aviso"): dlg(s + 2.1, e, "pequeno", f"{{\\pos(540,1760)\\fs30\\fad(200,0)}}{c['aviso']}", 3)
            pops.append(s + 1.6)
    escrever_ass(f"{trab}/textos.ass", ev)
    mixar(total, voz, partes, pops, whoosh, dings, f"{trab}/audio.wav")
    with open(f"{trab}/lista.txt", "w") as f:
        for i in range(len(d)): f.write(f"file 'c{i}.mp4'\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{trab}/lista.txt", "-c", "copy", f"{trab}/montado.mp4"])
    fim_em = next((st[i] for i, c in enumerate(cfg["cenas"]) if c["tipo"] == "fim"), total)
    out = os.path.join(pasta, f"{cfg['id']}.mp4"); tmp = f"{trab}/tmp.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{trab}/montado.mp4", "-i", f"{trab}/audio.wav", "-loop", "1", "-i", f"{trab}/selo.png", "-filter_complex",
         f"[0:v][2:v]overlay=x=966:y=96:shortest=1:enable='lt(t,{fim_em:.2f})'[w];[w]ass={trab}/textos.ass:fontsdir={FONTES}[v]",
         "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-shortest", tmp])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", out])
    quadros(out, [st[i] + min(d[i] - 0.2, max(0.6, d[i] * 0.7)) for i in range(len(d))], os.path.join(pasta, "quadros.png"))
    shutil.rmtree(trab)
    return out, total, avisos

def quadros(video, tempos, saida):
    ims = []
    for k, t in enumerate(tempos):
        f = f"{saida}.{k}.png"
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=270:-1", f])
        ims.append(Image.open(f).copy()); os.remove(f)
    folha = Image.new("RGB", (280 * len(ims), 480), "#333")
    for k, im in enumerate(ims): folha.paste(im, (k * 280, 0))
    folha.save(saida)

# ---------------------------------------------------------------- Short a partir das páginas
def short_de_paginas(paginas, out, per=3.2, primeira=3.6, tr=0.35):
    trab = out + ".trab"; os.makedirs(trab, exist_ok=True)
    durs = [primeira] + [per] * (len(paginas) - 1); durs[-1] += 1.0
    ins, parts = [], []
    for i, (f, dd) in enumerate(zip(paginas, durs)):
        r, g, b = Image.open(f).convert("RGB").getpixel((5, 1340))
        ins += ["-loop", "1", "-t", f"{dd + tr:.2f}", "-i", f]
        parts.append(f"[{i}:v]scale=1080:1350,pad=1080:1920:0:285:color=0x{r:02X}{g:02X}{b:02X},fps=30,format=yuv420p,settb=AVTB[v{i}]")
    chain, last, off = ";".join(parts), "v0", 0.0
    for i in range(1, len(paginas)):
        off += durs[i - 1]; chain += f";[{last}][v{i}]xfade=transition=slideleft:duration={tr}:offset={off:.2f}[x{i}]"; last = f"x{i}"
    total = sum(durs) + tr
    m = music_bed(total); m = m / np.abs(m).max() * 0.6
    with wave.open(f"{trab}/bed.wav", "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((m * 32767).astype(np.int16).tobytes())
    run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-i", f"{trab}/bed.wav", "-filter_complex", chain, "-map", f"[{last}]",
         "-map", f"{len(paginas)}:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30",
         "-af", "loudnorm=I=-16:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out])
    shutil.rmtree(trab); print(f"Short: {out} ({total:.1f} s)")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1]))
    out, total, avisos = reel(cfg)
    print(f"Reel: {out} ({total:.1f} s)")
    for a in avisos: print("AVISO:", a)
    print("Confira os quadros em", os.path.join(os.path.dirname(out), "quadros.png"))
