# Dossiê dos relógios: como escrever para um relógio novo

Pedido do Nevander (13/11/2026): cada relógio tem na descrição um dossiê completo e útil para quem está escolhendo:

- história e curiosidades da marca;
- história e curiosidades do modelo;
- para que ele foi feito e onde usar.

O foco é trazer valor de verdade a quem está lendo.

## O que sai sozinho e o que precisa de pesquisa

| Seção na descrição | De onde vem | Relógio novo |
|---|---|---|
| **O dossiê do {modelo}** (antes de "Destaques") | família em `relogios_dossie_modelos.json` | **precisa de pesquisa**: escrever a família |
| **Feito para quê e onde usar** (depois da Ficha técnica) | ficha técnica (`carrossel/relogios.json`) + tipo do relógio | sozinho |
| **A {marca} em N momentos** (linha do tempo) | `relogios_dossie_marcas.json` | sozinho, se a marca já existe |
| **Você sabia?** (5 ou 6 curiosidades) | modelo + marca | sozinho, com as curiosidades da marca |

O verificador diário (item 9, `ferramentas/verificador.py --corrigir`) faz duas coisas:

- grava as seções automáticas no relógio que ainda não tem;
- avisa quando falta a família do modelo ou a marca.

## Relógio de família nova

1. Pesquise em fontes confiáveis:
   - Wikipédia;
   - site e notícias oficiais da marca;
   - revistas de relojoaria (Hodinkee, Fratello, Monochrome, Worn & Wound, aBlogtoWatch, WatchTime, Europa Star).

   Anote cada fonte. Não use fato sem fonte, nem "dizem que".
2. Acrescente em `relogios_dossie_modelos.json`, dentro de `familias`, uma entrada com:
   - `titulo`: "O dossiê do {modelo}";
   - `cats`: para que o tipo de relógio foi feito, um ou dois de `mergulho`, `campo`, `cronografo`, `gmt`, `social`, `integrado` ou `dia_a_dia`; o primeiro é o principal;
   - `p`: 2 parágrafos. O primeiro conta de onde o modelo veio (ano, contexto, o significado do nome). O segundo fala da tecnologia ou do que ele tem de especial (calibre, material, recorde);
   - `vs`: 3 curiosidades no formato `["Título curto", "Uma ou duas frases."]`;
   - `fontes`: lista de URLs.
3. Em `produtos`, ligue o ID do produto à família: `"ID": {"f": "familia"}`.
   - Opcional: `"vs"` com 1 ou 2 curiosidades só daquela versão (cor, apelido do bisel, pulseira).
4. Rode:

   ```
   python3 ferramentas/relogios_dossie.py --mostrar ID
   python3 ferramentas/relogios_dossie.py --gravar ID
   ```

   Rodar de novo é seguro: as seções antigas são trocadas pelas novas.

## Marca nova

Em `relogios_dossie_marcas.json`, acrescente:

- `intro`: 2 versões de 1 frase sobre a origem;
- `linha`: de 6 a 11 momentos `["ano", "fato"]`, com o primeiro sendo a fundação;
- `vs`: 3 a 5 curiosidades;
- `fontes`.

Relógios da mesma marca mostram 7 momentos em rodízio, para os textos não ficarem iguais.

## Regras do texto

- Português do Brasil, frases curtas, tom positivo.
- Nunca "réplica", "contratipo", "inspirado em" ou "homenagem a" outra marca. Não cite outras marcas de relógio como comparação.
- Só fatos com fonte. Números como no original (anos, metros, horas, rubis, alternâncias).
- Sem promessa que a loja não faz (garantia, prazos).
- O texto deve ajudar a escolher:
  - para que serve;
  - o que tem de especial;
  - o que a pessoa vai sentir ou ganhar usando.
