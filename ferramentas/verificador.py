#!/usr/bin/env python3
"""Verificador diário: todo perfume no ar está em TODOS os sistemas do site? (12/11/2026, pedido do Nevander:
"todos os sistemas do site se atualizarem sozinhos sempre que adiciono um novo perfume").

Lê só dados públicos (não precisa de chave): a base dos filtros do robô "Vitrine LojaBit" (todos os produtos dos departamentos,
com categorias, tamanhos e as etiquetas dia/noite, estação e ocasião lidas da página) e os carrosséis do repositório.

Confere, para cada perfume (árabe, nicho, importado):
  1. família olfativa  — está em pelo menos uma página de estilo (Doces, Amadeirados...)            [dossiê liga]
  2. dia ou noite      — está em Para o Dia a Dia, Para a Noite ou Versáteis                         [corrige com chave]
  3. estação           — o robô achou a estação no texto ou está em Para o Calor/Para o Frio         [corrige com chave]
  4. ocasião           — o robô achou a ocasião no texto (trabalho, encontros...)                    [só avisa]
  5. carrossel         — tem "Parecidos com"/"Mesma proposta" (ou é estilo raro e usa o carrossel antigo) [tarefa dos carrosséis]
  6. promoção decants  — produto com decant (3/5/10 ml) à venda está na categoria escondida 24495076 [corrige com chave]
  7. listagem decants  — perfume com decant à venda está em Decants (/decants) e na subcategoria do tipo [corrige com chave]
  9. dossiê do relógio — seções "Feito para quê e onde usar", "A <marca> em N momentos" e "Você sabia?" (saem da ficha,
                         corrige com chave) e "O dossiê do <modelo>" (precisa de pesquisa: só avisa se faltar a família)
  8. relógio no padrão — ficha técnica com os campos que o site usa (movimento, caixa com diâmetro e espessura, água,
                         vidro, fundo, funções, pulseira; reserva e frequência nos mecânicos) e o diâmetro no título
                         (ex.: "... Automático 40mm Mostrador Azul ...")                               [título: corrige com chave]
 10. páginas-guia      — cada relógio está exatamente nas páginas-guia que a regra manda (Relógios de Mergulho, Sociais,
                         Automáticos, Primeiro Automático, Cronógrafo, Para Presentear, Até R$ 2.000; regras em
                         ferramentas/relogios.py, GUIAS)                                               [corrige com chave]
 11. página da marca   — a categoria de cada marca de relógio tem a história completa ("A história da <marca> em N
                         momentos" + "Você sabia?", de relogios_dossie_marcas.json)                    [corrige com chave]
                         Marca sem categoria em Relógios, sem dossiê ou sem "criador" (para os posts): só avisa.

Com --corrigir e o token da API em ~/.lb/li_token, corrige 2, 3, 6 e 7 (SÓ ACRESCENTA categoria, nunca tira; a única exceção
são as páginas-guia de relógio do item 10, que seguem a regra nos dois sentidos: preço passou de R$ 2.000, sai da guia):
  - 6: todo produto com decant à venda entra na promoção, menos os da lista FORA (frasco daria prejuízo com 15% + Pix;
       a mesma lista do código src/1799002.html, que mostra o aviso na página do perfume).
  - 7: Decants + "Decants de Perfumes Árabes/de Nicho/Importados" (os da lista FORA só são avisados).
  - 2: pela etiqueta dia/noite do robô (d -> Dia a Dia, n -> Noite, v -> Versáteis).
  - 3: sem estação no texto nem página de calor/frio: pela linha "Melhores estações" da página, com a regra do dossiê
       (verão entre as melhores -> Para o Calor; inverno -> Para o Frio).
  - 8: põe o diâmetro da ficha no título do relógio (único caso em que mexe no nome; confere antes que o nome não mudou).
       Campo que falta na ficha só é avisado (o dado tem de vir do fabricante).
Uso: python3 ferramentas/verificador.py [--corrigir] [--json saida.json]
Saída 0 = tudo certo (ou corrigido); 1 = sobrou aviso (vai no resumo para o Nevander).
"""
import base64, gzip, html, json, os, re, subprocess, sys, time, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROBO = 'https://script.google.com/macros/s/AKfycbz38mCpIBq9a1tlmwBAZG3LdmhTaKQRKDDAAbz5DCAU3Jw-7HpZZJkssxODPcK8zUBi/exec?arquivo=filtros'
LOJA = 'https://www.lojabit.com'
API = 'https://api.awsli.com.br/v1'
PROMO, DECANTS = 24495076, 22896349
DEC_ARABES, DEC_NICHO, DEC_IMPORTADOS = 24474614, 24474615, 24474616  # subcategorias de Decants
FORA = {35021295, 19254482, 351474067, 334121425, 8623615, 15746440, 403336099}  # igual ao EXCL do src/1799002.html
DIA, NOITE, VERSATIL, CALOR, FRIO = 24474625, 24474626, 24474627, 24484495, 24484496
# páginas de estilo (subcategorias de "Encontre seu Perfume" que são família); categoria nova de família: o dossiê avisa
FAMILIAS = {24484487, 24474620, 24484485, 24484492, 24484481, 24484486, 24484480, 24474619, 24484490, 24474621, 24484491,
            24474618, 24484482, 24474622, 24474623, 24484483, 24484493, 24484489}
CAMPOS = ['id', 'u', 'nome', 'foto', 'tipo', 'marca', 'cats', 'vars', 'pv', 'po', 'ap', 'fam', 'pq', 'dn', 'es', 'oc', 'pj', 'co',
          'rank', 'ano', 'nota', 'notas', 'parecido', 'votos']


def baixa(url, tent=3):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; lojabit-verificador/1.0)'})
    for t in range(tent):
        try:
            return urllib.request.urlopen(req, timeout=90).read().decode('utf-8', 'ignore')
        except Exception:
            time.sleep(5 * (t + 1))
    return ''


def base_robo():
    t = baixa(ROBO).strip()
    d = json.loads(gzip.decompress(base64.b64decode(t)))
    cats = d['cats']
    out = []
    for x in d['p']:
        p = dict(zip(CAMPOS, x))
        p['cs'] = {cats[i] for i in p['cats']}
        out.append(p)
    return out, d.get('t', 0)


def tem_decant(p):
    # [ml, preço, antigo, disponível, variação, produto do tamanho, esgotado]
    return any(v[0] in (3, 5, 10) and v[3] == 1 and not (len(v) > 6 and v[6]) for v in p['vars'])


def estacoes_da_pagina(url):
    """Mesma regra do dossiê (plano.py): verão entre as melhores estações -> Para o Calor; inverno -> Para o Frio."""
    h = baixa(LOJA + url, 2)
    m = re.search(r'<strong>\s*Melhores esta[çc][õo]es\s*:?\s*</strong>\s*:?([^<]*)', h, re.I)
    if not m:
        return set()
    t = html.unescape(m.group(1)).lower()
    s = set()
    if re.search(r'ver[ãa]o', t):
        s.add(CALOR)
    if re.search(r'inverno', t):
        s.add(FRIO)
    return s


class Api:
    def __init__(self):
        self.tok = open(os.path.expanduser('~/.lb/li_token')).read().strip()
        self.ult = 0.0

    def req(self, metodo, caminho, corpo=None):
        espera = 1.5 - (time.time() - self.ult)
        if espera > 0:
            time.sleep(espera)
        self.ult = time.time()
        cmd = ['curl', '-sS', '-m', '60', '-X', metodo, '-w', '\n%{http_code}', '-H', 'Authorization: Basic ' + self.tok,
               '-H', 'Content-Type: application/json', API + caminho]
        if corpo is not None:
            cmd += ['--data-binary', '@-']
        for t in range(4):
            r = subprocess.run(cmd, input=json.dumps(corpo) if corpo is not None else None, capture_output=True, text=True)
            txt, _, code = r.stdout.rpartition('\n')
            if code == '429':
                time.sleep(20 * (t + 1))
                continue
            return int(code or 0), txt
        return 429, ''

    def acrescenta(self, pid, novas):
        """Soma categorias às que o produto já tem (nunca tira). Devolve o texto do resultado."""
        st, t = self.req('GET', f'/produto/{pid}')
        if st != 200:
            return f'ERRO leitura {st}'
        atuais = [c.rstrip('/').split('/')[-1] for c in json.loads(t).get('categorias') or []]
        falta = [c for c in novas if str(c) not in atuais]
        if not falta:
            return 'ok já tinha'
        st, t = self.req('PUT', f'/produto/{pid}', {'categorias': [f'/api/v1/categoria/{x}' for x in atuais] +
                                                     [f'/api/v1/categoria/{x}' for x in falta]})
        return f'ok +{falta}' if st == 200 else f'ERRO {st} {t[:120]}'

    def renomeia(self, pid, antigo, novo):
        """Troca o nome só se ainda for o esperado; confere depois."""
        st, t = self.req('GET', f'/produto/{pid}')
        if st != 200:
            return f'ERRO leitura {st}'
        if json.loads(t).get('nome') != antigo:
            return 'pulado (o nome mudou no painel)'
        st, t = self.req('PUT', f'/produto/{pid}', {'nome': novo})
        st2, t2 = self.req('GET', f'/produto/{pid}')
        return 'ok' if st2 == 200 and json.loads(t2).get('nome') == novo else f'ERRO {st} {t[:120]}'


def main():
    corrigir = '--corrigir' in sys.argv
    saida = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
    api = None
    if corrigir:
        if os.path.exists(os.path.expanduser('~/.lb/li_token')):
            api = Api()
        else:
            print('sem o token da API (~/.lb/li_token): só confiro, não corrijo')
    P, t = base_robo()
    if len(P) < 200:
        sys.exit(f'a base do robô veio com {len(P)} produtos — nada foi conferido')
    perf = [p for p in P if p['tipo'] in ('a', 'i', 'n')]
    tem_carr = {f[:-5] for f in os.listdir(os.path.join(RAIZ, 'carrossel', 'p'))}
    ac = json.load(open(os.path.join(RAIZ, 'carrossel', 'acordes.json'), encoding='utf-8'))
    av = {k: [] for k in ('familia', 'dia_noite', 'estacao', 'ocasiao', 'carrossel', 'promo', 'listagem_decants')}
    feito = []
    for p in perf:
        pid, nome = p['id'], p['nome']
        if not p['cs'] & FAMILIAS:
            av['familia'].append(nome)
        if not p['cs'] & {DIA, NOITE, VERSATIL}:
            cat = {'d': DIA, 'n': NOITE, 'v': VERSATIL}.get(p['dn'])
            if api and cat:
                r = api.acrescenta(pid, [cat]); feito.append(f'{nome}: dia/noite {r}')
                if not r.startswith('ok'): av['dia_noite'].append(nome)
            else:
                av['dia_noite'].append(nome)
        if not p['es'] and not p['cs'] & {CALOR, FRIO}:
            # o filtro "Estação" usa o texto (robô) e, se faltar, as páginas Para o Calor/Para o Frio (código 1718611)
            cats = sorted(estacoes_da_pagina(p['u']))
            if api and cats:
                r = api.acrescenta(pid, cats); feito.append(f'{nome}: estação {r}')
                if not r.startswith('ok'): av['estacao'].append(nome)
            else:
                av['estacao'].append(nome)
        if not p['oc']:
            av['ocasiao'].append(nome)
        if str(pid) not in tem_carr and not (str(pid) in ac and ac[str(pid)].get('a')):
            av['carrossel'].append(nome)
    for p in P:
        if not tem_decant(p):
            continue
        if PROMO not in p['cs'] and p['id'] not in FORA:
            if api:
                r = api.acrescenta(p['id'], [PROMO]); feito.append(f"{p['nome']}: promoção {r}")
                if not r.startswith('ok'): av['promo'].append(p['nome'])
            else:
                av['promo'].append(p['nome'])
        if DECANTS not in p['cs'] and p['tipo'] in ('a', 'i', 'n'):
            # entra em Decants e na subcategoria do tipo; os da lista FORA (sem promoção) só são avisados
            sub = {'a': DEC_ARABES, 'n': DEC_NICHO, 'i': DEC_IMPORTADOS}[p['tipo']]
            if api and p['id'] not in FORA:
                r = api.acrescenta(p['id'], [DECANTS, sub]); feito.append(f"{p['nome']}: página Decants {r}")
                if not r.startswith('ok'): av['listagem_decants'].append(p['nome'])
            else:
                av['listagem_decants'].append(p['nome'])
    # 8. relógios no padrão: lê a página de cada relógio (ficha técnica + título), como a base carrossel/relogios.json
    av['relogio'] = []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import relogios as RL
        try:
            import relogios_dossie as RD
        except Exception:
            RD = None
        RX = []
        for p in [p for p in P if p['tipo'] == 'r']:
            try:
                x = RL.le(p['id'], p['u'])
            except Exception:
                x = None
            time.sleep(1)
            if not x:
                continue
            RX.append(x)
            falta = list(x['falta'])
            if 'diâmetro no título' in falta:
                novo = RL.titulo_com_diametro(x['n'], x.get('diam'))
                if api and novo:
                    r = api.renomeia(p['id'], x['n'], novo); feito.append(f"{x['n']}: título -> \"{novo}\" ({r})")
                    if r == 'ok':
                        falta.remove('diâmetro no título')
            # 9. dossiê na descrição (ferramentas/relogios_dossie.py): onde usar, linha do tempo da marca e "Você sabia?" saem
            #    sozinhos da ficha; o dossiê do modelo precisa de uma família escrita com pesquisa em relogios_dossie_modelos.json
            sec = x.get('_sec', '')
            fam = RD.MODELOS['produtos'].get(str(p['id']), {}).get('f') if RD else None
            precisa = any(k not in sec for k in 'utv') or (fam and 'm' not in sec)
            if precisa and api and RD and x.get('mk') in RD.MARCAS:
                r = RD.grava(api.req, p['id'], x); feito.append(f"{x['n'][:60]}: dossiê na descrição ({r})")
                if r in ('ok', 'já estava igual'):
                    sec = 'utv' + ('m' if fam or 'm' in sec else '')
            if 'm' not in sec and not fam:
                falta.append('dossiê do modelo (história e curiosidades: escrever a família em ferramentas/relogios_dossie_modelos.json)')
            elif any(k not in sec for k in 'utv'):
                falta.append('seções do dossiê na descrição' + ('' if x.get('mk') in (RD.MARCAS if RD else {}) else ' (marca sem dossiê em relogios_dossie_marcas.json)'))
            if falta:
                av['relogio'].append(f"{x['n'][:60]}: {', '.join(falta)}")
        # 10. páginas-guia: cada relógio exatamente nas guias que a regra manda (põe e tira; só mexe nas categorias-guia)
        if api and RX:
            try:
                import relogios_guias as RG
                av['relogio'] += RG.sincroniza(api.req, RX, feito)
            except Exception as e:
                av['relogio'].append(f'não conferi as páginas-guia ({e})')
        # 11. página da marca com a história completa; marca nova sem categoria, sem dossiê ou sem "criador": aviso
        if RD and RX:
            marcas = sorted({x.get('mk') for x in RX if x.get('mk')})
            try:
                cats = RD.categorias_de_marca(api.req) if api else None
            except Exception:
                cats = None
            for mk in marcas:
                if mk not in RD.MARCAS:
                    av['relogio'].append(f'marca {mk}: sem dossiê (escrever em ferramentas/relogios_dossie_marcas.json)'); continue
                if not RD.MARCAS[mk].get('criador'):
                    av['relogio'].append(f'marca {mk}: sem "criador" no dossiê (os posts das redes precisam; ver ferramentas/relogios_dossie.md)')
                if cats is None:
                    continue
                if mk not in cats:
                    av['relogio'].append(f'marca {mk}: sem página (criar a subcategoria "{mk}" em Relógios; a história entra sozinha)'); continue
                r = RD.grava_marca(api.req, cats[mk], mk)
                if r == 'ok':
                    feito.append(f'página da marca {mk}: história completa atualizada')
                elif r != 'já estava igual':
                    av['relogio'].append(f'página da marca {mk}: {r}')
    except Exception as e:
        av['relogio'].append(f'não conferi os relógios ({e})')
    nomes = {'familia': 'sem família olfativa (dossiê)', 'dia_noite': 'sem dia/noite', 'estacao': 'sem estação',
             'ocasiao': 'sem ocasião no filtro (texto)', 'carrossel': 'sem carrossel', 'promo': 'decant fora da promoção',
             'listagem_decants': 'decant à venda fora da página Decants', 'relogio': 'relógio fora do padrão'}
    print(f'base do robô: {len(P)} produtos, {len(perf)} perfumes')
    for f in feito:
        print('  corrigido:', f)
    for k, l in av.items():
        print(f'{nomes[k]}: {len(l)}' + (' — ' + '; '.join(x[:60] for x in l[:12]) + (' ...' if len(l) > 12 else '') if l else ''))
    if saida:
        json.dump({'perfumes': len(perf), 'corrigido': feito, 'avisos': av}, open(saida, 'w'), ensure_ascii=False, indent=1)
    sys.exit(1 if any(av[k] for k in ('familia', 'dia_noite', 'estacao', 'carrossel', 'promo', 'relogio')) else 0)


if __name__ == '__main__':
    main()
