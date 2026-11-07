#!/usr/bin/env python3
"""Regressão técnica com outro tema e áudio sintético; não valida ASR acústico."""
import argparse,copy,json,subprocess,sys,tempfile
from pathlib import Path
from projeto import write,read,sha,audio_identity,config

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',required=True,type=Path);ap.add_argument('--ffmpeg',required=True);ap.add_argument('--ffprobe',required=True);ap.add_argument('--node',default='node');a=ap.parse_args();work=a.workspace.resolve();work.mkdir(parents=True,exist_ok=True);scripts=Path(__file__).parent.resolve();root=work/'projeto';results=[]
 def run(name,script,args=(),error=None):
  r=subprocess.run([sys.executable,str(scripts/script),'--root',str(root),*map(str,args)],capture_output=True,text=True)
  if error:
   if r.returncode==0 or error.casefold() not in (r.stdout+r.stderr).casefold():raise AssertionError((name,r.stdout,r.stderr))
  elif r.returncode:raise AssertionError((name,r.stdout,r.stderr))
  results.append({'cenario':name,'passou':True});return r
 inp=work/'entrada.wav';subprocess.run([a.ffmpeg,'-y','-v','error','-f','lavfi','-i','sine=frequency=440:sample_rate=16000','-t','6',str(inp)],check=True)
 text='Atender começa pela escuta.\n\nPrioridade orienta a fila. Cada resposta esclarece o próximo passo.\n\nEncerramos confirmando o entendimento.\n';(work/'roteiro.txt').write_text(text)
 run('Preparar tema diferente com três parágrafos','preparar.py',['--audio',inp,'--roteiro',work/'roteiro.txt','--titulo','Atendimento ao cliente','--autor','Equipe','--ffprobe',a.ffprobe,'--perfil-visual','legado'])
 # Simula a configuração de um projeto salvo antes da política de trilha.
 legacy=read(root/'projeto.json');legacy.pop('trilha_obrigatoria');write(root/'projeto.json',legacy)
 ps=read(root/'material/paragrafos.json');scenes=[{'id':'S001','p':1,'tipo':'capa','title':'Atendimento ao cliente','frase_gatilho':'Atender começa'},{'id':'S002','p':2,'tipo':'ideia','title':'Escuta e prioridade','frase_gatilho':'Prioridade orienta'},{'id':'S003','p':2,'tipo':'ideia','title':'Clareza no próximo passo','frase_gatilho':'Cada resposta'},{'id':'S004','p':3,'tipo':'final','title':'Confirmar o entendimento','frase_gatilho':'Encerramos confirmando'}];write(root/'material/slides.json',scenes)
 run('Áudio único sem marcações é bloqueado','sincronizar.py',['--ffprobe',a.ffprobe],error='exige marcações')
 bad=copy.deepcopy(scenes);bad[2]['frase_gatilho']='não existe';write(root/'material/slides.json',bad);run('Gatilho ausente é rejeitado','gerar_slides.py',['--html-only'],error='gatilho ausente');write(root/'material/slides.json',scenes)
 original=copy.deepcopy(ps);ps[1]['texto']='Prioridade orienta a fila. Prioridade orienta a fila. Cada resposta esclarece o próximo passo.';write(root/'material/paragrafos.json',ps);run('Gatilho ambíguo é rejeitado','gerar_slides.py',['--html-only'],error='ambíguo');write(root/'material/paragrafos.json',original)
 words=[];tokens=' '.join(p['texto'] for p in original).split();step=6/len(tokens)
 for i,w in enumerate(tokens):words.append({'word':w,'start':i*step,'end':(i+1)*step})
 cfg=config(root);identity=audio_identity(root,cfg,original);tr={'audio_identidade':identity,'duracao_s':6.,'motor':'fixture sintética de contrato, sem fala','segmentos':[{'words':words}]};write(root/'material/transcricao_asr.json',tr)
 run('Alinhar fixture textual de outro tema','alinha_audio.py')
 mark=read(root/'material/marcacoes_audio.json');wrong=copy.deepcopy(mark);wrong['audio_identidade']={'unico':'0'*64};write(root/'material/marcacoes_audio.json',wrong);run('Áudio incompatível por hash é rejeitado','sincronizar.py',['--ffprobe',a.ffprobe],error='SHA-256');write(root/'material/marcacoes_audio.json',mark)
 wrong=copy.deepcopy(mark);wrong['duracao_s']=10;write(root/'material/marcacoes_audio.json',wrong);run('Duração incompatível é rejeitada','sincronizar.py',['--ffprobe',a.ffprobe],error='Duração');write(root/'material/marcacoes_audio.json',mark)
 wrong=copy.deepcopy(mark);wrong['revisao']['pendencias']=['S002'];write(root/'material/marcacoes_audio.json',wrong);run('Revisão pendente bloqueia exportação','sincronizar.py',['--ffprobe',a.ffprobe],error='revisão');write(root/'material/marcacoes_audio.json',mark)
 wrongtr=copy.deepcopy(tr);wrongtr['segmentos']=[{'words':[{'word':'incompatível','start':0.,'end':1.}]}];write(root/'material/transcricao_asr.json',wrongtr);run('Alinhamento sem correspondência é rejeitado','alinha_audio.py',error='insuficiente');write(root/'material/transcricao_asr.json',tr)
 # Count and identity checks on paragraph files, without overwriting the single-track project.
 from projeto import audio_files
 folder=work/'audios';folder.mkdir(exist_ok=True)
 for n in [1,3]: (folder/f'P{n:03}.wav').write_bytes(inp.read_bytes())
 try:audio_files(folder,3);raise AssertionError('Deveria faltar P002')
 except ValueError as e:assert 'P002' in str(e)
 results.append({'cenario':'Áudio intermediário ausente identificado','passou':True});(folder/'P002.wav').write_bytes(inp.read_bytes());(folder/'P01.wav').write_bytes(inp.read_bytes())
 try:audio_files(folder,3);raise AssertionError('Deveria detectar duplicidade')
 except ValueError as e:assert 'ambíguos' in str(e)
 results.append({'cenario':'Duplicidade de áudios identificada','passou':True})
 # Invalid scene metadata must not replace an approved video.
 (root/'video.mp4').write_bytes(b'arquivo anterior preservado');saved=(root/'video.mp4').read_bytes();wrong=copy.deepcopy(mark);wrong['slides'][1]['inicio_s']=-1.;write(root/'material/marcacoes_audio.json',wrong);run('Erro preserva a saída anterior','sincronizar.py',['--ffprobe',a.ffprobe,'--ffmpeg',a.ffmpeg,'--renderizar'],error='Entradas inválidas');assert (root/'video.mp4').read_bytes()==saved;write(root/'material/marcacoes_audio.json',mark)
 run('Renderizar padrão 16:9 sem fontes fixas','gerar_slides.py',['--node',a.node]);run('Exportar MP4 sintético para verificar o motor','sincronizar.py',['--ffprobe',a.ffprobe,'--ffmpeg',a.ffmpeg,'--renderizar']);run('Validar vídeo e cobertura','validar.py',['--video','--ffprobe',a.ffprobe,'--ffmpeg',a.ffmpeg])
 for fmt in ['21:9','9:16']:
  run('Renderizar formato '+fmt,'gerar_slides.py',['--formato',fmt,'--node',a.node]);run('Validar formato '+fmt,'validar.py',['--formato',fmt])
 write(work/'resultados.json',{'limite':'Áudio sintético: estes casos verificam contratos, renderização e falhas, não reconhecimento acústico.','cenarios':results});print(f'{len(results)} cenários passaram.')
if __name__=='__main__':main()
