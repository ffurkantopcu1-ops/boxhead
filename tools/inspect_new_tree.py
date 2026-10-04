"""Costs and concrete paths in the generated graph (zero-cost roots included)."""
import sys, json, heapq, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from logic.skill_tree import SkillTree


def distances(start, free=()):
    free=set(free)|{start}
    costs={start:0}; parents={}; queue=[(0,start)]
    while queue:
        cost,n=heapq.heappop(queue)
        if cost!=costs[n]: continue
        for other in SkillTree.ADJ[n]:
            candidate=cost+(0 if other in free else SkillTree.get_cost(other))
            if candidate<costs.get(other,10**9):
                costs[other]=candidate; parents[other]=n
                heapq.heappush(queue,(candidate,other))
    return costs,parents


def path_to(start,target):
    costs,parents=distances(start); path=[target]
    while path[-1]!=start: path.append(parents[path[-1]])
    return list(reversed(path))


def report():
    centers=[n['id'] for n in SkillTree.NODES if n['id'].startswith('central_')]
    result={'nodes':len(SkillTree.NODES),'class_costs':{},'central_costs':{},'second_oath_costs':{}}
    for cls,start in SkillTree.START_BY_CLASS.items():
        costs,_=distances(start)
        result['class_costs'][cls]={other:min(costs[n['id']] for n in SkillTree.NODES if n['arm']==other and n['type']=='notable') for other in SkillTree.START_BY_CLASS}
        result['central_costs'][cls]={n:costs[n] for n in centers}
        result['second_oath_costs'][cls]={}
        for first in centers:
            paid=path_to(start,first)
            marginal,_=distances(start,paid)
            result['second_oath_costs'][cls][first]=min(marginal[n] for n in centers if n!=first)
    close=[]
    for i,a in enumerate(SkillTree.NODES):
        for b in SkillTree.NODES[i+1:]:
            dist=math.dist(a['pos'],b['pos'])
            if dist<44: close.append([a['id'],b['id'],round(dist,1)])
    result['close_pairs_under_44']=close
    return result


if __name__=='__main__':
    out=report()
    Path(sys.argv[1]).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Nodes:',out['nodes'],'overlap candidates:',len(out['close_pairs_under_44']))
    print('Cheapest center:',{k:min(v.values()) for k,v in out['central_costs'].items()})
    print('Second center minimum:',min(v for c in out['second_oath_costs'].values() for v in c.values()))
