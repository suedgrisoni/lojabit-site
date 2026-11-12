#!/usr/bin/env python3
"""Dados dos carrosséis da página do produto ("Parecidos com o X" e "Com a mesma proposta"), código src/1799001.html.

- carrossel/base.json  (feito pelo Claude a partir da base de perfumes): para cada produto, as listas p (parecidos) e m (mesma
  proposta), o nome curto (n), a página "Parecidos com..." (g) e o estilo (t); e, para cada produto citado, [nome curto, "Marca · tipo"].
- Cartão: [nome curto, link, foto, preço, Pix, "Marca · tipo", preço antigo (promoção) ou null, 1 se "a partir de", nome completo].
- Este script lê a listagem pública da loja (/encontre-seu-perfume, ~17 páginas de 40) para pegar link, foto e PREÇO ATUAL
  (preço "a partir de", promoção e Pix) e grava carrossel/p/<id>.json, um arquivo pequeno por produto.
  Produto que não aparece na listagem (fora do ar ou sem estoque) sai dos carrosséis sozinho.
- Depois do commit + push dos dados, `python3 ferramentas/carrossel.py versao` grava carrossel/v.json com o commit dos dados;
  o site lê o v.json pelo raw.githubusercontent (cache de ~5 min) e os dados pelo jsDelivr preso a esse commit.

Uso:  python3 ferramentas/carrossel.py atualizar   (lê a loja e grava carrossel/p/)
      git add carrossel && git commit -m "Carrossel: preços AAAA-MM-DD HH:MM" && git push
      python3 ferramentas/carrossel.py versao      (grava carrossel/v.json com o commit acima)
      git add carrossel/v.json && git commit -m "Carrossel: versão" && git push
"""
import json, os, re, sys, subprocess, time, html, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(RAIZ, 'carrossel')
LOJA = 'https://www.lojabit.com'
ITEM = re.compile(r'<div class="listagem-item([^"]*)"\s+data-id="(\d+)">(.*?)(?=<div class="listagem-item|<div class="pagination|</section|<footer)', re.S)


def baixa(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; lojabit-carrossel/1.0)'})
    for t in range(3):
        try:
            return urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'ignore')
        except Exception:
            time.sleep(5 * (t + 1))
    return ''


def reais(s):
    m = re.search(r'R\$\s*([\d.]+,\d{2})', s or '')
    return float(m.group(1).replace('.', '').replace(',', '.')) if m else None


def listagem():
    # a mesma leitura serve para carrossel_novos, carrossel_listas e atualizar na mesma rodada (guardada por 20 min)
    import tempfile
    cache = os.path.join(tempfile.gettempdir(), 'lojabit_listagem.json')
    try:
        if time.time() - os.path.getmtime(cache) < 1200:
            c = json.load(open(cache, encoding='utf-8'))
            if len(c) >= 200:
                return c
    except Exception:
        pass
    c = _listagem()
    if len(c) >= 200:
        json.dump(c, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
    return c


def _listagem():
    cards = {}
    for pg in range(1, 60):
        h = baixa(f'{LOJA}/encontre-seu-perfume' + (f'?pagina={pg}' if pg > 1 else ''))
        achou = 0
        for classes, pid, bloco in ITEM.findall(h):
            achou += 1
            url = re.search(r'<a href="([^"]+)" class="produto-sobrepor"(?: title="([^"]*)")?', bloco)
            img = re.search(r'<img[^>]+src="([^"]+)"', bloco)
            promo = re.search(r'class="preco-promocional[^"]*"[^>]*>([^<]+)<', bloco)
            venda = re.search(r'class="preco-venda[^"]*"[^>]*>([^<]+)<', bloco)
            pix = re.search(r'desconto-a-vista[^>]*>\s*ou\s*<strong[^>]*>([^<]+)<', bloco)
            preco = reais(promo.group(1)) if promo else reais(venda.group(1) if venda else '')
            if not (url and preco):
                continue
            cards[pid] = {'u': url.group(1).replace(LOJA, ''), 'i': img.group(1) if img else '', 'p': preco, 't': html.unescape(url.group(2) or ''),
                          'd': reais(venda.group(1)) if promo and venda else None, 'x': reais(pix.group(1)) if pix else None,
                          'a': 'preco-a-partir' in bloco, 'cats': sorted(set(re.findall(r'prod-cat-(\d+)', classes)))}
        if not achou:
            break
        time.sleep(1.5)
    return cards


def atualizar():
    base = json.load(open(os.path.join(D, 'base.json'), encoding='utf-8'))
    cards = listagem()
    if len(cards) < 200:
        sys.exit(f'a listagem veio com {len(cards)} produtos — algo errado na loja; nada foi gravado')
    os.makedirs(os.path.join(D, 'p'), exist_ok=True)
    feitos = set()
    for k, v in base['l'].items():
        def cartoes(ids):
            out = []
            for x in ids:
                c, b = cards.get(x), base['c'].get(x)
                if c and b:
                    out.append([b[0], c['u'], c['i'], c['p'], c['x'], b[1], c['d'], 1 if c['a'] else 0, c['t']])
            return out
        p, m = cartoes(v['p']), cartoes(v['m'])
        if k not in cards or (not p and not m):
            continue
        dado = {'n': v['n'], 'g': v['g'], 't': v['t'], 'p': p, 'm': m}
        caminho = os.path.join(D, 'p', f'{k}.json')
        novo = json.dumps(dado, ensure_ascii=False, separators=(',', ':'))
        if not os.path.exists(caminho) or open(caminho, encoding='utf-8').read() != novo:
            open(caminho, 'w', encoding='utf-8').write(novo)
        feitos.add(f'{k}.json')
    for f in os.listdir(os.path.join(D, 'p')):
        if f not in feitos:
            os.remove(os.path.join(D, 'p', f))
    print(f'listagem: {len(cards)} produtos | carrosséis gravados: {len(feitos)}')


def versao():
    sha = subprocess.run(['git', 'log', '-1', '--format=%H', '--', 'carrossel/p'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    if not sha:
        sys.exit('carrossel/p ainda não tem commit')
    pend = subprocess.run(['git', 'status', '--porcelain', '--', 'carrossel/p'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    if pend:
        sys.exit('carrossel/p tem mudanças fora do commit — faça o commit e o push antes')
    json.dump({'h': sha, 'em': time.strftime('%Y-%m-%d %H:%M')}, open(os.path.join(D, 'v.json'), 'w'))
    print('v.json ->', sha)


if __name__ == '__main__':
    {'atualizar': atualizar, 'versao': versao}[sys.argv[1] if len(sys.argv) > 1 else 'atualizar']()
