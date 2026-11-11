"""Синтетичний біомедичний граф (НЕ реальні дані): 600 вузлів. Детермінований (seed=42)."""
import csv, random, json
random.seed(42)
D=[f'D{i:03d}' for i in range(200)]; R=[f'R{i:03d}' for i in range(150)]; G=[f'G{i:03d}' for i in range(150)]; S=[f'S{i:03d}' for i in range(100)]
sub=[(D[i],D[random.randrange(max(0,i-30),i)]) for i in range(1,200)]          # дерево/дерево-подібна ієрархія (дитина -> батько)
treats={(random.choice(R),random.choice(D)) for _ in range(900)}
assoc={(random.choice(D),random.choice(G)) for _ in range(700)}
hassym={(random.choice(D),random.choice(S)) for _ in range(800)}
inter={tuple(sorted(random.sample(R,2))) for _ in range(350)}
def w(f,rows,h=None):
    with open(f'../data/{f}.csv','w',newline='') as fh:
        c=csv.writer(fh)
        if h: c.writerow(h)
        c.writerows(rows)
w('disease',[(x,'Disease '+x[1:]) for x in D],['id','name']); w('drug',[(x,'Drug '+x[1:]) for x in R],['id','name'])
w('gene',[(x,'Gene '+x[1:]) for x in G],['id','name']); w('symptom',[(x,'Symptom '+x[1:]) for x in S],['id','name'])
w('subclass',sorted(sub)); w('treats',sorted(treats)); w('assoc',sorted(assoc)); w('hassym',sorted(hassym)); w('interacts',sorted(inter))
print('nodes',len(D)+len(R)+len(G)+len(S),'edges',len(sub)+len(treats)+len(assoc)+len(hassym)+len(inter))
