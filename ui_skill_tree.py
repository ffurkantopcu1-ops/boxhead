"""Cached gothic artwork and semantic medallions for the passive tree."""
import os
from functools import lru_cache
import pygame

ART_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'ui', 'gothic')
ICON_ORDER = ('bounce','pierce','volley','reach','shield','leech','speed','crit',
              'fire','frost','poison','tempo','turret','minion','heart','coin')
CLASS_COLORS = {
    'warrior':(200,100,85), 'ninja':(175,190,210), 'bloodwalker':(210,65,65),
    'beastmaster':(140,190,110), 'engineer':(205,151,74), 'sniper':(218,193,122),
    'sorcerer':(160,135,215), 'alchemist':(135,184,94), 'bomber':(218,132,65),
    'core':(175,152,113),
}


@lru_cache(maxsize=4)
def source(name):
    return pygame.image.load(os.path.join(ART_DIR,name)).convert_alpha()


@lru_cache(maxsize=8)
def background(size):
    result=pygame.transform.smoothscale(source('tree_background.png'),size)
    shade=pygame.Surface(size,pygame.SRCALPHA)
    pygame.draw.rect(shade,(0,0,0,100),(30,110,size[0]-60,size[1]-145))
    result.blit(shade,(0,0))
    return result


@lru_cache(maxsize=384)
def medallion(icon, diameter, state):
    atlas = source('tree_icons.png')
    index = ICON_ORDER.index(icon) if icon in ICON_ORDER else 3
    w,h=atlas.get_size(); cw,ch=w//4,h//4
    cell=atlas.subsurface((index%4*cw,index//4*ch,cw,ch))
    image=pygame.transform.smoothscale(cell,(diameter,diameter)).copy()
    # The original black atlas margin becomes transparent; embossed material
    # is kept intact inside a circular mask, without per-frame pixel work.
    mask=pygame.Surface((diameter,diameter),pygame.SRCALPHA)
    pygame.draw.circle(mask,(255,255,255,255),(diameter//2,diameter//2),int(diameter*.47))
    image.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    if state=='locked': image.fill((205,205,210,255),special_flags=pygame.BLEND_RGBA_MULT)
    return image


def draw_node(screen,node,center,r,state,matched=False):
    color=CLASS_COLORS.get(node.get('arm','core'),CLASS_COLORS['core'])
    if state=='allocated': color=(246,209,121)
    if matched or state=='allocated':
        pygame.draw.circle(screen,(78,60,31),center,r+4)
        pygame.draw.circle(screen,color,center,r+2,2)
    if node['type']=='keystone':
        cx,cy=center
        points=[(cx,cy-r-5),(cx+r+5,cy),(cx,cy+r+5),(cx-r-5,cy)]
        pygame.draw.polygon(screen,(50,39,27),points)
        pygame.draw.polygon(screen,color,points,2)
    image=medallion(node.get('icon','reach'),max(8,2*r),state)
    screen.blit(image,image.get_rect(center=center))
    if r<=7:
        muted=tuple(int(c*.65) for c in color)
        pygame.draw.circle(screen,muted,center,max(2,r-1),1)
    if node['type']=='start' or state=='open':
        pygame.draw.circle(screen,color,center,max(3,r-1),1)


def class_guide(scene, rect, player):
    """A persistent class detail shrine beside the full-screen tree."""
    from logic.skill_tree import SkillTree
    from ui_elements import render_fit,wrap_text
    import ui_theme
    screen=scene.screen
    ui_theme.draw_inset_frame(screen,rect,'panel_frame_small.png',fill=(20,17,22),alpha=230,pad=12)
    def line(label,y,color=(212,189,145),size=17,indent=15):
        surface=render_fit(label,size,color,rect.width-indent-15)
        screen.blit(surface,(rect.x+indent,y))
    cls=player.class_id
    line(cls.title()+' • SINIF REHBERİ',rect.y+16,size=20)
    start=SkillTree.BY_ID[SkillTree.START_BY_CLASS[cls]]
    image=medallion(start.get('icon','reach'),66,'allocated')
    screen.blit(image,image.get_rect(center=(rect.centerx,rect.y+90)))
    nodes=[n for n in SkillTree.NODES if n.get('arm')==cls]
    line(f'{len(nodes)} sınıf düğümü',rect.y+136)
    y=rect.y+174
    for stat,label,icon in (('bounce','Sekme','bounce'),('pierce','Delme','pierce'),('projectileCount','Çoklu atış','volley')):
        count=sum(n.get('stats',{}).get(stat,0)>0 for n in nodes)
        screen.blit(medallion(icon,34,'open'),(rect.x+17,y))
        line(f'{label} • {count} düğüm',y+8,size=16,indent=59)
        y+=49
    y+=8
    line('İLK BÜYÜK SEÇİM: 4 SP',y,size=16);y+=30
    line('MERKEZ ÖZELLİKLERİ',y,size=17);y+=26
    message='İlk merkez: 19 puan. İkinci merkez: en az 15 ek puan. Merkezler arasında doğrudan yol yok.'
    for part in wrap_text(scene.font_desc,message,rect.width-32):
        line(part,y,(178,170,153),15);y+=21
    if y+58<rect.bottom:
        y+=18
        line('Küçük: destek • Büyük: uzmanlık',y,size=14)
        line('Elmas: güçlü, bedelli özellik',y+23,size=14)
