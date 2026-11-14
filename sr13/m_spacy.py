import spacy,json,time
from m_rules import LEX
V={v:p for p,vs in LEX.items() for v in vs if ' ' not in v}
V.update({'depend':'uses'})
t0=time.time(); nlp=spacy.load('en_core_web_sm'); load=time.time()-t0
def chunk(tok,doc):
    for c in doc.noun_chunks:
        if c.start<=tok.i<c.end: return c.text
    return tok.text
def heads(tok):
    return [tok]+[c for c in tok.conjuncts]
def extract(doc):
    T=[]
    for t in doc:
        if t.pos_ not in ('VERB','AUX'): continue
        subj=[c for c in t.children if c.dep_=='nsubj']; ps=[c for c in t.children if c.dep_=='nsubjpass']
        if t.lemma_ in V:
            p=V[t.lemma_]
            objs=[c for c in t.children if c.dep_=='dobj']
            prep=[c for c in t.children if c.dep_=='prep' and c.lemma_=='on'] if t.lemma_=='depend' else []
            for pr in prep: objs+=[c for c in pr.children if c.dep_=='pobj']
            if subj and objs:
                for o in objs:
                    for oo in heads(o):
                        for s in subj: T.append((chunk(s,doc),p,chunk(oo,doc)))
            if ps:
                ag=[g for c in t.children if c.dep_=='agent' for g in c.children if g.dep_=='pobj']
                for a in ag:
                    for s in ps: T.append((chunk(a,doc),p,chunk(s,doc)))
        if t.lemma_=='be':
            attr=[c for c in t.children if c.dep_=='attr' and c.pos_ in ('NOUN','PROPN')]
            for s in subj:
                for a in attr: T.append((chunk(s,doc),'is_a',chunk(a,doc)))
    return T
if __name__=='__main__':
    S=json.load(open('sentences_only.json')); t0=time.time()
    out={x['id']:extract(nlp(x['sentence'])) for x in S}; dt=time.time()-t0
    json.dump({'time_s':dt,'load_s':load,'preds':out},open('spacy_out.json','w'),ensure_ascii=False,indent=1)
    print(sum(len(v) for v in out.values()),'triples',round(dt,2),'s; load',round(load,2))
