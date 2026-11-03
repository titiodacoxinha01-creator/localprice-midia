"""Gera as aplicações do logo LocalPrice sobre branco, sem alterar as cores do logo.

- assets/logos/etiqueta-logo.png: etiqueta de preço branca (com furo e cordão) segurando o logo horizontal colorido.
- assets/logos/selo-simbolo.png: selo redondo branco com o símbolo colorido (marca d'água dos reels).
Uso: python3 -I estudio/ferramentas/gerar_marca.py
"""
import os
from PIL import Image, ImageDraw, ImageFilter

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS = os.path.join(AQUI, "assets", "logos")
S = 4  # supersampling para bordas lisas

def etiqueta():
    logo = Image.open(os.path.join(LOGOS, "02-horizontal-colorida.png")).convert("RGBA")
    lh = 150 * S; logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
    pad, ponta, furo = 44 * S, 74 * S, 15 * S
    w, h = logo.width + 2 * pad + ponta, lh + 2 * pad
    m = 40 * S  # margem para sombra e cordão
    base = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    x0, y0 = m, m
    forma = [(x0, y0 + h / 2), (x0 + ponta, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0 + ponta, y0 + h)]
    # sombra suave
    sombra = Image.new("L", base.size, 0)
    ImageDraw.Draw(sombra).polygon([(x + 6 * S, y + 10 * S) for x, y in forma], fill=90)
    sombra = sombra.filter(ImageFilter.GaussianBlur(14 * S))
    base.paste((0, 0, 0, 255), (0, 0), sombra)
    # etiqueta branca com cantos levemente arredondados
    corpo = Image.new("L", base.size, 0); d = ImageDraw.Draw(corpo)
    d.polygon(forma, fill=255)
    d.rounded_rectangle([x0 + ponta, y0, x0 + w, y0 + h], radius=22 * S, fill=255)
    base.paste((255, 255, 255, 255), (0, 0), corpo)
    dd = ImageDraw.Draw(base)
    # furo e cordão
    cx, cy = x0 + ponta * 0.62, y0 + h / 2
    dd.ellipse([cx - furo, cy - furo, cx + furo, cy + furo], fill=(0, 0, 0, 0), outline=(205, 205, 205, 255), width=4 * S)
    furo_mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(furo_mask).ellipse([cx - furo + 4 * S, cy - furo + 4 * S, cx + furo - 4 * S, cy + furo - 4 * S], fill=255)
    base.paste((0, 0, 0, 0), (0, 0), furo_mask)
    dd.line([(cx, cy), (cx - 26 * S, cy - 22 * S), (6 * S, 6 * S)], fill=(33, 33, 33, 255), width=5 * S, joint="curve")
    base.alpha_composite(logo, (int(x0 + ponta + pad - 18 * S), int(y0 + pad)))
    out = base.resize((base.width // S, base.height // S), Image.LANCZOS)
    out.save(os.path.join(LOGOS, "etiqueta-logo.png")); print("etiqueta-logo.png", out.size)

def selo():
    av = Image.open(os.path.join(LOGOS, "05-avatar-perfil.png")).convert("RGBA")  # símbolo colorido em círculo branco
    t = 240; m = 24
    base = Image.new("RGBA", (t + 2 * m, t + 2 * m), (0, 0, 0, 0))
    sombra = Image.new("L", base.size, 0)
    ImageDraw.Draw(sombra).ellipse([m + 3, m + 6, m + t + 3, m + t + 6], fill=110)
    base.paste((0, 0, 0, 255), (0, 0), sombra.filter(ImageFilter.GaussianBlur(9)))
    base.alpha_composite(av.resize((t, t), Image.LANCZOS), (m, m))
    base.save(os.path.join(LOGOS, "selo-simbolo.png")); print("selo-simbolo.png", base.size)

if __name__ == "__main__":
    etiqueta(); selo()
