#!/usr/bin/env python3
"""Testa uma mudança ANTES de publicar: abre páginas do site ao vivo duas vezes —
A = como está no ar; B = igual, mas com os arquivos do jsDelivr trocados pelos de dist/ deste computador —
e compara o que aparece (elementos visíveis, textos, classes do <html>, erros de JavaScript e do console).

Uso:  python3 build.py && python3 ferramentas/testa.py [home categoria produto sacola busca ...]
Precisa: pip install playwright (e o Chromium do Playwright). Leva ~1 min por página.
Diferenças pequenas em animações (faixa do topo, botão do WhatsApp) e em coisas que carregam depois
(relógios da home, tamanhos nos cartões) acontecem sozinhas entre duas cargas; o teste roda A duas vezes para mostrar esse ruído.
"""
import asyncio, os, sys, time, json, re
from playwright.async_api import async_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'https://www.lojabit.com'
PAGS = {'home': '/', 'categoria': '/perfumes-arabes', 'produto': '/perfume-arabe-khamrah-dukhan-lattafa-eau-de-parfum',
        'sacola': '/carrinho/index', 'busca': '/buscar?q=lattafa', 'decants': '/decants', 'marca': '/marca/lattafa.html',
        'pagina': '/pagina/fast-delivery.html', 'conta': '/conta/login'}
ARQ = re.compile(r'^https://(?:cdn|fastly)\.jsdelivr\.net/gh/suedgrisoni/lojabit-site@[^/]+/dist/(cab\.css|cab\.js|rod\.css|rod\.js)$')
PROXY = {'server': os.environ['HTTPS_PROXY']} if os.environ.get('HTTPS_PROXY') else None
LER = r"""() => { const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0; };
  const cont = {}; for (const e of document.body.querySelectorAll('*')) { if (!vis(e)) continue;
    const k = e.tagName.toLowerCase() + (e.classList.length ? '.' + [...e.classList].sort().join('.') : ''); cont[k] = (cont[k] || 0) + 1; }
  return {cont, html: document.documentElement.className, txt: document.body.innerText.split('\n').map(s => s.trim()).filter(Boolean),
    e3: [!!window.lbE3c, !!window.lbE3r, document.querySelectorAll('head style[data-lbv]').length], h: document.documentElement.scrollHeight}; }"""


async def carga(b, disp, path, local):
    kw = {'cel': {'viewport': {'width': 390, 'height': 844}, 'device_scale_factor': 3, 'is_mobile': True, 'has_touch': True,
                  'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'},
          'pc': {'viewport': {'width': 1440, 'height': 900}}}[disp]
    ctx = await b.new_context(**kw); pg = await ctx.new_page(); erros = []; cons = []; usados = []
    pg.on('pageerror', lambda e: erros.append(str(e)[:160]))
    pg.on('console', lambda m: cons.append(m.text[:160]) if m.type == 'error' and 'NSTheme' not in m.text else None)
    if local:
        async def rota(route):
            m = ARQ.match(route.request.url)
            if not m: return await route.continue_()
            usados.append(m.group(1))
            corpo = open(os.path.join(RAIZ, 'dist', m.group(1)), 'rb').read()
            ct = 'text/css; charset=utf-8' if m.group(1).endswith('.css') else 'application/javascript; charset=utf-8'
            await route.fulfill(status=200, body=corpo, headers={'content-type': ct, 'access-control-allow-origin': '*'})
        await pg.route('**/*', rota)
    await pg.goto(f'{B}{path}{"&" if "?" in path else "?"}nc={int(time.time() * 1000)}', wait_until='load', timeout=150000)
    await pg.wait_for_timeout(5000)
    r = await pg.evaluate(LER); r.update(erros=erros, console=sorted(set(cons)), usados=sorted(set(usados)))
    await ctx.close()
    return r


def diferencas(a, b, a2=None):
    """O que muda de A para B. Com a2 (outra carga igual a A), só conta o que muda tanto de A quanto de A2 para B."""
    def dif(x, y):
        ks = set(x['cont']) | set(y['cont'])
        cont = {k: (x['cont'].get(k, 0), y['cont'].get(k, 0)) for k in ks if x['cont'].get(k, 0) != y['cont'].get(k, 0)}
        sx, sy = set(x['txt']), set(y['txt'])
        cls = set(x['html'].split()) ^ set(y['html'].split())
        return cont, sx - sy, sy - sx, cls
    c, some, aparece, cls = dif(a, b)
    if a2 is not None:
        c2, some2, aparece2, cls2 = dif(a2, b)
        c = {k: v for k, v in c.items() if k in c2}; some &= some2; aparece &= aparece2; cls &= cls2
    out = []
    if c: out.append('elementos: ' + ', '.join(f'{k} {x}->{y}' for k, (x, y) in sorted(c.items(), key=lambda kv: -abs(kv[1][0] - kv[1][1]))[:6]))
    if some: out.append('texto some: ' + ' | '.join(sorted(some)[:4])[:200])
    if aparece: out.append('texto aparece: ' + ' | '.join(sorted(aparece)[:4])[:200])
    if cls: out.append(f'classes do html: {cls}')
    return out


async def main():
    nomes = [a for a in sys.argv[1:] if a in PAGS] or ['home', 'categoria', 'produto', 'sacola', 'busca']
    async with async_playwright() as p:
        b = await p.chromium.launch(proxy=PROXY)
        for n in nomes:
            for disp in ('cel', 'pc'):
                a = await carga(b, disp, PAGS[n], False); a2 = await carga(b, disp, PAGS[n], False); bb = await carga(b, disp, PAGS[n], True)
                ruido = diferencas(a, a2); dif = diferencas(a, bb, a2)
                probl = []
                if bb['erros']: probl.append('ERROS JS: ' + ' | '.join(bb['erros'][:3]))
                if set(bb['console']) - set(a['console']): probl.append('console novo: ' + ' | '.join(sorted(set(bb['console']) - set(a['console']))[:3]))
                if bb['usados'] != ['cab.css', 'cab.js', 'rod.css', 'rod.js']: probl.append(f"arquivos locais usados: {bb['usados']}")
                if bb['e3'][:2] != [True, True]: probl.append(f"marcas lbE3c/lbE3r: {bb['e3']}")
                print(f"{n:9} {disp}: " + ('OK' if not dif and not probl else 'VER') + f"  (ruído entre duas cargas iguais: {len(ruido)} item(ns))")
                for x in probl + dif: print('    - ' + x)
        await b.close()

asyncio.run(main())
