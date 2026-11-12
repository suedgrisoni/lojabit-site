#!/usr/bin/env python3
"""Refaz carrossel/base.json (QUEM aparece nos carrosséis de cada perfume) — rodar quando entrar perfume novo.

Entradas (todas no repositório, menos a listagem, que é lida da loja):
- carrossel/acordes.json  {id: {a: [[acorde, força 0-100], ...], m: "Marca", c: "nome curto", n: "nome completo"}}
  (a rotina diária do dossiê acrescenta aqui os perfumes novos com carrossel_exportar.py do pacote LOJABIT-dossie)
- carrossel/paginas.json  páginas "Perfumes Parecidos com X": [{cat, u, ref, produtos (do mais parecido), original}]
- listagem /encontre-seu-perfume: quem está no ar e as categorias de cada um (classes prod-cat-ID: famílias e ocasiões)

Regras (as mesmas de 04/11/2026):
- p "Parecidos com o X" (até 8): colegas da página de parecidos (o original primeiro) + semelhança de acordes (cosseno) >= 0,80;
  sem o mesmo perfume em outra concentração.
- m "Com a mesma proposta" (até 8): outras marcas, 2 das 3 famílias principais iguais, mesma hora do dia e mesma estação
  (quando o perfume tem essas ocasiões), pela semelhança. Se ninguém passar (estilo raro), vale 1 família principal igual,
  a mesma hora do dia e semelhança de acordes >= 0,6 (12/11/2026: todo perfume fica com carrossel).
- t estilo: as 3 famílias pela força do acorde + dia/noite/calor/frio; g: a página de parecidos dele (se tiver).

Uso: python3 ferramentas/carrossel_listas.py   (depois: carrossel.py atualizar, commit/push, carrossel.py versao, commit/push)
"""
import json, math, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carrossel as CR

D = CR.D
FAM = {  # categoria -> (acordes da família)  — igual a claude/seo-produtos/familias-regras.py
    '24474618': ['doce', 'caramelo', 'mel', 'cacau', 'chocolate', 'gourmand'], '24474621': ['baunilha'], '24474620': ['amadeirado'],
    '24474619': ['oud'], '24474622': ['floral', 'floral branco', 'rosa', 'tuberosa', 'floral amarelo', 'íris', 'violeta', 'jasmim'],
    '24484483': ['frutado', 'tropical', 'cereja', 'coco'], '24484480': ['cítrico'], '24474623': ['cítrico', 'fresco', 'aquático', 'marinho', 'ozônico'],
    '24484492': ['aquático', 'marinho', 'ozônico'], '24484489': ['verde', 'herbal'], '24484481': ['aromático', 'lavanda'],
    '24484482': ['especiado quente', 'especiado fresco', 'especiado suave', 'canela'], '24484485': ['âmbar'], '24484486': ['atalcado'],
    '24484487': ['almiscarado'], '24484491': ['couro'], '24484490': ['tabaco'], '24484493': ['terroso', 'patchouli', 'musgo']}
ADJ = {'24474618': 'doce', '24474621': 'de baunilha', '24474620': 'amadeirado', '24474619': 'com oud', '24474622': 'floral',
       '24484483': 'frutado', '24484480': 'cítrico', '24474623': 'fresco', '24484492': 'aquático', '24484489': 'verde',
       '24484481': 'aromático', '24484482': 'especiado', '24484485': 'ambarado', '24484486': 'atalcado', '24484487': 'almiscarado',
       '24484491': 'com couro', '24484490': 'com tabaco', '24484493': 'terroso'}
OCA_TXT = [('24474625', 'para o dia a dia'), ('24474626', 'para a noite'), ('24484495', 'para o calor'), ('24484496', 'para o frio')]


def sa(s): return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()


def junta(xs): return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' e ' + xs[-1]


def cos(a, b):
    num = sum(a[k] * b.get(k, 0) for k in a)
    da = math.sqrt(sum(x * x for x in a.values())); db = math.sqrt(sum(x * x for x in b.values()))
    return num / (da * db) if da and db else 0


def tipo(n):
    return 'árabe' if n.startswith('Perfume Árabe') else 'nicho' if n.startswith('Perfume de Nicho') else 'importado'


def main():
    AC = json.load(open(os.path.join(D, 'acordes.json'), encoding='utf-8'))
    PG = json.load(open(os.path.join(D, 'paginas.json'), encoding='utf-8'))
    lista = CR.listagem()
    if len(lista) < 200:
        sys.exit(f'a listagem veio com {len(lista)} produtos — nada foi gravado')
    ATV = [k for k in AC if k in lista]
    V = {k: {a: float(s) for a, s in AC[k]['a']} for k in ATV}
    cats = {k: set(lista[k]['cats']) for k in ATV}

    def base_nome(k):
        n = sa(re.sub(r'^Perfume (Importado|Árabe|de Nicho) ', '', AC[k]['n']))
        n = re.sub(r'\b(eau de (parfum|toilette|cologne)|extrait de parfum|parfum|elixir|intense|edp|edt|\d+ ?ml)\b', '', n)
        return re.sub(r'\s+', ' ', n).strip()

    def forca(k, c): return max([V[k].get(n, 0) for n in FAM[c]] or [0])

    def fams(k):
        f = [c for c in FAM if c in cats[k]]
        f.sort(key=lambda c: -forca(k, c))
        return f[:3]

    def liga(k, a, b): return [i for i, c in enumerate((a, b)) if c in cats[k]]

    l = {}; usados = set()
    for k in ATV:
        p = []
        for pg in sorted([pg for pg in PG if k in pg['produtos']], key=lambda pg: pg['produtos'].index(k)):
            p += [x for x in [x for x in pg.get('original', []) if x != k] + pg['produtos'] if x != k and x in V]
        sims = sorted(((cos(V[k], V[x]), x) for x in ATV if x != k and V[k] and V[x]), reverse=True)
        p += [x for s, x in sims if s >= 0.80]
        vist = set(); pp = []
        for x in p:
            if x in vist or base_nome(x) == base_nome(k): continue
            vist.add(x); pp.append(x)
        pp = pp[:8]
        fk = set(fams(k)); hk = liga(k, '24474625', '24474626'); ck = liga(k, '24484495', '24484496'); m = []
        for s, x in sims:
            if x in vist or sa(AC[x]['m']) == sa(AC[k]['m']) or base_nome(x) == base_nome(k): continue
            if len(fk & set(fams(x))) >= 2 and (not hk or set(hk) & set(liga(x, '24474625', '24474626'))) \
               and (not ck or set(ck) & set(liga(x, '24484495', '24484496'))):
                m.append(x)
            if len(m) == 8: break
        if not m:
            # perfume de estilo raro (ex.: Kouros): sem ninguém na regra completa, vale 1 família principal igual e a mesma hora do dia
            for s, x in sims:
                if x in vist or sa(AC[x]['m']) == sa(AC[k]['m']) or base_nome(x) == base_nome(k) or s < 0.6: continue
                if fk & set(fams(x)) and (not hk or set(hk) & set(liga(x, '24474625', '24474626'))):
                    m.append(x)
                if len(m) == 8: break
        # menos de 3 cartões no total: fica sem dados e a página mostra o "Perfumes parecidos" antigo (mais vendidos com as mesmas notas)
        if len(pp) + len(m) < 3: continue
        f = sorted([c for c in FAM if c in cats[k]], key=lambda c: -forca(k, c))
        if '24484480' in f and '24474623' in f: f.remove('24474623')
        f = f[:3]
        oc = [t for c, t in OCA_TXT if c in cats[k]]
        t = (junta([ADJ[c] for c in f]) if f else '') + (' · ' + junta(oc) if oc else '')
        pgs = sorted([pg for pg in PG if k in pg['produtos']], key=lambda pg: (0 if k in pg.get('original', []) else 1, pg['produtos'].index(k)))
        l[k] = {'n': AC[k]['c'], 'g': pgs[0]['u'] if pgs else None, 't': t, 'p': pp, 'm': m}
        usados |= set(pp) | set(m)
    c = {x: [AC[x]['c'], (AC[x]['m'] + ' · ' if AC[x]['m'] else '') + tipo(AC[x]['n'])] for x in sorted(usados)}
    import time
    json.dump({'gerado': time.strftime('%Y-%m-%d'), 'l': l, 'c': c}, open(os.path.join(D, 'base.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, separators=(',', ':'))
    print(f'listagem: {len(lista)} | com acordes e no ar: {len(ATV)} | com carrossel: {len(l)} | cartões: {len(c)}')


if __name__ == '__main__':
    main()
