# Estúdio LocalPrice

Um arquivo JSON de conteúdo entra e o post sai pronto: carrossel (1080x1350), reel (1080x1920) e Short. As regras de tom, estilo e honestidade estão na skill `localprice-conteudo`.

## Comandos

```
python3 -I estudio/carrossel.py estudio/conteudo/<arquivo>.json [--short]
python3 -I estudio/video.py estudio/conteudo/<reel>.json
python3 -I estudio/publicar.py <id>
git add midia estudio/conteudo && git commit -m "..." && git push    # branch gh-pages
```

- As peças saem em `estudio/saida/<id>/` (fora do git), com `folha.png` (carrossel) ou `quadros.png` (reel) para conferir.
- O carrossel para com erro se um texto sair da arte ou não couber. O reel avisa quando um texto pode não caber na largura.
- Sempre abra a folha ou os quadros como imagem antes de publicar.
- `publicar.py` copia para `midia/AAAA-MM/` e mostra os links públicos que vão para o Metricool.
- Requisitos do ambiente: Python com Pillow e numpy, Node com Playwright, ffmpeg com libass e as fontes Inter.

## Marcação nos textos

| Escrita | Encarte | Print nativo | Reel |
| --- | --- | --- | --- |
| `**texto**` | vermelho | marca-texto amarelo | amarelo |
| `==texto==` | marca-texto | marca-texto amarelo | (não usar) |
| `++texto++` | verde | verde | (não usar) |
| `\n` | quebra de linha | quebra de linha | (use outro texto) |

"R$ 9,99" nunca quebra a linha entre o R$ e o número.

## Carrossel: campos gerais

| Campo | Uso |
| --- | --- |
| `id` | `AAAA-MM-DD-tema` (data de publicação). Vira o nome dos arquivos e a pasta do mês |
| `estilo` | `encarte` (A) ou `print` (B) |
| `aviso` | Rodapé de todas as páginas: "Valores ilustrativos" ou "Preços da comunidade em DD/MM/AAAA". Uma página pode ter o seu próprio `aviso` |
| `paginas` | Lista de páginas (abaixo). A primeira mostra "Arrasta pro lado", as outras a numeração n/N |

## Páginas do Encarte (estilo A)

Toda página aceita `faixa` (tarja vermelha), `titulo`, `linhas` (caixa branca), `selo` (selo preto girado; `selo_vermelho: true` para vermelho) e `aviso`.

| `tipo` | Campos próprios | Para quê |
| --- | --- | --- |
| `capa` / `etiquetas` | `tags`: 1 ou 2 etiquetas `{rotulo, preco, cor: branco/vermelho/verde, riscado, nota}` | Comparação de preços. Uma etiqueta só aparece grande |
| `conta` | `linhas`, `centro` | Conta passo a passo. A letra se ajusta ao tamanho da linha |
| `etiqueta` | `oferta`, `preco`, `produto`, `destaque` | Etiqueta de gôndola com um detalhe circulado |
| `lista` | `itens` | Lista com marcas de conferido |
| `cta` | `titulo`, `texto`, `selo` | Última página verde com logo branco |

## Páginas do Print nativo (estilo B)

Toda página é um cartão do perfil @localprice1 e aceita `texto` (`grande: false` para letra normal), `sub`, `meta` (`["esquerda", "direita"]`) e `foto` (arquivo em `assets/fotos/`).

| `tipo` | Campos próprios |
| --- | --- |
| `post` | nenhum |
| `lista` | `itens`, `falta` (último item tracejado) |
| `campo` | `placeholder`, `botao` (caixa de comentário desenhada) |
| `cta` | fundo verde |

## Reel: cenas

Campos gerais: `id`, `foto` (em `assets/fotos/`), `voz` (em `assets/vozes/`), `cenas`.

| `tipo` | Campos | O que mostra |
| --- | --- | --- |
| `foto` | `dur`, `zoom [z0, z1]`, `foco [x, y]`, `circulo {t, pos, tam}` | Foto real com zoom lento e gradiente escuro |
| `fundo` | `dur` | Foto desfocada e escura, só para texto |
| `tela` | `tela`: abrir, menu, foto, leitura ou mercado; `passo {n, l1, l2}` | Trecho da gravação do app dentro de um celular |
| `resultado` | `dur`, `selo {t, pos, linha1, linha2}` | Cartão "Encontramos um preço menor" do app |
| `fim` | `dur`, `titulo` (3 linhas), `aviso` | Cartão verde com logo, URL e aviso de preços |

Toda cena aceita `textos` (lista de `{t, estilo, texto, pos [x, y], alinhar: "esq", tam, efeito: "pop" ou "fade"}`), `caixa {t, y, linhas}` (caixa amarela) e `voz [início, fim]` (trecho do arquivo de voz que começa junto com a cena).

Estilos de texto: `giga` (200 px), `grande` (116), `medio` (80), `sub` (54), `pequeno` (36). Para centralizar, use `pos [540, y]` sem `alinhar`.

Durações das telas prontas: abrir 3,05 s; menu 2,7 s; foto 1,75 s; leitura 2,75 s; mercado 1,9 s.

### Trechos da voz `narracao-tutorial.wav` (voz Mário, ElevenLabs)

| Trecho (s) | Fala |
| --- | --- |
| 0,00 a 5,10 | "Você pagaria cinco e noventa e nove num detergente que custa dois e cinquenta ali do lado?" |
| 5,10 a 8,15 | "Olha como é fácil descobrir isso com o LocalPrice." |
| 8,15 a 10,85 | "Toque no mais e em Registrar preço." |
| 10,85 a 12,60 | "Tire uma foto da etiqueta." |
| 12,60 a 15,35 | "O app lê o produto e o preço sozinho." |
| 15,35 a 17,25 | "Escolha o mercado e publique." |
| 17,25 a 24,65 | "Pronto! Ele mostra onde está mais barato: três e quarenta e nove de economia só nesse produto." |
| 24,65 a 30,35 | "Cadastre-se grátis em localprice ponto com ponto br e ajude Altamira a economizar." |

Voz nova: grave no ElevenLabs com a mesma voz, salve o .wav em `assets/vozes/` e anote os trechos aqui.

## Recursos

- `assets/fotos/detergente-limpol-599.jpg`: etiqueta real de R$ 5,99 (29/10/2026). Mande mais fotos reais de etiquetas para ampliar o banco.
- `assets/gravacoes/tela-registrar-preco.mp4`: gravação de tela do fluxo "Registrar preço".
- `assets/logos/`: as 6 versões do logo.

## Exemplos

`conteudo/2026-11-11-pacote-economico.json` (Encarte), `conteudo/2026-11-04-mercado-que-falta.json` (Print) e `conteudo/2026-11-08-reel-mesmo-mercado.json` (reel).
