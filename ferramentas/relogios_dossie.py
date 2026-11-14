#!/usr/bin/env python3
"""Dossiê dos relógios na descrição (13/11/2026, pedido do Nevander: "um dossiê completo sobre história e curiosidade de
cada um dos relógios... e também onde usar e a ocasião do relógio... algo interessante que traga muito valor ao cliente").

Monta 4 seções na descrição de cada relógio, a partir de:
  - carrossel/relogios.json            (ficha técnica de cada relógio, refeita 5x por dia por ferramentas/relogios.py)
  - ferramentas/relogios_dossie_marcas.json   (história de cada marca: linha do tempo + curiosidades, com fontes)
  - ferramentas/relogios_dossie_modelos.json  (história de cada família de relógio + curiosidades, com fontes)

  1. "O dossiê do <modelo>"            antes de "Destaques"   (só se a família existir no JSON de modelos)
  2. "Feito para quê e onde usar"      depois da Ficha técnica: o propósito do tipo de relógio (mergulho, campo,
                                        cronógrafo, GMT, social, integrado, dia a dia) e o mapa de ocasiões, calculado
                                        da ficha (espessura, água, pulseira, peso, funções)
  3. "A <marca> em N momentos"          linha do tempo da marca (marca nova: acrescentar no JSON das marcas)
  4. "Você sabia?"                      curiosidades do modelo + da marca
O dist/rel.js (código 1799004) transforma a linha do tempo, o mapa de ocasiões e o "Você sabia?" em blocos visuais;
sem JavaScript, continuam texto normal (bom para o Google).

Relógio novo: as seções 2, 3 e 4 saem sozinhas da ficha (marca conhecida). A seção 1 precisa de uma família no JSON de
modelos, escrita com pesquisa e fontes (guia: ferramentas/relogios_dossie.md).

Uso:
  python3 ferramentas/relogios_dossie.py --mostrar ID       mostra o HTML das seções (não grava)
  python3 ferramentas/relogios_dossie.py --gravar [IDs]     grava pela API (token em ~/.lb/li_token), com cópia da descrição antiga
  python3 ferramentas/relogios_dossie.py --faltam           lista relógios sem as seções ou sem família no JSON
Rodar de novo é seguro: as seções antigas são trocadas pelas novas (nada se repete).
"""
import html, json, os, re, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
MARCAS = json.load(open(os.path.join(AQUI, 'relogios_dossie_marcas.json'), encoding='utf-8'))
MODELOS = json.load(open(os.path.join(AQUI, 'relogios_dossie_modelos.json'), encoding='utf-8'))
BASE = {str(x['id']): x for x in json.load(open(os.path.join(RAIZ, 'carrossel', 'relogios.json'), encoding='utf-8'))['r']}
E = html.escape

PROP = {
    'mergulho': ('Feito para mergulhar', 'Os relógios de mergulho nasceram nos anos 1950 para mergulhadores profissionais e militares. O bisel giratório marca o tempo debaixo d\'água e só gira para um lado, para que um esbarrão nunca aumente o tempo restante; ponteiros e índices luminosos garantem a leitura no fundo escuro, e a coroa rosqueada ajuda a vedar a caixa. Hoje esse desenho é um dos mais versáteis do mundo: aguenta piscina, praia e chuva e vai bem tanto com bermuda quanto com camisa.'),
    'campo': ('Feito para o campo', 'O relógio de campo nasceu para os soldados das guerras do século 20: mostrador limpo, números grandes e marcação de 24 horas para ler a hora num relance, de dia ou de noite. A mesma lógica faz dele um ótimo relógio para a rotina: leve, robusto e fácil de ler, do trabalho à trilha.'),
    'cronografo': ('Feito para cronometrar', 'O cronógrafo nasceu para medir tempos nas pistas, no esporte e na aviação: os botões iniciam, param e zeram a contagem sem mexer na hora. No dia a dia ele cronometra o treino, o forno, o estacionamento ou a volta de bicicleta, e o visual de painel de carro deixa o pulso esportivo e sofisticado.'),
    'gmt': ('Feito para viajar', 'O GMT ganhou fama nos anos 1950 com os pilotos das linhas aéreas que cruzavam continentes e precisavam ver a hora local e a hora de referência ao mesmo tempo. O ponteiro extra de 24 horas mostra um segundo fuso: ideal para quem viaja, trabalha com outros países ou tem família longe.'),
    'social': ('Feito para acompanhar a roupa', 'O relógio social nasceu para acompanhar terno e camisa: caixa fina que passa por baixo do punho, mostrador limpo e acabamento caprichado. Ele não disputa atenção com a roupa e mostra cuidado nos detalhes, do trabalho aos eventos.'),
    'integrado': ('Feito para ir a qualquer lugar', 'Os esportivos de aço com pulseira integrada marcaram os anos 1970: caixa e pulseira formam uma peça só, elegante como um social e resistente como um esportivo. É o relógio que vai do escritório ao fim de semana sem precisar trocar.'),
    'dia_a_dia': ('Feito para o dia a dia', 'Este é um automático de uso diário: resistente, fácil de ler e com a data à vista, pensado para acompanhar a rotina inteira sem pedir cuidado especial. É o relógio que você coloca de manhã e esquece que está usando.'),
}
CURTO = {
    'cronografo': 'E ainda tem cronógrafo, para medir tempos com um toque nos botões.',
    'integrado': 'A pulseira integrada deixa o conjunto elegante e firme no pulso.',
    'campo': 'O visual de campo deixa a leitura rápida e o relógio pronto para o ar livre.',
    'social': 'O acabamento caprichado deixa o relógio à vontade também em ocasiões formais.',
    'mergulho': 'E tem a robustez dos relógios de mergulho.',
    'gmt': 'E tem GMT, para acompanhar um segundo fuso horário.',
    'dia_a_dia': 'E é robusto o bastante para o uso de todo dia.',
}
TITULOS = ('O dossiê d', 'Feito para quê e onde usar', 'Você sabia?')


def br(v):
    return ('%g' % v).replace('.', ',')


def infere_cats(x):
    """Relógio sem família no JSON: deduz para que ele foi feito pela ficha e pelo nome."""
    n = (x.get('n') or '').lower()
    fn = x.get('fn', '')
    c = []
    if re.search(r'diver|mergulh|mako|skydiver|prospex.*(?:diver|200m)|submar', n) or (x.get('agua', 0) >= 200):
        c.append('mergulho')
    if 'g' in fn:
        c.append('gmt')
    if 'c' in fn:
        c.append('cronografo')
    if re.search(r'field|expedition|garrison|campo|militar|pilot|aviador', n):
        c.append('campo')
    if not c and x.get('esp') and x['esp'] <= 11.5 and x.get('agua', 0) <= 50:
        c.append('social')
    return c or ['dia_a_dia']


ROTULO = {  # (ideal, também combina)
    'trabalho': ('Ideal para o trabalho', 'Também vai bem no trabalho'),
    'terno': ('Ideal para terno, casamento e eventos', 'Também acompanha terno e eventos'),
    'dia': ('Ideal para o dia a dia', 'Também vai bem no dia a dia'),
    'viagem': ('Ideal para viajar', 'Também vai bem em viagens e no fim de semana'),
    'praia': ('Ideal para praia e piscina', 'Também vai à praia e à piscina'),
    'esporte': ('Ideal para esporte e treino', 'Também acompanha esporte e treino'),
    'trilha': ('Ideal para trilha e ar livre', 'Também vai bem na trilha e ao ar livre'),
    'noite': ('Ideal para jantar e noite', 'Também vai bem num jantar e à noite'),
}
PRIOR = ['terno', 'noite', 'trabalho', 'viagem', 'praia', 'esporte', 'dia', 'trilha']


def ocasioes(x, cats, fam):
    """[(nivel, rótulo, porquê)] para a descrição."""
    return [(n, ROTULO[k][0 if n == 'ideal' else 1], r) for n, k, r in ocasioes_chaves(x, cats, fam)]


def ocasioes_chaves(x, cats, fam):
    """Mapa de ocasiões calculado da ficha. Devolve [(nivel, chave, porquê)]: todas as 'ideal' + até 3 'combina'."""
    esp, agua, pul = x.get('esp'), x.get('agua', 0), x.get('pul', '')
    couro, metal = pul == 'couro', pul == 'metal'
    leve = pul in ('tecido', 'borracha') or (x.get('peso') and x['peso'] <= 100) or x.get('mat') == 'titanio'
    lume = 'l' in x.get('fn', '')
    tipo = x.get('tipo')
    mov = {'auto': 'Automático, ganha corda sozinho enquanto você usa', 'manual': 'De corda manual, um ritual de poucos segundos por dia',
           'quartzo': 'Quartzo preciso, sem precisar de corda', 'solar': 'Carrega com qualquer luz, sem troca de pilha comum'}.get(tipo, 'Fácil de usar')
    O = []
    # trabalho
    if 'social' in cats or 'integrado' in cats:
        O.append(('ideal', 'trabalho', 'Visual limpo e elegante, que combina com camisa social e fica bem em qualquer reunião.'))
    elif 'campo' in cats:
        O.append(('combina', 'trabalho', 'Leitura rápida e visual casual, ótimo para ambientes de trabalho menos formais.'))
    elif 'mergulho' in cats:
        if metal:
            O.append(('combina', 'trabalho', 'Com pulseira de aço, o visual de mergulhador também fica bem com camisa.'))
    else:
        O.append(('combina', 'trabalho', 'Discreto o bastante para o escritório, com personalidade de sobra.'))
    # terno e eventos
    if esp and esp <= 12.5 and ('social' in cats or 'integrado' in cats or 'dia_a_dia' in cats):
        nivel = 'ideal' if 'social' in cats and esp <= 12 else 'combina'
        O.append((nivel, 'terno', 'Com %s mm de espessura, passa por baixo do punho da camisa e acompanha bem o terno.' % br(esp)))
    # dia a dia
    agua_txt = (' e aguenta chuva, banho de piscina e o suor do dia' if agua >= 100 else ' e aguenta chuva e respingos' if agua >= 30 else '')
    if agua >= 100 or 'dia_a_dia' in cats or 'campo' in cats:
        O.append(('ideal', 'dia', mov + agua_txt + '.'))
    else:
        O.append(('combina', 'dia', mov + agua_txt + '.'))
    # viagem
    if 'gmt' in cats:
        O.append(('ideal', 'viagem', 'O ponteiro GMT mostra a hora de casa e a do destino ao mesmo tempo.'))
    elif tipo in ('solar', 'quartzo'):
        O.append(('combina', 'viagem', 'Sem corda para dar: é colocar na mala e usar.'))
    elif x.get('res', 0) >= 60:
        O.append(('combina', 'viagem', 'Com %d horas de reserva de marcha, aguenta dias na mala e continua funcionando.' % x['res']))
    else:
        O.append(('combina', 'viagem', 'Versátil para levar na mala e usar com qualquer roupa.'))
    # praia e piscina
    if agua >= 200 and not couro:
        O.append(('ideal', 'praia', 'São %d metros de resistência à água: natação, snorkel e mergulho livre à vontade. Depois do mar, é só enxaguar em água doce.' % agua))
    elif agua >= 100 and not couro:
        nivel = 'ideal' if ('mergulho' in cats or 'campo' in cats or 'integrado' in cats or pul in ('borracha', 'tecido')) else 'combina'
        O.append((nivel, 'praia', 'Com %d metros de resistência à água, dá para nadar com ele; depois do mar, é só enxaguar em água doce.' % agua))
    # esporte
    if 'cronografo' in cats and not couro:
        O.append(('ideal', 'esporte', 'O cronógrafo marca séries, voltas e intervalos sem precisar do celular.'))
    elif leve and agua >= 50 and not couro:
        O.append(('ideal', 'esporte', 'Leve no pulso, acompanha caminhada, bicicleta e academia com conforto.'))
    elif agua >= 100 and not couro and esp and esp <= 13.6:
        O.append(('combina', 'esporte', 'Aguenta suor e água e fica firme no pulso nas atividades do dia.'))
    # trilha
    if 'campo' in cats or 'mergulho' in cats:
        O.append(('ideal', 'trilha', 'Leitura rápida%s e construção robusta para trilha, acampamento e pescaria.' % (', brilho no escuro' if lume else '')))
    elif agua >= 100 and not couro:
        O.append(('combina', 'trilha', 'Carrega com a luz do dia e aguenta chuva.' if tipo == 'solar' else 'Aguenta chuva e poeira e fica firme no pulso num passeio ao ar livre.'))
    # noite
    if fam == 'cocktail':
        O.append(('ideal', 'noite', 'Nasceu da cultura dos bares de coquetel de Tóquio: o lugar dele é o jantar, o happy hour e o encontro.'))
    elif 'social' in cats:
        O.append(('ideal', 'noite', 'O brilho do mostrador e o acabamento caprichado chamam atenção à luz baixa de um jantar.'))
    elif 'integrado' in cats or metal:
        O.append(('combina', 'noite', 'O aço polido ganha brilho à noite e combina com roupa de sair.'))
    ide = [o for o in O if o[0] == 'ideal']
    com = sorted([o for o in O if o[0] == 'combina'], key=lambda o: PRIOR.index(o[1]))[:3]
    return sorted(ide, key=lambda o: PRIOR.index(o[1])) + com


def secoes(pid, x=None):
    pid = str(pid)
    x = x or BASE.get(pid)
    if not x:
        return None
    pr = MODELOS['produtos'].get(pid, {})
    fam = pr.get('f')
    F = MODELOS['familias'].get(fam) if fam else None
    marca = MARCAS.get(x.get('mk'))
    cats = (F or {}).get('cats') or infere_cats(x)
    irmaos = sorted(set(k for k, v in BASE.items() if v.get('mk') == x.get('mk')) | {pid})
    i = irmaos.index(pid) if pid in irmaos else 0
    out = {}
    # 1. dossiê do modelo
    if F:
        out['modelo'] = '<h3>%s</h3>\r\n%s' % (E(F['titulo']), '\r\n'.join('<p>%s</p>' % E(p) for p in F['p']))
    # 2. feito para quê e onde usar
    t, txt = PROP[cats[0]]
    extra = ' '.join(CURTO[c] for c in cats[1:2])
    lis = ''.join('\r\n<li><strong>%s.</strong> %s</li>' % (E(o), E(r)) for n, o, r in ocasioes(x, cats, fam))
    out['uso'] = '<h3>Feito para quê e onde usar</h3>\r\n<p><strong>%s.</strong> %s%s</p>\r\n<ul>%s\r\n</ul>' % (E(t), E(txt), (' ' + E(extra)) if extra else '', lis)
    # 3. linha do tempo da marca (7 momentos; a fundação sempre; os outros variam entre relógios da mesma marca)
    if marca:
        L = marca['linha']
        if len(L) > 7:
            resto, k = L[1:], len(L) - 1
            n = k - 6
            tira = {(i + j * (k // n)) % k for j in range(n)}  # tira n momentos espalhados, num rodízio que muda de relógio para relógio
            L = [L[0]] + [m for j, m in enumerate(resto) if j not in tira]
        intro = marca['intro'][i % len(marca['intro'])]
        lis = ''.join('\r\n<li><strong>%s:</strong> %s</li>' % (E(a), E(t)) for a, t in L)
        out['marca'] = '<h3>A %s em %d momentos</h3>\r\n<p>%s</p>\r\n<ol>%s\r\n</ol>' % (E(x['mk']), len(L), E(intro), lis)
    # 4. você sabia? (modelo + variante + 2 da marca, sem repetir assunto do dossiê)
    V = list(pr.get('vs', [])) + list((F or {}).get('vs', []))
    if marca:
        texto_modelo = ' '.join((F or {}).get('p', [])).lower()
        linha_txt = ' '.join(t for a, t in L)
        nomes_linha = set(re.findall(r'\b[A-Z][\w-]{3,}', linha_txt)) - {'Seiko', 'Tissot', 'Citizen', 'Invicta', 'Timex', 'Orient', 'Mido', 'Technos', 'Suíça', 'Japão', 'Tóquio', 'Chega', 'Nasce', 'Estreia', 'Sai'}
        bv = [v for v in marca['vs'] if v[1][:40].lower() not in texto_modelo and not (set(re.findall(r'\b[A-Z][\w-]{3,}', v[1])) & nomes_linha)]
        V += [bv[(i + j) % len(bv)] for j in range(min(2, len(bv)))]
    vistos, VV = set(), []
    for a, t in V:
        if a not in vistos:
            vistos.add(a); VV.append((a, t))
    if VV:
        out['vs'] = '<h3>Você sabia?</h3>\r\n<ul>%s\r\n</ul>' % ''.join('\r\n<li><strong>%s.</strong> %s</li>' % (E(a), E(t)) for a, t in VV[:6])
    return out


def limpa(d, modelo=True):
    """Tira as seções geradas antes (para rodar de novo sem repetir). O dossiê do modelo só sai se houver um novo."""
    for t in (('O dossiê d',) if modelo else ()) + ('Feito para quê e onde usar', 'A [^<]{2,40} em \\d+ momentos', 'Você sabia\\?'):
        d = re.sub(r'<h3>' + t + r'[^<]*</h3>[\s\S]*?(?=<h3>)', '', d)
    return d


def aplica(d, S):
    d = limpa(d, 'modelo' in S)
    if 'modelo' in S:
        i = d.find('<h3>Destaques</h3>')
        if i >= 0:
            d = d[:i] + S['modelo'] + '\r\n' + d[i:]
    bloco = '\r\n'.join(S[k] for k in ('uso', 'marca', 'vs') if k in S)
    i = d.find('<h3>Para quem é</h3>')
    if i < 0:
        i = d.find('<h3>Perguntas frequentes</h3>')
    if i >= 0 and bloco:
        d = d[:i] + bloco + '\r\n' + d[i:]
    return d


def grava(req, pid, x=None, bk='/tmp/relogios_dossie_antigas'):
    """Grava as seções na descrição pela API (req = função de requisição com o token). Devolve o resultado em texto."""
    S = secoes(pid, x)
    if not S:
        return 'fora da base'
    c, t = req('GET', f'/produto/{pid}')
    if c != 200:
        return 'erro leitura %s' % c
    p = json.loads(t); d = p.get('descricao_completa') or ''
    if '<h3>Destaques</h3>' not in d and '<h3>Para quem é</h3>' not in d and '<h3>Perguntas frequentes</h3>' not in d:
        return 'descrição fora do padrão (sem Destaques/Para quem é/Perguntas frequentes): não mexi'
    os.makedirs(bk, exist_ok=True)
    open(os.path.join(bk, f'{pid}_{int(time.time())}.html'), 'w', newline='').write(d)
    nd = aplica(d, S)
    if nd == d:
        return 'já estava igual'
    c, t = req('PUT', f'/produto/{pid}', {'descricao_completa': nd})
    c2, t2 = req('GET', f'/produto/{pid}'); q = json.loads(t2)
    return 'ok' if q.get('descricao_completa') == nd and q.get('nome') == p.get('nome') else 'ERRO %s' % c


# ---------- página da marca (categoria): a história completa, embaixo da lista de relógios ----------
RE_MARCA = r'\s*<h2>A história d[ao] [^<]{2,40} em \d+ momentos</h2>[\s\S]*$'


def secao_marca(nome):
    """Bloco da página da marca: TODOS os momentos da linha do tempo e TODAS as curiosidades. Sai de relogios_dossie_marcas.json."""
    m = MARCAS.get(nome)
    if not m:
        return None
    lis = ''.join('\r\n<li><strong>%s:</strong> %s</li>' % (E(a), E(t)) for a, t in m['linha'])
    h = '<h2>A história da %s em %d momentos</h2>\r\n<p>%s</p>\r\n<ol>%s\r\n</ol>' % (E(nome), len(m['linha']), E(m['intro'][0]), lis)
    if m.get('vs'):
        h += '\r\n<h2>Você sabia?</h2>\r\n<ul>%s\r\n</ul>' % ''.join('\r\n<li><strong>%s.</strong> %s</li>' % (E(a), E(t)) for a, t in m['vs'])
    return h


# lista viva dos modelos da marca (14/11/2026): sai do carrossel/relogios.json, então acompanha o que está à venda
TIPO_N = {'auto': 'automático', 'manual': 'de corda manual', 'quartzo': 'a quartzo', 'solar': 'solar'}
TIPO_NS = {'auto': 'automáticos', 'manual': 'de corda manual', 'quartzo': 'a quartzo', 'solar': 'solares'}
ORIG_N = {'japones': 'japonês', 'suico': 'suíço'}
VIDRO_N = {'safira': 'vidro de safira', 'hardlex': 'vidro Hardlex', 'mineral': 'vidro mineral', 'acrilico': 'vidro acrílico'}
RE_MODELOS = r'<p>Na <strong>@LOJABIT</strong> você encontra[\s\S]*?<p>Não sabe qual escolher\?[\s\S]*?</p>'
RE_SEM_ESTOQUE = r'<p>Os relógios [^<]{2,40} da <strong>@LOJABIT</strong> estão a caminho[\s\S]*?</p>'
_CUR = None


def curiosidades():
    """{id: (título, texto)}: uma curiosidade por relógio, sem repetir entre relógios (a do produto primeiro, depois as da família).
    Percorre do mais antigo para o mais novo: relógio novo não muda a curiosidade dos antigos."""
    global _CUR
    if _CUR is None:
        _CUR, usados = {}, set()
        for pid in sorted(BASE, key=int):
            pr = MODELOS['produtos'].get(pid, {})
            F = MODELOS['familias'].get(pr.get('f')) or {}
            V = list(pr.get('vs', [])) + list(F.get('vs', []))
            livre = [v for v in V if v[0] not in usados] or V
            if livre:
                _CUR[pid] = tuple(livre[0]); usados.add(livre[0][0])
    return _CUR


def _lista(itens):
    return itens[0] if len(itens) == 1 else ', '.join(itens[:-1]) + ' e ' + itens[-1]


def secao_modelos(nome):
    """Bloco "Na @LOJABIT você encontra…": um item por relógio da marca À VENDA, com link, ficha em uma linha, uso ideal e uma curiosidade."""
    R = sorted([x for x in BASE.values() if x.get('mk') == nome and x.get('disp') and x.get('p', 0) > 0],
               key=lambda x: (MODELOS['produtos'].get(str(x['id']), {}).get('f', 'zz'), x['n']))
    if not R:
        return ('<p>Os relógios %s da <strong>@LOJABIT</strong> estão a caminho: fale com a gente no WhatsApp (24) 98122-6521 para saber da próxima chegada.</p>' % E(nome))
    cur = curiosidades()
    L = []
    for x in R:
        pid = str(x['id'])
        fam = MODELOS['produtos'].get(pid, {}).get('f')
        cats = (MODELOS['familias'].get(fam) or {}).get('cats') or infere_cats(x)
        f = [TIPO_N.get(x.get('tipo'), '') + ((' ' + ORIG_N[x['orig']]) if x.get('orig') in ORIG_N and x.get('tipo') in ('auto', 'manual') else '')]
        if x.get('agua'):
            f.append('%d m de resistência à água' % x['agua'])
        if x.get('vidro') in VIDRO_N:
            f.append(VIDRO_N[x['vidro']])
        f = [i for i in f if i]
        txt = (f[0][0].upper() + f[0][1:] + (', ' + ', '.join(f[1:]) if len(f) > 1 else '') + '.') if f else ''
        ideal = [k for n, k, r in ocasioes_chaves(x, cats, fam) if n == 'ideal']
        if ideal:
            txt += ' ' + ROTULO[ideal[0]][0] + '.'
        if pid in cur:
            txt += ' ' + cur[pid][1]
        nm = re.sub(r'^Relógio (Masculino|Feminino|Unissex)\s+', '', x['n'])
        L.append('\r\n<li><a href="%s">%s</a>: %s</li>' % (E(x['u']), E(nm), E(txt.strip())))
    n = len(R)
    if n == 1:
        cab = 'Na <strong>@LOJABIT</strong> você encontra 1 relógio %s original:' % E(nome)
    else:
        tipos = {}
        for x in R:
            tipos[x.get('tipo')] = tipos.get(x.get('tipo'), 0) + 1
        partes = ['%d %s' % (q, (TIPO_N if q == 1 else TIPO_NS).get(t, 'relógio' if q == 1 else 'relógios')) for t, q in sorted(tipos.items(), key=lambda kv: -kv[1]) if t]
        D = sorted(x['diam'] for x in R if x.get('diam'))
        med = (' com caixas de %s a %s mm' % (br(D[0]), br(D[-1])) if D and D[0] != D[-1] else (' com caixa de %s mm' % br(D[0]) if D else ''))
        if len(tipos) == 1 and partes:
            um = {'auto': 'automáticos', 'solar': 'solares', 'quartzo': 'a quartzo', 'manual': 'de corda manual'}.get(list(tipos)[0], '')
            um = (('os dois ' if n == 2 else 'todos ') + um) if um else ''
            cab = 'Na <strong>@LOJABIT</strong> você encontra %d relógios %s originais%s%s:' % (n, E(nome), (', ' + um) if um else '', (',' + med) if med and um else med)
        elif partes:
            cab = 'Na <strong>@LOJABIT</strong> você encontra %d relógios %s originais: %s,%s.' % (n, E(nome), _lista(partes), med)
        else:
            cab = 'Na <strong>@LOJABIT</strong> você encontra %d relógios %s originais:' % (n, E(nome))
    return ('<p>%s</p>\r\n<ul>%s\r\n</ul>\r\n<p>Não sabe qual escolher? <a href="/relogios-originais#quiz">Faça o quiz</a> e veja em 4 perguntas qual combina com você.</p>' % (cab, ''.join(L)))


def aplica_modelos(d, nome):
    """Põe (ou atualiza) a lista viva dos modelos. Na 1ª vez troca o parágrafo antigo "Na @LOJABIT você encontra…" e o comentário
    que vinha logo depois dele (os dois citavam modelos e ficavam velhos)."""
    bloco = secao_modelos(nome)
    d = d or ''
    if re.search(RE_MODELOS, d):
        return re.sub(RE_MODELOS, lambda m: bloco, d, count=1)
    if re.search(RE_SEM_ESTOQUE, d):
        return re.sub(RE_SEM_ESTOQUE, lambda m: bloco, d, count=1)
    m = re.search(r'<p>Na <strong>@LOJABIT</strong> você encontra[\s\S]*?</p>', d)
    if m:
        fim = m.end()
        m2 = re.match(r'\s*<p>([\s\S]*?)</p>', d[fim:])
        if m2 and 'garantia legal' not in m2.group(1) and '<a ' not in m2.group(1) and '<h2' not in m2.group(1):
            fim += m2.end()
        return d[:m.start()] + bloco + d[fim:]
    # descrição sem a lista: entra antes do parágrafo final (garantia), antes da história ou no fim
    for pat in (r'<p>(?:(?!</p>)[\s\S])*garantia legal(?:(?!</p>)[\s\S])*</p>', r'<h2>A história d[ao] '):
        m = re.search(pat, d)
        if m:
            return d[:m.start()] + bloco + '\r\n\r\n' + d[m.start():]
    if not d.strip():  # categoria nova, sem texto: começa com o título e a origem da marca
        mk = MARCAS.get(nome) or {}
        d = '<h2>Relógio %s original</h2>\r\n\r\n<p>%s</p>' % (E(nome), E((mk.get('intro') or [''])[0]))
    return d.rstrip() + '\r\n\r\n' + bloco


def aplica_marca(d, nome):
    bloco = secao_marca(nome)
    if not bloco:
        return d
    d = aplica_modelos(re.sub(RE_MARCA, '', d or '').rstrip(), nome)
    return d.rstrip() + '\r\n\r\n' + bloco


def grava_marca(req, cat_id, nome, bk='/tmp/relogios_dossie_antigas'):
    """Põe (ou atualiza) a história completa no fim da descrição da categoria da marca. O texto que já existe fica como está."""
    if nome not in MARCAS:
        return 'marca sem dossiê'
    c, t = req('GET', f'/categoria/{cat_id}')
    if c != 200:
        return 'erro leitura %s' % c
    p = json.loads(t); d = p.get('descricao') or ''
    nd = aplica_marca(d, nome)
    if nd == d:
        return 'já estava igual'
    os.makedirs(bk, exist_ok=True)
    open(os.path.join(bk, f'categoria_{cat_id}_{int(time.time())}.html'), 'w', newline='').write(d)
    c, t = req('PUT', f'/categoria/{cat_id}', {'descricao': nd})
    c2, t2 = req('GET', f'/categoria/{cat_id}'); q = json.loads(t2)
    return 'ok' if q.get('descricao') == nd and q.get('nome') == p.get('nome') and q.get('url') == p.get('url') else 'ERRO %s' % c


def categorias_de_marca(req, pai=24410277):
    """{nome da marca: id} das subcategorias de Relógios cujo nome é uma marca do dossiê."""
    out, off = {}, 0
    while True:
        c, t = req('GET', f'/categoria/?limit=100&offset={off}')
        if c != 200:
            break
        o = json.loads(t).get('objects', [])
        for x in o:
            if x.get('nome') in MARCAS and str(pai) in str(x.get('categoria_pai') or ''):
                out[x['nome']] = x['id']
        if len(o) < 100:
            break
        off += 100
    return out


def main():
    if '--mostrar' in sys.argv:
        S = secoes(sys.argv[sys.argv.index('--mostrar') + 1])
        for k, v in (S or {}).items():
            print('=====', k); print(v)
        return
    if '--faltam' in sys.argv:
        for pid, x in BASE.items():
            pr = MODELOS['produtos'].get(pid)
            if not pr or pr.get('f') not in MODELOS['familias']:
                print('sem família no dossiê:', x['n'][:80])
            if x.get('mk') not in MARCAS:
                print('marca sem dossiê:', x.get('mk'), '-', x['n'][:60])
        return
    if '--marcas' in sys.argv:
        sys.path.insert(0, '/home/claude/compilado')
        from api_li import req
        for nome, cid in sorted(categorias_de_marca(req).items()):
            print(nome, cid, grava_marca(req, cid, nome), flush=True)
        return
    if '--gravar' in sys.argv:
        sys.path.insert(0, '/home/claude/compilado')
        from api_li import req
        ids = [a for a in sys.argv[sys.argv.index('--gravar') + 1:] if a.isdigit()] or list(BASE)
        for pid in ids:
            print(pid, grava(req, pid), BASE.get(pid, {}).get('n', '')[:60], flush=True)


if __name__ == '__main__':
    main()
