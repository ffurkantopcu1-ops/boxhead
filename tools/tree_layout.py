"""Separate passive nodes from straight connections; graph IDs stay unchanged."""
import math

RADII = {'minor': 30, 'notable': 50, 'keystone': 58, 'start': 75}


def arrange(nodes):
    by_id = {n['id']: n for n in nodes}
    edges = sorted({tuple(sorted((n['id'], other))) for n in nodes for other in n['connects']})
    fixed = {n['id'] for n in nodes if n['type'] == 'start'}
    for iteration in range(3000):
        cells = {}
        for node in nodes:
            x,y = node['pos']
            cells.setdefault((int(x//160),int(y//160)), []).append(node)
        forces = {}
        conflicts = 0
        def push(nid, dx, dy):
            if nid not in fixed:
                f = forces.setdefault(nid, [0.0,0.0,0])
                f[0] += dx; f[1] += dy; f[2] += 1
        for first,second in edges:
            a,b = by_id[first]['pos'],by_id[second]['pos']
            dx,dy = b[0]-a[0],b[1]-a[1]
            length2 = dx*dx+dy*dy
            for gx in range(int((min(a[0],b[0])-85)//160),int((max(a[0],b[0])+85)//160)+1):
                for gy in range(int((min(a[1],b[1])-85)//160),int((max(a[1],b[1])+85)//160)+1):
                    for n in cells.get((gx,gy), ()):
                        if n['id'] in (first,second): continue
                        x,y = n['pos']
                        t = max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/max(1,length2)))
                        vx,vy = x-a[0]-t*dx,y-a[1]-t*dy
                        dist = math.hypot(vx,vy)
                        gap = RADII[n['type']]+5
                        if dist >= gap: continue
                        conflicts += 1
                        if dist < .001:
                            vx,vy = -dy,dx; dist=max(.001,math.hypot(vx,vy))
                        shift = min(20,gap-math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)+1)
                        ux,uy = vx/dist*shift,vy/dist*shift
                        push(n['id'], ux,uy)
                        push(first,-ux*(1-t)*.45,-uy*(1-t)*.45)
                        push(second,-ux*t*.45,-uy*t*.45)
        for n in nodes:
            x,y=n['pos']; gx,gy=int(x//160),int(y//160)
            for ix in range(gx-1,gx+2):
                for iy in range(gy-1,gy+2):
                    for other in cells.get((ix,iy),()):
                        if n['id']>=other['id']:continue
                        vx,vy=x-other['pos'][0],y-other['pos'][1]
                        dist=math.hypot(vx,vy);gap=RADII[n['type']]+RADII[other['type']]+8
                        if dist>=gap:continue
                        conflicts+=1
                        if dist<.001:vx,vy,dist=1,0,1
                        amount=min(20,(gap-dist+1)/2)
                        ux,uy=vx/dist*amount,vy/dist*amount
                        push(n['id'],ux,uy);push(other['id'],-ux,-uy)
        if not conflicts:
            for n in nodes: n['pos']=[round(v,2) for v in n['pos']]
            return nodes
        for nid,(dx,dy,count) in forces.items():
            node=by_id[nid]
            node['pos'][0]+=dx/max(1,count*.5)
            node['pos'][1]+=dy/max(1,count*.5)
    raise ValueError(f'Straight tree layout unresolved: {conflicts} collisions')
