"""Stone hall, portrait shrine and relic cards for the inventory screens."""
from pathlib import Path
from functools import lru_cache
import pygame
import ui_theme
import ui_skill_tree
import ui_nineslice
from ui_elements import ImageLoader, render_fit, get_skull_crest


def hall(screen, rect):
    screen.blit(ui_skill_tree.background(rect.size), rect)
    veil = shade(rect.size)
    screen.blit(veil, rect)


@lru_cache(maxsize=8)
def shade(size):
    surface=pygame.Surface(size,pygame.SRCALPHA)
    surface.fill((8,6,9,115))
    return surface


@lru_cache(maxsize=32)
def portrait(class_id,size):
    folder=Path(__file__).resolve().parent/'assets'/'classes'
    paths=list(folder.glob(class_id+'.*'))
    if not paths: paths=list(folder.glob('warrior.*'))
    image=pygame.image.load(str(paths[0])).convert()
    scale=max(size[0]/image.get_width(),size[1]/image.get_height())
    scaled=pygame.transform.smoothscale(image,(int(image.get_width()*scale),int(image.get_height()*scale)))
    result=pygame.Surface(size)
    result.blit(scaled,((size[0]-scaled.get_width())//2,(size[1]-scaled.get_height())//2))
    return result


def portrait_shrine(scene,p,rect):
    inner=rect.inflate(-24,-24)
    scene.screen.blit(portrait(p.class_id,inner.size),inner)
    ui_nineslice.draw(scene.screen,'portrait_frame.png',rect)


def equipped(scene,row,item):
    labels={'weapon':'SİLAH','helmet':'MİĞFER','chest':'ZIRH','amulet':'MUSKA','pet':'YOLDAŞ','artifact':'ESER'}
    r=row.rect
    color=ui_theme.rarity_color(item.get('rarity','Normal')) if item else ui_theme.METAL_LO
    ui_theme.draw_inset_frame(scene.screen,r,'panel_frame_small.png',pad=16,
                              tint=tuple(int(c*.28) for c in color),alpha=220)
    title=render_fit(labels[row.slot_type],13,ui_theme.TEXT_COL,r.width-34,bold=True)
    scene.screen.blit(title,title.get_rect(midtop=(r.centerx,r.y+13)))
    size=max(26,min(58,r.height-58))
    box=pygame.Rect(r.centerx-size//2,r.y+34,size,size)
    ui_theme.draw_item_slot(scene.screen,box,item.get('rarity') if item else None,row.is_hovered)
    if item:
        icon=ImageLoader.get_item_icon(item.get('icon_id',''),(size-8,size-8))
        if icon:scene.screen.blit(icon,(box.x+4,box.y+4))
    name=render_fit(item['name'] if item else 'Boş yuva',13,color,r.width-24)
    scene.screen.blit(name,name.get_rect(midbottom=(r.centerx,r.bottom-10)))


def backpack(scene,card,item):
    from scenes.game_scene import ITEM_STAT_LABEL,_fmt_stat_val
    r=card.rect
    color=ui_theme.rarity_color(item.get('rarity','Normal')) if item else ui_theme.METAL_LO
    ui_theme.draw_inset_frame(scene.screen,r,'panel_frame_small.png',pad=18,
                             tint=tuple(int(c*.25) for c in color),alpha=225)
    if not item:return
    size=max(28,min(68,r.height-85))
    card.slot_rect.update(r.x+18,r.y+20,size,size)
    ui_theme.draw_item_slot(scene.screen,card.slot_rect,item.get('rarity'))
    icon=ImageLoader.get_item_icon(item.get('icon_id',''),(size-8,size-8))
    if icon:scene.screen.blit(icon,(card.slot_rect.x+4,card.slot_rect.y+4))
    tx=card.slot_rect.right+10
    name=render_fit(item['name'],17,color,max(40,r.right-tx-18),bold=True)
    scene.screen.blit(name,(tx,r.y+24))
    rarity=render_fit(item.get('rarity','Normal').upper(),13,ui_theme.TEXT_COL,max(40,r.right-tx-18))
    scene.screen.blit(rarity,(tx,r.y+48))
    values=list(item.get('itemBase',{}).items())
    if values and r.height>=120:
        stat,val=values[0]
        line=render_fit(f'{ITEM_STAT_LABEL.get(stat,stat)}: {_fmt_stat_val(stat,val)}',15,ui_theme.TEXT_COL,r.width-36)
        scene.screen.blit(line,(r.x+18,card.use_rect.top-24))
    from ui_workshop import plate
    plate(scene,card.use_rect,'TÜKET' if item.get('type')=='essence' else 'GİY','moss',item.get('type')!='orb')
    plate(scene,card.sell_rect,'SAT','ember')
    plate(scene,card.craft_rect,'CRAFT','arcane',item.get('type') in ('weapon','helmet','chest','amulet','pet','artifact'))


def filter_layout(scene):
    x=scene.bag_drop_rect.x
    w=scene.bag_drop_rect.width
    y=scene._inventory_panel_rect().y+50
    scene.inv_search_rect=pygame.Rect(x,y,w,32)
    widths=[int(w*.28),int(w*.28),int(w*.23)]
    scene.inv_combo_rects=[]
    bx=x
    for width in widths:
        scene.inv_combo_rects.append(pygame.Rect(bx,y+39,width-5,32));bx+=width
    scene.inv_clear_rect=pygame.Rect(bx,y+39,x+w-bx,32)
    # Closed menus have no hidden active hitboxes.
    for r in scene.filter_rects:r.update(-1000,-1000,1,1)
    scene.orb_toggle_rect.update(-1000,-1000,1,1)


def market_relic(scene,card,item,owned,p):
    from ui_workshop import plate
    r=card.rect
    color=ui_theme.rarity_color(item.get('rarity','Normal'))
    ui_theme.draw_inset_frame(scene.screen,r,'panel_frame_small.png',pad=20,
                             tint=tuple(int(c*.25) for c in color),alpha=220)
    size=max(30,min(66,r.height-70))
    box=pygame.Rect(r.x+18,r.y+20,size,size)
    ui_theme.draw_item_slot(scene.screen,box,item.get('rarity'))
    icon=ImageLoader.get_item_icon(item.get('icon_id',''),(size-8,size-8))
    if icon:scene.screen.blit(icon,(box.x+4,box.y+4))
    tx=box.right+10
    title=render_fit(item['name'],17,color,r.right-tx-16,bold=True)
    scene.screen.blit(title,(tx,r.y+24))
    label=render_fit(f"{item.get('price',0):,} G",17,ui_theme.readable(ui_theme.COLORS['gold']),r.width-40)
    scene.screen.blit(label,(r.x+20,card.buy_rect.y+5))
    if owned:
        label=render_fit(f'Sende {owned}',14,ui_theme.TEXT_COL,r.width-36)
        scene.screen.blit(label,(tx,r.y+49))
    plate(scene,card.buy_rect,'SATIN AL','moss',p.gold>=item.get('price',0))


def filter_click(scene,pos):
    if scene.inv_search_rect.collidepoint(pos):
        scene._inv_search_focus=True
        return True
    scene._inv_search_focus=False
    if scene.inv_clear_rect.collidepoint(pos):
        scene.inv_filter_rarity=scene.inv_filter_type='TÜMÜ'
        scene._inv_query=''
        scene.hide_orbs=False
        scene.inventory_page=0
        scene._filter_open=None
        return True
    for i,r in enumerate(scene.inv_combo_rects):
        if r.collidepoint(pos):
            if i==2:
                modes=('loot','rarity','name')
                scene.inv_sort_mode=modes[(modes.index(getattr(scene,'inv_sort_mode','loot'))+1)%3]
            else:
                scene._filter_open=None if getattr(scene,'_filter_open',None)==i else i
            return True
    for value,r in getattr(scene,'_filter_options',[]):
        if getattr(scene,'_filter_open',None) is not None and r.collidepoint(pos):
            if scene._filter_open==0:scene.inv_filter_rarity=value
            else:scene.inv_filter_type=value
            scene._filter_open=None
            scene.inventory_page=0
            return True
    scene._filter_open=None
    return False


def filters(scene,popup=False):
    from ui_workshop import plate
    labels={'TÜMÜ':'Tümü','Normal':'Normal','Magic':'Büyülü','Rare':'Nadir','Unique':'Eşsiz','SET':'Set',
            'weapon':'Silah','armor':'Zırh','accessory':'Aksesuar','special':'Özel','pet':'Yoldaş','essence':'Öz','orb':'Orb'}
    if not popup:
        r=scene.inv_search_rect
        ui_theme.draw_inset_frame(scene.screen,r,'panel_frame_small.png',pad=8)
        label=getattr(scene,'_inv_query','') or 'Eşya adıyla ara…'
        if getattr(scene,'_inv_search_focus',False):label+=' |'
        scene.screen.blit(render_fit(label,17,ui_theme.TEXT_COL,r.width-28),(r.x+14,r.y+7))
        for r,label in zip(scene.inv_combo_rects,(f"Nadirlik: {labels.get(scene.inv_filter_rarity,scene.inv_filter_rarity)}  ▾",
                    f"Tür: {labels.get(scene.inv_filter_type,scene.inv_filter_type)}  ▾",
                    'Sırala: '+{'loot':'Geliş','rarity':'Nadirlik','name':'İsim'}[getattr(scene,'inv_sort_mode','loot')])):
            plate(scene,r,label,'night')
        plate(scene,scene.inv_clear_rect,'TEMİZLE','ember')
        return
    opened=getattr(scene,'_filter_open',None)
    scene._filter_options=[]
    if opened is None:return
    values=scene.rarity_filters if opened==0 else list(scene.type_filters)+['pet','essence','orb']
    base=scene.inv_combo_rects[opened]
    panel=pygame.Rect(base.x,base.bottom+4,max(170,base.width),len(values)*31+24)
    panel.clamp_ip(scene.screen.get_rect().inflate(-20,-20))
    ui_theme.draw_inset_frame(scene.screen,panel,'panel_frame_small.png',pad=12,alpha=255)
    for i,value in enumerate(values):
        row=pygame.Rect(panel.x+12,panel.y+12+i*31,panel.width-24,29)
        plate(scene,row,labels.get(value,value),'gold')
        scene._filter_options.append((value,row))
