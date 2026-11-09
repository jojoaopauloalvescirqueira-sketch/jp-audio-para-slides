"""Substituições de exibição vinculadas às palavras canônicas."""
from ancoras import norm, tokens


def keys(text):
    return [norm(word) for word,_ in tokens(text)]


def rules(project):
    entries=project.get('substituicoes_legenda',[])
    names=project.get('pessoas_privadas',[])
    if (not isinstance(entries,list) or not isinstance(names,list)
            or any(not isinstance(name,str) or not keys(name) for name in names)):
        raise ValueError('Preferências de privacidade da legenda inválidas.')
    seen=set()
    for entry in entries:
        fields=('original','substituto','motivo','origem','data')
        if not isinstance(entry,dict) or any(not isinstance(entry.get(key),str) or not entry[key].strip()
                                             for key in fields) or entry['origem']!='usuario':
            raise ValueError('A substituição da legenda exige termo, motivo, data e origem usuario.')
        original=tuple(keys(entry['original']))
        substitute=tokens(entry['substituto'])
        if (not original or original in seen or len(original)!=len(substitute)
                or ' '.join(word for word,_ in substitute)!=entry['substituto']):
            raise ValueError('Use pares distintos com a mesma quantidade de palavras e sem pontuação.')
        seen.add(original)
    return entries,names


def display_tokens(raw, entries):
    result=list(raw)
    found=[]
    canonical=[keys(word)[0] for word in raw]
    for index,word in enumerate(raw):
        matches=[entry for entry in entries
                 if canonical[index:index+len(keys(entry['original']))]==keys(entry['original'])]
        if not matches:
            continue
        if len(matches)>1 or found and index<found[-1]['inicio']+found[-1]['palavras']:
            raise ValueError('Substituições de legenda se sobrepõem.')
        entry=matches[0]
        replacement=entry['substituto'].split()
        if word[0].isupper():
            replacement[0]=replacement[0][0].upper()+replacement[0][1:]
        for j,new_word in enumerate(replacement,index):
            spoken=tokens(raw[j])[0][0]
            result[j]=new_word+raw[j][len(spoken):]
        found.append({'inicio':index,'palavras':len(replacement),'motivo':entry['motivo']})
    return result,found


def private_hits(texts, names):
    patterns=[keys(name) for name in names]
    return any(candidate[i:i+len(pattern)]==pattern for text in texts
               for candidate in [keys(text)] for pattern in patterns for i in range(len(candidate)))
