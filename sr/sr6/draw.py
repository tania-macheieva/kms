import sys, json, subprocess, textwrap
sys.path.insert(0,'.'); import sr6
M=sr6.FIXED; N=M['nodes']
COL={'G':'#dbe9f6','Q':'#e4f1de','C':'#fbe5d6',None:'#eeeeee'}
def esc(s): return s.replace('"','\\"')
def wrap(s,w=22): return "\\n".join(textwrap.wrap(s,w)) or s
L=['digraph G {','rankdir=LR; nodesep=0.12; ranksep=0.9; fontname="Helvetica"; bgcolor="white";',
   'node [fontname="Helvetica",fontsize=11,style=filled,shape=box,margin="0.10,0.05"]; edge [fontname="Helvetica",fontsize=9,color="#777777",fontcolor="#333333"];']
ids={n:f"n{i}" for i,n in enumerate(N)}
for n,k in N.items():
    if k!='concept': L.append(f'{ids[n]} [label="{esc(wrap(n,26))}",shape=ellipse,fillcolor="#fff2b3"];')
    else: L.append(f'{ids[n]} [label="{esc(wrap(n))}",fillcolor="{COL.get(sr6.cl(n),"#eeeeee")}"];')
for e in M['edges']:
    new=e.get('fix') and e['id'].startswith('N'); chg=e.get('fix') and not new
    lab=e['p']+(" ["+e['qualifier']+"]" if e.get('qualifier') else "")
    if e.get('cross'): st='color="#c00000",fontcolor="#c00000",style=dashed,penwidth=2'
    elif new: st='color="#1a8a3a",fontcolor="#1a8a3a",penwidth=2'
    elif chg: st='color="#d98200",fontcolor="#d98200",penwidth=2'
    else: st=''
    L.append(f'{ids[e["s"]]} -> {ids[e["o"]]} [label="{esc(lab)}",{st}];')
L.append('}'); open('cmap_llm_fixed.dot','w',encoding='utf-8').write("\n".join(L))
try:
    subprocess.run(['dot','-Tpng','-Gdpi=80','cmap_llm_fixed.dot','-o','cmap_llm_fixed.png'],check=True)
except FileNotFoundError:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import networkx as nx

    graph=nx.DiGraph()
    graph.add_nodes_from(N)
    colors=[]; shapes={}
    for node,kind in N.items():
        color='#fff2b3' if kind!='concept' else COL.get(sr6.cl(node),'#eeeeee')
        shapes.setdefault(color,[]).append(node)
        colors.append(color)
    for e in M['edges']:
        new=e.get('fix') and e['id'].startswith('N'); changed=e.get('fix') and not new
        color='#c00000' if e.get('cross') else '#1a8a3a' if new else '#d98200' if changed else '#777777'
        graph.add_edge(e['s'],e['o'],label=e['p'],color=color)
    pos=nx.spring_layout(graph,seed=6,k=1.5,iterations=100)
    fig,ax=plt.subplots(figsize=(24,18))
    edge_colors=[data['color'] for _,_,data in graph.edges(data=True)]
    edge_labels={(source,target):data['label'] for source,target,data in graph.edges(data=True)}
    for color,nodes in shapes.items():
        nx.draw_networkx_nodes(graph,pos,nodelist=nodes,node_color=color,node_size=1500,ax=ax)
    nx.draw_networkx_edges(graph,pos,edge_color=edge_colors,arrows=True,arrowsize=12,alpha=.7,ax=ax)
    nx.draw_networkx_labels(graph,pos,font_size=7,ax=ax)
    nx.draw_networkx_edge_labels(graph,pos,edge_labels=edge_labels,font_size=5,rotate=False,ax=ax)
    ax.set_axis_off(); fig.tight_layout(); fig.savefig('cmap_llm_fixed.png',dpi=180); plt.close(fig)
print('ok')
