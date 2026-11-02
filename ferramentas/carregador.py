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


def main():
    aviso = '<!-- LOJABIT Etapa 3: códigos de todas as páginas em arquivos com cache. Fonte e instruções: github.com/' + REPO + ' -->'
    # sem preload/preconnect: o HTML ficou pequeno e o navegador já acha o rod.js cedo sozinho
    # (assim, mudar só o rodapé não obriga a mexer no carregador do cabeçalho)
    cab = '\n'.join([css('cab.css'), js('cab.js', 'lbE3c'), aviso])
    rod = '\n'.join([css('rod.css'), js('rod.js', 'lbE3r'), aviso])
    os.makedirs(os.path.join(RAIZ, 'painel'), exist_ok=True)
    for nome, txt in (('cabecalho.html', cab), ('rodape.html', rod)):
        open(os.path.join(RAIZ, 'painel', nome), 'w', encoding='utf-8').write(txt + '\n')
        print(f'painel/{nome}:\n{txt}\n')


if __name__ == '__main__':
    main()
