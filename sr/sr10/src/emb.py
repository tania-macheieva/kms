"""Чотири моделі на ONNX Runtime / numpy. Ваги: models/ (npm-пакети; див. README)."""
import json, struct, time
from pathlib import Path
import numpy as np, onnxruntime as ort
from tokenizers import Tokenizer, BertWordPieceTokenizer
ROOT=Path(__file__).resolve().parents[1]
CFG={ # dir, onnx file, query prefix, passage prefix, max_len, pooling, мови
 'minilm':('models/minilm','model.onnx','','',256,'mean','all-MiniLM-L6-v2 int8, EN, 384d'),
 'bge':('models/bge','model.onnx','Represent this sentence for searching relevant passages: ','',512,'cls','bge-small-en-v1.5 fp32, EN, 384d'),
 'e5':('models/e5','model_quantized.onnx','query: ','passage: ',512,'mean','multilingual-e5-small int8, ~100 мов, 384d'),
}
class Onnx:
    def __init__(s,name):
        d,f,s.qp,s.pp,s.ml,s.pool,s.note=CFG[name]; s.name=name; p=ROOT/d
        so=ort.SessionOptions(); so.intra_op_num_threads=2
        s.sess=ort.InferenceSession(str(p/f),so,providers=['CPUExecutionProvider'])
        s.tok=Tokenizer.from_file(str(p/'tokenizer.json')); s.tok.enable_truncation(s.ml); s.tok.enable_padding()
        s.names={i.name for i in s.sess.get_inputs()}; s.model_bytes=(p/f).stat().st_size
    def _run(s,texts):
        enc=s.tok.encode_batch(texts); ids=np.array([e.ids for e in enc],dtype=np.int64); am=np.array([e.attention_mask for e in enc],dtype=np.int64)
        feed={'input_ids':ids,'attention_mask':am}
        if 'token_type_ids' in s.names: feed['token_type_ids']=np.zeros_like(ids)
        return s.sess.run(None,feed)[0],am
    def encode(s,texts,query=False,bs=16,normalize=True):
        pre=s.qp if query else s.pp; texts=[pre+t for t in texts]; order=np.argsort([len(t) for t in texts]); out=[]
        for i in range(0,len(texts),bs):
            idx=order[i:i+bs]; h,am=s._run([texts[j] for j in idx])
            v=h[:,0] if s.pool=='cls' else (h*am[...,None]).sum(1)/am.sum(1,keepdims=True); out.append((idx,v))
        res=np.zeros((len(texts),out[0][1].shape[1]),dtype=np.float32)
        for idx,v in out: res[idx]=v
        return res/np.linalg.norm(res,axis=1,keepdims=True) if normalize else res
class Potion:
    """potion-base-8M (model2vec): WordPiece-токени -> таблиця embeddings -> середнє. Власна реалізація (без бібліотеки model2vec)."""
    name='potion'; note='potion-base-8M static, EN, 256d'
    def __init__(s):
        p=ROOT/'models/potion'; b=(p/'model.safetensors').read_bytes(); n=struct.unpack('<Q',b[:8])[0]; h=json.loads(b[8:8+n]); t=h['embeddings']
        a,e=t['data_offsets']; s.E=np.frombuffer(b[8+n+a:8+n+e],dtype=np.float32).reshape(t['shape']); s.model_bytes=len(b)
        s.tok=BertWordPieceTokenizer(str(p/'vocab.txt'),lowercase=True)
    def encode(s,texts,query=False,bs=64,normalize=True):
        out=np.zeros((len(texts),s.E.shape[1]),dtype=np.float32)
        for i,t in enumerate(texts):
            ids=[x for x in s.tok.encode(t,add_special_tokens=False).ids]
            if ids: out[i]=s.E[ids].mean(0)
        return out/np.maximum(np.linalg.norm(out,axis=1,keepdims=True),1e-9) if normalize else out
def get(name): return Potion() if name=='potion' else Onnx(name)
