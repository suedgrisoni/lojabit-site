#!/usr/bin/env python3
"""Perfume novo entra sozinho nos carrosséis (12/11/2026).

Acha os perfumes que estão no ar na loja e ainda não estão em carrossel/acordes.json e monta os acordes deles
a partir da PRÓPRIA PÁGINA PÚBLICA do produto (o dossiê já escreveu lá):
- "Estilo olfativo: A · B · C" (as 3 famílias, da mais forte para a mais fraca)  -> força 100, 90, 80
- "Acordes principais: x, y e z" (ficha técnica, do mais forte para o mais fraco) -> força 75, 68, 61, 54...
Não precisa de chave nem do computador do Nevander: roda em qualquer sessão (tarefa automática dos carrosséis).
Perfume sem "Estilo olfativo" nem "Acordes principais" na página (dossiê ainda não feito) fica para a próxima rodada.

Uso: python3 ferramentas/carrossel_novos.py           (grava carrossel/acordes.json)
     python3 ferramentas/carrossel_novos.py --teste   (só mostra o que faria)
Depois: python3 ferramentas/carrossel_listas.py e python3 ferramentas/carrossel.py atualizar (veja o README).
"""
import html, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import carrossel as CR

D = CR.D
# família do "Estilo olfativo" -> acorde (o mesmo vocabulário do acordes.json e de carrossel_listas.FAM)
FAMILIA = {'doce': 'doce', 'baunilha': 'baunilha', 'amadeirado': 'amadeirado', 'oud': 'oud', 'floral': 'floral',
           'frutado': 'frutado', 'cítrico': 'cítrico', 'fresco': 'fresco', 'aquático': 'aquático', 'verde': 'verde',
           'aromático': 'aromático', 'especiado': 'especiado quente', 'ambarado': 'âmbar', 'atalcado': 'atalcado',
           'almiscarado': 'almiscarado', 'couro': 'couro', 'tabaco': 'tabaco', 'terroso': 'terroso'}
# palavras da ficha técnica -> acorde
SIN = {'ambar': 'âmbar', 'âmbar': 'âmbar', 'ambarado': 'âmbar', 'oriental': 'âmbar', 'citrico': 'cítrico', 'cítricos': 'cítrico',
       'aquatico': 'aquático', 'marinho': 'marinho', 'ozonico': 'ozônico', 'aromatico': 'aromático', 'especiado': 'especiado quente',
       'quente especiado': 'especiado quente', 'especiado quente': 'especiado quente', 'fresco especiado': 'especiado fresco',
       'especiado fresco': 'especiado fresco', 'especiado suave': 'especiado suave', 'talcado': 'atalcado', 'almíscar': 'almiscarado',
       'almiscar': 'almiscarado', 'balsamico': 'balsâmico', 'frutal': 'frutado', 'frutas': 'frutado', 'floral branco': 'floral branco',
       'flores brancas': 'floral branco', 'amadeirada': 'amadeirado', 'madeira': 'amadeirado', 'madeiras': 'amadeirado',
       'gourmand': 'gourmand', 'lactonico': 'lactônico', 'whisky': 'uísque', 'fumaça': 'esfumaçado', 'defumado': 'esfumaçado',
       'esfumacado': 'esfumaçado', 'terroso': 'terroso', 'musgo': 'musgo', 'patchouli': 'patchouli', 'herbal': 'herbal', 'verde': 'verde',
       'adocicado': 'doce', 'açucarado': 'doce', 'baunilhado': 'baunilha', 'resinoso': 'balsâmico', 'salino': 'salgado',
       'cremoso': 'lactônico', 'aquoso': 'aquático', 'atalcada': 'atalcado', 'fougère': 'aromático', 'fougere': 'aromático'}
PREF = re.compile(r'^(Perfume (Importado|Árabe|de Nicho)|Decant)\s+', re.I)
CONC = re.compile(r'\s+(Eau de (Parfum|Toilette|Cologne)|Extrait de Parfum|Parfum|Elixir|EDP|EDT|\d+ ?ml)(\s+.*)?$', re.I)


def texto(h):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))).strip()


def item(desc, nome):
    m = re.search(r'<strong>\s*' + nome + r'\s*:?\s*</strong>\s*:?([\s\S]*?)</(li|p)>', desc, re.I)
    return texto(m.group(1)) if m else ''


def lista(s):
    s = re.sub(r'\s*\(.*?\)', '', s or '').strip(' .;')
    return [p.strip(' .;').lower() for p in re.split(r'\s*,\s*|\s+e\s+', s) if p.strip(' .;')]


def ler(url, nome_lista):
    h = CR.baixa(CR.LOJA + url)
    if 'pagina-produto' not in h:
        return None
    i = h.find('id="descricao"')
    i = h.find('>', i) + 1 if i >= 0 else -1
    desc = h[i:i + 90000] if i > 0 else ''
    if not desc:
        return None
    t = texto(desc)
    acs = {}
    m = re.search(r'Estilo olfativo:\s*(.+?)(?:\s+O\s|\s+A\s|\s+Os\s|\s+As\s|\s+Este\s|\s+Esta\s|$)', t)
    fams = []
    if m:
        for p in re.split(r'\s*·\s*', m.group(1))[:3]:
            a = FAMILIA.get(p.strip().lower())
            if a and a not in fams:
                fams.append(a)
    for a, f in zip(fams, (100, 90, 80)):
        acs[a] = max(acs.get(a, 0), f)
    fic = lista(item(desc, 'Acordes principais'))
    for pos, p in enumerate(fic[:8]):
        a = SIN.get(p, p)
        f = max(75 - 7 * pos, 30)
        acs[a] = max(acs.get(a, 0), f)
    if not acs:
        return None
    # marca: a do cadastro (link /marca/ da página); se faltar, a da ficha técnica sem o que vem depois de vírgula/parêntese
    mb = re.search(r'itemprop="brand"[\s\S]{0,500}?href="[^"]*/marca/[^"/]+?\.html"[^>]*>([^<]+)<', h)
    marca = texto(mb.group(1)) if mb else re.split(r'\s*[,(]', item(desc, 'Marca'))[0].strip()
    nome = nome_lista or ''
    h1 = re.search(r'<h1[^>]*class="[^"]*nome-produto[^"]*"[^>]*>([\s\S]*?)</h1>', h)
    if h1:
        nome = texto(h1.group(1)) or nome
    # nome curto: o título do dossiê ("Hawas Fire: brisa do mar...") ou o nome sem tipo, marca e concentração
    curto = ''
    m = re.match(r'([^:]{2,40}):', t)
    if m and not re.search(r'estilo olfativo', m.group(1), re.I):
        curto = re.sub(r'\s+(Eau de (Parfum|Toilette|Cologne)|Extrait de Parfum)$', '', m.group(1).strip(), flags=re.I)
    if not curto:
        curto = PREF.sub('', nome)
        if marca and curto.lower().startswith(marca.lower() + ' '):
            curto = curto[len(marca) + 1:]
        curto = CONC.sub('', curto).strip() or nome
    # tira a marca grudada no começo ou no fim do nome curto ("Maktub Gold Bidaya" -> "Maktub Gold"), menos quando sobra só "Pour Homme" etc.
    if marca:
        for mm in sorted({marca, marca.split()[0]}, key=len, reverse=True):
            if curto.lower().endswith(' ' + mm.lower()):
                curto = curto[:-len(mm) - 1].strip()
                break
        for mm in sorted({marca, marca.split()[0]}, key=len, reverse=True):
            resto = curto[len(mm) + 1:] if curto.lower().startswith(mm.lower() + ' ') else ''
            if resto and not re.match(r'(pour|for|eau|homme|femme|man|men|woman|women|l\'|le|la)\b', resto, re.I):
                curto = resto
                break
    ordem = sorted(acs.items(), key=lambda x: -x[1])[:8]
    return {'a': [[a, f] for a, f in ordem], 'm': marca, 'c': curto, 'n': nome}


def main():
    teste = '--teste' in sys.argv
    AC = json.load(open(os.path.join(D, 'acordes.json'), encoding='utf-8'))
    lista_loja = CR.listagem()
    if len(lista_loja) < 200:
        sys.exit(f'a listagem veio com {len(lista_loja)} produtos — nada foi gravado')
    # sem acordes = não está no acordes.json ou está com a lista vazia (perfume que a base antiga não tinha dados)
    faltam = [(k, v) for k, v in lista_loja.items() if (k not in AC or not AC[k].get('a')) and re.match(r'^(Perfume|Decant)', v['t'] or '', re.I)]
    novos, sem = {}, []
    for k, v in faltam:
        r = ler(v['u'], v['t'])
        if r:
            novos[k] = r
        else:
            sem.append(v['t'] or k)
        time.sleep(1.2)
    for k, r in novos.items():
        print(f"+ {k} {r['c']} ({r['m']}): " + ', '.join(f'{a} {f}' for a, f in r['a']))
    for s in sem:
        print('  sem dados na página (fica para a próxima rodada):', s)
    if novos and not teste:
        AC.update(novos)
        json.dump(AC, open(os.path.join(D, 'acordes.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'perfumes no ar sem acordes: {len(faltam)} | acrescentados: {0 if teste else len(novos)} | sem dados: {len(sem)}')


if __name__ == '__main__':
    main()
