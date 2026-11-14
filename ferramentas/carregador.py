#!/usr/bin/env python3
"""Gera o conteúdo dos 2 códigos carregadores do painel (painel/cabecalho.html e painel/rodape.html).

Cada arquivo de dist/ é chamado pelo commit em que ele mudou pela última vez (git log),
assim, depois de uma mudança, o celular do cliente só baixa de novo o arquivo que mudou.
Rode depois do commit + push:   python3 ferramentas/carregador.py
"""
import os, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = 'suedgrisoni/lojabit-site'
CDN = 'https://cdn.jsdelivr.net/gh/' + REPO
RESERVA = 'https://fastly.jsdelivr.net/gh/' + REPO   # se o cdn.jsdelivr.net falhar


def commit_de(arquivo):
    r = subprocess.run(['git', 'log', '-1', '--format=%H', '--', 'dist/' + arquivo], cwd=RAIZ, capture_output=True, text=True)
    sha = r.stdout.strip()
    if not sha:
        sys.exit(f'dist/{arquivo} ainda não tem commit — faça o commit e o push antes')
    pend = subprocess.run(['git', 'status', '--porcelain', '--', 'dist/' + arquivo], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    if pend:
        sys.exit(f'dist/{arquivo} mudou e não foi para o commit — faça o commit e o push antes')
    return sha


def url(base, arquivo):
    return f'{base}@{commit_de(arquivo)}/dist/{arquivo}'


def css(arquivo):
    return (f'<link rel="stylesheet" href="{url(CDN, arquivo)}" crossorigin '
            f'onerror="this.onerror=null;this.href=this.href.replace(\'//cdn.\',\'//fastly.\')">')


def js(arquivo, marca):
    return (f'<script src="{url(CDN, arquivo)}" crossorigin></script>\n'
            f'<script>window.{marca}||document.write(\'<script src="{url(RESERVA, arquivo)}" crossorigin><\\/script>\')</script>')


# Foto principal do produto no celular (é o "maior bloco" da página, LCP): a Loja Integrada põe loading="lazy" nela,
# então o navegador só começa a baixar depois de montar a página. Aqui ela começa a baixar já no cabeçalho, com prioridade alta.
# O endereço vem do og:image (800x800) trocado pelo tamanho que a galeria do celular vai mostrar (o mesmo arquivo da foto
# principal, conferido em 60 produtos). Desde 14/11/2026 (Nitidez das fotos, src/1799008) a galeria do celular pede a foto
# nítida: largura da tela x densidade (até 3; 1,5 no modo economia de dados), no mesmo degrau de tamanhos do 1799008
# (600, 800, 1000, 1200 ou 2500 = arquivo inteiro de 1448 px). Se a 600x700 já basta (tela de densidade 1) ou se a nitidez
# está desligada neste aparelho (?lbnit=0), continua 600x700, como antes.
# Só em telas até 979 px (no computador a galeria usa outra foto) e só em página de produto (og:image com /produto/).
FOTO = ('<script>!function(d){try{if(screen.width>979)return;var m=d.querySelector(\'meta[property="og:image"]\'),u=m&&m.content||"";'
        'if(u.indexOf("/produto/")<0)return;var p=Math.min(window.devicePixelRatio||1,3),z="600x700",t=[600,800,1000,1200,2500],n,i,k;'
        'try{if(navigator.connection&&navigator.connection.saveData)p=Math.min(p,1.5)}catch(e){}'
        'n=screen.width*p*.97;for(i=0;i<t.length;i++){k=t[i]>=2500?1448:t[i];if(k>=n||t[i]>=2500)break}'
        'try{if(localStorage.getItem("lbnit")==="0")k=0}catch(e){}if(k>630)z=t[i]+"x"+t[i];'
        'u=u.replace(/\\/\\d+x\\d+\\//,"/"+z+"/");var l=d.createElement("link");l.rel="preload";l.as="image";'
        'l.href=u;l.setAttribute("fetchpriority","high");d.head.appendChild(l)}catch(e){}}(document)</script>')


def main():
    aviso = '<!-- LOJABIT Etapa 3: códigos de todas as páginas em arquivos com cache. Fonte e instruções: github.com/' + REPO + ' -->'
    # sem preload/preconnect dos arquivos: o HTML ficou pequeno e o navegador já acha o rod.js cedo sozinho
    # (assim, mudar só o rodapé não obriga a mexer no carregador do cabeçalho)
    cab = '\n'.join([FOTO, css('cab.css'), js('cab.js', 'lbE3c'), aviso])
    rod = '\n'.join([css('rod.css'), js('rod.js', 'lbE3r'), aviso])
    os.makedirs(os.path.join(RAIZ, 'painel'), exist_ok=True)
    for nome, txt in (('cabecalho.html', cab), ('rodape.html', rod)):
        open(os.path.join(RAIZ, 'painel', nome), 'w', encoding='utf-8').write(txt + '\n')
        print(f'painel/{nome}:\n{txt}\n')


if __name__ == '__main__':
    main()
