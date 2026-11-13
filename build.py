#!/usr/bin/env python3
"""Monta os arquivos do site (dist/) a partir dos códigos em src/, na ordem de ordem.json.

Como funciona (Etapa 3, 02/11/2026):
- Os códigos HTML "de todas as páginas" da Loja Integrada saíram do painel e viraram 4 arquivos:
  dist/cab.css e dist/cab.js (os do cabeçalho) e dist/rod.css e dist/rod.js (os do rodapé).
- A ordem é a MESMA em que a Loja Integrada punha os códigos na página (ordem.json). Não mude a ordem sem testar.
- Cada <script> de cada código vira um bloco try/catch: se um código der erro, os outros continuam (como antes).
- Os <style> do cabeçalho com data-lbv (estilos do "Visual novo") NÃO vão para o .css: o cab.js recria cada um como
  <style data-lbv="N"> no cabeçalho, no mesmo ponto da sequência, porque o "Visual novo 1 - interruptor" (1717239)
  liga esses estilos e os leva para o fim do cabeçalho (é isso que faz o visual novo ganhar do tema).
- O "Celular app 1 - interruptor" (1717518) troca, nos estilos do próprio site, max-width 767px -> 979px e
  min-width 768px -> 980px (para o tablet usar o visual do celular). Ele não mexe em arquivo de outro endereço
  (como o jsDelivr), por isso essa troca é feita aqui, na montagem, enquanto o 1717518 estiver ligado (var c=!0).
- Os outros <style> viram CSS na mesma ordem (o do cabeçalho em cab.css, o do rodapé em rod.css).
- O site carrega os arquivos pelo jsDelivr, presos a um commit (veja README.md e ferramentas/carregador.py).

Uso: python3 build.py   -> gera dist/ (minifica o JS com terser se houver node + terser; senão deixa como está)
"""
import json, os, re, sys, hashlib, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
TAG = re.compile(r'<(script|style)\b([^>]*)>([\s\S]*?)</\1\s*>', re.I)


def attr(attrs, nome):
    m = re.search(r'\b' + nome + r'\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))', attrs or '', re.I)
    return None if not m else next(g for g in m.groups() if g is not None)


def partes(seg):
    out = []; pos = 0
    for m in TAG.finditer(seg):
        antes = seg[pos:m.start()]
        if antes.strip(): out.append(('outro', antes, ''))
        tag, attrs, corpo = m.group(1).lower(), m.group(2), m.group(3)
        if tag == 'style':
            out.append(('css', corpo, attrs))
        else:
            src = attr(attrs, 'src')
            t = (attr(attrs, 'type') or 'text/javascript').lower()
            if src: out.append(('jsext', src, attrs))
            elif t in ('text/javascript', 'application/javascript'): out.append(('js', corpo, attrs))
            else: out.append(('dado', m.group(0), attrs))
        pos = m.end()
    resto = seg[pos:]
    if resto.strip(): out.append(('outro', resto, ''))
    return out


def css_min(t):
    """Minificação segura: tira comentários e espaços em volta de { } ; (não mexe dentro de seletores)."""
    t = re.sub(r'/\*[\s\S]*?\*/', '', t)
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'\s*([{};])\s*', r'\1', t)
    return t.strip()


def troca_tablet(css):
    """O mesmo que o 1717518 faz nas regras @media dos estilos do site: 767px -> 979px e 768px -> 980px."""
    def f(m):
        p = m.group(0)
        p = re.sub(r'max-width\s*:\s*767px', 'max-width: 979px', p)
        return re.sub(r'min-width\s*:\s*768px', 'min-width: 980px', p)
    return re.sub(r'@media\b[^{;]*\{', f, css)


def terser(js):
    """Minifica com terser (se existir). Mantém nomes de funções; não mexe em nomes globais."""
    try:
        r = subprocess.run(['node', '-e', '''
const {minify}=require("terser");let s="";process.stdin.setEncoding("utf8");process.stdin.on("data",d=>s+=d).on("end",async()=>{
 const o=await minify(s,{ecma:5,compress:{keep_fnames:true,passes:1},mangle:{keep_fnames:true},format:{comments:false}});
 process.stdout.write(o.code);});'''], input=js, capture_output=True, text=True, cwd=AQUI, timeout=300)
        if r.returncode == 0 and r.stdout.strip():
            # proteção: um acento quebrado (\ufffd) que não existia no original = erro de leitura, não publica
            if r.stdout.count('\ufffd') > js.count('\ufffd'):
                sys.exit('terser quebrou um acento (\\ufffd) — não publique, confira o build')
            return r.stdout, True
        print('terser não rodou:', r.stderr[:300])
    except Exception as e:
        print('terser não rodou:', e)
    return js, False


# rel = arquivos dos relógios (dist/rel.css e dist/rel.js), carregados sob demanda pelo código 1799005 só em página de relógio
NOMES = {'cab': 'cabeçalho', 'rod': 'rodapé', 'rel': 'relógios (só nas páginas de relógio)'}
INJETA = ('window.__lbE3s=function(t,a){var s=document.createElement("style");for(var k in a)s.setAttribute(k,a[k]);'
          's.textContent=t;(document.head||document.documentElement).appendChild(s)};')


def main():
    ordem = json.load(open(os.path.join(AQUI, 'ordem.json'), encoding='utf-8'))
    tablet = 'var c=!0,d="lbMob"' in open(os.path.join(AQUI, 'src', '1717518.html'), encoding='utf-8').read()
    print('troca 767/768 -> 979/980 (celular app 1 ligado):', tablet)
    blocos = {('cab', 'css'): [], ('cab', 'js'): [INJETA], ('rod', 'css'): [], ('rod', 'js'): [], ('rel', 'css'): [], ('rel', 'js'): []}
    for c in ordem:
        seg = open(os.path.join(AQUI, 'src', f"{c['id']}.html"), encoding='utf-8').read()
        cab = f"/* {c['id']} {c['nome']} */"
        for tipo, txt, attrs in partes(seg):
            if tipo == 'css':
                corpo = css_min(txt)
                if tablet: corpo = troca_tablet(corpo)
                lbv, media = attr(attrs, 'data-lbv'), attr(attrs, 'media')
                if c['grupo'] == 'cab' and lbv is not None:
                    a = {'data-lbv': lbv}
                    if media is not None: a['media'] = media
                    blocos[('cab', 'js')].append(cab + '\n__lbE3s(' + json.dumps(corpo, ensure_ascii=False) + ',' + json.dumps(a) + ');')
                    continue
                if media and media.strip().lower() not in ('all', 'screen'):
                    corpo = f'@media {media}{{{corpo}}}'
                blocos[(c['grupo'], 'css')].append(cab + corpo)
            elif tipo == 'js':
                blocos[(c['grupo'], 'js')].append(cab + '\ntry{\n' + txt.strip() + '\n}catch(e){window.console&&console.error("lojabit codigo ' + str(c['id']) + '",e)}')
            elif tipo == 'outro' and not re.sub(r'<!--[\s\S]*?-->', '', txt).strip():
                continue  # só comentário
            else:
                sys.exit(f"código {c['id']} {c['nome']}: tem {tipo} — não pode ir para o arquivo (deixe no painel)")
    os.makedirs(os.path.join(AQUI, 'dist'), exist_ok=True)
    man = {'arquivos': {}, 'codigos': ordem, 'troca_tablet': tablet}
    # rel antes de rod: a "versão" dos arquivos dos relógios vai dentro do rod.js (__REL_V__ no código 1799005), assim toda
    # mudança em rel.* também muda o rod.js e entra no mesmo commit que o carregador do painel aponta
    relv = ''
    for (g, t) in [('cab', 'css'), ('cab', 'js'), ('rel', 'css'), ('rel', 'js'), ('rod', 'css'), ('rod', 'js')]:
        bl = blocos[(g, t)]
        texto = '\n'.join(bl) + '\n'
        if (g, t) == ('rod', 'js'):
            texto = texto.replace('__REL_V__', relv)
        minif = False
        if t == 'js':
            texto, minif = terser(texto)
            # marca de "arquivo rodou até o fim": se faltar, o carregador do painel tenta o endereço reserva
            texto = ('/* LOJABIT - códigos do ' + NOMES[g] + ' (fonte: github.com/suedgrisoni/lojabit-site, src/) */\n'
                     + texto.rstrip().rstrip(';') + ';\nwindow.lbE3' + {'cab': 'c', 'rod': 'r', 'rel': 'l'}[g] + '=1;\n')
        else:
            texto = '/* LOJABIT - estilos do ' + NOMES[g] + ' (fonte: github.com/suedgrisoni/lojabit-site, src/) */\n' + texto + '\n'
        nome = f'{g}.{t}'
        open(os.path.join(AQUI, 'dist', nome), 'w', encoding='utf-8').write(texto)
        man['arquivos'][nome] = {'bytes': len(texto.encode()), 'sha256': hashlib.sha256(texto.encode()).hexdigest(), 'minificado': minif or t == 'css'}
        if g == 'rel':
            relv = hashlib.sha256((relv + texto).encode()).hexdigest()[:10]
        print(f"dist/{nome}: {len(texto.encode())/1024:.0f} KB{' (minificado)' if minif else ''}")
    json.dump(man, open(os.path.join(AQUI, 'dist', 'manifesto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # confere a sintaxe dos JS
    for g in ('cab', 'rod', 'rel'):
        r = subprocess.run(['node', '--check', os.path.join(AQUI, 'dist', f'{g}.js')], capture_output=True, text=True)
        if r.returncode != 0: sys.exit(f'ERRO de sintaxe em dist/{g}.js: {r.stderr[:300]}')
    print('ok')


if __name__ == '__main__':
    main()
