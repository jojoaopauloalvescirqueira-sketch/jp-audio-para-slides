from pathlib import Path
import sys,subprocess,json,argparse,wave

ap=argparse.ArgumentParser(description='Teste de entrada por artigo, roteiro sem áudio e retomada; usa tom sintético, não ASR.')
ap.add_argument('--workspace',required=True,type=Path);ap.add_argument('--ffprobe',required=True);ap.add_argument('--node',default='node');args=ap.parse_args()
stage=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(stage/'scripts'))
from fluxo import iniciar,registrar,anexar
from projeto import write,read,load,sha
root=args.workspace.resolve();root.mkdir(parents=True,exist_ok=True)
article=root/'artigo.md';article.write_text('# Ciclo da água\nA evaporação converte água líquida em vapor. Na condensação, o vapor passa ao estado líquido. Esses processos participam do ciclo da água; não são o ciclo inteiro.\n')
clean=root/'limpo.txt';clean.write_text('A evaporação converte água líquida em vapor.\n\nNa condensação, o vapor passa ao estado líquido. Esses processos participam do ciclo da água; não são o ciclo inteiro.\n')
studio=root/'studio.txt';studio.write_text('[thoughtful] '+clean.read_text())
p=root/'projeto';iniciar(p,'Ciclo da água',article);registrar(p,clean,studio)
write(p/'material/slides.json',[{'id':'S001','p':1,'tipo':'capa','title':'Ciclo da água','frase_gatilho':'A evaporação'},{'id':'S002','p':2,'tipo':'definicao','title':'Condensação','body':'O vapor passa ao estado líquido.','frase_gatilho':'Na condensação'},{'id':'S003','p':2,'tipo':'sintese','lines':['Evaporação e condensação participam do ciclo','O ciclo inclui outros processos'],'frase_gatilho':'Esses processos'}])
for name,text in {'guia_producao.md':'Modelo recomendado: eleven_v4. Voz e interpretação não testadas. Áudio pendente. P001: definir evaporação; P002: explicar condensação e preservar limite.','mapa_didatico.md':'Blocos reconstruídos. P001 → artigo, frase 1 → S001; P002 → frases 2–3 → S002–S003.','fidelidade.md':'Conferência manual: todos os processos e a ressalva final do artigo constam da fala. Sem novos dados ou omissões centrais. Nenhuma evidência de aprendizagem foi medida.'}.items():(p/'material'/name).write_text(text)
def run(script,*args):subprocess.run([sys.executable,str(stage/'scripts'/script),'--root',str(p),*args],check=True,capture_output=True,text=True)
run('gerar_slides.py','--node',args.node);run('validar.py')
html=(p/'slides/apresentacao.html').read_text();assert 'Áudio pendente' in html and 'onclick="listen(' not in html
assert not (p/'slides/timeline.csv').exists() and not (p/'video.mp4').exists()
snap={name:sha(p/'material'/name) for name in ['paragrafos.json','slides.json','roteiro_limpo.txt']}
tone=root/'tom.wav'
with wave.open(str(tone),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\x00\x00'*16000*6)
anexar(p,tone,args.ffprobe)
assert snap=={name:sha(p/'material'/name) for name in snap};load(p)
# Check measured audio handoff and no invented marks; acoustic transcription is a separate operation.
assert read(p/'material/entradas.json')[0]['duracao_s']==6
assert not (p/'material/marcacoes_audio.json').exists()
run('gerar_slides.py','--html-only')
write(root/'resultado.json',{'artigo_roteiro_sem_audio':True,'preview_sem_tempos_medidos':True,'retomada_audio_ffprobe':True,'fala_paragrafos_plano_preservados':True,'limite':'Áudio sintético de seis segundos; teste de contrato e medição, sem reconhecimento acústico.'})
print('Entrada por artigo, planejamento sem áudio e retomada passaram.')
