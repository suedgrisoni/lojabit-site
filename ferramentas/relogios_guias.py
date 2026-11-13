#!/usr/bin/env python3
"""Páginas-guia de relógio (13/11/2026): subcategorias de "Relógios" como "Relógios de Mergulho" e "Relógios Sociais".

- Regras de quem entra em cada guia: ferramentas/relogios.py (GUIAS), calculadas da ficha técnica e do preço.
- Textos: ferramentas/relogios_guias.json.
- O verificador diário chama sincroniza(): cada relógio fica exatamente nas guias em que a regra manda
  (põe a que falta e TIRA a que deixou de valer, por exemplo quando o preço passa de R$ 2.000). Só mexe nas categorias-guia;
  as outras categorias do produto nunca mudam.

Uso (precisa do token da API em ~/.lb/li_token):
  python3 ferramentas/relogios_guias.py --criar        cria a categoria que faltar e regrava texto e SEO de todas
  python3 ferramentas/relogios_guias.py --sincronizar  põe/tira os relógios das guias (o verificador faz isso todo dia)
"""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
RELOGIOS = 24410277  # categoria "Relógios"
TEXTOS = json.load(open(os.path.join(AQUI, 'relogios_guias.json'), encoding='utf-8'))


def criar(req):
    import relogios as RL
    for k, g in RL.GUIAS.items():
        t = TEXTOS[k]; cid = g[0]
        if not cid:
            # a API monta o link pelo nome e troca letra acentuada por "-" ("rel-gios"): cria sem acento e renomeia depois
            import unicodedata
            sem = ''.join(ch for ch in unicodedata.normalize('NFD', t['nome']) if unicodedata.category(ch) != 'Mn').replace('$', '')
            c, r = req('POST', '/categoria', {'nome': sem, 'descricao': t['html'], 'categoria_pai': f'/api/v1/categoria/{RELOGIOS}'})
            if c not in (200, 201):
                print(k, 'ERRO ao criar', c, r[:200]); continue
            cid = json.loads(r)['id']
            print(k, 'CRIADA: ponha o id', cid, 'em GUIAS (ferramentas/relogios.py)')
        c, r = req('GET', f'/categoria/{cid}')
        cat = json.loads(r)
        if cat.get('descricao') != t['html'] or cat.get('nome') != t['nome']:
            c, r2 = req('PUT', f'/categoria/{cid}', {'nome': t['nome'], 'descricao': t['html'], 'categoria_pai': f'/api/v1/categoria/{RELOGIOS}'})
            print(k, 'texto', c)
        seo = (cat.get('seo') or '').rstrip('/').split('/')[-1]
        if seo:
            c, r3 = req('GET', f'/seo/{seo}'); s = json.loads(r3) if c == 200 else {}
            if s.get('title') != t['seo_title'] or s.get('description') != t['seo_description']:
                c, r4 = req('PUT', f'/seo/{seo}', {'title': t['seo_title'], 'description': t['seo_description']})
                print(k, 'seo', c, r4[:120] if c not in (200, 204) else '')
        print(k, cid, cat.get('url'))


def sincroniza(req, R, feito=None):
    """R = relógios lidos por relogios.le() (com 'id' e os campos da ficha). Devolve a lista de avisos."""
    import relogios as RL
    ids = {g[0]: k for k, g in RL.GUIAS.items() if g[0]}
    avisos = []
    for r in R:
        try:
            cats, _, _ = RL.uso(r)
            quer = {RL.GUIAS[k][0] for k in RL.guias_de(r, cats) if RL.GUIAS[k][0]}
        except Exception as e:
            avisos.append(f"{r.get('n', '')[:50]}: guias não calculadas ({e})"); continue
        c, t = req('GET', f"/produto/{r['id']}")
        if c != 200:
            avisos.append(f"{r.get('n', '')[:50]}: leitura {c}"); continue
        atuais = [int(x.rstrip('/').split('/')[-1]) for x in json.loads(t).get('categorias') or []]
        tem = {x for x in atuais if x in ids}
        if tem == quer:
            continue
        novas = [x for x in atuais if x not in ids] + sorted(quer)
        c, t = req('PUT', f"/produto/{r['id']}", {'categorias': [f'/api/v1/categoria/{x}' for x in novas]})
        txt = '+' + ','.join(ids[x] for x in sorted(quer - tem)) if quer - tem else ''
        txt += (' ' if txt else '') + '-' + ','.join(ids[x] for x in sorted(tem - quer)) if tem - quer else ''
        (feito if feito is not None else avisos).append(f"{r.get('n', '')[:50]}: guias {txt} ({'ok' if c == 200 else 'ERRO %s' % c})")
    return avisos


if __name__ == '__main__':
    sys.path.insert(0, '/home/claude/compilado')
    try:
        from api_li import req
    except Exception:
        import verificador as VF
        req = VF.Api().req
    if '--criar' in sys.argv:
        criar(req)
    if '--sincronizar' in sys.argv:
        import relogios as RL
        R = [x for x in (RL.le(pid, u) for pid, u in RL.lista_relogios()) if x]
        feito = []
        for a in sincroniza(req, R, feito) + feito:
            print(a)
