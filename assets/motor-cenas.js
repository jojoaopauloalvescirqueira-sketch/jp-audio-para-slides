(() => {
  'use strict';
  const kits = new Map();
  const NS = 'http://www.w3.org/2000/svg';
  window.MotorCenas = {
    registrarKit(name, kit) {
      if (kits.has(name) || typeof kit !== 'function') throw new Error('Kit inválido ou já registrado.');
      kits.set(name, kit);
    },
    iniciar(data) {
      const svg = document.getElementById('palco');
      const [width, height] = data.dimensoes;
      const landscape = width > height;
      const colors = data.paleta;
      const kit = kits.get(data.kit);
      if (!kit) throw new Error('Kit ausente.');
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
      function layer(parent, attrs, {x=0,y=0,scale=1,rotation=0,opacity=1,parallax=0}={}, camera=null) {
        const dx = camera ? (width/2-camera.x) * parallax : 0;
        const dy = camera ? (height/2-camera.y) * parallax : 0;
        return node('g', {...attrs, opacity,
          transform:`translate(${x+dx} ${y+dy}) rotate(${rotation}) scale(${scale})`}, parent);
      }
      function cameraLayer(parent, {zoom=1,x=.5,y=.5}={}) {
        return node('g',{transform:`translate(${width/2} ${height/2}) scale(${zoom}) translate(${-x*width} ${-y*height})`},parent);
      }
      const api = {data, width, height, landscape, colors, node, set, text, rectangle, line, circle,
        clamped, smoothstep, mix, colorMix, sample, layer, cameraLayer};
      const prepare = kit(api);
      const scenes = [];
      for (const scene of data.cenas) scenes.push({ ...scene, paint: prepare(scene, scenes[scenes.length-1]) });
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
        if (data.legendas) {
          const frame=Math.floor(t*30+1e-7);
          if (frame<(data.legenda_a_partir ?? 0)) return;
          const group=data.legendas.findLast(row=>row.inicio<=frame);
          if (!group || frame>=group.fim) return;
          const active=new Set(group.linhas.flat().filter(index=>words[index].quadro<=frame));
          const latest=Math.max(...[...active].map(index=>words[index].quadro));
          group.linhas.forEach((indices,lineIndex)=>{
            const label=text(svg,'',landscape?960:478,(landscape?960:1375)+lineIndex*(landscape?35:44),
              landscape?1420:790,landscape?31:38);
            label.dataset.legenda='sim';
            indices.forEach((index,i)=>{
              const shown=active.has(index);
              const span=node('tspan',{fill:words[index].quadro===latest?colors.acento:colors.osso,
                visibility:shown?'visible':'hidden','data-palavra':index},label);
              span.textContent=(i?' ':'')+ (words[index].exibicao ?? words[index].texto);
            });
            const available=landscape?1420:790;
            if (label.getComputedTextLength()>available) set(label,{textLength:available,lengthAdjust:'spacingAndGlyphs'});
          });
          return;
        }
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


      function render(time) {
        const t = Math.max(0, Math.min(data.duracao, Number(time)));
        const index = sceneIndex(t);
        const scene = scenes[index];
        svg.replaceChildren();
        const defs = node('defs', {}, svg);
        rectangle(svg, 0, 0, width, height, colors.fundo);
        const world = node('g', {}, svg);
        scene.paint(world, defs, t, true, scenes[index+1]);
        const previous = scenes[index-1];
        const elapsed = t - scene.inicio;
        const transition = previous?.paint.transition;
        const transitionDuration = transition?.duration ?? .24;
        if (previous && previous.saida !== 'corte' && elapsed < transitionDuration) {
          const u = smoothstep(elapsed/transitionDuration);
          const overlap = node('g', {opacity:1-u}, svg);
          if (previous.saida === 'deslize') set(overlap, {transform:`translate(${-(transition?.distance ?? width)*u} 0)`});
          const suppressed = scene.paint.events && previous.paint.events;
          if (suppressed) overlap.dataset.transicao = 'saida';
          previous.paint(overlap, defs, previous.fim - .001, false, scene);
        }
        if (data.interface_cena !== false) {
          const x = landscape ? 160 : 70, y = landscape ? 82 : 376;
          const bar = landscape ? 1600 : 805;
          rectangle(svg, x, y, bar, 3, colors.linha, 1.5).setAttribute('data-progresso','sim');
          rectangle(svg, x, y, bar * (data.repouso == null ? t / data.duracao : Math.min(1,t / data.repouso)), 3, colors.acento, 1.5).setAttribute('data-progresso','sim');
          if (data.rotulo_cena !== false)
            text(svg, 'CENA ' + scene.id, x, y + 45, 680, 27, { anchor: 'start', fill: colors.suave });
        }
        if (data.legenda) captions(scene, t);
        if (data.marca) node('image', { href: data.marca, x: width - (landscape ? 270 : 240),
          y: landscape ? 940 : 1390, width: 110, height: 35, opacity: .55 }, svg);
        return scene.id;
      }
      window.render = render;
      window.duration = data.duracao;
      window.sceneSize = [width, height];
      window.animationEvents = scenes.flatMap(scene => scene.paint.events || []);
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
        const elapsed = (now - previous) / 1000;
        const tail = audio && audio.ended && data.repouso != null;
        show(audio && !tail ? audio.currentTime : Math.max(current, tail ? audio.duration : 0) + elapsed);
        previous = now;
        if (current >= data.duracao || (audio && audio.ended && !tail)) pause();
        else request = requestAnimationFrame(tick);
      }
      function start() {
        if (current >= data.duracao) show(0);
        playing = true;
        play.textContent = 'Pausar';
        if (audio && !(data.repouso != null && current >= audio.duration)) { audio.currentTime = current; audio.play().catch(() => pause()); }
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
      const effects = document.getElementById('alternar-efeitos');
      effects?.addEventListener('click', () => {
        const enabled = effects.getAttribute('aria-pressed') === 'true';
        effects.setAttribute('aria-pressed', String(!enabled));
        window.render(current);
      });
      window.seek = goto;
      show(0);
      if (document.fonts) document.fonts.ready.then(() => show(current));
    }
  };
})();
