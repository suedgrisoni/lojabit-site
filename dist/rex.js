/* LOJABIT - códigos do relógios, extras sob demanda (quiz, tamanho real, guia do proprietário) (fonte: github.com/suedgrisoni/lojabit-site, src/) */
/* 1799006 Relógios, extras sob demanda: quiz, tamanho real e guia do proprietário — vai para dist/rex.* (só no repositório) */
try{
/* LOJABIT - Relógios, extras sob demanda (dist/rex.js). Usa as funções que o rel.js deixa em window.__lbRelX.
   Tudo aqui se monta com o que já existe: a lista de relógios (carrossel/relogios.json) e a ficha/descrição da página.
   Relógio novo entra sozinho no quiz; o tamanho real e o guia leem a ficha da própria página. */
(function () {
  'use strict';
  var X = window.__lbRelX;
  if (!X || window.__lbRex) return;
  var esc = X.esc, rs = X.rs;
  function guarda(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} }
  function le(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function unicos(s) { var o = {}, r = ''; String(s || '').split('').forEach(function (c) { if (!o[c]) { o[c] = 1; r += c; } }); return r; }

  /* ---------- folha: a janela que sobe sobre a página ---------- */
  var ABERTA = null;
  function fecha() {
    if (!ABERTA) return;
    var o = ABERTA; ABERTA = null;
    try { o.__f(); } catch (e) {}
    o.classList.remove('on');
    setTimeout(function () { if (o.parentNode) o.parentNode.removeChild(o); }, 280);
  }
  function folha(cls, k, h, aoFechar) {
    fecha();
    var o = document.createElement('div');
    o.className = 'lbrj ' + cls;
    o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true'); o.setAttribute('aria-label', h);
    o.innerHTML = '<div class="lbrj-cx"><div class="lbrj-cab"><button type="button" class="lbrj-v" aria-label="Voltar" hidden>&#8249;</button><div><div class="lbrj-k">' + k + '</div><div class="lbrj-h">' + h + '</div></div>' +
      '<button type="button" class="lbrj-f" aria-label="Fechar">&times;</button></div><div class="lbrj-co"></div></div>';
    document.body.appendChild(o);
    var de = document.documentElement, antes = de.style.overflow;
    de.style.overflow = 'hidden';
    function tecla(e) { if (e.key === 'Escape') fecha(); }
    document.addEventListener('keydown', tecla);
    o.__f = function () { de.style.overflow = antes; document.removeEventListener('keydown', tecla); if (aoFechar) aoFechar(); };
    o.addEventListener('click', function (e) { if (e.target === o || (e.target.closest && e.target.closest('.lbrj-f'))) fecha(); });
    requestAnimationFrame(function () { requestAnimationFrame(function () { o.classList.add('on'); }); });
    setTimeout(function () { try { o.querySelector('.lbrj-f').focus({ preventScroll: true }); } catch (e) {} }, 80);
    ABERTA = o;
    return o;
  }

  /* ================= 1. QUIZ: qual relógio combina com você? ================= */
  /* cada opção de uso aponta para as ocasiões da ficha (ferramentas/relogios.py: oi = ideal, oc = também vai bem) */
  var USOS = [
    ['t', 'Trabalho e escritório', 'Camisa, reunião e o dia inteiro no pulso', 'tn'],
    ['n', 'Eventos, terno e noite', 'Casamento, jantar e ocasiões especiais', 'nj'],
    ['d', 'Dia a dia', 'Um relógio para usar sempre, com tudo', 'd'],
    ['p', 'Praia, piscina e esporte', 'Água, treino e fim de semana', 'pe'],
    ['v', 'Viagens e aventura', 'Aeroporto, estrada e trilha', 'vr'],
    ['x', 'Um pouco de tudo', 'Quero o mais versátil', '']
  ];
  var IDEAL = { t: 'Ideal para o trabalho', n: 'Ideal com terno e em ocasiões especiais', j: 'Ideal para a noite', d: 'Ideal para o dia a dia', p: 'Ideal para praia e piscina', e: 'Ideal para o esporte', v: 'Ideal para viagens', r: 'Ideal para trilha e aventura' };
  var VAI = { t: 'Vai bem no trabalho', n: 'Vai bem com terno', j: 'Vai bem à noite', d: 'Vai bem no dia a dia', p: 'Vai bem na praia e na piscina', e: 'Vai bem no esporte', v: 'Vai bem em viagens', r: 'Vai bem na trilha' };
  var MOVS = [
    ['a', 'Automático', 'Mecânica viva, sem pilha: funciona com o movimento do pulso'],
    ['q', 'Prático', 'Quartzo ou solar: sempre na hora, sem dar corda'],
    ['x', 'Tanto faz', 'Quero ver o melhor dos dois']
  ];
  var FAIXAS = [[0, 2000, 'Até R$ 2.000'], [2000, 4000, 'De R$ 2.000 a R$ 4.000'], [4000, 8000, 'De R$ 4.000 a R$ 8.000'], [8000, 1e9, 'Acima de R$ 8.000']];

  function pontua(x, R) {
    var s = 0, mot = [], oi = x.oi || '', oc = x.oc || '', tudo = unicos(oi + oc);
    if (R.uso) {
      var ks = R.uso[3];
      if (!ks) {
        s += Math.min(4, oi.length * .7 + oc.length * .35);
        if (tudo.length >= 4) mot.push('Versátil: vai bem em ' + tudo.length + ' ocasiões diferentes');
      } else {
        var melhor = 0, frase = '';
        ks.split('').forEach(function (k, i) {
          var v = oi.indexOf(k) >= 0 ? 4 : oc.indexOf(k) >= 0 ? 2 : 0;
          if (v - i * .01 > melhor) { melhor = v - i * .01; frase = (v > 3 ? IDEAL : VAI)[k]; }
        });
        s += melhor;
        if (ks.length > 1 && ks.split('').every(function (k) { return tudo.indexOf(k) >= 0; })) s += .8;
        if (frase) mot.push(frase); else s -= 2.5;
      }
    }
    if (R.cm && x.diam) {
      var e = X.encaixe(x, R.cm), cm = X.cmTxt(R.cm);
      s += e === 'i' ? 3 : e === 'g' ? -2 : 1.2;
      if (e === 'i') mot.push('Proporção ideal no seu pulso de ' + cm);
      else if (e === 'd') mot.push('Discreto e elegante no seu pulso de ' + cm);
      else if (e === 'm') mot.push('Marcante, com presença no seu pulso de ' + cm);
    }
    var mec = x.tipo === 'auto' || x.tipo === 'manual';
    if (R.mov === 'a') { if (mec) { s += 3; mot.push('Automático: funciona sem pilha, com o movimento do pulso'); } else s -= 2; }
    if (R.mov === 'q') { if (!mec && x.tipo) { s += 3; mot.push(x.tipo === 'solar' ? 'Solar: carrega com qualquer luz, sem troca de pilha' : 'Quartzo: sempre na hora, sem dar corda'); } else s -= 2; }
    if (R.fx) {
      var a = R.fx[0], b = R.fx[1], pix = x.p * .9;
      if (x.p >= a && x.p <= b) { s += 4; mot.push('Cabe no que você quer investir: ' + rs(pix) + ' no Pix'); }
      else if (x.p > b && pix <= b) { s += 3; mot.push('No Pix, cabe no que você quer investir: ' + rs(pix)); }
      else if (x.p < a) { s += 1.2; mot.push('Sai por menos do que você pensou: ' + rs(pix) + ' no Pix'); }
      else if (x.p <= b * 1.15) s += .3;
      else s -= 6;
    }
    if (mot.length < 3 && x.vidro === 'safira') mot.push('Vidro de safira, o que mais resiste a riscos');
    if (mot.length < 3 && x.agua >= 200) mot.push('Pronto para o mar: ' + x.agua + ' m de resistência à água');
    else if (mot.length < 3 && x.agua >= 100) mot.push('Pode nadar com ele: ' + x.agua + ' m de resistência à água');
    s += (x.vidro === 'safira' ? .3 : 0) + (x.agua >= 100 ? .2 : 0);
    return [s, mot.slice(0, 4)];
  }
  function escolhe(B, R) {
    var L = B.r.filter(function (x) { return x.disp && x.p > 0; }).map(function (x) { var p = pontua(x, R); return { x: x, s: p[0], m: p[1] }; })
      .sort(function (a, b) { return b.s - a.s || a.x.p - b.x.p; });
    /* três opções diferentes: as outras cores do mesmo modelo ficam para depois */
    var visto = {}, T = [], resto = [];
    L.forEach(function (o) {
      var k = [o.x.mk, o.x.tipo, o.x.diam, Math.round(o.x.p), o.x.ct].join('|');
      if (visto[k]) resto.push(o); else { visto[k] = 1; T.push(o); }
    });
    return T.concat(resto).slice(0, 3);
  }

  function quiz() {
    var hashAntes = location.hash === '#quiz' ? '' : location.hash;
    var o = folha('lbrq', 'Quiz', 'Qual relógio combina com você?', function () {
      try { history.replaceState(null, '', location.pathname + location.search + hashAntes); } catch (e) {}
    });
    try { if (location.hash !== '#quiz') history.replaceState(null, '', location.pathname + location.search + '#quiz'); } catch (e) {}
    var co = o.querySelector('.lbrj-co'), volta = o.querySelector('.lbrj-v'), R = {}, passo = 0, B = null;
    co.innerHTML = '<p class="lbrj-p">Carregando os relógios…</p>';
    X.base(function (b) {
      if (ABERTA !== o) return;
      if (!b || !b.r || !b.r.length) { co.innerHTML = '<p class="lbrj-p">Não foi possível carregar os relógios agora. Tente de novo em instantes.</p>'; return; }
      B = b;
      var salvo = null;
      try { salvo = JSON.parse(sessionStorage.getItem('lbQuiz') || 'null'); } catch (e) {}
      if (salvo && salvo.u) {
        R = { uso: USOS.filter(function (u) { return u[0] === salvo.u; })[0], cm: salvo.c || 0, mov: salvo.m || 'x', fx: salvo.f >= 0 ? FAIXAS[salvo.f] : null };
        if (R.uso) { resultado(); return; }
      }
      R = {}; vai(0);
    });
    volta.addEventListener('click', function () { if (passo > 0) vai(passo - 1); });

    function topo(n, q, a) {
      volta.hidden = n === 0;
      return '<div class="lbrq-pg"><i style="width:' + ((n + 1) * 25) + '%"></i></div><h3 class="lbrq-q">' + q + '</h3><p class="lbrq-a">' + a + '</p>';
    }
    function opcoes(L, sel) {
      return '<div class="lbrq-o">' + L.map(function (l) {
        return '<button type="button" data-k="' + l[0] + '"' + (sel === l[0] ? ' class="sel"' : '') + '><span>' + l[1] + (l[2] ? '<small>' + l[2] + '</small>' : '') + '</span>' + (l[3] ? '<i>' + l[3] + '</i>' : '') + '</button>';
      }).join('') + '</div>';
    }
    function aoEscolher(f) {
      [].forEach.call(co.querySelectorAll('.lbrq-o button'), function (b) {
        b.addEventListener('click', function () { b.classList.add('sel'); var k = b.getAttribute('data-k'); setTimeout(function () { f(k); }, 140); });
      });
    }
    function vai(n) {
      passo = n;
      co.scrollTop = 0;
      if (n === 0) {
        co.innerHTML = topo(0, 'Onde ele vai mais com você?', '4 perguntas rápidas e mostramos os 3 relógios que mais combinam.') + opcoes(USOS.map(function (u) { return [u[0], u[1], u[2]]; }), R.uso && R.uso[0]);
        aoEscolher(function (k) { R.uso = USOS.filter(function (u) { return u[0] === k; })[0]; vai(1); });
      } else if (n === 1) {
        var cm = R.cm || X.pulsoCm() || 17;
        co.innerHTML = topo(1, 'Qual é a medida do seu pulso?', 'Passe uma fita métrica ou uma tira de papel em volta do pulso, logo acima do ossinho.') +
          '<div class="lbrq-cm"><b>' + String(cm).replace('.', ',') + '</b><small>cm</small></div><input type="range" min="14" max="22" step="0.5" value="' + cm + '" aria-label="Medida do pulso em centímetros">' +
          '<div class="lbrq-esc"><span>14 cm</span><span>18 cm</span><span>22 cm</span></div>' +
          '<div class="lbrq-bt"><button type="button" class="lbrj-b lbrq-ok">Continuar</button><button type="button" class="lbrj-b2 lbrq-ns">Não sei a medida</button></div>' +
          '<p class="lbrj-n">A medida fica guardada só neste aparelho, para mostrar em cada relógio como ele veste no seu pulso.</p>';
        var rg = co.querySelector('input'), nb = co.querySelector('.lbrq-cm b');
        rg.addEventListener('input', function () { nb.textContent = String(+rg.value).replace('.', ','); });
        co.querySelector('.lbrq-ok').addEventListener('click', function () { R.cm = +rg.value; X.guardaPulso(R.cm); vai(2); });
        co.querySelector('.lbrq-ns').addEventListener('click', function () { R.cm = 0; vai(2); });
      } else if (n === 2) {
        co.innerHTML = topo(2, 'Como você prefere o movimento?', 'É o que faz o relógio funcionar.') + opcoes(MOVS, R.mov);
        aoEscolher(function (k) { R.mov = k; vai(3); });
      } else {
        var disp = B.r.filter(function (x) { return x.disp && x.p > 0; });
        var L = FAIXAS.map(function (f, i) {
          var q = disp.filter(function (x) { return x.p >= f[0] && x.p <= f[1]; }).length;
          return q ? [String(i), f[2], '', q + (q > 1 ? ' relógios' : ' relógio')] : null;
        }).filter(Boolean);
        L.push(['x', 'Tanto faz', 'Quero ver o que mais combina comigo']);
        co.innerHTML = topo(3, 'Quanto você quer investir?', 'No Pix, todo relógio tem 10% off; no cartão, até 6x sem juros.') + opcoes(L, R.fx ? String(FAIXAS.indexOf(R.fx)) : '');
        aoEscolher(function (k) { R.fx = k === 'x' ? null : FAIXAS[+k]; resultado(); });
      }
    }
    function resultado() {
      passo = 4; volta.hidden = true; co.scrollTop = 0;
      try { sessionStorage.setItem('lbQuiz', JSON.stringify({ u: R.uso[0], c: R.cm || 0, m: R.mov || 'x', f: R.fx ? FAIXAS.indexOf(R.fx) : -1 })); } catch (e) {}
      var T = escolhe(B, R), ch = [R.uso[1]];
      if (R.cm) ch.push('Pulso de ' + X.cmTxt(R.cm));
      if (R.mov && R.mov !== 'x') ch.push(R.mov === 'a' ? 'Automático' : 'Quartzo ou solar');
      if (R.fx) ch.push(R.fx[2]);
      var SELO = ['Melhor combinação', '2ª opção', '3ª opção'];
      var zap = X.WA + encodeURIComponent('Olá! Fiz o quiz de relógios no site (' + ch.join(', ') + ') e fiquei entre: ' + T.map(function (t) { return X.nomeCurto(t.x.n); }).join('; ') + '. Pode me ajudar a escolher?');
      co.innerHTML = '<h3 class="lbrq-q">Os 3 relógios que mais combinam com você</h3><div class="lbrq-ch">' + ch.map(function (c) { return '<span>' + esc(c) + '</span>'; }).join('') + '</div>' +
        '<div class="lbrq-res">' + T.map(function (t, i) {
          var x = t.x;
          return '<div class="lbrq-r' + (i ? '' : ' um') + '"><a href="' + esc(x.u) + '" tabindex="-1"><img src="' + esc(X.foto(x)) + '" alt="' + esc(x.n) + '" width="104" height="104"></a><div><span class="lbrq-sl">' + SELO[i] + '</span>' +
            '<a class="lbrq-nm" href="' + esc(x.u) + '">' + esc(X.nomeCurto(x.n)) + '</a><div class="lbrq-et">' + esc(X.etiqueta(x, true)) + '</div>' +
            '<div class="lbrq-pr">' + rs(x.p) + '<small>' + rs(x.p * .9) + ' no Pix</small></div></div>' +
            (t.m.length ? '<ul class="lbrq-mt">' + t.m.map(function (m) { return '<li>' + esc(m) + '</li>'; }).join('') + '</ul>' : '') +
            '<a class="lbrj-b" href="' + esc(x.u) + '">Ver este relógio</a></div>';
        }).join('') + '</div><div class="lbrq-bt"><a class="lbrj-b2" href="' + esc(zap) + '" target="_blank" rel="noopener">Tirar dúvida no WhatsApp</a>' +
        '<button type="button" class="lbrj-b2 lbrq-rf">Refazer o quiz</button></div>';
      co.querySelector('.lbrq-rf').addEventListener('click', function () { try { sessionStorage.removeItem('lbQuiz'); } catch (e) {} R = {}; vai(0); });
    }
  }

  /* ================= 2. TAMANHO REAL NA TELA ================= */
  var CARTAO_L = 53.98, CARTAO_A = 85.6, MOEDA = 27; /* mm: lado menor e maior do cartão (ISO 7810 ID-1) e moeda de R$ 1 */
  function pxPorMm() { var v = parseFloat(le('lbPxMm')); return v >= 2.5 && v <= 12 ? v : 0; }
  function chute() { return Math.min(window.innerWidth, window.innerHeight) < 600 || /Mobi|Android|iPhone/i.test(navigator.userAgent) ? 6.05 : 3.78; }
  var COR = { azul: '#1D3557', preto: '#16171A', 'azul-gelo': '#BFDCEB', prata: '#DCDCD8', branco: '#F5F2EA', bege: '#E6D8BE', verde: '#1E4A38', cinza: '#5B6068', vermelho: '#7A1F1F', vinho: '#5E1B26', marrom: '#4A3222',
    dourado: '#C9A55C', champagne: '#E6D3A8', salmao: '#E8B9A0', rosa: '#E9C3C0', amarelo: '#E3B93B', laranja: '#D9742B', turquesa: '#3FB8B0', roxo: '#4B2E63' };
  var PUL = { metal: '#C6C9CE', couro: '#5B3B29', borracha: '#1C1C1E', tecido: '#46503F' };
  function claro(h) { var n = parseInt(h.slice(1), 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255 > .6; }
  function f1(v) { return (+v).toFixed(2).replace(/\.?0+$/, ''); }
  function medidas(r) {
    var d = r.diam;
    return { d: d, l2l: r.l2l || +(d * 1.18).toFixed(1), l2lReal: !!r.l2l, lg: r.lug || Math.round(d * .5 / 2) * 2, lgReal: !!r.lug };
  }
  function desenho(r, x, W, H, cm) {
    var M = medidas(r), d = M.d, Rc = d / 2, ct = x.ct || '', fn = x.fn || '', bisel = /m/.test(ct);
    var cd = COR[x.cor] || '#1B1F27', ci = claro(cd) ? '#1b1b1d' : '#F4F1EA', pu = PUL[x.pul || r.pul] || PUL.metal, metal = (x.pul || r.pul || 'metal') === 'metal';
    var rd = bisel ? Rc * .74 : Rc * .86, ww = cm ? cm * 3.2 : 0, s = '', i, a;
    s += '<defs><linearGradient id="lbrrA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F2F3F5"/><stop offset=".5" stop-color="#C2C5CB"/><stop offset="1" stop-color="#8E939B"/></linearGradient></defs>';
    if (ww) s += '<rect x="' + f1(-W / 2) + '" y="' + f1(-ww / 2) + '" width="' + f1(W) + '" height="' + f1(ww) + '" fill="#F4EDE3"/><path d="M' + f1(-W / 2) + ' ' + f1(-ww / 2) + 'H' + f1(W / 2) + 'M' + f1(-W / 2) + ' ' + f1(ww / 2) + 'H' + f1(W / 2) + '" stroke="#C9BBA6" stroke-width=".35" stroke-dasharray="1.6 1.2" fill="none"/>';
    /* pulseira: sobre o pulso ela some na borda; sem pulso informado, vai até o fim do desenho */
    var py = ww ? Math.max(ww / 2, M.l2l / 2 + 1) : H / 2;
    s += '<rect x="' + f1(-M.lg / 2) + '" y="' + f1(-py) + '" width="' + f1(M.lg) + '" height="' + f1(py * 2) + '" fill="' + pu + '"/>';
    if (metal) for (i = Math.ceil(-py / 4.2); i * 4.2 < py; i++) s += '<path d="M' + f1(-M.lg / 2) + ' ' + f1(i * 4.2) + 'h' + f1(M.lg) + '" stroke="#8E939B" stroke-width=".25"/>';
    /* alças */
    var lx = M.lg / 2, ly = M.l2l / 2, lb = Rc * .55;
    [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(function (k) {
      s += '<path d="M' + f1(k[0] * lx) + ' ' + f1(k[1] * lb) + 'L' + f1(k[0] * (lx + 3.6)) + ' ' + f1(k[1] * lb) + 'L' + f1(k[0] * (lx + 2.9)) + ' ' + f1(k[1] * (ly - .9)) +
        'Q' + f1(k[0] * (lx + 2.8)) + ' ' + f1(k[1] * ly) + ' ' + f1(k[0] * (lx + 1.9)) + ' ' + f1(k[1] * ly) + 'L' + f1(k[0] * lx) + ' ' + f1(k[1] * ly) + 'Z" fill="url(#lbrrA)" stroke="#7C8087" stroke-width=".2"/>';
    });
    /* coroa e botões */
    s += '<rect x="' + f1(Rc - .4) + '" y="-1.7" width="2.8" height="3.4" rx=".7" fill="url(#lbrrA)" stroke="#7C8087" stroke-width=".2"/>';
    if (/c/.test(fn)) [-1, 1].forEach(function (k) { s += '<rect x="-1.2" y="' + f1(-Rc - 1.9) + '" width="2.4" height="2.6" rx=".6" fill="url(#lbrrA)" stroke="#7C8087" stroke-width=".2" transform="rotate(' + (90 + k * 32) + ')"/>'; });
    /* caixa, bisel e mostrador */
    s += '<circle r="' + f1(Rc) + '" fill="url(#lbrrA)" stroke="#7C8087" stroke-width=".25"/>';
    if (bisel) {
      s += '<circle r="' + f1(Rc - .7) + '" fill="#1B1D22"/>';
      for (i = 0; i < 12; i++) { a = i * 30; s += '<rect x="-.35" y="' + f1(-Rc + 1.3) + '" width=".7" height="' + f1(i ? Rc * .11 : Rc * .16) + '" fill="#E9E4D8" transform="rotate(' + a + ')"/>'; }
    }
    s += '<circle r="' + f1(rd) + '" fill="' + cd + '" stroke="' + (bisel ? '#0d0e10' : '#9A9FA6') + '" stroke-width=".3"/>';
    for (i = 0; i < 12; i++) s += '<rect x="' + f1(i % 3 ? -.45 : -.7) + '" y="' + f1(-rd + 1.1) + '" width="' + f1(i % 3 ? .9 : 1.4) + '" height="' + f1(rd * (i % 3 ? .15 : .2)) + '" rx=".2" fill="' + ci + '" transform="rotate(' + (i * 30) + ')"/>';
    if (/c/.test(fn)) [[-rd * .46, 0], [rd * .46, 0], [0, rd * .46]].forEach(function (p) { s += '<circle cx="' + f1(p[0]) + '" cy="' + f1(p[1]) + '" r="' + f1(rd * .22) + '" fill="none" stroke="' + ci + '" stroke-width=".3" opacity=".7"/>'; });
    else if (/d/.test(fn)) s += '<rect x="' + f1(rd * .52) + '" y="-1.5" width="3.4" height="3" rx=".4" fill="#F4F1EA" stroke="#9A9FA6" stroke-width=".15"/>';
    /* ponteiros na hora certa */
    s += '<g class="h"><rect x="-.75" y="' + f1(-rd * .5) + '" width="1.5" height="' + f1(rd * .5 + 1.5) + '" rx=".7" fill="' + ci + '"/></g>' +
      '<g class="m"><rect x="-.55" y="' + f1(-rd * .8) + '" width="1.1" height="' + f1(rd * .8 + 1.5) + '" rx=".5" fill="' + ci + '"/></g>' +
      '<g class="s"><rect x="-.18" y="' + f1(-rd * .88) + '" width=".36" height="' + f1(rd * .88 + 3.5) + '" fill="#C9A55C"/></g><circle r="1" fill="' + ci + '"/><circle r=".4" fill="#C9A55C"/>';
    return s;
  }
  function real(r) {
    if (!r || !r.diam) return;
    var T = 0;
    var o = folha('lbrr', 'Tamanho real', 'Do tamanho que ele é', function () { clearInterval(T); });
    var co = o.querySelector('.lbrj-co'), x = {};
    X.base(function (B) { if (B && B.u && B.u[location.pathname]) { x = B.u[location.pathname]; if (ABERTA === o && o.__m) o.__m(); } });
    var v = pxPorMm();
    if (v) mostra(v); else calibra(chute());

    function calibra(v0) {
      clearInterval(T); o.__m = null;
      var v = v0;
      co.innerHTML = '<p class="lbrj-p">Cada tela tem um tamanho. Para o relógio aparecer na medida certa, ajuste uma vez só: <b>encoste um cartão em pé</b> (de banco ou de crédito) na tela e arraste até a moldura ficar da largura do cartão.</p>' +
        '<div class="lbrr-area"><div class="lbrr-ct"><span>Encoste o cartão aqui,<br>em pé</span></div></div>' +
        '<div class="lbrr-aj"><button type="button" class="lbrr-me" aria-label="Diminuir">&minus;</button><input type="range" min="3" max="9" step="0.01" value="' + v + '" aria-label="Ajuste do tamanho"><button type="button" class="lbrr-ma" aria-label="Aumentar">+</button></div>' +
        '<button type="button" class="lbrj-b lbrr-ok">Pronto, ficou da largura do cartão</button><p class="lbrj-n">O ajuste fica guardado neste aparelho e vale para todos os relógios.</p>';
      var ct = co.querySelector('.lbrr-ct'), rg = co.querySelector('input');
      function poe() {
        ct.style.width = (CARTAO_L * v).toFixed(1) + 'px';
        ct.style.height = Math.min(CARTAO_A * v, Math.max(170, window.innerHeight * .4)).toFixed(0) + 'px';
        ct.style.borderRadius = (3.2 * v).toFixed(1) + 'px ' + (3.2 * v).toFixed(1) + 'px 0 0';
      }
      poe();
      rg.addEventListener('input', function () { v = +rg.value; poe(); });
      function passo(k) { v = Math.max(3, Math.min(9, +(v + k).toFixed(2))); rg.value = v; poe(); }
      co.querySelector('.lbrr-me').addEventListener('click', function () { passo(-.03); });
      co.querySelector('.lbrr-ma').addEventListener('click', function () { passo(.03); });
      co.querySelector('.lbrr-ok').addEventListener('click', function () { guarda('lbPxMm', String(v)); mostra(v); });
    }
    function mostra(v) {
      clearInterval(T);
      var M = medidas(r), cm = X.pulsoCm();
      function monta() {
        var W = Math.max(40, co.clientWidth / v), H = Math.max(M.l2l + 26, cm ? cm * 3.2 + 12 : 0, M.d + 30);
        var leg = [M.l2lReal ? X.mm(M.l2l) + ' de ponta a ponta' : '', M.lgReal ? 'pulseira de ' + M.lg + ' mm' : '', r.esp ? X.mm(r.esp) + ' de espessura' : ''].filter(Boolean).join(' · ');
        co.innerHTML = '<div class="lbrr-pal"><svg width="' + (W * v).toFixed(1) + '" height="' + (H * v).toFixed(1) + '" viewBox="' + f1(-W / 2) + ' ' + f1(-H / 2) + ' ' + f1(W) + ' ' + f1(H) + '" role="img" aria-label="Desenho do relógio em tamanho real">' + desenho(r, x, W, H, cm) + '</svg></div>' +
          '<div class="lbrr-reg" style="width:' + (M.d * v).toFixed(1) + 'px"></div><p class="lbrr-leg"><b>Caixa de ' + X.mm(M.d) + '</b>' + esc(leg) + '</p>' +
          '<p class="lbrj-p">' + (cm ? 'A faixa clara é o seu pulso de <b>' + X.cmTxt(cm) + '</b>, visto de cima. ' : '') + 'Encoste o pulso ao lado da tela e compare: o desenho está do tamanho do relógio de verdade.' +
          (cm ? '' : ' Informe a medida do seu pulso no simulador da página para ver os dois juntos.') + ' O desenho é ilustrativo: aqui, o que vale é a medida.</p>' +
          '<div class="lbrr-cf"><i style="width:' + (MOEDA * v).toFixed(1) + 'px;height:' + (MOEDA * v).toFixed(1) + 'px"></i><span><b>Quer conferir?</b> Uma moeda de R$ 1 cobre este círculo certinho. Se não cobrir, ajuste a tela de novo.</span></div>' +
          '<button type="button" class="lbrj-b2 lbrr-rc">Ajustar a tela de novo</button>';
        co.querySelector('.lbrr-rc').addEventListener('click', function () { calibra(v); });
        hora();
      }
      function hora() {
        var sv = co.querySelector('.lbrr-pal svg'); if (!sv) return;
        var t = new Date(), sg = t.getSeconds(), mi = t.getMinutes() + sg / 60, ho = (t.getHours() % 12) + mi / 60;
        sv.querySelector('.h').setAttribute('transform', 'rotate(' + (ho * 30).toFixed(2) + ')');
        sv.querySelector('.m').setAttribute('transform', 'rotate(' + (mi * 6).toFixed(2) + ')');
        sv.querySelector('.s').setAttribute('transform', 'rotate(' + (sg * 6) + ')');
      }
      monta();
      o.__m = monta;
      T = setInterval(hora, 1000);
    }
  }

  /* ================= 3. GUIA DO PROPRIETÁRIO (?guia=1) ================= */
  function limpo(e) { return (e.textContent || '').replace(/\s+/g, ' ').trim(); }
  function itemHtml(li) {
    var t = limpo(li), s = li.querySelector('strong, b'), st = s ? limpo(s) : '';
    if (st && t.indexOf(st) === 0) return '<b>' + esc(st.replace(/[:\s]+$/, '')) + (/[.!?]$/.test(st) ? '' : '.') + '</b> ' + esc(t.slice(st.length).replace(/^[\s:]+/, ''));
    return esc(t);
  }
  function mesAno(d) { return ('0' + (d.getMonth() + 1)).slice(-2) + '/' + d.getFullYear(); }
  function guia(r) {
    if (document.querySelector('.lbrgd')) return;
    var d = document.getElementById('descricao');
    if (!d || !r) return;
    var nome = X.nomeCurto(r.nome), og = document.querySelector('meta[property="og:image"]'), img = og ? og.getAttribute('content') : '';
    if (!img) { var im = document.querySelector('#imagemProduto, .conteiner-imagem img'); img = im ? im.src : ''; }
    var et = [X.TN[r.tipo] ? X.TN[r.tipo] + (r.origem ? ' ' + r.origem : '') : '', r.diam ? X.mm(r.diam) : '', r.agua ? r.agua + ' m' : '', X.VN[r.vidro] ? 'Vidro ' + X.VN[r.vidro].toLowerCase() : ''].filter(Boolean).join(' · ');
    var h = '';
    /* ficha técnica, como está na descrição */
    var sf = X.secao(d, /^Ficha t[ée]cnica/i), ul = sf && sf.um('UL'), F = [];
    if (ul) [].forEach.call(ul.children, function (li) {
      var s = li.querySelector('strong'); if (!s) return;
      var k = limpo(s).replace(/[:\s]+$/, ''), t = limpo(li), val = t.slice(t.indexOf(limpo(s)) + limpo(s).length).replace(/^[\s:]+/, '');
      if (k && val) F.push('<li><b>' + esc(k) + '</b>' + esc(val.charAt(0).toUpperCase() + val.slice(1)) + '</li>');
    });
    if (F.length) h += '<h2>Ficha técnica</h2><ul class="lbrgd-fi">' + F.join('') + '</ul>';
    /* cuidados e água: o mesmo texto da página, aberto */
    var cu = document.createElement('div');
    cu.innerHTML = X.cuidados(r);
    var hc = '';
    [].forEach.call(cu.querySelectorAll('details'), function (dt) {
      var sm = dt.querySelector('summary');
      hc += '<h3>' + esc(limpo(sm)) + '</h3>';
      [].forEach.call(dt.children, function (c) { if (c !== sm) hc += c.outerHTML; });
    });
    if (hc) h += '<h2>Cuidados com o seu relógio</h2>' + hc;
    /* para que foi feito */
    var su = X.secao(d, /^Feito para qu/i), lu = su && su.um('UL');
    if (lu) {
      h += '<h2>Feito para quê e onde usar</h2>';
      su.nos.forEach(function (n) { if (n.tagName === 'P') h += '<p>' + esc(limpo(n)) + '</p>'; });
      var gi = [], gt = [];
      [].forEach.call(lu.children, function (li) {
        var c = li.cloneNode(true), s = c.querySelector('strong'), ideal = li.classList.contains('id') || /^Ideal/i.test(s ? limpo(s) : '');
        if (s) s.textContent = limpo(s).replace(/^Ideal para (o |a |os |as )?/i, '').replace(/^Também (vai bem|acompanha|combina)( com)? /i, '').replace(/^./, function (m) { return m.toUpperCase(); });
        (ideal ? gi : gt).push('<li>' + itemHtml(c) + '</li>');
      });
      if (gi.length) h += '<h3>Ideal para</h3><ul>' + gi.join('') + '</ul>';
      if (gt.length) h += '<h3>Também vai bem</h3><ul>' + gt.join('') + '</ul>';
    }
    /* história do modelo e da marca */
    var sd = X.secao(d, /^O dossi[êe] d/i), st = X.secao(d, /^A .{2,40} em \d+ momentos$/), sv = X.secao(d, /^Voc[êe] sabia/i), hh = '';
    if (sd) sd.nos.forEach(function (n) { if (n.tagName === 'P') hh += '<p>' + esc(limpo(n)) + '</p>'; });
    if (st) {
      var ol = st.um('OL');
      hh += '<h3>' + esc(X.titulo(st.h)) + '</h3>';
      st.nos.forEach(function (n) { if (n.tagName === 'P') hh += '<p>' + esc(limpo(n)) + '</p>'; });
      if (ol) hh += '<ol class="lbrgd-tl">' + [].map.call(ol.children, function (li) {
        var s = li.querySelector('strong'), a = s ? limpo(s).replace(/[:\s]+$/, '') : '', t = limpo(li);
        return '<li><b>' + esc(a) + '</b><span>' + esc(a ? t.slice(t.indexOf(limpo(s)) + limpo(s).length).replace(/^[\s:]+/, '') : t) + '</span></li>';
      }).join('') + '</ol>';
    }
    if (sv) { var lv = sv.um('UL'); if (lv) hh += '<h3>Você sabia?</h3><ul>' + [].map.call(lv.children, function (li) { return '<li>' + itemHtml(li) + '</li>'; }).join('') + '</ul>'; }
    if (hh) h += '<h2>A história do seu relógio</h2>' + hh;

    var chave = 'lbGuia:' + location.pathname, S = {};
    try { S = JSON.parse(le(chave) || '{}') || {}; } catch (e) {}
    var url = location.origin + location.pathname;
    var zap = 'https://wa.me/?text=' + encodeURIComponent('Guia do proprietário do ' + nome + ': ' + url + '?guia=1');
    var pg = document.createElement('div');
    pg.className = 'lbrgd';
    pg.innerHTML = '<div class="lbrgd-ac"><a href="' + esc(location.pathname) + '">&#8249; Voltar ao relógio</a><button type="button" class="pri lbrgd-im">Imprimir ou salvar em PDF</button><a href="' + esc(zap) + '" target="_blank" rel="noopener">Enviar pelo WhatsApp</a></div>' +
      '<article class="lbrgd-pg"><div class="lbrgd-top"><div><div class="lbrgd-lg">@LOJABIT</div><div class="lbrgd-k">Guia do proprietário</div><h1>' + esc(nome) + '</h1><p class="lbrgd-et">' + esc(et) + '</p></div>' +
      (img ? '<img src="' + esc(img) + '" alt="' + esc(r.nome) + '">' : '') + '</div>' +
      '<div class="lbrgd-dono"><label>Proprietário<input type="text" name="n" autocomplete="name" placeholder="Seu nome" value="' + esc(S.n || '') + '"></label>' +
      '<label>Data da compra<input type="date" name="d" value="' + esc(S.d || '') + '"></label><label>Pedido nº<input type="text" name="p" inputmode="numeric" placeholder="Número do pedido" value="' + esc(S.p || '') + '"></label></div>' +
      '<div class="lbrgd-ag"></div>' + h +
      '<div class="lbrgd-rod"><p><b>Na caixa:</b> relógio original com caixa, manual e certificado.</p><p><b>Garantia legal:</b> 90 dias, contados a partir do recebimento.</p>' +
      '<p><b>Atendimento @LOJABIT:</b> WhatsApp (24) 98122-6521 · ' + esc(location.host.replace(/^www\./, '')) + '</p><p>Este guia está sempre atualizado em ' + esc(url.replace(/^https?:\/\//, '')) + '</p></div></article>';
    document.body.appendChild(pg);
    document.documentElement.classList.add('lbrgd-on');
    window.scrollTo(0, 0);
    var ag = pg.querySelector('.lbrgd-ag');
    function agenda() {
      var v = pg.querySelector('input[name=d]').value, m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v), t = '';
      function mais(a) { return mesAno(new Date(+m[1] + a, +m[2] - 1, 1)); }
      if (m) {
        if (r.tipo === 'auto' || r.tipo === 'manual') t = '<b>Revisão sugerida:</b> entre ' + mais(4) + ' e ' + mais(5) + ', para o movimento seguir funcionando bem por muitos anos.';
        else if (r.tipo === 'quartzo') t = '<b>Troca de pilha prevista:</b> entre ' + mais(2) + ' e ' + mais(3) + ', em relojoaria de confiança.';
        else if (r.tipo === 'solar') t = '<b>Sem troca de pilha:</b> a luz mantém a carga. É só deixar o relógio perto da claridade.';
      }
      ag.innerHTML = t;
    }
    [].forEach.call(pg.querySelectorAll('.lbrgd-dono input'), function (i) {
      i.addEventListener('input', function () {
        var o = {}; [].forEach.call(pg.querySelectorAll('.lbrgd-dono input'), function (j) { if (j.value) o[j.name] = j.value; });
        guarda(chave, JSON.stringify(o)); agenda();
      });
    });
    agenda();
    pg.querySelector('.lbrgd-im').addEventListener('click', function () { window.print(); });
    document.title = 'Guia do proprietário: ' + nome;
  }

  window.__lbRex = { quiz: quiz, real: real, guia: guia };
})();
}catch(e){window.console&&console.error("lojabit codigo 1799006",e)};
window.lbE3x=1;
