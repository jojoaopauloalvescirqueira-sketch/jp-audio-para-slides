(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('dados').textContent);
  const svg = document.getElementById('palco');
  const NS = 'http://www.w3.org/2000/svg';
  const [width, height] = data.dimensoes;
  const landscape = width > height;
  const colors = data.paleta;
  const clamped = (x) => Math.max(0, Math.min(1, x));
  const smoothstep = (x) => { const u = clamped(x); return u * u * (3 - 2 * u); };
  const mix = (a, b, x) => a + (b - a) * x;
  const colorMix = (a, b, u) => {
    const from = a.slice(1).match(/../g).map((v) => parseInt(v, 16));
    const to = b.slice(1).match(/../g).map((v) => parseInt(v, 16));
    return '#' + from.map((v, i) => Math.round(mix(v, to[i], u)).toString(16).padStart(2, '0')).join('');
  };
  function node(name, attrs, parent) {
    const element = document.createElementNS(NS, name);
    set(element, attrs);
    if (parent) parent.append(element);
    return element;
  }
  function set(element, attrs) {
    for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value);
  }
  function text(parent, value, x, y, maxWidth, size, options = {}) {
    const label = node('text', { x, y, 'font-size': size, 'text-anchor': options.anchor || 'middle',
      'font-weight': options.weight || 700, fill: options.fill || colors.osso }, parent);
    label.textContent = value;
    const measure = label.getComputedTextLength();
    if (measure > maxWidth) set(label, { 'font-size': size * maxWidth / measure });
    return label;
  }
  function rectangle(parent, x, y, w, h, fill, rx = 0) {
    return node('rect', { x, y, width: w, height: h, fill, rx }, parent);
  }
  function line(parent, x1, y1, x2, y2, color, stroke = 4) {
    return node('line', { x1, y1, x2, y2, stroke: color, 'stroke-width': stroke,
      'stroke-linecap': 'round', pathLength: 1 }, parent);
  }
  function circle(parent, cx, cy, r, fill) {
    return node('circle', { cx, cy, r, fill }, parent);
  }

  function placement(row, state) {
    if (!landscape) return [state.x, row.y, row.w, row.h];
    return [160 + (state.x - 64) * 1600 / 828, 148 + (row.y - 440) * 730 / 880,
      row.w * 1600 / 828, row.h * 730 / 880];
  }

  function pose(row) {
    return { x: row.x, sit: row.estado === 'sentado' ? 1 : 0, opacity: row.visivel === false ? 0 : 1,
      halo: 0, draw: 1, color: colors[row.cor || 'osso'], spin: null, pulse: null,
      word: row.texto || '', note: row.anotacao || '', flip: null, bob: 0 };
  }

  const limits = { aparecer: 0.24, sumir: 0.22, sentar: 0.44, levantar: 0.40,
    andar: 0.60, destacar: 0.32, mudar_cor: 0.32, desenhar: 0.35, trocar_letra: 0.35 };
  const channels = { aparecer: 'opacity', sumir: 'opacity', sentar: 'sit', levantar: 'sit',
    andar: 'x', destacar: 'halo', mudar_cor: 'color', desenhar: 'draw',
    girar: 'spin', pulsar: 'pulse', palavra: 'word', trocar_letra: 'word', anotar: 'note' };
  const durationScale = { sobrio: 1.3, didatico: 1, energetico: 0.78 }[data.tom] || 1;

  // Each track is a series of [time, value] keys. A later action interrupts
  // the prior transition at its actual value, so seeking is independent of playback.
  function sample(track, t, channel) {
    let last = track[0];
    for (let i = 1; i < track.length; i++) {
      const next = track[i];
      if (t < next[0]) {
        const u = smoothstep((t - last[0]) / (next[0] - last[0]));
        return typeof last[1] === 'number' ? mix(last[1], next[1], u) :
          channel === 'color' ? colorMix(last[1], next[1], u) : last[1];
      }
      last = next;
    }
    return last[1];
  }
  function prepare(row, actions) {
    const initial = pose(row);
    const tracks = Object.fromEntries(Object.entries(initial).map(([key, value]) => [key, [[-1, value]]]));
    const flip = [], walks = [];
    for (const item of actions) {
      const t = item.tempo;
      const channel = channels[item.acao];
      const track = tracks[channel];
      let from = sample(track, t, channel);
      while (track.length > 1 && track[track.length - 1][0] >= t) track.pop();
      const finish = t + (limits[item.acao] || 0) * durationScale;
      const values = { aparecer: 1, sumir: 0, sentar: 1, levantar: 0,
        andar: item.valor, destacar: 1, mudar_cor: colors[item.valor],
        desenhar: 1, girar: t, pulsar: t, palavra: item.valor,
        trocar_letra: item.valor, anotar: item.valor };
      if (item.acao === 'desenhar') {
        from = 0;
        if (track.length === 1) track[0][1] = 0;
      }
      if (item.acao === 'trocar_letra') flip.push([t, finish, from, item.valor]);
      if (item.acao === 'andar') walks.push([t, finish]);
      track.push([t, from]);
      track.push([channel === 'word' ? t : finish, values[item.acao]]);
    }
    return (t) => {
      const state = Object.fromEntries(Object.entries(tracks).map(([key, keys]) => [key, sample(keys, t, key)]));
      state.flip = flip.find(([start, end]) => start <= t && t < end);
      const walk = walks.find(([start, end]) => start <= t && t < end);
      if (walk) {
        const u = (t - walk[0]) / (walk[1] - walk[0]);
        state.bob = 3 * Math.sin(Math.PI * u) * Math.abs(Math.sin(3 * Math.PI * u));
      }
      return state;
    };
  }

  function figure(parent, row, state, defs) {
    if (state.halo) {
      const key = 'halo';
      if (!defs.querySelector('#halo')) {
        const gradient = node('radialGradient', { id: key }, defs);
        node('stop', { offset: '0%', 'stop-color': colors.acento, 'stop-opacity': .42 }, gradient);
        node('stop', { offset: '100%', 'stop-color': colors.acento, 'stop-opacity': 0 }, gradient);
      }
      const glow = circle(parent, 50, 50, 49, 'url(#halo)');
      set(glow, { opacity: state.halo });
    }
    const s = state.sit;
    const baseline = mix(87, 72, s) - state.bob;
    const head = mix(24, 39, s) - state.bob;
    circle(parent, mix(50, 42, s), head, 12, state.color);
    rectangle(parent, mix(35, 28, s), head + 15, 30, baseline - head - 15, state.color, 15);
    if (s > 0) {
      const legs = node('g', { opacity: s }, parent);
      rectangle(legs, 44, baseline - 9, 30, 10, state.color, 5);
      rectangle(legs, 65, baseline - 4, 9, 21, state.color, 4.5);
    }
    if (row.rotulo) text(parent, row.rotulo, 50, 98, 90, 9, { fill: colors.suave });
  }

  function drawText(parent, state, t) {
    const [, , width] = parent.getAttribute('viewBox').split(' ').map(Number);
    const center = width / 2;
    const wordY = state.note ? 56 : 67;
    const size = state.note ? 51 : 58;
    const options = { fill: state.color, weight: 800 };
    if (!state.flip) {
      text(parent, state.word, center, wordY, width * .96, size, options);
    } else {
      const [start, end, oldWord, newWord] = state.flip;
      const u = clamped((t - start) / (end - start));
      const active = u < .5 ? oldWord : newWord;
      const oldLetters = [...oldWord], newLetters = [...newWord];
      const sizing = text(parent, active, center, wordY, width * .96, size, options);
      const fitting = Number(sizing.getAttribute('font-size'));
      const letters = [...active].map((letter, index) => {
        const glyph = text(parent, letter, 0, wordY, width, fitting, { ...options, anchor: 'start' });
        const changed = oldLetters[index] !== newLetters[index];
        return { glyph, changed, length: glyph.getComputedTextLength() };
      });
      sizing.remove();
      let x = center - letters.reduce((sum, glyph) => sum + glyph.length, 0) / 2;
      for (const { glyph, changed, length } of letters) {
        set(glyph, { x });
        if (changed) {
          const scale = Math.max(.001, Math.abs(Math.cos(u * Math.PI)));
          const axis = wordY - fitting * .34;
          set(glyph, { fill: colors.acento, transform: 'translate(0 ' + axis + ') scale(1 ' + scale +
            ') translate(0 ' + -axis + ')' });
        }
        x += length;
      }
    }
    if (state.note) text(parent, state.note, center, 85, width * .94, 13, { fill: colors.suave });
  }

  function drawShape(parent, row, state, t, defs) {
    if (row.tipo === 'figura') {
      figure(parent, row, state, defs);
    } else if (row.tipo === 'texto') {
      drawText(parent, state, t);
    } else if (row.tipo === 'banco') {
      rectangle(parent, 6, 37, 88, 11, state.color, 5);
      rectangle(parent, 14, 46, 7, 36, state.color, 3);
      rectangle(parent, 79, 46, 7, 36, state.color, 3);
    } else if (row.tipo === 'relogio') {
      const outline = circle(parent, 50, 50, 39, 'none');
      set(outline, { stroke: state.color, 'stroke-width': 5 });
      circle(parent, 50, 50, 4, state.color);
      const pointer = line(parent, 50, 50, 50, 22, state.color, 5);
      if (state.spin !== null) set(pointer, { transform: 'rotate(' + ((t - state.spin) * 215) + ' 50 50)' });
    } else if (row.tipo === 'reticencias') {
      for (let i = 0; i < 3; i++) {
        const dot = circle(parent, 22 + 28 * i, 50, 7, state.color);
        if (state.pulse !== null) set(dot, { opacity: .35 + .65 * (1 + Math.sin((t - state.pulse) * 7 - i)) / 2 });
      }
    } else if (row.tipo === 'coluna') {
      const outline = rectangle(parent, 3, 3, 94, 94, 'none', 8);
      set(outline, { stroke: colors.linha, 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke' });
    } else {
      const segments = {
        direita: [8, 50, 90, 50], esquerda: [92, 50, 10, 50],
        cima: [50, 91, 50, 10], baixo: [50, 9, 50, 90],
      };
      const points = segments[row.direcao || 'direita'];
      const stroke = line(parent, ...points, state.color, row.tipo === 'divisoria' ? 1 : 5);
      set(stroke, { 'stroke-dasharray': row.tipo === 'divisoria' ? '0.04 0.04' : '1',
        'stroke-dashoffset': 1 - state.draw });
      if (row.tipo === 'seta' && state.draw > .88) {
        const [, , x, y] = points;
        const angle = { direita: 0, esquerda: 180, cima: -90, baixo: 90 }[row.direcao || 'direita'];
        node('path', { d: 'M-10 -7 L0 0 L-10 7', stroke: state.color,
          'stroke-width': 4, 'stroke-linecap': 'round', fill: 'none',
          transform: 'translate(' + x + ' ' + y + ') rotate(' + angle + ')' }, parent);
      }
    }
  }

  const scenes = data.cenas.map((scene) => ({ ...scene, states: scene.elementos.map((row) =>
    prepare(row, scene.acoes.filter((item) => item.alvo === row.id))) }));

  function sceneIndex(t) {
    let lo = 0, hi = scenes.length;
    while (lo + 1 < hi) {
      const mid = (lo + hi) >> 1;
      if (scenes[mid].inicio <= t) lo = mid; else hi = mid;
    }
    return lo;
  }

  function captions(scene, t) {
    const words = data.palavras;
    let i = scene.palavra;
    while (i + 1 < scene.fim_palavra && words[i + 1].tempo <= t) i++;
    const group = scene.palavra + 4 * Math.floor((i - scene.palavra) / 4);
    const label = text(svg, '', landscape ? 960 : 478, landscape ? 985 : 1385,
      landscape ? 1420 : 790, landscape ? 35 : 39);
    for (let k = group; k < Math.min(group + 4, scene.fim_palavra); k++) {
      const span = node('tspan', { fill: k === i ? colors.acento : colors.osso,
        opacity: words[k].tempo <= t ? 1 : .45 }, label);
      span.textContent = (k === group ? '' : ' ') + words[k].texto;
    }
    const available = landscape ? 1420 : 790;
    if (label.getComputedTextLength() > available) set(label, { textLength: available, lengthAdjust: 'spacingAndGlyphs' });
  }

  window.render = (time) => {
    const t = Math.max(0, Math.min(data.duracao, Number(time)));
    const index = sceneIndex(t);
    const scene = scenes[index];
    svg.replaceChildren();
    const defs = node('defs', {}, svg);
    rectangle(svg, 0, 0, width, height, colors.fundo);
    const x = landscape ? 160 : 70, y = landscape ? 82 : 376;
    const bar = landscape ? 1600 : 805;
    rectangle(svg, x, y, bar, 3, colors.linha, 1.5);
    rectangle(svg, x, y, bar * t / data.duracao, 3, colors.acento, 1.5);
    text(svg, 'CENA ' + scene.id, x, y + 45, 680, 27, { anchor: 'start', fill: colors.suave });
    scene.elementos.forEach((row, i) => {
      const state = scene.states[i](t);
      if (state.opacity <= 0) return;
      const [ex, ey, w, h] = placement(row, state);
      const contentWidth = row.tipo === 'texto' ? 100 * w / h : 100;
      const stretch = ['braco', 'linha', 'divisoria', 'coluna'].includes(row.tipo);
      const frame = node('svg', { x: ex, y: ey, width: w, height: h,
        viewBox: '0 0 ' + contentWidth + ' 100', preserveAspectRatio: stretch ? 'none' : 'xMidYMid meet',
        opacity: state.opacity, 'data-elemento': row.id }, svg);
      drawShape(frame, row, state, t, defs);
    });
    if (data.legenda) captions(scene, t);
    if (data.marca) node('image', { href: data.marca, x: width - (landscape ? 270 : 240),
      y: landscape ? 940 : 1390, width: 110, height: 35, opacity: .55 }, svg);
    return scene.id;
  };

  const play = document.getElementById('assistir');
  const restart = document.getElementById('recomecar');
  const seek = document.getElementById('tempo');
  const timeLabel = document.getElementById('posicao');
  const audio = document.getElementById('narracao');
  let current = 0, previous, playing = false, request;
  seek.max = data.duracao;
  function show(t) {
    current = Math.min(data.duracao, Math.max(t, 0));
    window.render(current);
    seek.value = current;
    timeLabel.textContent = current.toFixed(2) + ' / ' + data.duracao.toFixed(2) + ' s';
  }
  function pause() {
    playing = false;
    cancelAnimationFrame(request);
    if (audio) audio.pause();
    play.textContent = 'Assistir';
  }
  function tick(now) {
    if (!playing) return;
    show(audio ? audio.currentTime : current + (now - previous) / 1000);
    previous = now;
    if (current >= data.duracao || (audio && audio.ended)) pause();
    else request = requestAnimationFrame(tick);
  }
  function start() {
    if (current >= data.duracao) show(0);
    playing = true;
    play.textContent = 'Pausar';
    if (audio) { audio.currentTime = current; audio.play().catch(() => pause()); }
    previous = performance.now();
    request = requestAnimationFrame(tick);
  }
  function goto(t) {
    pause();
    show(t);
    if (audio) audio.currentTime = t;
  }
  play.addEventListener('click', () => playing ? pause() : start());
  restart.addEventListener('click', () => { goto(0); start(); });
  seek.addEventListener('input', () => goto(Number(seek.value)));
  document.querySelectorAll('[data-cena]').forEach((button) =>
    button.addEventListener('click', () => goto(scenes[Number(button.dataset.cena)].inicio)));
  show(0);
})();
