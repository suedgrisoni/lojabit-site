# lojabit-site

Arquivos do visual do site **www.lojabit.com** (Loja Integrada), entregues pelo **jsDelivr** e guardados em cache no celular do cliente.

## Por que existe (Etapa 3 — 02/11/2026)

Antes, os ~80 códigos HTML "de todas as páginas" do painel da Loja Integrada iam **dentro de cada página** (≈1 MB de HTML por página).
O celular baixava tudo de novo a cada página aberta.

Agora esses códigos viraram **4 arquivos** que o celular baixa **uma vez** e guarda:

| arquivo | o que tem | onde entra |
|---|---|---|
| `dist/cab.css` | estilos dos códigos do cabeçalho | cabeçalho |
| `dist/cab.js` | scripts dos códigos do cabeçalho | cabeçalho |
| `dist/rod.css` | estilos dos códigos do rodapé | rodapé |
| `dist/rod.js` | scripts dos códigos do rodapé | rodapé |

No painel ficaram só **2 códigos carregadores** (veja `painel/`), mais os que precisam ficar no HTML
(dados estruturados do Google, pixel da Meta, CSS do tema que vale também no checkout, códigos de uma página só e os desligados).

## Como está organizado

- `src/<id>.html` — o conteúdo de cada código, igual ao que estava no painel (o número é o ID do código na Loja Integrada).
- `ordem.json` — a ordem em que a Loja Integrada punha os códigos na página. **Os arquivos seguem essa ordem.**
- `build.py` — monta `dist/` a partir de `src/` e `ordem.json`:
  - cada `<script>` de cada código vira um bloco `try/catch` (se um código der erro, os outros continuam, como antes);
  - os `<style>` viram CSS na mesma ordem;
  - o JavaScript é compactado (terser) e o CSS tem comentários e espaços removidos.
- `dist/manifesto.json` — tamanho e impressão digital (sha256) de cada arquivo e a lista de códigos.
- `painel/` — o conteúdo exato dos 2 códigos carregadores do painel (gerado por `ferramentas/carregador.py`).

## Como mudar um código

1. Edite `src/<id>.html` (ou crie um novo e coloque em `ordem.json` no lugar certo).
2. Rode `python3 build.py` (precisa de Node com `terser` para compactar o JS; sem ele o JS sai sem compactar).
3. Teste antes de publicar: `python3 ferramentas/testa.py` abre o site ao vivo com os arquivos novos de `dist/`
   (só no navegador do teste) e compara com o site de hoje, no celular e no computador.
4. Faça o commit e o push.
5. Rode `python3 ferramentas/carregador.py` — ele gera `painel/cabecalho.html` e `painel/rodape.html`
   com o endereço de cada arquivo preso ao **commit em que ele mudou pela última vez**
   (assim o cliente só baixa de novo o arquivo que mudou).
6. Cole no painel só o carregador que mudou — cabeçalho no código **1720982 "Etapa 3 - arquivos cabeçalho"**,
   rodapé no **1718611 "Etapa 3 - arquivos rodapé"** — e confira o site no celular (as páginas ficam ~5 min em cache).

**Não cole o código de volta no painel**: ele rodaria duas vezes (no painel e no arquivo).

Atenção: a Loja Integrada pode mudar a ordem dos códigos de "todas as páginas" quando muitos são salvos de uma vez
(em 02/11, depois de salvar os 80, vários trocaram de lugar). Dentro dos arquivos a ordem é a de `ordem.json` e não muda.
No painel sobraram poucos códigos com conteúdo, e nenhum depende dos carregadores; o que importa é o que a loja já garante:
códigos de uma página só vêm antes dos de todas as páginas, e a "Configuração CSS do tema NDellas" (todas as páginas, com checkout) vem por último.

Os endereços são presos a um commit (`@<sha>`), por isso o jsDelivr e o celular podem guardar o arquivo por 1 ano sem risco:
um conteúdo novo sempre tem um endereço novo.

## Segurança

- Se o `cdn.jsdelivr.net` falhar, os carregadores tentam `fastly.jsdelivr.net` sozinhos.
- Cada código continua isolado (`try/catch`): o erro de um não derruba os outros (aparece no console como `lojabit codigo <id>`).
- Os conteúdos antigos de cada código estão guardados no projeto (backup antes de cada mudança).
