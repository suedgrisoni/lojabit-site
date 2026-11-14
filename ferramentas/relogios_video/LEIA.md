# Vídeo do relógio a partir das fotos (PILOTO de 14/11/2026)

Piloto feito para o Nevander avaliar: um vídeo em pé (720x1280, 30 qps, ~12,6 s) montado só com as fotos reais do
relógio, sem nada inventado. Ainda NÃO está ligado ao site nem roda sozinho: falta o Nevander aprovar o formato.

- `modelo.html`: a página animada. `window.seek(t)` desenha o instante `t` (em segundos). Usa 4 fotos (`f1.jpg` frente,
  `f2.jpg` mostrador de perto, `f3.jpg` perfil, `f4.jpg` três quartos) e 4 máscaras (`m1.png`...`m4.png`, onde a foto
  não é branca) para o brilho passar só sobre o relógio. Os textos entram no lugar de `__TXT__` (JSON com k1, t1, k2, l2,
  k3, l3, k4, t4, l4). Nos textos, o nome do produto vai sem a marca.
- `quadros.js`: tira alguns quadros para conferir antes de filmar (`node quadros.js pagina.html 2.0 5.2 8.2 11.8`).
- `filma.js`: filma a página em cenas (um .mp4 por cena) e junta sem recodificar
  (`node filma.js pagina.html mudo.mp4 12.6 3.7 6.9 9.8`).
- Som: tique-taque sintetizado no ritmo do movimento (6 batidas por segundo para 21.600 alternâncias/h), juntado com
  `ffmpeg -i mudo.mp4 -i tique.wav -map 0:v -map 1:a -c:v copy -c:a aac`.

Fotos: `https://cdn.awsli.com.br/2500x2500/278/278816/produto/<id>/<arquivo>.jpg` (a página do produto lista os arquivos).
As fotos têm fundo branco; na página elas entram com `mix-blend-mode:multiply` sobre o fundo creme, sem recorte.

Se o formato for aprovado, o próximo passo é um programa que monte os textos pela ficha (`carrossel/relogios.json`) e
pelo dossiê, gere o vídeo de cada relógio e do relógio novo, e ligue o vídeo à página do produto sem pesar (só baixa
quando o cliente toca).
