"""Troca no dist/ só o bloco de um ou mais códigos, sem recompactar o resto (para quando o terser não está disponível).
O bloco novo entra sem compactar, no mesmo formato do build.py (try{...}catch). Atualiza dist/manifesto.json.
Uso: python3 ferramentas/troca_bloco.py ID [ID ...]"""
import json, re, sys, os, hashlib, subprocess
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ordem = json.load(open(os.path.join(AQUI, 'ordem.json'), encoding='utf-8'))
grupo = {c['id']: c['grupo'] for c in ordem}


def script_de(i):
    seg = open(os.path.join(AQUI, 'src', f'{i}.html'), encoding='utf-8').read()
    ms = re.findall(r'<script[^>]*>([\s\S]*?)</script>', seg)
    assert len(ms) == 1, f'{i}: esperava 1 <script>'
    return ms[0].strip()


for i in map(int, sys.argv[1:]):
    g = grupo[i]; f = os.path.join(AQUI, 'dist', f'{g}.js')
    s = open(f, encoding='utf-8').read()
    m = re.search(r'lojabit codigo %d"' % i, s)
    fim = s.find(')}', m.end()) + 2
    # início: logo depois do bloco anterior que tem marca; confere que não pega outro código
    ant = [x for x in re.finditer(r'lojabit codigo (\d+)"', s[:m.start()])]
    ini = s.find(')}', ant[-1].end()) + 2 if ant else None
    seg = s[ini:fim]
    if not seg.startswith('try{') or re.findall(r'lojabit codigo (\d+)', seg) != [str(i)]:
        # bloco precedido por estilos (__lbE3s): procura o try{ do próprio código
        ini = s.rfind('try{!function', ant[-1].end() if ant else 0, m.start())
        seg = s[ini:fim]
    assert seg.startswith('try{') and re.findall(r'lojabit codigo (\d+)', seg) == [str(i)], f'{i}: não achei o bloco com segurança'
    novo = 'try{\n' + script_de(i) + '\n}catch(e){window.console&&console.error("lojabit codigo ' + str(i) + '",e)}'
    s = s[:ini] + novo + s[fim:]
    open(f, 'w', encoding='utf-8').write(s)
    print(i, g, 'bloco trocado:', len(seg), '->', len(novo), 'caracteres')
man = json.load(open(os.path.join(AQUI, 'dist', 'manifesto.json'), encoding='utf-8'))
for g in ('cab', 'rod'):
    t = open(os.path.join(AQUI, 'dist', f'{g}.js'), encoding='utf-8').read()
    man['arquivos'][f'{g}.js'].update({'bytes': len(t.encode()), 'sha256': hashlib.sha256(t.encode()).hexdigest()})
    r = subprocess.run(['node', '--check', os.path.join(AQUI, 'dist', f'{g}.js')], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'ERRO de sintaxe em dist/{g}.js: {r.stderr[:300]}')
json.dump(man, open(os.path.join(AQUI, 'dist', 'manifesto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
