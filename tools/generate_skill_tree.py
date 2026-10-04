"""Generate the connected passive tree, preserving the published branch IDs.
Shared bridges begin at mastery, never at class starts.
"""
import json
import math
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "skill_tree.json")

CAT_PRIORITY = ["turret", "minion", "utility", "element", "dot", "defense", "damage"]

STAT_CAT = {
    # --- saldırı ---
    "dmgMult": "damage", "physDmgFlat": "damage", "physDmgMult": "damage",
    "critChance": "damage", "critDmg": "damage", "attack_speed_bonus": "damage",
    "armorPenFlat": "damage", "armorPen": "damage", "bossDmgMult": "damage", "bullet_speed": "damage",
    "pierce": "damage", "bounce": "damage", "projectileCount": "damage",
    "meleeRangeFlat": "damage",
    # --- element ---
    "fireDmgFlat": "element", "fireDmgMult": "element",
    "frostDmgFlat": "element", "frostDmgMult": "element",
    "elementDmgMult": "element",
    # --- süreli hasar / alan ---
    "dotDmgMult": "dot", "poisonDps": "dot", "aoe_bonus": "dot",
    # --- hayatta kalma ---
    "max_hp": "defense", "max_hp_pct": "defense", "armor": "defense",
    "regen": "defense", "combatRegen": "defense", "lifesteal": "defense",
    "dodgeChance": "defense", "maxEnergyShield": "defense", "esRegen": "defense",
    "speed": "defense",
    # --- minyon ---
    "minionDamage": "minion", "minionRate": "minion", "minionMaxHpFlat": "minion",
    "minionCount": "minion", "minionArmor": "minion", "minionRange": "minion",
    "minionPierce": "minion", "minionBounce": "minion",
    # --- taret ---
    "turretDmg": "turret", "turretRate": "turret", "turretMaxHp": "turret",
    "turretLimit": "turret", "turretCharges": "turret", "turretRange": "turret",
    # --- yardımcı ---
    "magicFind": "utility", "goldGain": "utility", "xpGain": "utility",
    "shopRarity": "utility", "magnetRadius": "utility",
}


def cat_of(stats):
    """Düğümün kategorisi: statları arasında en yüksek öncelikli olan."""
    if not stats:
        return "core"
    cats = {STAT_CAT.get(k, "damage") for k in stats}
    for c in CAT_PRIORITY:
        if c in cats:
            return c
    return "damage"


# ----------------------------------------------------------------------
# STAT ETİKETLERİ — işaret duyarlı (negatif bedeller de okunabilir yazılır)
# ----------------------------------------------------------------------
def _pct(v):
    return f"%{abs(v) * 100:g}"


def _flat(v, dec=0):
    return f"{abs(v):.{dec}f}"


def _sg(v):
    return "+" if v >= 0 else "-"


STAT_LABEL = {
    "max_hp":             lambda v: f"{_sg(v)}{_flat(v)} Can",
    "max_hp_pct":         lambda v: (f"Max Can %{-v:.0f} azalır" if v < 0
                                     else f"+%{v:.0f} Max Can"),
    "maxEnergyShield":    lambda v: f"{_sg(v)}{_flat(v)} Enerji Kalkanı",
    "esRegen":            lambda v: f"{_sg(v)}{_flat(v)} ES Yenilenme",
    "armor":              lambda v: f"{_sg(v)}{_flat(v)} Zırh",
    "regen":              lambda v: f"{_sg(v)}{_flat(v, 1)} Can Yenilenme",
    "combatRegen":        lambda v: f"{_sg(v)}{_flat(v, 1)} Savaş Yenilenme",
    "lifesteal":          lambda v: f"{_sg(v)}{_pct(v)} Can Çalma",
    "dodgeChance":        lambda v: f"{_sg(v)}{_pct(v)} Kaçınma",
    "speed":              lambda v: f"{_sg(v)}{_flat(v, 1)} Hareket Hızı",
    "dmgMult":            lambda v: f"{_sg(v)}{_pct(v)} Hasar",
    "attack_speed_bonus": lambda v: f"{_sg(v)}{_pct(v)} Saldırı Hızı",
    "critChance":         lambda v: f"{_sg(v)}{_pct(v)} Kritik Şans",
    "critDmg":            lambda v: f"{_sg(v)}{_pct(v)} Kritik Hasar",
    "physDmgFlat":        lambda v: f"{_sg(v)}{_flat(v)} Fiziksel Hasar",
    "physDmgMult":        lambda v: f"{_sg(v)}{_pct(v)} Fiziksel Hasar",
    "fireDmgFlat":        lambda v: f"{_sg(v)}{_flat(v)} Ateş Hasarı",
    "fireDmgMult":        lambda v: f"{_sg(v)}{_pct(v)} Ateş Hasarı",
    "frostDmgFlat":       lambda v: f"{_sg(v)}{_flat(v)} Buz Hasarı",
    "frostDmgMult":       lambda v: f"{_sg(v)}{_pct(v)} Buz Hasarı",
    "elementDmgMult":     lambda v: f"{_sg(v)}{_pct(v)} Element Hasarı",
    "dotDmgMult":         lambda v: f"{_sg(v)}{_pct(v)} DoT Hasarı",
    "poisonDps":          lambda v: f"{_sg(v)}{_flat(v)} Zehir DPS",
    "aoe_bonus":          lambda v: f"{_sg(v)}{_pct(v)} Alan (AoE)",
    "pierce":             lambda v: f"{_sg(v)}{_flat(v)} Delme",
    "bounce":             lambda v: f"{_sg(v)}{_flat(v)} Sekme",
    "projectileCount":    lambda v: f"{_sg(v)}{_flat(v)} Mermi",
    "bullet_speed":       lambda v: f"{_sg(v)}{_flat(v)} Mermi Hızı",
    "meleeRangeFlat":     lambda v: f"{_sg(v)}{_flat(v)} Menzil",
    "armorPenFlat":       lambda v: f"{_sg(v)}{_flat(v, 1)} Düz Zırh Delme",
    "armorPen":           lambda v: f"{_sg(v)}{_flat(v, 1)} Zırh Delme",
    "bossDmgMult":        lambda v: f"{_sg(v)}{_pct(v)} Boss Hasarı",
    "turretDmg":          lambda v: f"{_sg(v)}{_pct(v)} Taret Hasarı",
    "turretRate":         lambda v: f"{_sg(v)}{_pct(v)} Taret Saldırı Hızı",
    "turretMaxHp":        lambda v: f"{_sg(v)}{_flat(v)} Taret Canı",
    "turretLimit":        lambda v: f"{_sg(v)}{_flat(v)} Taret Limiti",
    "turretCharges":      lambda v: f"{_sg(v)}{_flat(v)} Taret Şarjı",
    "turretRange":        lambda v: f"{_sg(v)}{_flat(v)} Taret Menzili",
    "minionDamage":       lambda v: f"{_sg(v)}{_pct(v)} Minyon Hasarı",
    "minionRate":         lambda v: f"{_sg(v)}{_pct(v)} Minyon Saldırı Hızı",
    "minionRange":        lambda v: f"{_sg(v)}{_pct(v)} Minyon Menzili",
    "minionMaxHpFlat":    lambda v: f"{_sg(v)}{_flat(v)} Minyon Canı",
    "minionCount":        lambda v: f"{_sg(v)}{_flat(v)} Minyon",
    "minionArmor":        lambda v: f"{_sg(v)}{_flat(v)} Minyon Zırhı",
    "minionPierce":       lambda v: f"{_sg(v)}{_flat(v)} Minyon Delmesi",
    "minionBounce":       lambda v: f"{_sg(v)}{_flat(v)} Minyon Sekmesi",
    "magicFind":          lambda v: f"{_sg(v)}{_pct(v)} Eşya Düşme Şansı",
    "goldGain":           lambda v: f"{_sg(v)}{_pct(v)} Altın Kazanımı",
    "xpGain":             lambda v: f"{_sg(v)}{_pct(v)} XP Kazanımı",
    "shopRarity":         lambda v: f"{_sg(v)}{_flat(v)} Kervan Nadirliği",
    "magnetRadius":       lambda v: f"{_sg(v)}{_flat(v)} Toplama Alanı",
}


def desc_of(stats):
    return ", ".join(STAT_LABEL.get(k, lambda v: f"{k} {v}")(v) for k, v in stats.items())


def label_of(stat, val):
    return STAT_LABEL.get(stat, lambda v: f"{stat} {v}")(val)


STAT_LABEL.update({
    'treePoisonConversion': lambda v: 'Doğrudan hasarın %50’sini 4 saniyelik zehre dönüştürür',
    'treeFireOnly': lambda v: '+%200 ateş hasarı; ateş dışı hasar sıfır',
    'treeSingleShot': lambda v: 'Tek mermi, sekme/delme yok; iki kat doğrudan hasar',
    'treeNoCrit': lambda v: 'Kritik vuruş kapanır',
    'treeNoRegen': lambda v: 'Can yenilenmesi kapanır',
    'treeNoArmor': lambda v: 'Zırh sıfıra kilitlenir',
    'treeNoDodge': lambda v: 'Kaçınma sıfıra kilitlenir',
    "aoe": lambda v: f"{_sg(v)}{_pct(v)} Alan Etkisi",
    "cooldownReduction": lambda v: f"{_sg(v)}{_pct(v)} Yetenek Bekleme Azaltma",
    "killComboDmg": lambda v: f"Kombo başına {_sg(v)}{_pct(v)} Hasar",
    "lowHpExec": lambda v: f"%{abs(v) * 100:g} canın altında İnfaz",
    "minionMaxHp": lambda v: f"{_sg(v)}{_pct(v)} Minyon Canı",
    "minionProjectileCount": lambda v: f"{_sg(v)}{_flat(v)} Minyon Mermisi",
})
STAT_CAT.update({"aoe": "dot", "cooldownReduction": "utility",
                 "killComboDmg": "damage", "lowHpExec": "damage",
                 "minionMaxHp": "minion", "minionProjectileCount": "minion"})


import sys
sys.path.insert(0, ROOT)
from tools.tree_clusters import CLUSTERS, KEYSTONES

CLASSES = ['warrior', 'ninja', 'bloodwalker', 'beastmaster', 'engineer',
           'sniper', 'sorcerer', 'alchemist', 'bomber']
TREE_VERSION = 2
STAT_LABEL.update({
    'meleeRangeMult': lambda v: f'{_sg(v)}{_pct(v)} Yakın Dövüş Menzili',
    'minionPhysDmgFlat': lambda v: f'{_sg(v)}{_flat(v)} Minyon Fiziksel Hasarı',
    'minionCrit': lambda v: f'{_sg(v)}{_pct(v)} Minyon Kritik Şansı',
    'minionFireDmgFlat': lambda v: f'{_sg(v)}{_flat(v)} Minyon Ateş Hasarı',
    'minionFrostDmgFlat': lambda v: f'{_sg(v)}{_flat(v)} Minyon Buz Hasarı',
})
STAT_CAT.update({k:'minion' for k in ('minionPhysDmgFlat','minionCrit',
                                    'minionFireDmgFlat','minionFrostDmgFlat')})

def icon_of(stats, arm='core'):
    priorities = [('bounce','bounce'),('minionBounce','bounce'),('pierce','pierce'),
                  ('minionPierce','pierce'),('projectileCount','volley'),
                  ('minionProjectileCount','volley'),('meleeRangeFlat','reach'),
                  ('meleeRangeMult','reach'),('lifesteal','leech'),
                  ('turretLimit','turret'),('minionCount','minion'),
                  ('fireDmgFlat','fire'),('fireDmgMult','fire'),
                  ('frostDmgFlat','frost'),('frostDmgMult','frost'),
                  ('poisonDps','poison'),('dotDmgMult','poison'),
                  ('speed','speed'),('critChance','crit'),('critDmg','crit'),
                  ('attack_speed_bonus','tempo'),('cooldownReduction','tempo'),
                  ('armor','shield'),('maxEnergyShield','shield'),
                  ('max_hp','heart'),('regen','heart'),('goldGain','coin')]
    for stat, icon in priorities:
        if stats.get(stat,0)>0: return icon
    if arm == 'engineer': return 'turret'
    if arm == 'beastmaster': return 'minion'
    return 'reach'

def generate():
    nodes, by_id = [], {}
    def add(nid, name, arm, typ, stats, pos, connects=(), **extra):
        node = dict(id=nid,name=name,arm=arm,type=typ,stats=dict(stats),
                    desc=desc_of(stats),cat=cat_of(stats),icon=icon_of(stats,arm),
                    pos=[round(v) for v in pos],connects=list(connects),**extra)
        if typ=='start': node['start']=True
        nodes.append(node); by_id[nid]=node
        return nid
    def link(a,b): by_id[a]['connects'].append(b)
    # Three near clusters, three mid clusters, two deep clusters. Every ring
    # has two equal-cost entry paths and independently useful support nodes.
    locations=[(-360,120),(0,120),(360,120),(-280,-350),(0,-350),(280,-350),(-130,-850),(130,-850)]
    edges=[(0,1),(1,2),(0,3),(1,4),(2,5),(3,6),(5,7),(6,7)]
    def position(cls,x,y):
        i=CLASSES.index(cls); a=-math.pi/2+i*2*math.pi/9
        # Local y grows outwards, local x follows the circumference.
        return (4000+math.cos(a)*(1500+y)-math.sin(a)*x,
                4000+math.sin(a)*(1500+y)+math.cos(a)*x)
    def ring(cls,k,j): return f'{cls}_{CLUSTERS[cls][k][0]}_{j}'
    for cls in CLASSES:
        start=add('start_'+cls,cls.title()+' Başlangıcı',cls,'start',{},position(cls,0,430))
        by_id[start]['icon']={'warrior':'reach','ninja':'reach','bloodwalker':'leech',
            'beastmaster':'minion','engineer':'turret','sniper':'crit',
            'sorcerer':'frost','alchemist':'poison','bomber':'fire'}[cls]
        for k,(key,name,minor,notable) in enumerate(CLUSTERS[cls]):
            x,y=locations[k]
            for j in range(7):
                a=math.pi/2+j*math.tau/7
                # Repeated theme stats are modest, not repeated major mechanics.
                stats=minor[j%4]
                radius=105 if k<3 else 90 if k<6 else 70
                add(ring(cls,k,j), name+' — '+desc_of(stats),cls,'minor',stats,
                    position(cls,x+radius*math.cos(a),y+radius*math.sin(a)),
                    route=name,cluster=key)
            for j in range(7): link(ring(cls,k,j),ring(cls,k,(j+1)%7))
            add(f'{cls}_{key}_notable',name,cls,'notable',notable,
                position(cls,x,y),[ring(cls,k,2),ring(cls,k,5)],cluster=key)
            if k<3: link(start,ring(cls,k,0))
        for ei,(a,b) in enumerate(edges):
            ax,ay=locations[a]; bx,by=locations[b]
            # Links attach to the far half of early rings, so no notable at 1–2 SP.
            ja,jb=(4,0) if b//3>a//3 else (2,6)
            stats=CLUSTERS[cls][b][2][ei%4]
            add(f'{cls}_cross_{ei}', 'Geçiş — '+desc_of(stats),cls,'minor',stats,
                position(cls,(ax+bx)/2,(ay+by)/2),[ring(cls,a,ja),ring(cls,b,jb)])
        for b,(name,stats) in enumerate(KEYSTONES[cls]):
            k=6+b; x,y=locations[k]
            add(f'{cls}_keystone_{b+1}',name,cls,'keystone',stats,
                position(cls,x,y+230),[ring(cls,k,4)],cluster='keystone')
        # Additional diagonals turn the region into a web rather than separate
        # rows of circles. Attach to support nodes, never chain major rewards.
        for a,b,ja,jb in ((0,4,4,0),(2,4,4,0),(3,4,2,6),(4,5,2,6)):
            link(ring(cls,a,ja),ring(cls,b,jb))
    shared=[
        ('Çelik Adımlar',{'meleeRangeFlat':8},{'physDmgMult':.04}),
        ('Kanlı Çeviklik',{'lifesteal':.01},{'attack_speed_bonus':.04}),
        ('Yaban Cephesi',{'meleeRangeFlat':8},{'minionDamage':.04}),
        ('Komuta Bağı',{'minionDamage':.03,'turretDmg':.03},{'minionRate':.04,'turretRate':.04}),
        ('Balistik',{'physDmgMult':.04},{'bullet_speed':.4}),
        ('Prizmatik Nişan',{'critChance':.02},{'elementDmgMult':.04}),
        ('Element Dokuma',{'elementDmgMult':.04},{'dotDmgMult':.04}),
        ('Yanıcı Karışım',{'fireDmgMult':.04},{'aoe_bonus':.04}),
        ('Savaş Cephesi',{'armor':4},{'physDmgMult':.04})]
    # Two independent passages between each neighboring region; neither
    # uses the central keystones or a mastery chokepoint.
    for i,cls in enumerate(CLASSES):
        nxt=CLASSES[(i+1)%9]; name,s1,s2=shared[i]
        for lane,k in enumerate((3,6)):
            a=ring(cls,k,2); b=ring(nxt,k,6)
            p1=by_id[a]['pos']; p2=by_id[b]['pos']; prev=a
            for j in range(1,2):
                t=j/2
                prev=add(f'bridge_{cls}_{nxt}_{lane}_{j}',name, 'core','minor',
                    s1 if j%2 else s2,
                    [p1[z]*(1-t)+p2[z]*t for z in (0,1)],[prev])
            link(prev,b)
        # A third inner passage fills the gap between the early regions. Its
        # two useful shared supports provide another way to pivot classes.
        a=ring(cls,2,2); b=ring(nxt,0,6)
        p1,p2=by_id[a]['pos'],by_id[b]['pos']; prev=a
        for j in (1,2):
            t=j/3
            prev=add(f'shared_inner_{cls}_{j}',name,'core','minor',s1 if j==1 else s2,
                     [p1[z]*(1-t)+p2[z]*t for z in (0,1)],[prev])
        link(prev,b)
    # Independent dead-end oath paths: no central ring or cheap oath chaining.
    central=[
        ('venom','Zehir Dönüşümü',{'treePoisonConversion':.5},'Doğrudan hasarın %50’si azalır; ayrılan hasar 4 saniyelik zehre dönüşür. Dönüşüm zehirden tekrar tetiklenmez.','poison'),
        ('flame','Saf Alev',{'treeFireOnly':1},'Ateş hasarı +%200. Fiziksel, buz ve zehir hasarı sıfır; ateş dışı DoT ve yavaşlatma uygulanmaz. Taret/minyonları da etkiler. Ateş sağlayan ekipman gerekir.','fire'),
        ('single','Son Mermi',{'treeSingleShot':1},'Oyuncu ve yardımcıları tek mermi atar; sekme/delme kapanır. Doğrudan vuruş hasarı iki katına çıkar.','crit'),
        ('certainty','Kesin Darbe',{'treeNoCrit':1,'dmgMult':.8},'Oyuncu/minyon kritik vuramaz. Oyuncu genel hasarı +%80; taretler normal miras kurallarını kullanır.','reach'),
        ('giant','Devlerin Alanı',{'aoe_bonus':1,'attack_speed_bonus':-.3},'Alan boyutu +%100; oyuncu saldırı hızı -%30. Yakın dövüş erişimini artırmaz.','fire'),
        ('horizon','Ufuk Kesen',{'meleeRangeMult':.8,'max_hp_pct':-30},'Yakın dövüş menzili +%80; maksimum can -%30. Mermi menzilini artırmaz.','reach'),
        ('army','Kalabalık Ordu',{'minionCount':2,'turretLimit':2,'minionDamage':-.3,'turretDmg':-.3},'İki ek minyon/taret limiti; her birinin hasarı -%30. Yardımcı varlık sağlayan ekipman gerekir.','minion'),
        ('overdrive','Kırılgan Devir',{'minionRate':.6,'turretRate':.6,'minionMaxHp':-.4,'turretMaxHp':-80},'Yardımcıların saldırı hızı +%60; minyon canı -%40, taret canı -80.','turret'),
        ('vampire','Açlığın Yemini',{'lifesteal':.2,'treeNoRegen':1},'Can çalma +%20; doğal ve savaş can yenilenmesi kapanır. İksir ve seviye iyileşmesi korunur.','leech'),
        ('astral','Astral Kabuk',{'maxEnergyShield':180,'esRegen':12,'max_hp_pct':-50},'+180 enerji kalkanı, +12 kalkan yenilenmesi; maksimum can -%50.','shield'),
        ('wind','Rüzgârın Bedeli',{'speed':2,'dodgeChance':.15,'treeNoArmor':1},'+2 hareket hızı ve +%15 kaçınma; zırh sıfıra kilitlenir.','speed'),
        ('fortress','Yürüyen Kale',{'armor':100,'max_hp_pct':25,'speed':-1.2,'treeNoDodge':1},'+100 zırh, +%25 can; hareket hızı -1.2, kaçınma sıfıra kilitlenir.','shield'),
    ]
    for i,(key,name,stats,desc,icon) in enumerate(central):
        a=-math.pi/2+i*math.tau/len(central)
        cls=CLASSES[min(8,i*9//len(central))]
        cluster=0 if i and min(8,(i-1)*9//len(central)) == CLASSES.index(cls) else 1
        prev=ring(cls,cluster,4)
        origin=by_id[prev]['pos']
        destination=[4000+420*math.cos(a),4000+420*math.sin(a)]
        for j in range(1,15):
            t=j/15
            stat={'max_hp':8} if j%3==0 else {'dmgMult':.025} if j%3==1 else {'speed':.1}
            prev=add(f'oath_path_{key}_{j}','Merkez Yolu — '+name,'core','minor',stat,
                     [origin[z]*(1-t)+destination[z]*t for z in (0,1)],[prev])
        node=add('central_'+key,name,'core','keystone',stats,destination,[prev],
                 downside=True)
        if key in ('venom','flame'): by_id[node]['exclusive_group']='conversion'
        by_id[node].update(desc=desc,icon=icon)
    # Economy remains optional off a shared passage, never free at a class start.
    prev='bridge_engineer_sniper_0_1'
    for j,stats in enumerate([{'goldGain':.04},{'shopRarity':.04},{'magicFind':.08},
                              {'magnetRadius':20},{'regen':.4}]):
        prev=add(f'shared_trade_{j}','Gezgin Tüccar','core','minor',stats,
                 [4100+j*65,4800],[prev])
    # Keep hand-laid cluster circles stable; route supports can move slightly
    # to avoid visually overlapping icons at crossings.
    movable={n['id'] for n in nodes if n['id'].startswith(('oath_path_','bridge_','shared_trade_','shared_inner_'))}
    cells={}
    def put(node):
        pos=node['pos']; cells.setdefault((pos[0]//100,pos[1]//100),[]).append(node)
    for node in nodes:
        if node['id'] not in movable: put(node)
    for node in nodes:
        if node['id'] not in movable: continue
        original=node['pos'][:]
        placed=False
        for radius in range(0,521,20):
            angles=1 if radius==0 else 24
            for j in range(angles):
                a=j*math.tau/angles
                candidate=[round(original[0]+radius*math.cos(a)),round(original[1]+radius*math.sin(a))]
                gx,gy=candidate[0]//100,candidate[1]//100
                valid=True
                for dx in range(-2,3):
                    for dy in range(-2,3):
                        for other in cells.get((gx+dx,gy+dy),()):
                            gap=115 if other['type']=='keystone' else 80 if other['type'] in ('notable','start') else 55
                            if math.dist(candidate,other['pos'])<gap:
                                valid=False; break
                        if not valid: break
                    if not valid: break
                if valid:
                    node['pos']=candidate; put(node); placed=True; break
            if placed: break
        if not placed: raise ValueError('No clear node position: '+node['id'])
    # Match the wide reference composition; the topology stays identical.
    for node in nodes: node['pos'][0]=round(4000+(node['pos'][0]-4000)*1.45)
    from tools.tree_layout import arrange
    return arrange(nodes)

if __name__ == '__main__':
    nodes = generate()
    with open(OUT,'w',encoding='utf-8') as f:
        json.dump(nodes,f,ensure_ascii=False,indent=2); f.write('\n')
    print(f'Yetenek ağacı: {len(nodes)} düğüm.')
