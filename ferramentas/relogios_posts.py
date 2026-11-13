#!/usr/bin/env python3
"""Série "Você sabia?" para as redes: um relógio por post, pronto para copiar e colar (13/11/2026, item 7 das sugestões).

Monta os textos a partir do dossiê (as mesmas fontes da descrição do site):
  - carrossel/relogios.json                    ficha de cada relógio
  - ferramentas/relogios_dossie_modelos.json   curiosidades de cada família/modelo
  - ferramentas/relogios_dossie_marcas.json    "criador": quem fundou a casa e as criações mais conhecidas (sem o nome da marca)

Regras dos posts do Nevander (valem para todo post de produto):
  - cita o nome do PRODUTO, nunca o nome da MARCA (nem em hashtag);
  - sempre diz quem criou e as criações mais conhecidas de quem criou;
  - curto, cheio de informação e curiosidade, pensando em busca de longo prazo, seguidores e credibilidade;
  - sempre com gancho de venda;
  - título para YouTube Shorts e BiliBili; BiliBili em português e sem emojis;
  - quantidade de hashtags recomendada para cada rede NA DATA DO POST e limite de caracteres de cada rede, conferidos por código.

A tabela REDES guarda os números e a data da pesquisa. Passados 60 dias, o programa avisa para pesquisar de novo (as redes mudam).

Uso:
  python3 ferramentas/relogios_posts.py --checar [--links]    confere todos (regras, limites, hashtags) e mostra um resumo;
                                                              com --links, abre o link de cada post e vê se o relógio aparece
  python3 ferramentas/relogios_posts.py --md [IDs]            imprime os posts em Markdown (todos ou só os IDs)
  python3 ferramentas/relogios_posts.py --pasta DIR           grava um arquivo .md por marca em DIR (nome do arquivo = marca)
  python3 ferramentas/relogios_posts.py --novos ARQ.md        grava em ARQ.md só os relógios que ainda não tiveram post
                                                              (lista em ferramentas/relogios_posts_feitos.json) e marca como feitos
Relógio novo: entra sozinho, desde que a família esteja no dossiê (guia: ferramentas/relogios_dossie.md).
"""
import datetime, json, os, re, sys, urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import relogios_dossie as RD

SITE = 'https://www.lojabit.com'
FEITOS = os.path.join(AQUI, 'relogios_posts_feitos.json')

# Pesquisa de 13/11/2026 (fontes no fim do arquivo .md de cada marca). max = limite de caracteres do texto; tags = hashtags.
PESQUISA = '2026-11-13'
REDES = [
    # chave, nome, limite do texto, limite do título, hashtags, observação
    ('instagram', 'Instagram Reels', 2200, 0, 5, 'O Instagram aceita no máximo 5 hashtags por post desde dezembro de 2025; o recomendado é de 3 a 5.'),
    ('tiktok', 'TikTok', 2200, 0, 4, 'Recomendado: de 3 a 5 hashtags.'),
    ('threads', 'Threads', 500, 0, 1, 'O Threads usa 1 tema (tag) por post.'),
    ('shorts', 'YouTube Shorts', 5000, 100, 3, 'As 3 primeiras hashtags da descrição aparecem acima do título.'),
    ('whatsapp', 'WhatsApp Stories', 700, 0, 0, 'Status de texto: até 700 caracteres. Hashtag não tem função no WhatsApp.'),
    ('bilibili', 'BiliBili', 250, 80, 5, 'Título de até 80 caracteres; texto sem emojis; as tags vão no campo de tags (até 10).'),
    ('x', 'X', 280, 0, 2, 'Até 280 caracteres (todo link conta 23). A ajuda do X recomenda no máximo 2 hashtags.'),
    ('kwai', 'Kwai', 300, 0, 4, 'O Kwai não publica limite oficial: legenda curta e de 3 a 5 hashtags, como no TikTok.'),
]
FONTES = [
    'https://metricool.com/how-many-hashtags-to-use/',
    'https://hashtagtools.io/blog/how-many-hashtags-per-platform-optimal-count-2026',
    'https://socialk.it/pt/tools/social-media-character-limits',
    'https://www.socialmediatoday.com/news/instagram-implements-new-limits-on-hashtag-use/808309/',
]
GANCHO = 'Original, com caixa, manual e certificado. 10% off no Pix e até 6x sem juros'
TN = {'auto': 'Automático', 'manual': 'Corda manual', 'quartzo': 'Quartzo', 'solar': 'Solar'}
ORIG = {'japones': 'japonês', 'suico': 'suíço'}
VIDRO = {'safira': 'vidro de safira', 'hardlex': 'vidro Hardlex', 'mineral': 'vidro mineral', 'acrilico': 'vidro acrílico'}
TAG_TIPO = {'auto': 'relogioautomatico', 'manual': 'relogiomecanico', 'quartzo': 'relogioquartzo', 'solar': 'relogiosolar'}
TAG_CAT = {'mergulho': 'relogiodemergulho', 'cronografo': 'cronografo', 'gmt': 'relogiogmt', 'social': 'relogiosocial', 'campo': 'relogiodecampo',
           'integrado': 'relogiodeaco', 'dia_a_dia': 'relogiododiaadia'}
MARCAS = sorted([k for k in RD.MARCAS if not k.startswith('_')], key=len, reverse=True)
RE_MARCA = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(m) for m in MARCAS) + r')(?![\w-])', re.I)


def sem_marca(t):
    """Tira o nome da marca de uma frase do dossiê, sem mudar o fato. Se ainda sobrar marca, devolve '' (a frase não entra)."""
    t = ' ' + t
    for m in MARCAS:
        M = re.escape(m)
        t = re.sub(r'\b(d)os %s 5\b' % M, r'\1a linha 5', t)
        t = re.sub(r'\b([Oo])s %s 5\b' % M, lambda g: ('A' if g.group(1) == 'O' else 'a') + ' linha 5', t)
        t = re.sub(r'\b([Dd])o %s 5(?! Sports)\b' % M, r'\1a linha 5', t)
        t = re.sub(r'\b([Oo]) %s 5(?! Sports)\b' % M, lambda g: ('A' if g.group(1) == 'O' else 'a') + ' linha 5', t)
        t = re.sub(r'\bQ %s\b' % M, 'Q', t)
        t = re.sub(r'\b(laranja|azul|verde) %s\b' % M, r'\1 da marca', t)
        t = re.sub(r'\b([AaÀà]|[DdNn]a|[Pp]ela|própria) %s\b(?! [A-Z0-9])' % M, r'\1 marca', t)
        t = re.sub(r'(?<![\w-])%s (?=[A-Z0-9])' % M, '', t)  # "Tissot PRX" -> "PRX"
        t = re.sub(r'\b([Dd])a marca\b(?=.*\bda marca\b)', r'\1a marca', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return '' if RE_MARCA.search(t) else t


def nome_post(x, ref=True):
    """Nome do produto sem a marca, sem a medida e sem a cor do mostrador."""
    n = re.sub(r'^Relógio (Masculino|Feminino|Unissex)\s+', '', x['n'])
    n = re.sub(r'(?<![\w-])%s(?![\w-])\s*' % re.escape(x['mk']), '', n)
    n = re.sub(r'\s*\b\d{2}(,\d)?\s?mm\b', '', n)
    n = re.sub(r'\s*Mostrador [A-ZÁ-Úa-zá-ú]+(-[A-Za-zá-ú]+)?( Claro| Escuro)?', '', n)
    n = re.sub(r'\s+-\s+', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    m = re.match(r'^5 (Automático.*)$', n)
    if m:  # "Seiko 5 Automático SNKE51K1" -> o nome da linha é só "5"
        n = m.group(1)
    if not ref:
        n2 = re.sub(r'(\s+[A-Z0-9][A-Z0-9./-]*\d[A-Z0-9./-]*)+$', '', n).strip()  # tira a referência do fim
        if len(n2.split()) >= 2 or m:  # nome de uma palavra só ("Automático") fica com a referência
            n = n2
    return n + (' da linha 5' if m else '')


def referencia(x):
    """Referência do relógio (o código no fim do nome), para o link de busca do site: o endereço do produto tem a marca."""
    n = re.sub(r'(?<![\w-])%s(?![\w-])' % re.escape(x['mk']), '', x['n'])
    T = [w for w in n.split() if len(w) >= 5 and re.search(r'\d', w) and re.search(r'[A-Z]|\d\.\d', w) and not re.search(r'mm$|^\d+M$', w)]
    return T[0] if T else ''


def link(x):
    r = referencia(x)
    return SITE + ('/buscar?q=' + urllib.parse.quote(r, safe='') if r else '/relogios-originais')


def tem_marca(t):
    """A marca aparece no texto? Confere palavra por palavra (pega também endereço com a marca; não confunde 'vendido' com Mido)."""
    P = set(re.split(r'[^a-zà-ú0-9]+', t.lower()))
    for m in MARCAS:
        partes = re.split(r'[^a-zà-ú0-9]+', m.lower())
        if all(q in P for q in partes) and (len(partes) == 1 or m.lower() in t.lower()):
            return m
    return ''


def artigo(n):
    return 'a' if re.match(r'^(linha|Esquadrilha)', n, re.I) else 'o'


def dados(pid):
    pid = str(pid)
    x = RD.BASE.get(pid)
    if not x:
        return None, 'fora da base (carrossel/relogios.json)'
    pr = RD.MODELOS['produtos'].get(pid, {})
    fam = pr.get('f')
    F = RD.MODELOS['familias'].get(fam) if fam else None
    mk = RD.MARCAS.get(x.get('mk'))
    if not F:
        return None, 'sem família no dossiê (ferramentas/relogios_dossie_modelos.json)'
    if not mk or not mk.get('criador'):
        return None, 'marca sem "criador" no dossiê (ferramentas/relogios_dossie_marcas.json)'
    cats = F.get('cats') or RD.infere_cats(x)
    V = []
    for a, t in list(pr.get('vs', [])) + list(F.get('vs', [])):
        a2, t2 = sem_marca(a), sem_marca(t)
        if a2 and t2 and a2 not in [v[0] for v in V]:
            V.append((a2.rstrip('.'), t2))
    if not V:
        return None, 'nenhuma curiosidade sem o nome da marca'
    oc = [(n, k, r) for n, k, r in RD.ocasioes_chaves(x, cats, fam) if n == 'ideal']
    uso = ''
    if oc:
        rot = RD.ROTULO[oc[0][1]][0]
        por = sem_marca(oc[0][2])
        uso = rot + ('.' if not por else ('. ' + por) if ':' in por else (': ' + por[0].lower() + por[1:]))
    ficha = [TN.get(x.get('tipo'), '') + ((' ' + ORIG[x['orig']]) if x.get('orig') in ORIG and x.get('tipo') in ('auto', 'manual') else '')]
    if x.get('diam'):
        ficha.append(RD.br(x['diam']) + ' mm')
    if x.get('agua'):
        ficha.append('%d m de resistência à água' % x['agua'])
    if x.get('vidro') in VIDRO:
        ficha.append(VIDRO[x['vidro']])
    cr = mk['criador']
    tags = ['relogios', TAG_CAT.get(cats[0], 'relogiomasculino'), 'relogiomasculino', TAG_TIPO.get(x.get('tipo'), 'relogiooriginal'), 'relogiooriginal', 'vocesabia']
    tags = [t for i, t in enumerate(tags) if t not in tags[:i]]
    return {
        'id': pid, 'x': x, 'marca': x['mk'], 'nome': nome_post(x), 'curto': nome_post(x, ref=False), 'V': V, 'uso': uso,
        'ficha': ', '.join(f for f in ficha if f), 'cr': cr, 'cats': cats, 'tags': tags, 'url': link(x), 'pagina': SITE + x['u'],
        'tema': 'Relógios',
    }, ''


def de(frase):
    """'a casa…' -> 'da casa…' (contração com 'de')."""
    return 'd' + frase if re.match(r'^(a|o|as|os) ', frase) else 'de ' + frase


def obras(cr, n=3, com_de=False):
    o = [de(i) if com_de else i for i in cr['obras'][:n]]
    if len(o) == 1:
        return o[0]
    virg = any(',' in i for i in o)
    if len(o) == 2:
        return o[0] + (', e ' if virg else ' e ') + o[1]
    sep = '; ' if virg else ', '
    return sep.join(o[:-1]) + (';' if virg else '') + ' e ' + o[-1]


def abre(T, t):
    """'Título. Texto', sem repetir quando o texto já começa pelo título ('Sprite. Sprite é o apelido…')."""
    return t if t.lower().startswith(T.lower()) else '%s. %s' % (T, t)


def hashtags(d, n):
    return ' '.join('#' + t for t in d['tags'][:n])


def conta_x(t):
    """Tamanho no X: todo link conta 23."""
    return len(re.sub(r'https?://\S+', 'x' * 23, t))


def monta(d):
    """Devolve {rede: {'titulo': ..., 'texto': ..., 'tags': ...}}."""
    V, cr, nome, curto, url = d['V'], d['cr'], d['nome'], d['curto'], d['url']
    A = artigo(curto).upper()
    T1, t1 = V[0]
    por_tamanho = sorted(V, key=lambda v: len(v[0]) + len(v[1]))  # da curiosidade mais curta para a mais longa
    quem, casa = cr['quem'], cr['curto']
    ficha = d['ficha'][0].lower() + d['ficha'][1:]
    out = {}

    def cabe(modelo, lim, conta=len):
        """A primeira curiosidade (a principal; depois as mais curtas) cujo texto cabe no limite."""
        for T, t in [V[0]] + por_tamanho:
            txt = modelo(T, t)
            if conta(txt) <= lim:
                return (T, t), txt
        T, t = por_tamanho[0]  # nenhuma coube: corta a mais curta na última frase que cabe
        fr = re.split(r'(?<=[.!?])\s+', t)
        while len(fr) > 1 and conta(modelo(T, ' '.join(fr))) > lim:
            fr.pop()
        return (T, ' '.join(fr)), modelo(T, ' '.join(fr))

    # Instagram Reels
    p = ['Você sabia? ' + abre(T1, t1)]
    if len(V) > 1:
        p.append(abre(V[1][0], V[1][1]))
    p.append('Quem criou: %s. Da mesma casa: %s.' % (quem, obras(cr)))
    p.append('⌚ %s: %s.%s' % (nome, ficha, (' ' + d['uso']) if d['uso'] else ''))
    p.append('%s. Link na bio para garantir o seu.' % GANCHO)
    out['instagram'] = {'texto': '\n\n'.join(p) + '\n\n' + hashtags(d, 5)}
    # TikTok
    out['tiktok'] = {'texto': 'Você sabia? %s\n\n⌚ %s, %s, a mesma %s.\n\n%s. Link na bio.\n\n%s' % (
        abre(T1, t1), nome, de(casa), de(cr['obras'][0]), GANCHO, hashtags(d, 4))}
    # Threads (500 caracteres, 1 tema)
    _, th = cabe(lambda T, t: 'Você sabia? %s\n\n%s %s vem %s, a mesma %s.\n\nOriginal, com 10%% off no Pix, na @lojabit: %s\n\n#%s' % (
        t, A, curto, de(quem), obras(cr, 2, True), url, d['tema']), 500)
    if len(th) > 500:
        _, th = cabe(lambda T, t: 'Você sabia? %s\n\n%s %s vem %s, a mesma %s.\n\nOriginal, com 10%% off no Pix, na @lojabit: %s\n\n#%s' % (
            t, A, curto, de(casa), de(cr['obras'][0]), url, d['tema']), 500)
    out['threads'] = {'texto': th}
    # YouTube Shorts (título de até 100; 3 hashtags)
    tit = 'Você sabia? %s | %s' % (T1, curto)
    if len(tit) > 100:
        tit = 'Você sabia? %s' % T1
    out['shorts'] = {'titulo': tit[:100], 'texto': '%s\n\nQuem criou: %s. Da mesma casa: %s.\n\n%s original, com caixa, manual e certificado, com 10%% off no Pix e até 6x sem juros: %s\n\n%s' % (
        t1, quem, obras(cr), nome, url, '#relogios #relogiomasculino #vocesabia')}
    # WhatsApp Stories (700, sem hashtag)
    _, wa = cabe(lambda T, t: 'Você sabia? %s\n\n⌚ %s, %s.\n%s.\n\n%s.\nVeja aqui: %s' % (abre(T, t), nome, de(casa), d['ficha'], GANCHO, url), 700)
    out['whatsapp'] = {'texto': wa}
    # BiliBili (título de até 80, texto de até 250, sem emojis; tags no campo de tags)
    (Tb, tb), bl = cabe(lambda T, t: '%s Quem criou: %s, a mesma %s. Relógio original na LOJABIT, com caixa, manual e certificado: lojabit.com' % (t, casa, de(cr['obras'][0])), 250)
    if len(bl) > 250:
        (Tb, tb), bl = cabe(lambda T, t: '%s Quem criou: %s. Relógio original na LOJABIT, com caixa, manual e certificado: lojabit.com' % (t, casa), 250)
    bt = 'Você sabia? %s: %s' % (Tb, curto)
    if len(bt) > 80:
        bt = 'Você sabia? %s' % Tb
    out['bilibili'] = {'titulo': bt[:80], 'texto': bl, 'tags': 'relógios, relógio masculino, relógio original, curiosidades, você sabia'}
    # X (280, link = 23, 2 hashtags)
    _, xt = cabe(lambda T, t: 'Você sabia? %s ⌚ %s, %s. Original, 10%% off no Pix: %s %s' % (t, curto, de(casa), url, hashtags(d, 2)), 280, conta_x)
    out['x'] = {'texto': xt}
    # Kwai (legenda curta, 4 hashtags)
    _, kw = cabe(lambda T, t: 'Você sabia? %s ⌚ %s, %s. Original, com 10%% off no Pix: link no perfil.\n\n%s' % (t, curto, de(casa), hashtags(d, 4)), 300)
    out['kwai'] = {'texto': kw}
    return out


def confere(d, P):
    """Lista de problemas do post (vazia = tudo certo)."""
    E = []
    for chave, nome, lim, limt, ntags, _ in REDES:
        p = P[chave]
        txt = p['texto']
        tudo = ' '.join([p.get('titulo', ''), txt, p.get('tags', '')])
        if tem_marca(tudo):
            E.append('%s: cita a marca (%s)' % (nome, tem_marca(tudo)))
        n = conta_x(txt) if chave == 'x' else len(txt)
        if n > lim:
            E.append('%s: %d caracteres (limite %d)' % (nome, n, lim))
        if limt and (not p.get('titulo') or len(p['titulo']) > limt):
            E.append('%s: título com %d caracteres (limite %d)' % (nome, len(p.get('titulo', '')), limt))
        h = len(re.findall(r'(?<![\w/=])#[\wÀ-ú]', txt))
        if chave == 'bilibili':
            if re.search('[←-⯿\U0001F000-\U0001FAFF]', tudo):
                E.append('BiliBili: tem emoji')
            if h:
                E.append('BiliBili: hashtag no texto (as tags vão no campo de tags)')
        elif h != ntags:
            E.append('%s: %d hashtags (o certo são %d)' % (nome, h, ntags))
        if not re.search(r'10% off no Pix|caixa, manual e certificado', txt):
            E.append('%s: sem gancho de venda' % nome)
        if 'a casa ' not in txt and ' casa ' not in txt:
            E.append('%s: sem o criador' % nome)
        if re.search(r'[.!?]\s*$', txt.split('\n\n')[0]) is None and chave in ('x', 'kwai'):
            pass
    return E


def markdown(d, P):
    L = ['## %s' % d['nome'], '', 'Página do relógio: %s' % d['pagina'], '']
    if not d['x'].get('disp'):
        L += ['**Sem estoque hoje:** guarde este post para quando o relógio voltar.', '']
    for chave, nome, lim, limt, ntags, _ in REDES:
        p = P[chave]
        n = conta_x(p['texto']) if chave == 'x' else len(p['texto'])
        L.append('### %s' % nome)
        if p.get('titulo'):
            L += ['', 'Título (%d de %d caracteres):' % (len(p['titulo']), limt), '', '```', p['titulo'], '```']
        L += ['', ('Texto' if p.get('titulo') else 'Legenda') + ' (%d de %d caracteres%s):' % (n, lim, ', %d hashtag%s' % (ntags, '' if ntags == 1 else 's') if ntags and chave != 'bilibili' else ''), '', '```', p['texto'], '```']
        if p.get('tags'):
            L += ['', 'Tags (campo de tags):', '', '```', p['tags'], '```']
        L.append('')
    return '\n'.join(L)


def cabecalho(titulo):
    L = ['# %s' % titulo, '',
         'Série "Você sabia?": um relógio por post, com legenda pronta para cada rede. Gerado por `ferramentas/relogios_posts.py` a partir do dossiê dos relógios.',
         '',
         'Regras seguidas em todos os textos: nome do produto sem o nome da marca; quem criou e as criações mais conhecidas; gancho de venda; título para YouTube Shorts e BiliBili; BiliBili sem emojis.',
         '',
         'Os links dos textos abrem a busca do site pela referência do relógio: o endereço da página do produto tem o nome da marca, e a regra é não citar a marca.',
         '', 'Hashtags e limites pesquisados em %s:' % datetime.date.fromisoformat(PESQUISA).strftime('%d/%m/%Y'), '']
    for chave, nome, lim, limt, ntags, obs in REDES:
        L.append('- **%s:** %s' % (nome, obs))
    L += ['', 'Fontes da pesquisa: ' + ', '.join(FONTES), '']
    return '\n'.join(L)


def todos(ids=None):
    """[(d, P, erros)] dos relógios pedidos (ou de todos) e a lista dos que ficaram de fora.
    O gancho (1ª curiosidade) não se repete entre relógios: percorre todos do mais antigo para o mais novo e cada um fica com a
    primeira curiosidade que ainda não abriu outro post (relógio novo não muda o post dos antigos)."""
    feitos, fora, usados = [], [], set()
    quer = set(str(i) for i in ids) if ids is not None else None
    for pid in sorted(RD.BASE, key=int):
        d, por = dados(pid)
        if not d:
            if quer is None or pid in quer:
                fora.append((pid, (RD.BASE.get(pid) or {}).get('n', '')[:70], por))
            continue
        livre = [v for v in d['V'] if v[0] not in usados]
        if livre and livre[0] != d['V'][0]:
            d['V'] = [livre[0]] + [v for v in d['V'] if v != livre[0]]
        usados.add(d['V'][0][0])
        if quer is not None and pid not in quer:
            continue
        P = monta(d)
        feitos.append((d, P, confere(d, P)))
    return feitos, fora


def velha():
    dias = (datetime.date.today() - datetime.date.fromisoformat(PESQUISA)).days
    return dias > 60, dias


def main():
    a = sys.argv[1:]
    v, dias = velha()
    if v:
        print('AVISO: a pesquisa de hashtags e limites tem %d dias. Pesquise de novo e atualize REDES e PESQUISA neste arquivo.' % dias, file=sys.stderr)
    if '--checar' in a:
        F, fora = todos()
        ruim = [(d, e) for d, P, e in F if e]
        for d, e in ruim:
            print('PROBLEMA', d['id'], d['nome'], '->', '; '.join(e))
        for pid, n, por in fora:
            print('sem post:', pid, n, '->', por)
        print('posts: %d relógios certos, %d com problema, %d sem post' % (len(F) - len(ruim), len(ruim), len(fora)))
        if '--links' in a:  # o link de busca de cada post mostra mesmo o relógio?
            import subprocess
            mal = 0
            for d, P, e in F:
                h = subprocess.run(['curl', '-sS', '-m', '40', d['url']], capture_output=True, text=True).stdout
                if d['x']['u'] not in h:
                    mal += 1
                    print('LINK não mostra o relógio:', d['url'], '->', d['nome'])
            print('links: %d de %d mostram o relógio' % (len(F) - mal, len(F)))
            ruim = ruim or mal
        sys.exit(1 if ruim else 0)
    if '--pasta' in a:
        pasta = a[a.index('--pasta') + 1]
        os.makedirs(pasta, exist_ok=True)
        F, fora = todos()
        por_marca = {}
        for d, P, e in F:
            if not e:
                por_marca.setdefault(d['marca'], []).append(markdown(d, P))
        for mk, L in sorted(por_marca.items()):
            arq = os.path.join(pasta, re.sub(r'[^a-z0-9]+', '-', mk.lower()).strip('-') + '.md')
            open(arq, 'w', encoding='utf-8').write(cabecalho('Posts "Você sabia?" dos relógios: %s (%d)' % (mk, len(L))) + '\n' + '\n'.join(L))
            print(arq, len(L))
        return
    if '--novos' in a:
        arq = a[a.index('--novos') + 1]
        ja = set(json.load(open(FEITOS))['ids']) if os.path.exists(FEITOS) else set()
        F, fora = todos([p for p in RD.BASE if p not in ja])  # lista vazia = nenhum relógio novo
        bons = [(d, P) for d, P, e in F if not e]
        for d, P, e in F:
            if e:
                print('PROBLEMA', d['id'], d['nome'], '->', '; '.join(e))
        for pid, n, por in fora:
            print('sem post ainda:', pid, n, '->', por)
        if bons:
            open(arq, 'w', encoding='utf-8').write(cabecalho('Posts "Você sabia?" dos relógios novos (%d)' % len(bons)) + '\n' + '\n'.join(markdown(d, P) for d, P in bons))
            json.dump({'_sobre': 'Relógios que já tiveram os posts "Você sabia?" entregues (ferramentas/relogios_posts.py --novos).', 'ids': sorted(ja | {d['id'] for d, P in bons})},
                      open(FEITOS, 'w'), ensure_ascii=False, indent=1)
        print('posts novos: %d%s' % (len(bons), (' em ' + arq) if bons else ''))
        return
    ids = [x for x in a if x.isdigit()]
    F, fora = todos(ids or None)
    if '--md' in a or ids:
        print(cabecalho('Posts "Você sabia?" dos relógios'))
        for d, P, e in F:
            print(markdown(d, P))
            if e:
                print('> PROBLEMA: ' + '; '.join(e) + '\n')
        return
    print(__doc__)


if __name__ == '__main__':
    main()
