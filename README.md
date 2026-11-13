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

## Carrosséis da página do produto (04/11/2026)

- Código `src/1799001.html` (só no repositório, não existe no painel) busca os dados; quem desenha é o `src/1718168.html`
  (Visual novo 31), com os mesmos cartões do site (tamanhos e preços dos decants, selos das famílias, sacola no celular):
  "Parecidos com o X" (+ link "Ver a comparação completa") e "Com a mesma proposta". Perfume sem dados continua com o
  "Perfumes parecidos" antigo (mais vendidos com as mesmas notas).
- Preços: tarefa agendada "Carrossel: preços atualizados" (7h17, 10h17, 15h17, 19h17 e 22h17).
- Dados: `carrossel/base.json` (listas feitas pelo Claude a partir da base de perfumes) + `carrossel/p/<id>.json`
  (um arquivo pequeno por produto, com link, foto e preço atual lidos da listagem pública da loja).
- O site lê `carrossel/v.json` pelo raw.githubusercontent (cache de ~5 min) e os dados pelo jsDelivr preso ao commit indicado nele;
  por isso atualizar preços NÃO precisa mexer no painel nem nos carregadores.
- Atualizar preços: `python3 ferramentas/carrossel.py atualizar` → commit + push de `carrossel/p` → `python3 ferramentas/carrossel.py versao`
  → commit + push de `carrossel/v.json`.
- Listas (quem aparece em cada carrossel): `python3 ferramentas/carrossel_listas.py` refaz `carrossel/base.json` a partir de
  `carrossel/acordes.json` (acordes de cada perfume), `carrossel/paginas.json` (páginas "Parecidos com…") e da listagem da loja.
  Perfume novo entra pelo passo 11 da rotina diária do dossiê (`carrossel_exportar.py` acrescenta em acordes.json).
- **Desde 12/11/2026 o perfume novo entra sozinho**: a tarefa "Carrossel: preços atualizados" (5x por dia) roda antes
  `python3 ferramentas/carrossel_novos.py` (perfume no ar sem acordes ganha acordes lidos da própria página pública:
  "Estilo olfativo" + "Acordes principais") e `python3 ferramentas/carrossel_listas.py` (refaz quem aparece em cada carrossel).
  Não precisa de chave nem do computador. A listagem da loja é lida uma vez e guardada por 20 min para os três passos.

## Verificador diário de todos os sistemas (12/11/2026)

`python3 ferramentas/verificador.py [--corrigir]` confere, para cada perfume no ar (base pública do robô dos filtros):
família olfativa, dia/noite, estação, ocasião, carrossel, decant na promoção (categoria escondida 24495076, menos a lista FORA)
e decant na página Decants. Com `--corrigir` e o token da API em `~/.lb/li_token`, acrescenta as categorias que faltam
(nunca tira). Roda na tarefa diária do dossiê; o resultado vai no resumo para o Nevander.

## Relógios (13/11/2026)

- `src/1799004.html` → `dist/rel.css` + `dist/rel.js` (grupo `rel` em `ordem.json`), carregados pelo `src/1799005.html`
  (dentro do rod.js) **só** na página de um relógio e nas listagens (categoria, marca, busca) com cartão de relógio,
  do mesmo commit do rod.js. O `build.py` põe a "versão" dos arquivos rel dentro do rod.js (`__REL_V__`): toda mudança
  em rel.* muda o rod.js, então basta seguir o passo a passo acima (commit, carregador, colar o rodapé 1718611).
- Página do relógio: "O relógio em números" (ficha em movimento), resumo perto do preço, simulador de pulso com
  "pulseira ajustada" pelo WhatsApp, "Na sua compra", "Encomendar pelo WhatsApp" quando esgota, guia de cuidados e de água,
  termos da ficha explicados ao tocar, "Com a mesma proposta" + comparador e dados estruturados (additionalProperty).
- Listagens: etiqueta "Automático · 40 mm · 100 m" nos cartões e filtros de relógio (movimento, tamanho, água, vidro,
  funções, cor, pulseira, caixa) no mesmo filtro do site.
- Tudo sai da "Ficha técnica" da descrição. A base dos outros relógios é `carrossel/relogios.json`
  (`python3 ferramentas/relogios.py`, lê as páginas públicas), refeita 5x por dia pela tarefa "Carrossel: preços atualizados";
  o site acha o arquivo pelo `carrossel/v.json` (o `carrossel.py versao` aponta para o commit mais novo de carrossel/p ou relogios.json).
- Padrão do anúncio novo: título com o diâmetro ("... Automático 40mm Mostrador Azul REF") e ficha com Movimento, Caixa
  (diâmetro e espessura), Resistência à água, Vidro, Fundo, Funções, Pulseira (+ Reserva de marcha e Frequência nos mecânicos;
  Peso, ponta a ponta e Luminescência quando houver). O verificador diário (item 8) confere e põe o diâmetro no título sozinho.

### Dossiê na descrição dos relógios (13/11/2026)

- `ferramentas/relogios_dossie.py` grava 4 seções na descrição de cada relógio, pela API: "O dossiê do {modelo}",
  "Feito para quê e onde usar", "A {marca} em N momentos" e "Você sabia?". Os dados, com fontes, ficam em
  `ferramentas/relogios_dossie_marcas.json` e `ferramentas/relogios_dossie_modelos.json`.
- O `dist/rel.js` desenha a linha do tempo, o mapa de ocasiões e os cartões; sem JavaScript continua texto normal.
- Relógio novo: o verificador (item 9) grava sozinho as seções que saem da ficha; família ou marca nova segue
  `ferramentas/relogios_dossie.md` (pesquisa com fonte), feito pela tarefa diária.
