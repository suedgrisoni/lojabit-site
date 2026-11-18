# Imagem de compartilhamento (14/11 → 18/11/2026)

Quando alguém manda o link da página inicial ou de uma categoria (Relógios, Seiko, Decants...) no WhatsApp, Instagram,
Facebook, Telegram ou X, o app mostra a "prévia do link" com a imagem do `og:image`. A Loja Integrada põe ali o logo da loja
(499x138, fundo transparente), menor que o mínimo dos apps (Facebook e WhatsApp pedem pelo menos 200 px de altura): a prévia
saía sem foto. Nas páginas de produto a Loja Integrada já põe a foto do produto (800x800) e está certo.

- `social/compartilhar-1200x630.jpg`: a imagem (1200x630, ~110 KB). Logo e texto ficam no quadrado do meio (285 a 915 px),
  porque o WhatsApp corta um quadrado do centro quando mostra a prévia pequena.
- `modelo.html` + `foto.js`: de onde ela sai. Para refazer: `node ferramentas/compartilhar/foto.js ferramentas/compartilhar/modelo.html social/compartilhar-1200x630.jpg 1200 630`
  (fotos já com o fundo levado ao branco puro; fontes de `ferramentas/relogios_video/fontes`).
- `painel/compartilhar.html` (gerado por `ferramentas/carregador.py`): as tags `og:image` que vão no painel em 2 códigos
  de cabeçalho, um em "Página inicial" e outro em "Página da categoria". Não vão no carregador de todas as páginas para não
  disputar com a foto do produto. Os apps usam a primeira imagem válida: como o logo da Loja Integrada é pequeno demais,
  a nossa é a primeira válida.
- Trocou a imagem? Commit + push, `python3 ferramentas/carregador.py` e cole `painel/compartilhar.html` de novo nos 2 códigos.
  Depois, no Depurador de Compartilhamento do Facebook, "Extrair novamente" na home e nas categorias principais. O WhatsApp
  guarda a prévia antiga por alguns dias; links novos (ou com ?v=2 no fim) já pegam a nova.
