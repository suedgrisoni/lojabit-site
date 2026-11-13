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
    return [(n, ROTULO[k][0 if n == 'ideal' else 1], r) for n, k, r in sorted(ide, key=lambda o: PRIOR.index(o[1])) + com]


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
    if '--gravar' in sys.argv:
        sys.path.insert(0, '/home/claude/compilado')
        from api_li import req
        ids = [a for a in sys.argv[sys.argv.index('--gravar') + 1:] if a.isdigit()] or list(BASE)
        for pid in ids:
            print(pid, grava(req, pid), BASE.get(pid, {}).get('n', '')[:60], flush=True)


if __name__ == '__main__':
    main()
