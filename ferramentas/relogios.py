#!/usr/bin/env python3
"""Base dos relógios (13/11/2026): carrossel/relogios.json, feita da FICHA TÉCNICA de cada página de relógio do site.

Usada pelo dist/rel.js (código 1799004) nas listagens (etiqueta "Automático · 40 mm · 100 m" nos cartões e filtros de
relógio) e na página do relógio (comparador e "relógios com a mesma proposta"). A ficha animada da página lê a própria
descrição; esta base serve para os outros relógios aparecerem juntos.

Relógio novo entra sozinho: a tarefa "Carrossel: preços atualizados" (5x por dia) roda este arquivo junto com os carrosséis.
Não precisa de chave: lê só páginas públicas (lista de relógios pela base do robô dos filtros, com a listagem /relogios-originais
como reserva).

Uso: python3 ferramentas/relogios.py            -> grava carrossel/relogios.json (só se mudou) e mostra o que falta nas fichas
     python3 ferramentas/relogios.py --faltas   -> só mostra os campos que faltam (não grava)
"""
import html, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carrossel as CR
import verificador as VF

SAIDA = os.path.join(CR.D, 'relogios.json')
FREQ = [(r'powermatic 80|calibre 80\b|c07\.\d', 21600), (r'nh3[5-9]', 21600), (r'4r3\d|7s2\d|7s3\d', 21600), (r'\b82[01]\d\b', 21600),
        (r'sw ?200|eta 2824|a05\.h31|valjoux 7750', 28800)]
CORES = ['azul-gelo', 'azul', 'preto', 'branco', 'prata', 'prateado', 'cinza', 'verde', 'bege', 'champanhe', 'dourado', 'marrom',
         'vermelho', 'rosa', 'creme', 'laranja', 'amarelo', 'roxo', 'bordô', 'grafite']
PADRAO = ['movimento', 'caixa', 'resistencia a agua', 'vidro', 'fundo', 'funcoes', 'pulseira', 'peso', 'reserva/frequencia', 'luminescencia', 'ponta a ponta']


def sa(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', str(s or '').lower()) if unicodedata.category(c) != 'Mn')


def num(s):
    return float(re.sub(r'\.(?=\d{3}\b)', '', str(s)).replace(',', '.'))


def texto(h):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))).strip()


def ficha(desc):
    o = {}
    for m in re.finditer(r'<li[^>]*>\s*<strong>([^<]+?)</strong>([\s\S]*?)</li>', desc):
        k = sa(m.group(1)).strip().rstrip(':').strip()
        v = texto(m.group(2)).lstrip(':').strip()
        if k and v and k not in o:
            o[k] = v
    return o


def le(pid, url):
    h = CR.baixa(CR.LOJA + url)
    if 'pagina-produto' not in h:
        return None
    i = h.find('id="descricao"')
    desc = h[h.find('>', i) + 1: i + 120000] if i >= 0 else ''
    mf = re.search(r'<h3>\s*Ficha t[ée]cnica\s*</h3>\s*<ul>([\s\S]*?)</ul>', desc)
    f = ficha(mf.group(1) if mf else desc)
    nome = texto((re.search(r'<h1[^>]*class="[^"]*nome-produto[^"]*"[^>]*>([\s\S]*?)</h1>', h) or [None, ''])[1])
    r = {'id': pid, 'n': nome, 'u': url}
    m = re.search(r'<div class="acoes-produto ([^"]*)" data-produto-id="' + str(pid) + r'"[\s\S]{0,4000}?data-sell-price="([\d.]+)"', h)
    r['p'] = float(m.group(2)) if m else 0
    r['disp'] = 1 if m and 'indisponivel' not in m.group(1) and 'disponivel' in m.group(1) else 0
    m2 = re.search(r'<div class="acoes-produto [^"]*" data-produto-id="' + str(pid) + r'"[\s\S]{0,4000}?class="preco-venda[^"]*"[^>]*>([\s\S]{0,80}?)<', h)
    if m2:
        try:
            po = num(re.search(r'([\d.]+,\d{2})', m2.group(1)).group(1))
            if po > r['p']:
                r['po'] = po
        except Exception:
            pass
    m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
    r['f'] = re.sub(r'/\d+x\d+/', '/400x400/', m.group(1)) if m else ''
    mb = re.search(r'itemprop="brand"[\s\S]{0,500}?href="[^"]*/marca/[^"/]+?\.html"[^>]*>([^<]+)<', h)
    r['mk'] = texto(mb.group(1)) if mb else re.split(r'\s*[,(]', f.get('marca', ''))[0]
    mov, cx, ag, fu, vd = sa(f.get('movimento')), sa(f.get('caixa')), sa(f.get('resistencia a agua')), sa(f.get('funcoes')), sa(f.get('vidro'))
    nm = sa(nome)
    r['tipo'] = 'solar' if re.search(r'solar|eco-drive|movido a luz', mov) else 'quartzo' if re.search(r'quartzo|pilha|bateria', mov) else \
        'auto' if 'automatico' in mov else 'manual' if re.search(r'manual|corda', mov) else ''
    m = re.search(r'(\d{2}(?:[.,]\d+)?)\s*(?:x\s*\d{2}(?:[.,]\d+)?\s*)?mm(?: de di[âa]metro)?', f.get('caixa', ''), re.I)
    if m and 24 <= num(m.group(1)) <= 60:
        r['diam'] = num(m.group(1))
    m = re.search(r'(\d{1,2}(?:[.,]\d+)?)\s*mm de espessura', f.get('caixa', ''), re.I)
    if m:
        r['esp'] = num(m.group(1))
    m = re.search(r'(\d{2}(?:[.,]\d+)?)\s*mm (?:de ponta a ponta|entre (?:as )?al[çc]as)', f.get('caixa', ''), re.I) or \
        re.search(r'(\d{2}(?:[.,]\d+)?)', f.get('distancia entre as alcas (lug-to-lug)', ''))
    if m and num(m.group(1)) > 34:
        r['l2l'] = num(m.group(1))
    m = re.search(r'(\d+)\s*bar', ag) or re.search(r'(\d+)\s*atm', ag)
    if m:
        r['agua'] = int(m.group(1)) * 10
    else:
        m = re.search(r'(\d+)\s*(?:metros|m\b)', ag)
        if m:
            r['agua'] = int(m.group(1))
    m = re.search(r'(\d{1,2}\.\d{3}|\d{5})\s*(?:alternancias|vph|a/h)', sa(f.get('frequencia', '')) + ' ' + mov)
    if m:
        r['freq'] = int(num(m.group(1)))
    elif r['tipo'] in ('auto', 'manual'):
        for rx, v in FREQ:
            if re.search(rx, mov):
                r['freq'] = v
                break
    m = re.search(r'(\d+)\s*horas', sa(f.get('reserva de marcha', '')))
    if m:
        r['res'] = int(m.group(1))
    m = re.search(r'(\d{2,3})\s*g\b', sa(f.get('peso', '')))
    if m:
        r['peso'] = int(m.group(1))
    r['vidro'] = 'safira' if 'safira' in vd else 'hardlex' if 'hardlex' in vd else 'acrilico' if 'acrilic' in vd else 'mineral' if 'mineral' in vd else ''
    r['mat'] = 'titanio' if re.search(r'titanio|titanium', cx) else 'aco' if 'aco' in cx else 'latao' if 'latao' in cx else 'bronze' if 'bronze' in cx else ''
    pul = sa(f.get('pulseira') or f.get('pulseiras') or '')
    r['pul'] = 'metal' if re.search(r'aco|titanio|titanium|metal|beads|elos', pul) and not re.search(r'^couro|^borracha|^nylon|^tecido|^silicone', pul) else \
        'couro' if 'couro' in pul else 'borracha' if re.search(r'borracha|silicone|fkm|resina', pul) else 'tecido' if re.search(r'nylon|tecido|nato|lona', pul) else ''
    fx = fu + ' ' + nm
    fn = ''
    if 'cronografo' in fx: fn += 'c'
    if re.search(r'gmt|segundo fuso', fx): fn += 'g'
    if re.search(r'dia da semana|\bdia,|\bdia e data|dia-data', fu): fn += 'd'
    if re.search(r'\bdata\b', fu): fn += 't'
    if f.get('luminescencia') or re.search(r'lumibrite|luminova|luminesc|indiglo', sa(json.dumps(f, ensure_ascii=False))): fn += 'l'
    if re.search(r'transparente|safira|exib', sa(f.get('fundo', ''))): fn += 'f'
    r['fn'] = fn
    mc = re.search(r'mostrador ([\w-]+(?: [\w-]+)?)', nome, re.I)
    cor = ''
    if mc:
        c0 = sa(mc.group(1))
        for c in CORES:
            if c0.startswith(sa(c)):
                cor = c
                break
    if not cor:
        for c in CORES:
            if re.search(r'\b' + re.escape(sa(c)) + r'\b', sa(f.get('mostrador', ''))):
                cor = c
                break
    r['cor'] = {'prateado': 'prata', 'azul-gelo': 'azul-gelo'}.get(cor, cor)
    pais = sa((re.search(r'\(([^,)]+)', f.get('marca', '')) or [None, ''])[1])
    r['orig'] = 'japones' if 'japones' in mov else 'suico' if 'suico' in mov else 'suico' if 'suica' in pais else 'japones' if 'japao' in pais else ''
    # o que falta para o padrão (vai no aviso das tarefas): obrigatório x "pode completar" (o painel funciona sem)
    ks = ' | '.join(f)
    falta = [k for k in ('movimento', 'caixa', 'resistencia a agua', 'vidro', 'funcoes') if k not in f]
    if 'fundo' not in ks: falta.append('fundo')
    if 'pulseira' not in ks: falta.append('pulseira')
    if r['tipo'] in ('auto', 'manual') and 'res' not in r: falta.append('reserva de marcha')
    if r['tipo'] in ('auto', 'manual') and 'freq' not in r: falta.append('frequência')
    if 'diam' not in r: falta.append('diâmetro')
    if 'esp' not in r: falta.append('espessura')
    if not r['tipo']: falta.append('tipo de movimento (automático, quartzo, solar...)')
    if r.get('diam') and not re.search(r'\d+(?:[.,]\d+)?\s?mm\b', nome, re.I): falta.append('diâmetro no título')
    r['falta'] = falta
    # seções do dossiê (ferramentas/relogios_dossie.py) que a descrição já tem: m=modelo, u=onde usar, t=marca, v=você sabia
    r['_sec'] = ''.join(k for k, t in (('m', '<h3>O dossiê d'), ('u', '<h3>Feito para quê e onde usar'), ('t', ' momentos</h3>'), ('v', '<h3>Você sabia?')) if t in desc)
    r['opc'] = [x for x, ok in (('peso', 'peso' in r), ('ponta a ponta', 'l2l' in r)) if not ok]
    return r


# Páginas-guia de relógio (13/11/2026): subcategorias de "Relógios" criadas para o Google e para quem está escolhendo.
# O verificador mantém cada relógio nas guias certas (põe e TIRA só estas categorias, conforme a regra abaixo).
# Guia nova: crie a subcategoria em Relógios, ponha o texto e acrescente uma linha aqui.
#   chave: (id da categoria, rótulo curto para o site, link, regra)
GUIAS = {
    'mergulho':   (24498592, 'De mergulho', '/relogios-de-mergulho', lambda r, c: r.get('agua', 0) >= 200),
    'sociais':    (24498593, 'Sociais', '/relogios-sociais', lambda r, c: 'c' not in r.get('fn', '') and 'campo' not in c and 'gmt' not in c and bool(r.get('esp')) and (
                      ('social' in c and r['esp'] <= 12.5) or (('integrado' in c or 'dia_a_dia' in c) and r['esp'] <= 11.5))),
    'automaticos': (24498594, 'Automáticos', '/relogios-automaticos', lambda r, c: r.get('tipo') in ('auto', 'manual')),
    'primeiro':   (24498595, 'Primeiro automático', '/primeiro-relogio-automatico', lambda r, c: r.get('tipo') == 'auto' and 0 < r.get('p', 0) <= 2500),
    'cronografo': (24498596, 'Cronógrafos', '/relogios-cronografo', lambda r, c: 'c' in r.get('fn', '')),
    'presente':   (24498597, 'Para presentear', '/relogios-para-presentear', lambda r, c: 37 <= r.get('diam', 0) <= 41 and 0 < r.get('p', 0) <= 5000),
    'ate2000':    (24498598, 'Até R$ 2.000', '/relogios-ate-2000-reais', lambda r, c: 0 < r.get('p', 0) <= 2000),
}
CAT_L = {'mergulho': 'm', 'campo': 'c', 'cronografo': 'k', 'gmt': 'g', 'social': 's', 'integrado': 'i', 'dia_a_dia': 'd'}
OC_L = {'trabalho': 't', 'terno': 'n', 'dia': 'd', 'viagem': 'v', 'praia': 'p', 'esporte': 'e', 'trilha': 'r', 'noite': 'j'}


def uso(r):
    """Para que o relógio foi feito (categorias) e as ocasiões, pelas mesmas regras do dossiê da descrição."""
    import relogios_dossie as RD
    fam = RD.MODELOS['produtos'].get(str(r['id']), {}).get('f')
    cats = (RD.MODELOS['familias'].get(fam) or {}).get('cats') or RD.infere_cats(r)
    oc = RD.ocasioes_chaves(r, cats, fam)
    return cats, fam, oc


def guias_de(r, cats):
    return [k for k, g in GUIAS.items() if g[3](r, cats)]


def titulo_com_diametro(n, diam):
    """Padrão do título (13/11/2026): '... Automático Mostrador Azul REF' -> '... Automático 40mm Mostrador Azul REF'.
    Devolve None se o título já tem a medida, se não há diâmetro na ficha ou se não há lugar claro para pôr."""
    if not diam or re.search(r'\d+(?:[.,]\d+)?\s?mm\b', n, re.I):
        return None
    dm = ('%g' % diam).replace('.', ',') + 'mm'
    if ' Mostrador' in n:
        return n.replace(' Mostrador', ' ' + dm + ' Mostrador', 1)
    m = re.search(r'\b(Automático|Quartzo|Solar|Eco-Drive|Corda Manual)\b', n, re.I)
    return n[:m.end()] + ' ' + dm + n[m.end():] if m else None


def lista_relogios():
    try:
        P, _ = VF.base_robo()
        L = [(p['id'], p['u']) for p in P if p['tipo'] == 'r']
        if L:
            return L
    except Exception as e:
        print('base do robô indisponível, usando a listagem:', e)
    out, pg = [], 1
    while pg < 10:
        h = CR.baixa(CR.LOJA + '/relogios-originais' + ('?pagina=%d' % pg if pg > 1 else ''))
        achou = re.findall(r'<div class="listagem-item[^"]*" data-id="(\d+)">[\s\S]{0,600}?<a href="https://www\.lojabit\.com(/[^"]+)" class="produto-sobrepor"', h)
        novos = [(int(a), b) for a, b in achou if int(a) not in [x[0] for x in out]]
        if not novos:
            break
        out += novos
        pg += 1
    return out


def main():
    so_faltas = '--faltas' in sys.argv
    L = lista_relogios()
    if len(L) < 5:
        sys.exit(f'só {len(L)} relógios encontrados — nada foi gravado')
    R = []
    for pid, u in L:
        try:
            r = le(pid, u)
        except Exception as e:
            print('erro lendo', pid, e)
            r = None
        if r:
            R.append(r)
        time.sleep(1)
    if len(R) < len(L) * .8:
        sys.exit(f'só {len(R)} de {len(L)} páginas lidas — nada foi gravado')
    for r in R:
        if r['falta']:
            print(f"falta no padrão: {r['n'][:70]} -> {', '.join(r['falta'])}")
    opc = [r for r in R if r['opc']]
    if opc:
        print(f"pode completar (opcional; o painel funciona sem): {len(opc)} relógios sem peso e/ou medida de ponta a ponta")
        if so_faltas:
            for r in opc:
                print(f"   {r['n'][:70]} -> {', '.join(r['opc'])}")
    if so_faltas:
        return
    conta = {k: 0 for k in GUIAS}
    for r in R:
        try:
            cats, fam, oc = uso(r)
            r['ct'] = ''.join(CAT_L[c] for c in cats)
            r['oi'] = ''.join(OC_L[k] for n, k, _ in oc if n == 'ideal')
            r['oc'] = ''.join(OC_L[k] for n, k, _ in oc if n == 'combina')
            r['_guias'] = guias_de(r, cats)
            for k in r['_guias']:
                conta[k] += 1 if r.get('disp') else 0
        except Exception as e:
            print('uso/ocasiões:', r.get('n', '')[:50], e)
    base = {'gerado': time.strftime('%Y-%m-%d %H:%M'), 'g': [[g[1], g[2]] for k, g in GUIAS.items() if g[0] and conta[k] >= 3], 'r': [{k: v for k, v in r.items() if k not in ('falta', 'opc') and not k.startswith('_') and v not in ('', None)} for r in R]}
    antigo = None
    try:
        antigo = json.load(open(SAIDA, encoding='utf-8'))
    except Exception:
        pass
    if antigo and antigo.get('r') == base['r'] and antigo.get('g') == base['g']:
        print(f'relógios: {len(R)} lidos, sem mudança')
        return
    json.dump(base, open(SAIDA, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'relógios: {len(R)} gravados em carrossel/relogios.json ({os.path.getsize(SAIDA)} bytes)')


if __name__ == '__main__':
    main()
