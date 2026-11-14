# Vídeo de cada relógio (no ar desde 14/11/2026)

Vídeo em pé (720x1280, 30 qps, 13 a 16 s, cerca de 2 MB) montado só com as fotos reais do relógio e os dados da ficha,
sem nada inventado. Aprovado pelo Nevander em 14/11/2026 ("Ficou bom, pode fazer nos outros também"). Quem gera e publica
é `ferramentas/relogios_video.py` (veja a seção "Vídeo de cada relógio" no README).

- `modelo.html`: a página animada. `window.seek(t)` desenha o instante `t` (em segundos). Os dados (fotos, enquadramento,
  textos e tempos de cada cena) entram no lugar de `__DADOS__`. Cada foto entra com `mix-blend-mode:multiply` sobre o
  fundo creme (o programa leva o fundo da foto ao branco puro antes) e o brilho passa só onde a máscara diz que há relógio.
- `filma.js`: filma a página em cenas (um .mp4 por cena, CRF 28) e junta sem recodificar
  (`node filma.js video.html mudo.mp4 13.0 3.7 6.9 10.1`).
- `quadros.js`: tira alguns quadros para conferir antes de filmar (`node quadros.js video.html 2.0 5.2 8.4`).
- `fontes/`: Cormorant Garamond e Jost (licença SIL OFL), locais, para filmar sem internet.

Regras dos textos: o nome do produto vai sem a marca; a curiosidade sai do dossiê (`relogios_dossie`), curta para a tela;
a que fala do fundo da caixa só entra se a página tiver a foto do fundo. Mudou o desenho? Aumente `VERSAO` no programa.
