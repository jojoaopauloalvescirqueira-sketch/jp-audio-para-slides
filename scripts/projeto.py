"""Contratos comuns de projeto; não contém conteúdo de apresentações."""
import hashlib,json,math,re,shutil,subprocess
from pathlib import Path
from editorial import PROFILE, KINDS, validate as validate_editorial

FORMATS={'16:9':(1920,1080),'21:9':(2520,1080),'9:16':(1080,1920)}
TYPES={'capa','figura','ideia','conta','definicao','sintese','final'}

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def binary(name,override=None):
 p=override or shutil.which(name)
 if not p:raise ValueError(f'{name} não encontrado. Instale-o ou indique --{name}.')
 return str(p)
def probe(path,ffprobe):
 p=Path(path)
 if not p.is_file():raise ValueError(f'Áudio/arquivo ausente: {p}')
 data=json.loads(subprocess.run([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(p)],check=True,capture_output=True,text=True).stdout)
 d=float(data['format']['duration'])
 if not math.isfinite(d) or d<=0:raise ValueError(f'Duração inválida: {p}')
 return data

def audio_files(path,count):
 path=Path(path)
 if path.is_file():return [path]
 if not path.is_dir():raise ValueError(f'Áudio ausente: {path}')
 found={}
 for p in path.iterdir():
  m=re.fullmatch(r'P0*(\d+)\.(mp3|wav|m4a|flac|aac|ogg)',p.name,re.I)
  if m:found.setdefault(int(m[1]),[]).append(p)
 files=[]
 for n in range(1,count+1):
  if n not in found:raise ValueError(f'Áudio ausente para P{n:03}.')
  if len(found[n])!=1:raise ValueError(f'Áudios ambíguos para P{n:03}.')
  files.append(found[n][0])
 if any(n<1 or n>count for n in found):raise ValueError('Há áudios numerados sem parágrafo correspondente.')
 return files

def config(root):
 c=read(Path(root)/'projeto.json')
 if not c.get('titulo','').strip():raise ValueError('Título do projeto ausente.')
 c.setdefault('autor','');c.setdefault('subtitulo','');c.setdefault('marca','');c.setdefault('cta_rotulo','');c.setdefault('cta_url','');c.setdefault('capa','');c.setdefault('formato','16:9');c.setdefault('idioma','pt');c.setdefault('fps',30)
 if c.get('estilo_video') not in (None,'editorial_jp','pictograma','ilustrado','legado'):
  raise ValueError('Estilo de vídeo desconhecido.')
 if c.get('estilo_video'):
  c['perfil_visual']=PROFILE if c['estilo_video']==PROFILE else 'legado'
 c.setdefault('perfil_visual','legado')
 if c['perfil_visual'] not in {'legado',PROFILE}:raise ValueError('Perfil visual desconhecido.')
 if c['formato'] not in FORMATS:raise ValueError('Formato desconhecido.')
 if c['fps']!=30:raise ValueError('Esta versão exporta em 30 fps.')
 return c

def audio(root,c):
 if not c.get('audio'):raise ValueError('Áudio pendente; forneça-o e execute anexar_audio.py antes de sincronizar.')
 return (Path(root)/c['audio']).resolve()
def audio_identity(root,c,ps):
 files=audio_files(audio(root,c),len(ps))
 return {f'P{i:03}':sha(p) for i,p in enumerate(files,1)} if audio(root,c).is_dir() else {'unico':sha(files[0])}

def load(root,require_audio=True):
 root=Path(root);c=config(root);ps=read(root/'material/paragrafos.json');scenes=read(root/'material/slides.json');sources=read(root/'material/fontes_figuras.json')
 if c.get('roteiro_sha256'):
  from fala import paragraphs,normalize
  canonical=root/'material/roteiro_limpo.txt'
  if sha(canonical)!=c['roteiro_sha256'] or [normalize(p['texto']) for p in ps]!=[normalize(p) for p in paragraphs(canonical.read_text(encoding='utf-8'))]:raise ValueError('Fala canônica alterada ou parágrafos incompatíveis; revise o projeto.')
 if not ps or not scenes:raise ValueError('Roteiro ou plano de slides vazio; prepare as cenas antes de gerar.')
 start=1
 if c.get('estilo_video') in {'pictograma','ilustrado'} and re.fullmatch(r'P\d{3,}',ps[0]['id']):
  start=int(ps[0]['id'][1:])
 if [p['id'] for p in ps]!=[f'P{i:03}' for i in range(start,start+len(ps))]:raise ValueError('Parágrafos precisam ter IDs consecutivos.')
 if require_audio:audio_files(audio(root,c),len(ps))
 offset=[0]
 for p in ps:
  if not p['texto'].strip():raise ValueError('Parágrafo vazio.')
  offset.append(offset[-1]+len(p['texto'].split()))
 ids=set();srcs={str(s['id']):s for s in sources}
 if any(not re.fullmatch(r'[A-Za-z0-9_-]+',str(x)) for x in srcs):raise ValueError('ID de figura inválido.')
 if len(srcs)!=len(sources):raise ValueError('IDs de fontes duplicados.')
 for s in scenes:
  if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',s['id']):raise ValueError('ID de slide inválido.')
  if s['id'] in ids:raise ValueError('IDs de slides duplicados.')
  ids.add(s['id'])
  if s['tipo'] not in (TYPES | KINDS if c['perfil_visual']==PROFILE else TYPES):raise ValueError(f'Tipo de slide inválido: {s["id"]}')
  if not isinstance(s['p'],int) or not 1<=s['p']<=len(ps):raise ValueError('Parágrafo inicial fora do roteiro.')
  text=ps[s['p']-1]['texto'];tr=s['frase_gatilho']
  if not isinstance(tr,str) or not tr.strip():raise ValueError(f'Gatilho vazio: {s["id"]}')
  hits=[m.start() for m in re.finditer(re.escape(tr),text)]
  if not hits:raise ValueError(f'Frase-gatilho ausente no roteiro: {s["id"]}')
  if len(hits)>1 and 'ocorrencia' not in s:raise ValueError(f'Gatilho ambíguo em {s["id"]}; informe ocorrencia (base 1).')
  occurrence=s.get('ocorrencia',1)
  if not isinstance(occurrence,int) or not 1<=occurrence<=len(hits):raise ValueError('Ocorrência inválida.')
  char=hits[occurrence-1]
  if char and text[char-1].isalnum():raise ValueError('Gatilho começa dentro de uma palavra.')
  s['char_start']=char;s['word_start']=offset[s['p']-1]+len(text[:char].split())
  for key,default in [('title',''),('body',''),('lines',[]),('fonte',''),('nota',''),('bloco',''),('figura',None)]:s.setdefault(key,default)
  if s['tipo']=='capa' and (s['title'] or c['titulo'])!=c['titulo']:raise ValueError('O título da capa precisa ser idêntico ao título confirmado.')
  if s['tipo']=='figura':
   if str(s['figura']) not in srcs:raise ValueError(f'Fonte da figura ausente em {s["id"]}.')
   f=srcs[str(s['figura'])]
   if Path(f['arquivo']).is_absolute() or '..' in Path(f['arquivo']).parts:raise ValueError('Copie a figura para dentro do projeto e use caminho relativo.')
   if not (root/f['arquivo']).is_file():raise ValueError(f'Arquivo da figura ausente: {f["arquivo"]}')
   if not f.get('credito','').strip():raise ValueError('Crédito da figura ausente.')
  if s['tipo']=='sintese' and len(s['lines'])>3:raise ValueError('Síntese excede três tópicos.')
  if s['tipo']!='capa' and len(s['title'].split())>12:raise ValueError(f'Título excede 12 palavras: {s["id"]}')
 if scenes[0]['word_start']!=0:raise ValueError('O primeiro slide não cobre o início do roteiro.')
 for i,s in enumerate(scenes):
  s['word_end']=scenes[i+1]['word_start'] if i+1<len(scenes) else offset[-1]
  if s['word_end']<=s['word_start']:raise ValueError('Entradas não crescentes ou intervalos vazios.')
  end=s['p']
  while end<len(ps) and offset[end]<s['word_end']:end+=1
  if 'end' in s and s['end']!=end:raise ValueError(f'Fim de parágrafo não corresponde ao intervalo: {s["id"]}')
  s['end']=end;s['estimativa_s']=(s['word_end']-s['word_start'])*60/140
 if c['perfil_visual']==PROFILE:validate_editorial(root,c,ps,scenes,sources)
 return c,ps,scenes,sources

def outdir(root,fmt):return Path(root)/('slides' if fmt=='16:9' else 'slides-'+fmt.replace(':','x'))
def ffquote(path):return "'"+str(Path(path).resolve()).replace("'","'\\''")+"'"
