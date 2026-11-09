MotorCenas.registrarKit('pictograma', ({data, width, height, landscape, colors, node, set, text,
  rectangle, line, circle, clamped, smoothstep, mix, sample, cameraLayer}) => {
  const abundant = data.densidade !== 'moderada';
  const maximal = data.densidade === 'maxima';
  function placement(row, state) {
    if (!landscape) return [state.x, state.y, state.w, state.h];
    return [160 + (state.x - 64) * 1600 / 828, 148 + (state.y - 440) * 730 / 880,
      state.w * 1600 / 828, state.h * 730 / 880];
  }

  function pose(row) {
    return { x: row.x, y:row.y, w:row.w, h:row.h, sit: ['sentado','ajoelhado'].includes(row.estado) ? 1 : 0, opacity: row.visivel === false ? 0 : 1,
      halo: 0, draw: 1, color: colors[row.cor || 'osso'], spin: null, pulse: null,
      gesture:0, transfer:0, counter:0, accent: row.acento || '', word: row.texto || '', note: row.anotacao || '', flip: null, bob: 0 };
  }

  const limits = { aparecer: 0.24, sumir: 0.22, sentar: 0.44, levantar: 0.40,
    andar: 0.60, andar_ate: .60, apontar: .38, ajudar_a_levantar: .48, abracar: .52,
    entregar: .48, contar: .64, desenhar_linha: .35, anotar:.23, destacar: 0.32, mudar_cor: 0.32, desenhar: 0.35, trocar_letra: 0.35 };
  const channels = { aparecer: 'opacity', sumir: 'opacity', sentar: 'sit', levantar: 'sit',
    andar: 'x', destacar: 'halo', mudar_cor: 'color', desenhar: 'draw',
    girar: 'spin', pulsar: 'pulse', andar_ate:'x', desenhar_linha:'draw',
    ajudar_a_levantar:'sit', apontar:'gesture', abracar:'gesture', entregar:'transfer', contar:'counter', palavra: 'word', trocar_letra: 'word', anotar: 'note' };
  const durationScale = { sobrio: 1.3, didatico: 1, energetico: 0.78 }[data.tom] || 1;

  const windowFor = item => [item.inicio_movimento ?? item.tempo,
    item.fim_movimento ?? (item.tempo + (limits[item.acao] || 0)*durationScale)];
  function prepare(row, actions, scene, previous) {
    const initial = pose(row);
    if (actions.some(item => ['desenhar','desenhar_linha'].includes(item.acao))) initial.draw = 0;
    const tracks = Object.fromEntries(Object.entries(initial).map(([key, value]) => [key, [[-1, value]]]));
    const flip = [], walks = [], entrances = [], gestures = [], notes = [];
    for (const item of actions) {
      const [t,finish] = windowFor(item);
      const peak = item.pousar==='pico' ? item.pouso_render : finish;
      const channel = channels[item.acao];
      const track = tracks[channel];
      let from = sample(track, t, channel);
      while (track.length > 1 && track[track.length - 1][0] >= t) track.pop();
      const values = { andar_ate:item.destino_x, desenhar_linha:1, ajudar_a_levantar:0,
        apontar:1, abracar:1, entregar:1, contar:item.valor, aparecer: 1, sumir: 0, sentar: 1, levantar: 0,
        andar: item.valor, destacar: 1, mudar_cor: colors[item.valor],
        desenhar: 1, girar: t, pulsar: t, palavra: item.valor,
        trocar_letra: item.valor, anotar: item.valor };
      if (['desenhar','desenhar_linha'].includes(item.acao)) {
        from = 0;
        if (track.length === 1) track[0][1] = 0;
      }
      if (item.acao === 'trocar_letra') flip.push([t, peak, from, item.valor]);
      if (['andar','andar_ate'].includes(item.acao)) walks.push([t, peak]);
      if (item.acao === 'aparecer') entrances.push([t,peak]);
      if (item.acao === 'anotar') notes.push([t,finish || t+.2,from,item.valor]);
      if (['apontar','abracar','ajudar_a_levantar','entregar'].includes(item.acao)) gestures.push([t,peak,item]);
      track.push([t, from]);
      track.push([channel === 'word' || ['spin','pulse'].includes(channel) ? item.tempo : peak, values[item.acao]]);
    }
    return (t) => {
      const state = Object.fromEntries(Object.entries(tracks).map(([key, keys]) => [key, sample(keys, t, key)]));
      const activeEntry = entrances.find(([a,b])=>a <= t && t < b);
      const uEntry = activeEntry ? clamped((t-activeEntry[0])/(activeEntry[1]-activeEntry[0])) : 1;
      const ease = 1 + 1.42*(uEntry-1)**3 + .42*(uEntry-1)**2;
      state.arrival = 16*(1-ease);
      state.noteBlend = notes.find(([a,b])=>a <= t && t < b);
      const gesture = gestures.filter(([a])=>a <= t).pop();
      if (gesture) state.gestureEvent = {row:gesture[2],u:smoothstep((t-gesture[0])/(gesture[1]-gesture[0]))};
      if (actions.some(item=>item.acao==='contar')) state.word = String(Math.round(state.counter));
      state.idle = abundant ? Math.sin(t*4.2 + row.x*.015) : 0;
      const pulse = state.pulse === null ? 0 : Math.sin((t-state.pulse)*6)*Math.min(1,(t-state.pulse)*5);
      if (row.tipo === 'figura' && pulse) state.halo = Math.max(state.halo,.28+.12*pulse);
      else if (row.tipo !== 'reticencias') state.opacity *= 1-.12*Math.abs(pulse);
      const completed = flip.filter(([, end]) => end <= t).pop();
      if (completed) state.letters = [...completed[3]].map((letter, index) => letter !== [...completed[2]][index]);
      if (previous && t < scene.inicio + .56) {
        const prior = previous(scene.inicio - .001);
        const u = smoothstep((t - scene.inicio) / .56);
        for (const key of ['x','y','w','h']) state[key]=mix(prior[key],state[key],u);
        state.sit = mix(prior.sit, state.sit, u);
        state.opacity = mix(prior.opacity, state.opacity, u);
      }
      state.flip = flip.find(([start, end]) => start <= t && t < end);
      const walk = walks.find(([start, end]) => start <= t && t < end);
      if (walk) {
        const u = (t - walk[0]) / (walk[1] - walk[0]);
        state.bob = 2.1 * Math.sin(Math.PI * u) * Math.abs(Math.sin(3 * Math.PI * u));
        state.step = 9 * Math.sin(6 * Math.PI * u) * Math.sin(Math.PI * u);
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
      set(glow, { opacity: state.halo*(.91+.09*state.idle), 'data-parte':'brilho' });
    }
    const s = state.sit;
    const floor = state.groundY ?? 96;
    const seat = state.seatY ?? floor - 12;
    const seatHip = mix(floor - 15, seat, s);
    const width = 58;
    const center = mix(50, 44, s)+.45*state.idle;
    const shoulder = seatHip - mix(43, 34, s)*(1+.015*state.idle) - state.bob;
    const headRadius = 10.5;
    const headY = shoulder - headRadius + 1.8;
    const step = state.step || 0;
    const knee = mix(center+10,state.kneeX ?? 74,s);
    const ink = state.color;
    const part = (element, name) => set(element,{'data-parte':name});
    const roundBlock = (x,y,w,h,name) => part(rectangle(parent,x,y,w,h,ink,Math.min(w/2,h/2)),name);

    // Keep one sole planted and let the other lift during a step.
    const footLift = Math.abs(step)*.26;
    const leftSole = floor - (step>0 ? footLift : 0);
    const rightSole = floor - (step<0 ? footLift : 0);
    if (s < .999) {
      const top = seatHip-7;
      const footWidth = mix(27,16,s);
      roundBlock(mix(center-28+step,center-15,s),top,footWidth,Math.max(.1,leftSole-top),'pe');
      roundBlock(mix(center+1-step,knee-8,s),top,footWidth,Math.max(.1,rightSole-top),'pe');
    }
    if (s > .01) {
      const shinWidth=16;
      const shinTop=seatHip-4;
      if (floor>shinTop) roundBlock(knee-shinWidth/2,shinTop,shinWidth,floor-shinTop,'canela');
      const thighLeft=center-13;
      roundBlock(thighLeft,seatHip-11,Math.max(10,knee+8-thighLeft),11,'coxa');
    }
    roundBlock(center-width/2,shoulder,width,seatHip-shoulder+mix(3,0,s),'tronco');
    const head = node('ellipse',{cx:center,cy:headY,rx:Math.min(30,headRadius*state.h/state.w),
      ry:headRadius,fill:ink},parent);
    part(head,'cabeca');
    parent.dataset.pose = s > .96 ? (row.apoio ? 'sentada' : 'ajoelhada') : s < .04 ? 'em_pe' : 'transicao';
    parent.dataset.juntas = String(Number.isFinite(shoulder) && headY+headRadius>=shoulder && seatHip>shoulder);
    if (row.apoio && s>.96) parent.dataset.apoio=row.apoio;
    if (state.groundY!=null && state.floorId) parent.dataset.chao=state.floorId;
    if (row.rotulo) text(parent, row.rotulo, 50, 98, 90, 9, { fill: colors.suave });
  }

  function drawText(parent, row, state, t) {
    const [, , width] = parent.getAttribute('viewBox').split(' ').map(Number);
    const center = width / 2;
    const wordY = state.note ? 62 : 70;
    const options = { fill: state.color, weight: 800 };
    const label = node('text', {x:center,y:wordY,'font-size':state.note ? 73 : 74,
      'text-anchor':'middle',fill:state.color,class:'picto-'+(row.estilo_texto || 'display'),
      'data-titulo':'sim'}, parent);
    const flip = state.flip;
    const u = flip ? clamped((t-flip[0])/(flip[1]-flip[0])) : 1;
    const active = flip ? flip[u < .5 ? 2 : 3] : state.word;
    const accentStart = state.accent ? active.indexOf(state.accent) : -1;
    if (flip || state.letters || accentStart >= 0) {
      const before = flip ? [...flip[2]] : [];
      const after = flip ? [...flip[3]] : [];
      [...active].forEach((letter, index) => {
        const changed = flip ? before[index] !== after[index] : state.letters?.[index];
        const accent = changed && u >= .5 || accentStart >= 0 && index >= accentStart &&
          index < accentStart + state.accent.length;
        const glyph = node('tspan',{fill:accent ? colors.acento : state.color},label);
        glyph.textContent = letter;
        if (flip && changed) {
          const scale = Math.max(.001,Math.abs(Math.cos(u*Math.PI)));
          glyph.setAttribute('font-size',String(73*scale));
        }
      });
    } else label.textContent = active;
    const measured = label.getComputedTextLength();
    if (measured > width*.96) set(label,{textLength:width*.96,lengthAdjust:'spacingAndGlyphs'});
    const noteOptions = {fill:state.letters ? colors.acento : colors.suave};
    if (state.noteBlend) {
      const [a,b,oldNote,newNote] = state.noteBlend;
      const blend = smoothstep((t-a)/(b-a));
      set(text(parent,oldNote,center,92,width*.94,14,noteOptions),{opacity:1-blend});
      set(text(parent,newNote,center,92,width*.94,14,noteOptions),{opacity:blend});
    } else if (state.note) text(parent,state.note,center,92,width*.94,14,noteOptions);
  }

  function drawShape(parent, row, state, t, defs) {
    if (row.tipo === 'figura') {
      figure(parent, row, state, defs);
    } else if (row.tipo === 'texto') {
      drawText(parent, row, state, t);
    } else if (row.tipo === 'objeto') {
      rectangle(parent,21,24,58,50,state.color,9);
    } else if (row.tipo === 'banco') {
      set(rectangle(parent,6,37,88,11,state.color,5),{'data-parte':'assento'});
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
      const points = row.pontos || segments[row.direcao || 'direita'];
      if (row.tipo === 'seta' || row.tipo === 'divisoria') {
        const w=Number(parent.getAttribute('width')), h=Number(parent.getAttribute('height'));
        const group=node('g',{transform:'scale('+100/w+' '+100/h+')'},parent);
        parent.setAttribute('overflow','visible');
        const [x1,y1,x2,y2]=points.map((value,index)=>value*(index%2?h:w)/100);
        const x=mix(x1,x2,state.draw), y=mix(y1,y2,state.draw);
        const divider=row.tipo==='divisoria';
        const shaft=line(group,x1,y1,x,y,state.color,divider?2:9);
        shaft.removeAttribute('pathLength');
        if (divider) set(shaft,{'stroke-dasharray':'6 10','stroke-linecap':'butt'});
        else if (state.draw>.20) {
          const angle=Math.atan2(y2-y1,x2-x1)*180/Math.PI;
          const opacity=smoothstep((state.draw-.20)/.37);
          node('path',{d:'M-29 -17 L6 0 L-29 17 Z',fill:state.color,opacity,
            transform:'translate('+x+' '+y+') rotate('+angle+')'},group);
        }
      } else {
        const stroke=line(parent,...points,state.color,5+.45*state.idle);
        if (row.piso) stroke.dataset.parte='piso';
        set(stroke,{'stroke-dasharray':'1','stroke-dashoffset':1-state.draw});
      }
    }
  }

  return (scene, previous) => {
    const ordered = [...scene.elementos].sort((a,b) => (a.z||0)-(b.z||0));
    const states = new Map(ordered.map(row => [row.id,prepare(row,
      scene.acoes.filter(item => item.alvo === row.id),scene,
      row.persistir ? previous?.paint.states?.get(row.id) : undefined)]));
    const paint = (world, defs, t, front, next) => {
      const transition = front && previous && previous.saida !== 'corte'
        ? smoothstep((t-scene.inicio)/.32) : 1;
      const paintTime = Math.min(t,data.repouso ?? t);
      const elapsed = smoothstep((paintTime-scene.inicio)/Math.max(.01,scene.fim-scene.inicio));
      const scenery = abundant ? cameraLayer(world, {zoom:1+.04*elapsed,x:.5+.006*elapsed,y:.5}) : world;
      const byId = new Map(ordered.map(row=>[row.id,row]));
      const hand = (row) => {
        const actor = states.get(row.id)(paintTime);
        const [x,y,w,h] = placement(row,actor);
        return [x+w*(.5+.06*actor.sit),y+h*(.56+.08*actor.sit)];
      };
      for (const row of ordered) {
        if (!front && row.persistir && next?.elementos.some(item => item.persistir && item.id === row.id)) continue;
        const state = states.get(row.id)(paintTime);
        if (!(row.persistir && previous?.paint.states?.has(row.id))) state.opacity *= transition;
        if (state.opacity <= 0) continue;
        let [ex, ey, w, h] = placement(row, state);
        if (front && previous?.saida==='deslize' && !row.persistir) ex+=30*(1-transition);
        const parent = row.tipo === 'texto' ? world : scenery;
        const event = state.gestureEvent;
        if (event && event.row.acao==='entregar') {
          const [ax,ay]=hand(byId.get(event.row.valor.de));
          const [bx,by]=hand(byId.get(event.row.valor.para));
          ex=mix(ax,bx,event.u)-w/2;
          ey=mix(ay,by,event.u)-h/2-25*Math.sin(Math.PI*event.u);
        } else if (event) {
          const peer = byId.get(event.row.valor);
          const actor = event.row.acao==='ajudar_a_levantar' ? peer : row;
          const receiver = actor===row ? peer : row;
          const [ax,ay]=hand(actor),[bx,by]=hand(receiver);
          const u=event.u*(event.row.acao==='apontar' ? .68 : 1);
          const stroke = line(scenery,ax,ay,mix(ax,bx,u),mix(ay,by,u),state.color,12);
          stroke.dataset.gesto = row.id;
        }
        if (row.de) {
          const from = ordered.find(item => item.id === row.de);
          const to = ordered.find(item => item.id === row.para);
          const [ax,ay,aw,ah] = placement(from,states.get(from.id)(paintTime));
          const [bx,by,bw,bh] = placement(to,states.get(to.id)(paintTime));
          const arm = line(scenery,ax+aw*.61,ay+ah*.57,bx+bw*.40,by+bh*.61,state.color,13);
          set(arm,{'stroke-dasharray':1,'stroke-dashoffset':1-state.draw,opacity:state.opacity,
            'data-elemento':row.id,'data-seguro':'forma','data-ajuda-de':row.de,'data-ajuda-para':row.para});
          continue;
        }

        const contentWidth = row.tipo === 'texto' ? 100 * w / h : 100;
        const stretch = ['braco','linha','seta','divisoria','coluna','figura','banco'].includes(row.tipo);
        const top=ey+(row.tipo==='texto' ? 0 : state.arrival);
        const frame = node('svg',{x:ex,y:top,width:w,height:h,viewBox:'0 0 '+contentWidth+' 100',
          preserveAspectRatio:stretch ? 'none' : 'xMidYMid meet',opacity:state.opacity,
          'data-elemento':row.id,'data-seguro':'forma'},parent);
        if (row.tipo==='figura') {
          const floor = ordered.find(item=>item.piso);
          if (floor) {
            const floorState=states.get(floor.id)(paintTime);
            const [,floorY,,floorH]=placement(floor,floorState);
            state.groundY=100*(floorY+floorH*(floor.pontos?.[1]??50)/100-top)/h;
            state.floorId=floor.id;
          }
          if (row.apoio) {
            const bench=byId.get(row.apoio);
            const benchState=states.get(bench.id)(paintTime);
            const [benchX,benchY,benchW,benchH]=placement(bench,benchState);
            state.seatY=100*(benchY+benchState.arrival+.37*benchH-top)/h;
            state.kneeX=100*(benchX+.94*benchW-ex)/w+11;
          }
        }
        if (row.legenda_de) frame.dataset.legendaDe=row.legenda_de;
        drawShape(frame,row,state,paintTime,defs);
        if (maximal && row.tipo === 'figura' && state.halo) {
          for (let i=0;i<3;i++) {
            const angle=paintTime*.8+i*Math.PI*2/3;
            set(circle(frame,50+32*Math.cos(angle),52+29*Math.sin(angle),.8,colors.acento),{opacity:.34});
          }
        }
      }
    };
    paint.states = states;
    paint.transition = {duration:.32,distance:56};
    paint.events = scene.acoes.map(item=>{
      const [start,end]=windowFor(item);
      return {scene:scene.id, element:item.alvo, action:item.acao, group:item.grupo||item.alvo,
        start,end, word:item.palavra, target:item.tempo,
        landing:item.pouso_render ?? start,
        emphasis: !['girar','pulsar','mudar_cor','destacar'].includes(item.acao),
        minimum: ['aparecer','sumir'].includes(item.acao) ? 6 :
          ['trocar_letra','anotar'].includes(item.acao) ? 4 : 0};
    });
    return paint;
  };
});
