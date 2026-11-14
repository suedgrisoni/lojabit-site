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

### Pulso, quiz, tamanho real, páginas-guia, página da marca, guia do proprietário e posts (13/11/2026)

Tudo abaixo se atualiza sozinho quando entra um relógio novo (sai da ficha técnica, do preço e do dossiê):

- **Meu pulso em todo o site** (`rel.js`): a medida fica guardada no aparelho (`localStorage lbPulso`); cada cartão de relógio ganha
  o selo "Ideal / Discreto / Marcante / Grande no seu pulso", os filtros ganham o grupo "No meu pulso" e a página do relógio,
  um chip. A barra "Encontre o seu" das listagens abre o quiz, guarda o pulso e liga as páginas-guia.
- **Som do tique-taque** (`rel.js`): toque no cartão das batidas; o som é sintetizado na hora (sem arquivo de áudio), na
  frequência real do movimento.
- **Extras sob demanda** (`src/1799006.html` → `dist/rex.css` + `dist/rex.js`, grupo `rex`): o `rel.js` só baixa esses dois arquivos
  quando o cliente pede. Têm o **quiz** de 4 perguntas (`#quiz` em qualquer listagem de relógio), o **tamanho real na tela**
  (ajuste único com um cartão em pé; `localStorage lbPxMm`) e o **guia do proprietário** (`?guia=1` na página do relógio: ficha,
  cuidados, usos e história, para imprimir ou salvar em PDF).
- **Páginas-guia** (subcategorias de Relógios): regras em `ferramentas/relogios.py` (`GUIAS`), textos em
  `ferramentas/relogios_guias.json`, criação e sincronização em `ferramentas/relogios_guias.py`. O verificador (item 10) põe e
  tira cada relógio das guias todo dia. Guia nova: acrescentar a regra em `GUIAS` (id 0), o texto no JSON, rodar
  `relogios_guias.py --criar`, pôr o id devolvido em `GUIAS` e acertar o endereço no painel (a API troca letra acentuada por "-").
- **Página da marca**: `relogios_dossie.py --marcas` (e o verificador, item 11) põe no fim do texto da categoria da marca
  "A história da {marca} em N momentos" e "Você sabia?", com todos os momentos de `relogios_dossie_marcas.json`.
  Desde 14/11/2026 a lista "Na @LOJABIT você encontra N relógios {marca} originais" também é viva: um item por relógio À VENDA
  (link, ficha em uma linha, uso ideal e uma curiosidade), tirada do `carrossel/relogios.json`. Relógio que esgota sai; relógio
  novo entra. O parágrafo de abertura e o parágrafo final da categoria continuam escritos à mão.
  **Atenção (visto em 14/11/2026):** o texto de categoria gravado pela API fica certo no cadastro, mas a loja pode levar horas
  para mostrar (6 das 9 páginas de marca ainda mostravam o texto antigo 8 horas depois). Salvar a categoria pelo formulário do
  painel (`/painel/catalogo/categoria/ID/editar`, enviando o próprio formulário da página, com o campo `parent` conferido)
  atualiza na hora. O verificador diário só usa a API: a mudança dele aparece sozinha, com esse atraso.
- **Menu Relógios em dois grupos** (`src/1799007.html`, só CSS + `src/1717276.html` no painel Departamentos): "Por marca" e
  "Por tipo e ocasião". Página-guia é a subcategoria cujo endereço tem "relogio"; marca é o resto. Está em PRÉVIA
  (`?lbmenu=1` liga, `?lbmenu=0` desliga); para publicar, `PUBLICADO = true` no `src/1799007.html`. O painel Departamentos
  já conta certo para todos: "9 marcas e 7 guias".
- **`carrossel/relogios.json`** leva, por relógio, `ct` (tipos), `oi`/`oc` (ocasiões ideais e em que também vai bem) e, no topo,
  `g` (páginas-guia com 3 relógios ou mais à venda). O quiz e a barra leem daí.
- **Posts "Você sabia?"** (`ferramentas/relogios_posts.py`): um relógio por post, com legenda para Instagram Reels, TikTok,
  Threads, YouTube Shorts, WhatsApp Stories, BiliBili, X e Kwai. Segue as regras dos posts (produto sem o nome da marca, criador,
  gancho de venda, limites e hashtags de cada rede, conferidos por código). `--novos ARQ.md` gera só os relógios que ainda não
  tiveram post (`relogios_posts_feitos.json`). Os números de hashtags e limites ficam na tabela `REDES`, com a data da pesquisa;
  depois de 60 dias o programa avisa para pesquisar de novo.

### Vídeo de cada relógio (14/11/2026)

Pedido do Nevander: um vídeo em cada relógio, que gere desejo. Piloto aprovado em 14/11/2026 ("Ficou bom, pode fazer nos outros também").

- **O que é**: vídeo em pé (720x1280, 30 qps, 13 a 16 s, cerca de 2 MB) feito só com as fotos reais do relógio e os dados
  da ficha. Cenas: a foto principal com o nome; um close (mostrador, cronógrafo, bisel ou zoom da foto principal) com o que
  ele tem de mais especial; outro ângulo (perfil ou três-quartos) com a segunda coisa especial ou o movimento; o fundo
  transparente com o movimento, quando existe a foto; e o convite final (original, 10% off no Pix, 6x sem juros). Som:
  tique-taque sintetizado no ritmo do movimento (6 ou 8 batidas por segundo nos mecânicos; 1 por segundo no quartzo e no
  solar). Os textos não citam a marca (o vídeo também serve para as redes).
- **Como gera**: `ferramentas/relogios_video.py` (lê a página do relógio, escolhe as fotos pelo nome do arquivo, leva o
  fundo da foto ao branco puro, enquadra pelo recorte do relógio, escreve os textos pela ficha e pelo dossiê, filma
  `ferramentas/relogios_video/modelo.html` com Playwright e junta o som com ffmpeg). As fontes ficam em
  `ferramentas/relogios_video/fontes/` (Cormorant Garamond e Jost, licença SIL OFL), para não depender da internet.
  - `--plano [IDs]` mostra fotos e textos; `--quadros ID` monta uma folha com um quadro de cada cena; `--gerar [IDs]`
    filma; `--novos` filma só o relógio sem vídeo ou cujo vídeo precisa ser refeito (pela impressão digital: nomes das
    fotos da página, campos da ficha usados nos textos, curiosidade do dossiê, `VERSAO` e o modelo); `--publicar` envia.
  - Mudou o desenho do vídeo? Aumente `VERSAO` no topo do arquivo: todos são refeitos na próxima rodada.
  - A curiosidade que fala do fundo da caixa só entra quando a página tem a foto do fundo (senão o texto não bate com a
    imagem); nesse caso vai a próxima curiosidade do dossiê.
- **Onde ficam**: no ramo `videos` do repositório (não pesa no `main` nem nos clones das tarefas). Cada publicação é um
  commit só com os vídeos daquele lote (até 8), para cada pacote ficar pequeno na jsDelivr; os anteriores continuam no
  histórico do ramo. `carrossel/videos.json` guarda, por relógio, o commit (`s`), a impressão digital (`h`) e a duração.
  `ferramentas/relogios.py` copia o commit para `carrossel/relogios.json` (`vd`) e a duração (`vt`).
- **No site** (`rel.js`, função `video`): botão "Ver em vídeo" no canto da foto do produto (no celular embaixo à esquerda,
  ao lado do "Toque para ampliar"; no computador em cima à esquerda, longe da dica de zoom e do contador). O vídeo
  só baixa quando o cliente toca: abre por cima da página, com som, e fecha no X, fora do vídeo ou no Esc.
  Endereço: `https://cdn.jsdelivr.net/gh/suedgrisoni/lojabit-site@<vd>/v/<id>.mp4` (capa: `.jpg`).
- **Relógio novo**: a tarefa "Carrossel: preços atualizados" roda `--novos` e `--publicar` e o vídeo entra sozinho.
