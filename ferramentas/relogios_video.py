#!/usr/bin/env python3
"""Vídeo de cada relógio (14/11/2026): 720x1280, 30 qps, 13 a 16 s, feito só com as fotos reais do relógio e os dados da ficha.

Pedido do Nevander: vídeo em cada modelo de relógio, que gere desejo; o piloto (5 Sports Field GMT) foi aprovado em 14/11/2026
("Ficou bom, pode fazer nos outros também"). Relógio novo ganha vídeo sozinho (tarefa "Carrossel: preços atualizados").

Como é feito:
  1. lê a página do relógio e escolhe as fotos pelo nome do arquivo (o padrão do site: a foto principal, depois
     "-mostrador-", "-perfil-", "-tres-quartos-", "-fundo-", "-movimento-", "-cronografo-", "-bisel-"...). Foto sem nome de
     vista (foto de ambiente, estojo) fica de fora. Só entram fotos de fundo branco.
  2. enquadra cada foto pelo recorte do relógio (onde a foto não é branca): relógio inteiro ou close que preenche a tela.
  3. escreve os textos pela ficha (carrossel/relogios.json): nome do produto SEM a marca (o vídeo também serve para as
     redes), o que o relógio tem de especial (GMT, cronógrafo, mergulho, COSC, silício, solar, reserva de marcha, safira...)
     e o convite final (original, 10% off no Pix, 6x sem juros).
  4. filma a página ferramentas/relogios_video/modelo.html (Playwright) e junta o tique-taque sintetizado no ritmo do
     movimento (6 ou 8 batidas por segundo nos mecânicos; 1 por segundo no quartzo e no solar).

Os vídeos ficam no ramo "videos" do repositório (não pesa no main); cada publicação é um commit só com os vídeos novos, e
carrossel/videos.json guarda, para cada relógio, o commit e a impressão digital dos dados. ferramentas/relogios.py copia o
commit para carrossel/relogios.json (campo "vd") e o rel.js mostra o botão "Vídeo" na foto do produto, que só baixa o vídeo
quando o cliente toca.

Uso:
  python3 ferramentas/relogios_video.py --plano [IDs]        mostra fotos escolhidas e textos (não filma)
  python3 ferramentas/relogios_video.py --quadros ID          filma 6 quadros e monta uma folha para conferir
  python3 ferramentas/relogios_video.py --gerar [IDs]         gera os vídeos (todos, ou os IDs) em SAIDA
  python3 ferramentas/relogios_video.py --novos               gera só os que faltam ou mudaram (pela impressão digital)
  python3 ferramentas/relogios_video.py --publicar            publica o que está em SAIDA no ramo "videos" e atualiza
                                                              carrossel/videos.json e carrossel/relogios.json (main)
  --saida DIR (padrão /tmp/relogios_video)
"""
import hashlib, json, math, os, re, shutil, subprocess, sys, time, wave

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
MODELO = os.path.join(AQUI, 'relogios_video')
SITE = 'https://www.lojabit.com'
CDN = 'https://cdn.awsli.com.br/2500x2500/278/278816/produto/%s/%s'
VIDEOS_JSON = os.path.join(RAIZ, 'carrossel', 'videos.json')
RELOGIOS_JSON = os.path.join(RAIZ, 'carrossel', 'relogios.json')
VERSAO = 'v2-2026-11-14'  # muda quando o desenho do vídeo muda (força refazer todos)
W, H, FPS = 720, 1280, 30

# ---------------------------------------------------------------- fotos
VISTAS = ['mostrador', 'cronografo', 'data-grande', 'bisel', 'perfil', 'tres-quartos', 'fundo', 'movimento', 'coroa',
          'fecho', 'pulseira', 'pulseiras', 'estojo']


def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)


def fotos_da_pagina(x):
    """[(arquivo, vista)] na ordem da página. vista = 'principal' para a 1ª foto, o nome da vista, ou None (sem nome)."""
    fs = []
    for tentativa in range(3):  # a loja às vezes não responde: sem isso, um tropeço vira "vídeo para refazer"
        h = sh('curl', '-s', '-m', '60', SITE + x['u']).stdout
        fs = re.findall(r'cdn\.awsli\.com\.br/(?:[0-9]+x[0-9]+|fit-in/[0-9x]+)/278/278816/produto/%d/([^"\'\s?)]+\.(?:jpg|jpeg|png|webp))' % x['id'], h)
        if fs:
            break
        time.sleep(3)
    L = []
    for f in fs:
        if f not in L:
            L.append(f)
    out = []
    for i, f in enumerate(L):
        base = re.sub(r'-[0-9a-f]{6,16}-[a-z0-9]{10}\.\w+$', '', f)
        v = next((v for v in sorted(VISTAS, key=len, reverse=True) if base.endswith('-' + v)), None)
        out.append((f, 'principal' if i == 0 else v))
    return out


def baixa(pid, f, pasta):
    """Baixa a foto (2500 px) e grava ao lado uma cópia com o fundo levado ao branco puro (é a que entra no vídeo)."""
    os.makedirs(os.path.join(pasta, 'orig'), exist_ok=True)
    org = os.path.join(pasta, 'orig', f)
    dst = os.path.join(pasta, re.sub(r'\.\w+$', '.jpg', f))
    if not os.path.exists(org) or os.path.getsize(org) < 1000:
        r = sh('curl', '-s', '-m', '120', '-o', org, '-w', '%{http_code}', CDN % (pid, f))
        if r.stdout != '200':
            raise RuntimeError('foto %s: http %s' % (f, r.stdout))
    if not os.path.exists(dst):
        from PIL import Image
        import numpy as np
        im = Image.open(org).convert('RGB')
        a = np.asarray(im).astype(np.float32)
        b = np.concatenate([a[:, :12].reshape(-1, 3), a[:, -12:].reshape(-1, 3), a[:12, :].reshape(-1, 3), a[-12:, :].reshape(-1, 3)])
        claros = b[b.min(axis=1) > 205]
        if len(claros) > len(b) * .3:
            fundo = np.median(claros, axis=0)
            a = np.clip(a * (255.0 / np.maximum(fundo, 1)), 0, 255)
        Image.fromarray(a.astype(np.uint8)).save(dst, quality=92)
    return dst


def analisa(arq):
    """Recorte do relógio na foto (frações de 0 a 1), se toca as bordas e se o fundo é branco."""
    from PIL import Image
    import numpy as np
    im = Image.open(arq).convert('RGB')
    a = np.asarray(im.resize((600, 600))).astype(np.int16)
    mn = a.min(axis=2)
    forte = mn < 200
    fraco = mn < 244
    ys, xs = np.nonzero(forte)
    if len(xs) < 50:
        return None
    x0, x1, y0, y1 = xs.min() / 600, (xs.max() + 1) / 600, ys.min() / 600, (ys.max() + 1) / 600
    ya, yb = ys.min(), ys.min() + int((ys.max() - ys.min()) * .85)  # sem os 15% de baixo (sombra)
    dir_ = np.array([np.nonzero(forte[y])[0].max() if forte[y].any() else -1 for y in range(600)])
    faixa = dir_[ya:yb + 1]
    lin = np.nonzero(faixa >= faixa.max() - 4)[0] + ya
    if len(lin) and (lin.max() - lin.min()) < (yb - ya) * .3:
        cy = float(np.median(lin)) / 600  # altura da coroa = centro da caixa
    else:
        larg = forte[ya:yb + 1].sum(axis=1)
        l2 = np.nonzero(larg > larg.max() * .85)[0] + ya
        cy = float(l2.mean()) / 600
    borda = {'e': fraco[:, :3].mean(), 'd': fraco[:, -3:].mean(), 'c': fraco[:3, :].mean(), 'b': fraco[-3:, :].mean()}
    branco = float(np.median(np.concatenate([mn[:, :6].ravel(), mn[:, -6:].ravel(), mn[:6, :].ravel(), mn[-6:, :].ravel()])))
    return {'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1, 'cx': (x0 + x1) / 2, 'cy': cy, 'bcy': (y0 + y1) / 2,
            'toca_lado': max(borda['e'], borda['d']) > .04, 'toca_cima': borda['c'] > .04, 'toca_baixo': borda['b'] > .04,
            'fundo_branco': branco > 236, 'cobre': float(fraco.mean())}


def mascara(arq, dst):
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(arq).convert('RGB').resize((1000, 1000))
    a = np.asarray(im).astype(np.int16)
    alpha = np.clip((248 - a.min(axis=2)) * 10, 0, 255).astype(np.uint8)
    m = Image.fromarray(alpha, 'L').filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new('RGBA', m.size, (255, 255, 255, 0))
    out.putalpha(m)
    out.save(dst, optimize=True)


# ---------------------------------------------------------------- textos
TIPO = {'auto': 'Automático', 'manual': 'Corda manual', 'quartzo': 'Quartzo', 'solar': 'Solar'}
ORIG = {'japones': 'japonês', 'suico': 'suíço'}
MAT = {'aco': 'Aço', 'titanio': 'Titânio', 'latao': 'Latão'}
COR = {'azul': 'azul', 'preto': 'preto', 'branco': 'branco', 'prata': 'prata', 'verde': 'verde', 'bege': 'bege', 'cinza': 'cinza',
       'azul-gelo': 'azul-gelo', 'vermelho': 'vermelho', 'champagne': 'champanhe'}


def br(v):
    return ('%.2f' % v).rstrip('0').rstrip('.').replace('.', ',')


def titulo(x):
    """Nome do produto sem a marca, sem o tipo do movimento (vai no rótulo de cima) e sem a referência, em 1 ou 2 linhas."""
    import relogios_posts as RP
    n = RP.nome_post(x, ref=False)
    n = re.sub(r'\s*\bEdi[çc][ãa]o Limitada\b', '', n, flags=re.I)
    tiraveis = r'\b(Automático|Quartzo|Solar|Eco-Drive)\b'
    n2 = re.sub(r'\s+', ' ', re.sub(tiraveis, '', n)).strip()
    m = re.match(r'^da linha 5$', n2)
    if m or n2.lower() == 'da linha 5':
        n2 = 'Linha 5'
    if len([w for w in n2.split() if not re.search(r'\d', w) or len(w) <= 3]) < 1 or len(n2) < 3:
        n2 = n
    n2 = re.sub(r'^(Automático) da linha 5$', r'Linha 5 \1', n2)
    w = n2.split()
    if len(w) == 1:
        return [esc(n2)]
    # divide em 2 linhas equilibradas; a 2ª em itálico dourado
    juntos = {('Cocktail', 'Time'), ('Powermatic', '80'), ('Pro', 'Diver'), ('Big', 'Date'), ('Multifort', 'TV'), ('Super', 'Titanium'),
              ('North', 'Sierra'), ('Vintage', 'GMT'), ('Q', 'GMT'), ('FAB', 'IV'), ('IV', 'T6'), ('Estilo', 'Militar'), ('Bisel', 'Batman'),
              ('Linha', '5'), ('5', 'Sports'), ('Zenshin', '60'), ('Sports', 'Field')}
    if len(w) == 2 and (w[0], w[1]) in juntos:
        return [esc(n2)]
    melhor, corte = 1e9, 1
    for i in range(1, len(w)):
        if (w[i - 1], w[i]) in juntos:
            continue
        d = abs(len(' '.join(w[:i])) - len(' '.join(w[i:])))
        if d < melhor:
            melhor, corte = d, i
    return [esc(' '.join(w[:corte])), '<em>%s</em>' % esc(' '.join(w[corte:]))]


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def recursos(x, F=None):
    """O que o relógio tem de especial, do mais forte para o mais fraco: [(chave, rótulo, frase)]."""
    n, fn, ct = x['n'], x.get('fn', ''), x.get('ct', '')
    R = []
    if 'g' in fn:
        R.append(('gmt', 'Ponteiro GMT', 'A hora de casa e a do destino, <b>ao mesmo tempo.</b>'))
    if 'c' in fn:
        R.append(('crono', 'Cronógrafo', 'Cronômetro no pulso: <b>inicia, para e zera</b> sem mexer na hora.'))
    if 'm' in ct and x.get('agua', 0) >= 200:
        R.append(('mergulho', '%d m de resistência à água' % x['agua'], 'Feito para o mar, com <b>bisel giratório</b> para marcar o mergulho.'))
    if re.search(r'\bCOSC\b', n):
        R.append(('cosc', 'Cronômetro certificado COSC', 'Testado por <b>15 dias, em 5 posições e 3 temperaturas</b>.'))
    if re.search(r'silicium', n, re.I):
        R.append(('silicio', 'Espiral de silício', 'Resiste ao <b>magnetismo do dia a dia</b>: celular, notebook e ímãs.'))
    if x.get('tipo') == 'solar':
        R.append(('solar', 'Solar', 'Carrega com <b>qualquer luz</b>: nada de trocar pilha.'))
    if x.get('mat') == 'titanio':
        R.append(('titanio', 'Titânio', 'Bem <b>mais leve que o aço</b> no pulso.'))
    if re.search(r'big date', n, re.I):
        R.append(('data', 'Data grande', 'A data em <b>dois discos</b>, grande e fácil de ler.'))
    res = x.get('res') or 0
    if res >= 60:
        d = res / 24
        quanto = 'mais de %d dias' % int(d) if res % 24 else '%d dias' % int(d)
        if res == 60:
            quanto = '2 dias e meio'
        R.append(('reserva', '%d horas de reserva de marcha' % res, 'Fora do pulso, <b>segue andando por %s</b>.' % quanto))
    cu = curiosidade(x, F)
    if cu:
        R.append(('curiosidade', esc(cu[0]), esc(cu[1])))
    ja = ' '.join(r[2] for r in R).lower()
    if 'd' in fn and 'dia da semana' not in ja:
        R.append(('diadata', 'Dia e data', 'O dia da semana e a data <b>sempre à vista</b>.'))
    if x.get('vidro') == 'safira' and 'safira' not in ja:
        R.append(('safira', 'Vidro de safira', 'O cristal que <b>mais resiste a riscos</b>, abaixo só do diamante.'))
    if x.get('esp') and x['esp'] <= 10.5 and 'c' not in fn:
        R.append(('fino', '%s mm de espessura' % br(x['esp']), 'Fino para <b>passar sob o punho</b> da camisa.'))
    if x.get('agua', 0) >= 100 and not any(k == 'mergulho' for k, _, _ in R):
        R.append(('agua', '%d m de resistência à água' % x['agua'], 'Pode <b>nadar</b> com ele.'))
    if 'l' in fn and 'escuro' not in ja:
        R.append(('lume', 'Brilha no escuro', 'Ponteiros e índices <b>legíveis à noite</b>.'))
    return R


def curiosidade(x, fotos=None):
    """Uma curiosidade do dossiê do relógio, sem o nome da marca e curta o bastante para a tela: (título, texto) ou None.
    Nos mecânicos pula a que só repete que ele funciona com o movimento do pulso (a cena do movimento já diz isso).
    Com as fotos (fotos), pula a que fala do fundo da caixa quando a página não tem foto do fundo: o texto não bateria com a imagem."""
    import relogios_dossie as RD
    import relogios_posts as RP
    pid = str(x['id'])
    pr = RD.MODELOS['produtos'].get(pid, {})
    F = RD.MODELOS['familias'].get(pr.get('f')) or {}
    cand = []
    u = RD.curiosidades().get(pid)
    if u:
        cand.append(u)
    cand += [tuple(v) for v in list(pr.get('vs', [])) + list(F.get('vs', [])) if tuple(v) not in cand]
    for a, t in cand:
        a2, t2 = RP.sem_marca(a).rstrip('.'), RP.sem_marca(t)
        if x.get('tipo') in ('auto', 'manual') and re.search(r'pulso', t2) and re.search(r'corda|pilha|bateria|sem pilha', a2 + ' ' + t2, re.I):
            continue
        if fotos is not None and not any(v in ('fundo', 'movimento') for f, v in fotos) and re.search(r'\bfundo\b', a2 + ' ' + t2, re.I):
            continue
        if a2 and t2 and len(t2) <= 120 and len(a2) <= 34 and not RP.tem_marca(a2 + ' ' + t2):
            return a2, t2
    return None


def linha_movimento(x):
    t = x.get('tipo')
    mat = MAT.get(x.get('mat'), '')
    k = ' · '.join([s for s in [mat, ('%d m de resistência à água' % x['agua']) if x.get('agua') else ''] if s])
    if t == 'auto':
        return ('movimento', k or 'Automático', 'Automático: funciona <b>com o movimento do pulso</b>, sem pilha.')
    if t == 'manual':
        return ('movimento', k or 'Corda manual', 'Corda manual: o ritual de <b>dar corda</b> no relógio.')
    if t == 'quartzo':
        return ('movimento', k or 'Quartzo', 'Quartzo: <b>sempre na hora</b>, sem dar corda.')
    return None


def rotulo_topo(x):
    t = TIPO.get(x.get('tipo'), '')
    if x.get('tipo') in ('auto', 'manual') and x.get('orig') in ORIG:
        t += ' ' + ORIG[x['orig']]
    return ' · '.join([s for s in [t, ('%s mm' % br(x['diam'])) if x.get('diam') else ''] if s])


# ---------------------------------------------------------------- plano (fotos + enquadramento + textos)
def enquadra(A, papel):
    """Posição da foto no palco: lado (px), centro (x, y relativos ao centro do palco) e zoom de início e fim."""
    if A['toca_lado'] and papel in ('angulo', 'verso', 'fim', 'heroi'):
        lado = 780
        cy = (.5 - A['bcy']) * lado + ((470 if papel != 'fim' else 420) - H / 2)
        return dict(lado=lado, x0=20, y0=cy, x1=-20, y1=cy, e0=1.06, e1=1.0)
    cobre = A['toca_lado'] or (papel == 'detalhe' and A['x1'] - A['x0'] > .9)
    if papel == 'zoom':  # close do mostrador tirado da foto principal
        lado = 1300 / (A['x1'] - A['x0'])
        cx, cy = (.5 - A['cx']) * lado, (.5 - A['cy']) * lado + (560 - H / 2)
        return dict(lado=round(lado), x0=cx + 40, y0=cy, x1=cx - 40, y1=cy - 30, e0=1.0, e1=1.07)
    if cobre:  # close que preenche a tela, com passeio de câmera
        lado = max(1360, 860 / (A['x1'] - A['x0']))
        cx = (.5 - A['cx']) * lado
        cy = (.5 - A['cy']) * lado + (520 - H / 2)
        lim_x = lado / 2 - W / 2 - 10  # não deixar a borda da foto aparecer dos lados
        lim_y = lado / 2 - H / 2 + 300  # embaixo o véu cobre
        def cx_ok(v): return max(-lim_x, min(lim_x, v))
        def cy_ok(v): return max(-lim_y, min(lado / 2 - (H / 2) - 0, v))
        return dict(lado=round(lado), x0=cx_ok(cx + 70), y0=cy_ok(cy + 20), x1=cx_ok(cx - 70), y1=cy_ok(cy - 40), e0=1.0, e1=1.06)
    alvo = {'heroi': 540, 'angulo': 600, 'verso': 560, 'detalhe': 640, 'fim': 470}[papel]
    yalvo = {'heroi': 470, 'angulo': 480, 'verso': 470, 'detalhe': 500, 'fim': 420}[papel]
    larg = A['x1'] - A['x0']
    lado = alvo / larg
    ref_y = A['cy'] if papel in ('heroi', 'fim', 'detalhe') else A['bcy']
    # relógio alto (perfil com a pulseira em volta): não passar de 760 px de altura
    alt = (A['y1'] - A['y0']) * lado
    if alt > 780:
        lado *= 780 / alt
    cx = (.5 - A['cx']) * lado
    cy = (.5 - ref_y) * lado + (yalvo - H / 2)
    if papel == 'heroi':
        return dict(lado=round(lado), x0=cx, y0=cy + 20, x1=cx, y1=cy, e0=1.14, e1=1.0)
    if papel == 'fim':
        return dict(lado=round(lado), x0=cx - 10, y0=cy - 20, x1=cx, y1=cy, e0=1.12, e1=1.0)
    if papel == 'angulo':
        return dict(lado=round(lado), x0=cx + 50, y0=cy, x1=cx - 20, y1=cy + 10, e0=1.08, e1=1.0, r0=-3, r1=0)
    return dict(lado=round(lado), x0=cx, y0=cy + 10, x1=cx, y1=cy - 10, e0=1.0, e1=1.07)


def plano(x, pasta, F=None):
    """Monta o plano do vídeo: cenas (foto, papel, enquadramento, textos e tempos)."""
    pid = str(x['id'])
    F = F if F is not None else fotos_da_pagina(x)
    F0 = list(F)
    if not F:
        raise RuntimeError('a página não tem fotos')
    an = {}

    def pega(vistas, usadas):
        for v in vistas:
            for f, vf in F:
                if vf == v and f not in usadas:
                    arq = baixa(pid, f, pasta)
                    if f not in an:
                        an[f] = analisa(arq)
                    if an[f] and an[f]['fundo_branco']:
                        return f, v
        return None, None

    # foto sem nome de vista (fora a principal): vira candidata pelo recorte, com prioridade menor que as nomeadas
    if not any(v for f, v in F if v and v != 'principal'):
        novo = []
        for f, v in F:
            if v is None:
                A = analisa(baixa(pid, f, pasta))
                an[f] = A
                if A and A['fundo_branco']:
                    larg, alt = A['x1'] - A['x0'], A['y1'] - A['y0']
                    v = '_detalhe' if (A['toca_lado'] or A['cobre'] > .42) else ('_perfil' if larg > alt * 1.25 else '_angulo')
            novo.append((f, v))
        F = novo
    usadas = []
    fp, _ = pega(['principal'], usadas)
    if not fp:
        raise RuntimeError('foto principal sem fundo branco')
    usadas.append(fp)
    mec = x.get('tipo') in ('auto', 'manual')
    fd, vd = pega(['mostrador', 'cronografo', 'data-grande', 'bisel', '_detalhe'], usadas)
    if fd:
        usadas.append(fd)
    fa, va = pega(['perfil', 'tres-quartos', 'bisel', 'coroa', 'cronografo', 'data-grande', '_angulo', '_perfil'], usadas)
    if fa:
        usadas.append(fa)
    fv = vv = None
    if mec and 'f' in x.get('fn', ''):
        fv, vv = pega(['movimento', 'fundo'], usadas)
        if fv:
            usadas.append(fv)
    ff, vf_ = pega(['tres-quartos'], usadas)
    if not ff:
        ff = fp

    R = recursos(x, F0)
    mov = linha_movimento(x)
    fracos = ('safira', 'fino', 'agua', 'lume', 'diadata')
    fortes = [r for r in R if r[0] not in fracos]
    # cena 2 e 3: o que o relógio tem de mais especial; se só tiver uma coisa forte, a 3 fala do movimento
    textos = (fortes + [r for r in R if r[0] in fracos])[:2]
    if len(fortes) < 2 and mov and not fv:
        textos = textos[:1] + [mov]
    if fv:  # fundo transparente com foto do verso: a cena 4 mostra o movimento
        k = 'Fundo transparente' + ((' · %d m' % x['agua']) if x.get('agua') else '')
        textos = (textos + [None, None])[:2] + [('verso', k, 'Automático: funciona <b>com o movimento do pulso</b>, e dá para vê-lo trabalhando.')]
        textos = [t for t in textos if t]
    textos = [t for t in textos if t]
    if not textos and mov:
        textos = [mov]

    fim = [None]

    def do_fundo(tx, f, papel):
        """Curiosidade que fala do fundo da caixa vai com a foto do fundo, quando a página tem (e ela ainda não foi usada)."""
        if tx and tx[0] == 'curiosidade' and not fv and re.search(r'\bfundo\b', tx[1] + ' ' + tx[2], re.I):
            f2, _ = pega(['fundo', 'movimento'], usadas)
            if f2:
                usadas.append(f2)
                if ff == fp and dict(F).get(f) == 'tres-quartos':
                    fim[0] = f  # a foto de três quartos que sobrou fecha o vídeo
                return f2, 'verso'
        return f, papel

    selo = 'Edição limitada' if re.search(r'edi[çc][ãa]o limitada', x['n'], re.I) else ''
    cenas = []
    cenas.append(dict(f=fp, papel='heroi', txt=dict(selo=selo, k=esc(rotulo_topo(x)), t=titulo(x), top=930 if not selo else 900)))
    if textos:
        f2, p2 = do_fundo(textos[0], fd or fp, 'detalhe' if fd else 'zoom')
        cenas.append(dict(f=f2, papel=p2, txt=dict(k=esc(textos[0][1]), l=textos[0][2], top=960)))
    if fa and len(textos) > 1 and textos[1][0] != 'verso':
        f3, p3 = do_fundo(textos[1], fa, 'angulo')
        cenas.append(dict(f=f3, papel=p3, txt=dict(k=esc(textos[1][1]), l=textos[1][2], top=960)))
    elif len(textos) > 1 and textos[1][0] != 'verso':
        cenas.append(dict(f=ff if ff != fp else fp, papel='angulo' if ff != fp else 'detalhe', txt=dict(k=esc(textos[1][1]), l=textos[1][2], top=960)))
        if ff != fp:
            ff = fp
    if fv and textos and textos[-1][0] == 'verso':
        cenas.append(dict(f=fv, papel='verso', txt=dict(k=esc(textos[-1][1]), l=textos[-1][2], top=960)))
    frete = ' · frete grátis' if x.get('p', 0) >= 450 else ''
    if fim[0] and ff == fp:
        ff = fim[0]
    cenas.append(dict(f=ff, papel='fim', txt=dict(fim=True, k='Original · caixa, manual e certificado', t=['10% off <em>no Pix</em>'],
                                                    l='ou até 6x sem juros' + frete, top=800)))
    cenas = [c for c in cenas if c]
    # tempos: 3,7 s por cena com 0,5 s de transição; a última fica 3,3 s
    t = 0.0
    for i, c in enumerate(cenas):
        c['a'] = round(t, 2)
        c['b'] = round(t + 3.7, 2)
        t += 3.2
    cenas[-1]['b'] = round(cenas[-1]['a'] + 3.4, 2)
    dur = cenas[-1]['b']
    for i, c in enumerate(cenas):
        A = an.get(c['f']) or analisa(baixa(pid, c['f'], pasta))
        an[c['f']] = A
        c.update(enquadra(A, c['papel']))
        c['f'] = re.sub(r'\.\w+$', '.jpg', c['f'])  # a cópia com o fundo branco puro
        c['veu'] = 640 if c['txt'].get('fim') else (560 if i == 0 else 520)
    return {'id': pid, 'dur': dur, 'cenas': cenas, 'bps': bps(x), 'vistas': [(c['papel'], c['f']) for c in cenas], 'h': impressao(x, F0)}


def bps(x):
    if x.get('tipo') in ('auto', 'manual'):
        return round((x.get('freq') or 21600) / 3600)
    return 1


CAMPOS = ('n', 'tipo', 'orig', 'diam', 'fn', 'ct', 'agua', 'res', 'freq', 'vidro', 'esp', 'mat')


def impressao(x, F=None):
    """Impressão digital barata do vídeo: fotos da página (nomes), campos da ficha usados nos textos, curiosidade do dossiê,
    frete no texto final, VERSAO e o modelo. Muda quando o vídeo precisa ser refeito; não precisa baixar foto nem filmar."""
    F = F if F is not None else fotos_da_pagina(x)
    if not F:
        raise RuntimeError('não li as fotos da página')
    cu = curiosidade(x, F)
    corpo = json.dumps({'f': [f for f, v in F], 'x': {k: x.get(k) for k in CAMPOS}, 'cu': cu, 'fr': x.get('p', 0) >= 450, 'v': VERSAO},
                       sort_keys=True, ensure_ascii=False)
    tpl = open(os.path.join(MODELO, 'modelo.html'), 'rb').read()
    return hashlib.sha1(corpo.encode() + tpl).hexdigest()[:12]


# ---------------------------------------------------------------- som
def tique(dst, dur, bps_):
    import numpy as np
    sr = 44100
    n = int(sr * dur)
    x = np.zeros(n)
    rng = np.random.default_rng(7)

    def burst(freq, tau, amp):
        m = int(sr * .05)
        t = np.arange(m) / sr
        F = np.fft.rfft(rng.standard_normal(m))
        f = np.fft.rfftfreq(m, 1 / sr)
        F *= np.exp(-((f - freq) / (freq * .35)) ** 2)
        y = np.fft.irfft(F, m)
        y = y / np.max(np.abs(y))
        return amp * y * np.exp(-t / tau) * (1 - np.exp(-t / .0004))
    if bps_ <= 1:  # quartzo: um toque seco por segundo
        for k in range(int(dur) + 1):
            i = int(k * sr)
            b = burst(3200, .006, .7)
            x[i:i + len(b)] += b[:max(0, n - i)]
    else:
        for k in range(int(dur * bps_)):
            i = int(k / bps_ * sr)
            b = burst(4300 if k % 2 == 0 else 3600, .007 if k % 2 == 0 else .009, .55 if k % 2 == 0 else .42)
            x[i:i + len(b)] += b[:max(0, n - i)]
    fade = np.ones(n)
    a, z = int(sr * .5), int(sr * .9)
    fade[:a] = np.linspace(0, 1, a)
    fade[-z:] = np.linspace(1, 0, z)
    x = x * fade * .5
    w = wave.open(dst, 'wb')
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
    w.close()


# ---------------------------------------------------------------- filmagem
def prepara(P, pasta):
    """Copia modelo, fontes e máscaras para a pasta de trabalho e grava a página do vídeo."""
    for f in os.listdir(os.path.join(MODELO, 'fontes')):
        shutil.copy(os.path.join(MODELO, 'fontes', f), pasta)
    D = {'cenas': []}
    for i, c in enumerate(P['cenas']):
        m = 'm_%s.png' % re.sub(r'\.\w+$', '', c['f'])
        if not os.path.exists(os.path.join(pasta, m)):
            mascara(os.path.join(pasta, c['f']), os.path.join(pasta, m))
        d = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in c.items() if k not in ('papel',)}
        d['m'] = m
        D['cenas'].append(d)
    html = open(os.path.join(MODELO, 'modelo.html')).read().replace('__DADOS__', json.dumps(D, ensure_ascii=False))
    pag = os.path.join(pasta, 'video.html')
    open(pag, 'w').write(html)
    return pag


def filma(P, pasta, saida):
    pag = prepara(P, pasta)
    dur = P['dur']
    cortes = [str(round(t, 2)) for t in [c['a'] + .25 for c in P['cenas'][1:]]]
    mudo = os.path.join(pasta, 'mudo.mp4')
    r = sh('node', os.path.join(MODELO, 'filma.js'), pag, mudo, str(dur), *cortes, cwd=pasta)
    if r.returncode:
        raise RuntimeError('filmagem: ' + (r.stderr or r.stdout)[-400:])
    som = os.path.join(pasta, 'tique.wav')
    tique(som, dur, P['bps'])
    os.makedirs(saida, exist_ok=True)
    tmp = os.path.join(saida, '%s.tmp.mp4' % P['id'])
    r = sh('ffmpeg', '-y', '-loglevel', 'error', '-i', mudo, '-i', som, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
           '-c:a', 'aac', '-b:a', '64k', '-ac', '1', '-shortest', '-movflags', '+faststart', tmp)
    if r.returncode:
        raise RuntimeError('ffmpeg: ' + r.stderr[-300:])
    os.replace(tmp, os.path.join(saida, '%s.mp4' % P['id']))
    # capa: o instante em que o nome aparece
    sh('ffmpeg', '-y', '-loglevel', 'error', '-ss', '1.9', '-i', os.path.join(saida, '%s.mp4' % P['id']), '-frames:v', '1',
       '-vf', 'scale=540:960', '-q:v', '5', os.path.join(saida, '%s.jpg' % P['id']))
    json.dump({'h': P['h'], 'dur': dur}, open(os.path.join(saida, '%s.json' % P['id']), 'w'))
    return os.path.join(saida, '%s.mp4' % P['id'])


# ---------------------------------------------------------------- publicação
def le_videos():
    try:
        return json.load(open(VIDEOS_JSON))
    except Exception:
        return {'_sobre': 'Vídeo de cada relógio (ferramentas/relogios_video.py): s = commit do ramo "videos" que tem v/<id>.mp4 e v/<id>.jpg; h = impressão digital dos dados do vídeo.', 'v': {}}


def publica(saida):
    """Commit no ramo "videos" só com os vídeos novos (cada commit fica pequeno para a CDN), depois carrossel/videos.json no main."""
    ids = sorted(f[:-4] for f in os.listdir(saida) if f.endswith('.mp4') and not f.endswith('.tmp.mp4'))
    if not ids:
        print('nada para publicar')
        return
    V = le_videos()
    wt = os.path.join('/tmp', 'lojabit-videos')
    sh('git', '-C', RAIZ, 'worktree', 'remove', '--force', wt)
    shutil.rmtree(wt, ignore_errors=True)
    tem = sh('git', '-C', RAIZ, 'ls-remote', '--heads', 'origin', 'videos').stdout.strip()
    if tem:
        sh('git', '-C', RAIZ, 'fetch', '-q', '--depth', '1', 'origin', 'videos:refs/remotes/origin/videos')
        r = sh('git', '-C', RAIZ, 'worktree', 'add', '-f', '--detach', wt, 'origin/videos')
    else:
        r = sh('git', '-C', RAIZ, 'worktree', 'add', '-f', '--detach', wt)
        sh('git', '-C', wt, 'checkout', '-q', '--orphan', 'videos-novo')
    if r.returncode:
        raise RuntimeError(r.stderr)
    # lotes de até 8 vídeos; cada commit tem só o seu lote (os anteriores continuam no histórico do ramo)
    lotes = [ids[i:i + 8] for i in range(0, len(ids), 8)]
    for lote in lotes:
        sh('git', '-C', wt, 'rm', '-rq', '--cached', '.')
        for f in os.listdir(wt):
            if f != '.git':
                p = os.path.join(wt, f)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        os.makedirs(os.path.join(wt, 'v'), exist_ok=True)
        open(os.path.join(wt, 'LEIA.md'), 'w').write('Vídeos dos relógios da @LOJABIT (ferramentas/relogios_video.py no ramo main). Cada commit tem só os vídeos daquele lote; o site usa o commit de cada vídeo (carrossel/videos.json).\n')
        for i in lote:
            shutil.copy(os.path.join(saida, i + '.mp4'), os.path.join(wt, 'v', i + '.mp4'))
            shutil.copy(os.path.join(saida, i + '.jpg'), os.path.join(wt, 'v', i + '.jpg'))
        sh('git', '-C', wt, 'add', '-A')
        r = sh('git', '-C', wt, 'commit', '-q', '-m', 'Vídeos: ' + ', '.join(lote) + '\n\nCo-Authored-By: Claude <noreply@anthropic.com>')
        if r.returncode:
            raise RuntimeError(r.stderr or r.stdout)
        s = sh('git', '-C', wt, 'rev-parse', 'HEAD').stdout.strip()
        B = base()
        for i in lote:
            info = json.load(open(os.path.join(saida, i + '.json')))
            try:
                h = impressao(B[i]) if i in B else info['h']
            except Exception:
                h = info['h']
            V['v'][i] = {'s': s, 'h': h, 'dur': info['dur']}
        print('lote', s[:7], len(lote), 'vídeos')
    r = sh('git', '-C', wt, 'push', '-q', 'origin', 'HEAD:refs/heads/videos')
    if r.returncode:
        raise RuntimeError('push do ramo videos: ' + r.stderr)
    sh('git', '-C', RAIZ, 'worktree', 'remove', '--force', wt)
    json.dump(V, open(VIDEOS_JSON, 'w'), ensure_ascii=False, indent=1, sort_keys=True)
    marca_relogios(V)
    print('videos.json:', len(V['v']), 'relógios com vídeo')


def marca_relogios(V=None):
    """Copia o commit do vídeo para carrossel/relogios.json (campo vd), sem reler as páginas."""
    V = V or le_videos()
    d = json.load(open(RELOGIOS_JSON))
    for x in d['r']:
        v = V['v'].get(str(x['id']))
        if v:
            x['vd'] = v['s']
            if v.get('dur'):
                x['vt'] = int(round(v['dur']))
        else:
            x.pop('vd', None)
            x.pop('vt', None)
    json.dump(d, open(RELOGIOS_JSON, 'w'), ensure_ascii=False, separators=(',', ':'))


# ---------------------------------------------------------------- linha de comando
def base():
    return {str(x['id']): x for x in json.load(open(RELOGIOS_JSON))['r']}


def main():
    a = sys.argv[1:]
    saida = a[a.index('--saida') + 1] if '--saida' in a else '/tmp/relogios_video'
    trab = os.path.join(saida, '_trabalho')
    ids = [i for i in a if i.isdigit()]
    B = base()
    import relogios_posts as RP
    if '--publicar' in a:
        publica(saida)
        return
    alvo = ids or list(B)
    if '--novos' in a:  # só lê a lista de fotos de cada página; baixa e filma só o que mudou
        V = le_videos()['v']
        alvo = []
        for i in B:
            try:
                h = impressao(B[i])
            except Exception as e:
                print('não li a página:', i, e)
                continue
            if V.get(i, {}).get('h') != h:
                alvo.append(i)
        print('relógios sem vídeo ou com vídeo para refazer:', len(alvo), alvo)
    for i in alvo:
        x = B[i]
        pasta = os.path.join(trab, i)
        os.makedirs(pasta, exist_ok=True)
        try:
            P = plano(x, pasta)
        except Exception as e:
            print('sem vídeo:', i, x['n'][:60], '->', e)
            continue
        txt = ' '.join(re.sub(r'<[^>]+>', '', ' '.join([c['txt'].get('k', ''), ' '.join(c['txt'].get('t', [])), c['txt'].get('l', ''), c['txt'].get('selo', '')])) for c in P['cenas'])
        if RP.tem_marca(txt):
            print('PROBLEMA', i, 'o texto cita a marca:', RP.tem_marca(txt))
            continue
        if '--plano' in a:
            print('==', i, x['n'][:70], '| %.1f s | %d bps' % (P['dur'], P['bps']))
            for c in P['cenas']:
                print('   %-8s %-60s lado=%-5d %s' % (c['papel'], c['f'][-60:], c['lado'], re.sub(r'<[^>]+>', '', ' / '.join([c['txt'].get('selo', ''), c['txt'].get('k', ''), ' '.join(c['txt'].get('t', [])), c['txt'].get('l', '')]))))
            continue
        if '--quadros' in a:
            pag = prepara(P, pasta)
            ts = []
            for c in P['cenas']:
                ts += [c['a'] + 1.6]
            ts.append(P['dur'] - .2)
            r = sh('node', os.path.join(MODELO, 'quadros.js'), pag, *[str(round(t, 2)) for t in ts], cwd=pasta)
            from PIL import Image
            ims = [Image.open(os.path.join(pasta, 'q-%s.jpg' % str(round(t, 2)))) for t in ts]
            folha = Image.new('RGB', (len(ims) * 370, 650), '#333')
            for k, im in enumerate(ims):
                folha.paste(im.resize((360, 640)), (k * 370, 5))
            dst = os.path.join(saida, 'quadros_%s.jpg' % i)
            os.makedirs(saida, exist_ok=True)
            folha.save(dst, quality=85)
            print(dst)
            continue
        t0 = time.time()
        try:
            out = filma(P, pasta, saida)
        except Exception as e:
            print('ERRO', i, e)
            continue
        print('ok', i, '%.1f s' % P['dur'], '%.1f MB' % (os.path.getsize(out) / 1e6), '%.0f s de filmagem' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
