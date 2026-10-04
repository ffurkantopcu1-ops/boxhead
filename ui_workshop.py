"""Shared inventory gestures and responsive workshop rendering."""
import pygame
import ui_theme
from ui_elements import render_fit, ImageLoader, wrap_text

EQUIPMENT = ('weapon', 'helmet', 'chest', 'amulet', 'pet', 'artifact')


def plate(scene, rect, label, key='gold', enabled=True):
    hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
    ui_theme.draw_plate(scene.screen, rect, 'hover' if hover else ('normal' if enabled else 'disabled'),
                        ui_theme.COLORS[key] if enabled else None)
    txt = render_fit(label, 17, ui_theme.TEXT_COL, rect.width - (10 if rect.width <= 70 else 28), bold=hover)
    scene.screen.blit(txt, txt.get_rect(center=rect.center))


def text(scene, label, rect, size=18, key='gold'):
    surf = render_fit(label, size, ui_theme.readable(ui_theme.COLORS[key]), rect.width, bold=True)
    scene.screen.blit(surf, (rect.x, rect.y))


def start_drag(scene, player, pos):
    if scene.show_craft_window or scene.active_tab != 'inventory':
        return False
    if getattr(scene,'_filter_open',None) is not None:
        return False
    scene._apply_inventory_layout()
    items = scene._filtered_inventory(player)
    for card in scene.bp_cards:
        idx = scene.inventory_page * 12 + card.idx
        if idx < len(items) and card.rect.collidepoint(pos):
            if any(r.collidepoint(pos) for r in (card.use_rect, card.sell_rect, card.craft_rect)):
                return False
            scene._item_drag = {'item': items[idx], 'source': None, 'start': pos, 'pos': pos, 'moved': False}
            return True
    for row in scene.equip_rows:
        item = player.inv_manager.equipped.get(row.slot_type)
        if item and row.rect.collidepoint(pos):
            scene._item_drag = {'item': item, 'source': row.slot_type, 'start': pos, 'pos': pos, 'moved': False}
            return True
    return False


def finish_drag(scene, player, pos):
    drag = getattr(scene, '_item_drag', None)
    scene._item_drag = None
    if not drag or not drag['moved']:
        return
    item, source = drag['item'], drag['source']
    # Identity matters: two equal rolls are still two distinct items.
    index = next((i for i, it in enumerate(player.inventory) if it is item), None)
    if source:
        if player.inv_manager.equipped.get(source) is not item:
            return
    elif index is None:
        return
    if scene.craft_drop_rect.collidepoint(pos) and item.get('type') in EQUIPMENT:
        scene.crafting_target = item
        scene.show_craft_window = True
        scene.orb_inv_page = scene.orb_market_page = 0
        scene.craft_error_msg = ''
        scene._selected_craft_orb = None
        scene._selected_recipe = None
        scene._recipe_page = 0
        return
    for row in scene.equip_rows:
        if row.rect.collidepoint(pos):
            if not source and item.get('type') == row.slot_type:
                if player.inv_manager.equip(item):
                    player.inventory.pop(index)
            return
    if source and scene.bag_drop_rect.collidepoint(pos):
        player.inv_manager.unequip(source)


def draw_drag(scene):
    drag = getattr(scene, '_item_drag', None)
    if not drag or not drag['moved']:
        return
    item = drag['item']
    for row in scene.equip_rows:
        if row.slot_type == item.get('type'):
            pygame.draw.rect(scene.screen,ui_theme.readable(ui_theme.COLORS['moss']),row.rect,2)
    plate(scene, scene.craft_drop_rect, 'ATÖLYEYE BIRAK', 'arcane', item.get('type') in EQUIPMENT)
    x, y = drag['pos']
    box = pygame.Rect(x + 14, y + 14, 64, 64)
    box.clamp_ip(scene.screen.get_rect())
    ui_theme.draw_item_slot(scene.screen, box, item.get('rarity'), True)
    icon = ImageLoader.get_item_icon(item.get('icon_id', ''), (48, 48))
    if icon:
        scene.screen.blit(icon, (box.x + 8, box.y + 8))


def craft_layout(scene):
    w, h = min(1220, scene.width-48), min(820, scene.height-48)
    panel = pygame.Rect((scene.width-w)//2, (scene.height-h)//2, w,h)
    inner = panel.inflate(-72,-64)
    left = int(inner.width*.34)
    right = pygame.Rect(inner.x+left+20, inner.y+76, inner.width-left-20, inner.height-212)
    item = pygame.Rect(inner.x, right.y, left, right.height)
    mode_w = (right.width-16)//3
    modes = [pygame.Rect(right.x+i*(mode_w+8),inner.y+34,mode_w,34) for i in range(3)]
    grid_h = right.height-120
    row_h = grid_h//3
    col_w = (right.width-10)//2
    orbs = [pygame.Rect(right.x+(i%2)*(col_w+10),right.y+(i//2)*row_h,col_w,row_h-6)
            for i in range(scene.ORB_ROWS_PER_PAGE)]
    market_y = right.bottom+32
    market_w = (inner.width-32)//5
    markets = [pygame.Rect(inner.x+i*(market_w+8),market_y,market_w,90)
               for i in range(scene.MARKET_ROWS_PER_PAGE)]
    return dict(panel=panel,inner=inner,item=item,preview=pygame.Rect(right.x,right.y+grid_h,right.width,76),
                orb_mode=modes[0],recipe_mode=modes[1],advanced_mode=modes[2],
                close=pygame.Rect(inner.right-36,inner.y-4,36,30),
                orb_rows=orbs,orb_use=orbs,
                mkt_rows=markets,mkt_buy=[pygame.Rect(r.x+8,r.bottom-29,r.width-16,24) for r in markets],
                take_back=pygame.Rect(item.x+16,item.bottom-36,item.width-32,28),
                apply=pygame.Rect(right.x,right.bottom-37,right.width-112,35),
                orb_prev=pygame.Rect(right.right-104,right.bottom-37,48,35),
                orb_next=pygame.Rect(right.right-48,right.bottom-37,48,35),
                mkt_prev=pygame.Rect(inner.right-82,market_y-28,36,24),
                mkt_next=pygame.Rect(inner.right-40,market_y-28,36,24))


def _paragraph(scene, label, rect, size=16, key='steel'):
    from ui_elements import get_font
    font = get_font(size)
    color = ui_theme.readable(ui_theme.COLORS[key])
    for i,line in enumerate(wrap_text(font,label,rect.width)[:max(1,rect.height//(size+3))]):
        scene.screen.blit(font.render(line,True,color),(rect.x,rect.y+i*(size+3)))


def _operation_icon(option):
    stat = option.get('stat',option.get('id','').split(':')[-1])
    if 'turret' in stat: return 'turret'
    if 'minion' in stat: return 'minion'
    if 'fire' in stat: return 'fire'
    if 'frost' in stat: return 'frost'
    if 'poison' in stat or 'dot' in stat: return 'poison'
    if 'crit' in stat: return 'crit'
    if 'hp' in stat or 'regen' in stat: return 'heart'
    if 'armor' in stat or 'Shield' in stat: return 'shield'
    if 'speed' in stat: return 'speed'
    return 'reach'


def draw_craft(scene):
    from scenes.game_scene import ITEM_STAT_LABEL, _fmt_stat_val
    from logic.crafting import recipes, recipe_cost, recipe_tier, advanced_recipes, recipe_error
    from logic.affix_rules import bench_value, item_level
    import ui_gothic_tabs
    import ui_skill_tree
    scene._overlay_surface.fill((0,0,0,225))
    scene.screen.blit(scene._overlay_surface,(0,0))
    L=craft_layout(scene)
    ui_gothic_tabs.hall(scene.screen,L['panel'])
    item=scene.crafting_target
    if not item: return
    p=scene.logic.players[scene.logic.local_player_id]
    recipe_mode=getattr(scene,'_craft_recipe_mode',False)
    advanced=recipe_mode and getattr(scene,'_craft_advanced_mode',False)
    text(scene,'DEMİRCİ ATÖLYESİ',pygame.Rect(L['inner'].x,L['inner'].y,L['inner'].width//2,32),27)
    text(scene,f"{p.gold:,} ALTIN  •  {getattr(p,'craft_dust',0)} ÖZ",pygame.Rect(L['inner'].centerx,L['inner'].y+2,L['inner'].width//2-46,25),18)
    for key,label,active in (('orb_mode','ORB İŞLEMLERİ',not recipe_mode),('recipe_mode','ÖZELLİK EKLE',recipe_mode and not advanced),('advanced_mode','USTA İŞÇİLİK',advanced)):
        plate(scene,L[key],label,'gold' if active else 'steel')
    text(scene,'ÜZERİNDE ÇALIŞILAN EŞYA',pygame.Rect(L['item'].x,L['inner'].y+40,L['item'].width,26),17)
    owned=[it for it in p.inventory if it.get('type')=='orb']
    options=advanced_recipes(item,p) if advanced else recipes(item) if recipe_mode else owned
    page=getattr(scene,'_recipe_page',0) if recipe_mode else scene.orb_inv_page
    page=min(page,max(0,(len(options)-1)//scene.ORB_ROWS_PER_PAGE))
    if recipe_mode: scene._recipe_page=page
    else: scene.orb_inv_page=page
    chosen=getattr(scene,'_selected_recipe',None) if recipe_mode else getattr(scene,'_selected_craft_orb',None)
    if chosen is not None and not any((o.get('id')==chosen.get('id')) if recipe_mode else o is chosen for o in options):
        chosen=None
        if recipe_mode: scene._selected_recipe=None
        else: scene._selected_craft_orb=None
    scene.craft_orb_use_rects=[]
    scene.craft_recipe_rects=[]
    for i,r in enumerate(L['orb_rows']):
        idx=page*scene.ORB_ROWS_PER_PAGE+i
        if idx>=len(options): break
        option=options[idx]
        selected=chosen is not None and (chosen.get('id')==option.get('id') if recipe_mode else chosen is option)
        hovered=r.collidepoint(pygame.mouse.get_pos())
        tint=ui_theme.COLORS['gold'] if selected else ui_theme.COLORS['arcane' if advanced else 'steel']
        ui_theme.draw_inset_frame(scene.screen,r,'panel_frame_small.png',pad=12,tint=tuple(int(v*.45) for v in tint),fill=(36,28,20) if selected else (22,20,26))
        icon_rect=pygame.Rect(r.x+14,r.centery-19,38,38)
        if recipe_mode:
            image=ui_skill_tree.medallion(_operation_icon(option),38,'allocated' if selected else 'locked')
        else:
            image=ImageLoader.get_item_icon(option.get('icon_id',''),(36,36))
        if image: scene.screen.blit(image,icon_rect)
        label=option['name'].split(' (')[0]
        text(scene,label,pygame.Rect(r.x+60,r.y+22,r.width-78,22),17,'gold' if selected or hovered else 'steel')
        if recipe_mode:
            if option.get('operation'):
                detail='Eşyayı söker' if option['id']=='salvage' else f"{option['cost']} işçilik özü"
            else:
                val=bench_value(option,recipe_tier(scene.logic.wave.get('level',1),item))
                detail=('Ön ek' if option['side']=='prefixes' else 'Son ek')+' • '+_fmt_stat_val(option['stat'],val)+' '+ITEM_STAT_LABEL.get(option['stat'],option['stat'])
        else: detail=f"Sende {option.get('stack',1)} adet • Seç ve uygula"
        text(scene,detail,pygame.Rect(r.x+60,r.y+47,r.width-78,18),13,'moss' if selected else 'steel')
        if recipe_mode: scene.craft_recipe_rects.append((option,r))
        else: scene.craft_orb_use_rects.append((idx,r))
    if not options:
        _paragraph(scene,'Uygun işlem yok.' if recipe_mode else 'Çantanda orb yok. Aşağıdaki orb mağazasından alabilirsin.',L['orb_rows'][0].inflate(-28,-12))
    plate(scene,L['orb_prev'],'‹','night',page>0)
    plate(scene,L['orb_next'],'›','night',(page+1)*scene.ORB_ROWS_PER_PAGE<len(options))
    c=ui_theme.draw_inset_frame(scene.screen,L['item'],'panel_frame_small.png',pad=24)
    box=pygame.Rect(c.centerx-36,c.y+2,72,72)
    ui_theme.draw_item_slot(scene.screen,box,item.get('rarity'),True)
    icon=ImageLoader.get_item_icon(item.get('icon_id',''),(56,56))
    if icon: scene.screen.blit(icon,(box.x+8,box.y+8))
    text(scene,item.get('name','Eşya'),pygame.Rect(c.x,c.y+80,c.width,25),21)
    text(scene,f"{item.get('rarity','Normal')} • Eşya seviyesi {item_level(item)}",pygame.Rect(c.x,c.y+108,c.width,20),14,'steel')
    y=c.y+136
    entries=[]
    for stat,val in item.get('itemBase',{}).items():
        entries.append((f"{_fmt_stat_val(stat,val)} {ITEM_STAT_LABEL.get(stat,stat)}",'steel'))
    limit={'Normal':1,'Magic':1,'Rare':2,'Unique':3}.get(item.get('rarity'),0)+(1 if item.get('is_corrupted') else 0)
    for side,title in (('prefixes','ÖN EK'),('suffixes','SON EK')):
        affixes=item.get(side,[])
        entries.append((f"{title}  {len(affixes)}/{limit}",'gold'))
        for aff in affixes:
            tag='◆' if aff.get('fractured') else '✦' if aff.get('crafted') else '•'
            entries.append((f"{tag} T{aff.get('tier',3)}  {_fmt_stat_val(aff['stat'],aff['val'])} {ITEM_STAT_LABEL.get(aff['stat'],aff['stat'])}",'moss' if aff.get('crafted') else 'steel'))
        if not affixes: entries.append(('Boş özellik yuvası','steel'))
    step=max(13,min(23,(L['take_back'].top-12-y)//max(1,len(entries))))
    old_clip=scene.screen.get_clip();scene.screen.set_clip(c)
    for label,key in entries:
        text(scene,label,pygame.Rect(c.x,y,c.width,step),min(16,step),key);y+=step
    scene.screen.set_clip(old_clip)
    preview=L['preview']
    ui_theme.draw_inset_frame(scene.screen,preview,'panel_frame_small.png',pad=12,fill=(20,18,25))
    blocked = recipe_error(p,item,chosen['id'],scene.logic.wave.get('level',1)) if recipe_mode and not advanced and chosen else None
    if advanced and chosen and chosen['id']=='salvage' and any(it is item for it in p.inv_manager.equipped.values()):
        blocked = 'Söküm için önce eşyayı çantaya çıkar.'
    if chosen:
        if recipe_mode and not chosen.get('operation'):
            val=bench_value(chosen,recipe_tier(scene.logic.wave.get('level',1),item))
            desc=f"Kesin sonuç: {_fmt_stat_val(chosen['stat'],val)} {ITEM_STAT_LABEL.get(chosen['stat'],chosen['stat'])}. Önceki tarif özelliği değişir; doğal özellikler korunur."
        else: desc=chosen.get('desc','')
        label='SEÇİLEN İŞLEM • '+chosen['name'].split(' (')[0]
    else:
        label='BİR İŞLEM SEÇ'
        desc='Kartlara tıklayarak sonucu incele. Uygula düğmesine basana kadar eşya değişmez ve kaynak harcanmaz.'
    if blocked: desc = blocked + ' ' + desc
    text(scene,label,preview.inflate(-32,-16),16)
    _paragraph(scene,desc,pygame.Rect(preview.x+16,preview.y+31,preview.width-32,40),14)
    wave=scene.logic.wave.get('level',1)
    cost=chosen.get('cost',0) if advanced and chosen else recipe_cost(wave,item) if recipe_mode else 1
    can_pay=(getattr(p,'craft_dust',0)>=cost) if advanced else p.gold>=cost if recipe_mode else True
    enabled=chosen is not None and can_pay and not blocked and not item.get('is_corrupted')
    label=('SÖK • EŞYAYI PARÇALA' if chosen and chosen.get('id')=='salvage' else f"UYGULA • {cost} ÖZ") if advanced else f"ÖZELLİĞİ EKLE • {cost:,} G" if recipe_mode else 'ORBU UYGULA • 1 ADET'
    if item.get('is_corrupted'): label='MÜHÜRLÜ • İŞLEM YAPILAMAZ'
    elif chosen and not can_pay: label=f"YETERSİZ {'ÖZ' if advanced else 'ALTIN'} • {cost:,} GEREKLİ"
    plate(scene,L['apply'],label,'moss',enabled)
    plate(scene,L['take_back'],'ENVANTERE DÖN','night')
    market_y=L['mkt_rows'][0].y
    text(scene,'ORB MAĞAZASI • Satın alınan orb çantana eklenir',pygame.Rect(L['inner'].x,market_y-26,L['inner'].width-100,24),16,'steel')
    market=scene.logic.orb_market
    for i,r in enumerate(L['mkt_rows']):
        idx=scene.orb_market_page*scene.MARKET_ROWS_PER_PAGE+i
        if idx>=len(market): break
        orb=market[idx]
        ui_theme.draw_inset_frame(scene.screen,r,'panel_frame_small.png',pad=10)
        icon=ImageLoader.get_item_icon(orb.get('icon_id',''),(32,32))
        if icon: scene.screen.blit(icon,(r.x+12,r.y+14))
        text(scene,orb['name'].split(' (')[0],pygame.Rect(r.x+48,r.y+20,r.width-60,20),14,'steel')
        amount=sum(it.get('stack',1) for it in owned if it['orb_id']==orb['orb_id'])
        text(scene,f"Sende {amount} adet",pygame.Rect(r.x+48,r.y+40,r.width-60,18),13,'steel')
        plate(scene,L['mkt_buy'][i],f"SATIN AL • {orb['price']:,} G",'night',p.gold>=orb['price'])
    plate(scene,L['mkt_prev'],'‹','night',scene.orb_market_page>0)
    plate(scene,L['mkt_next'],'›','night',(scene.orb_market_page+1)*scene.MARKET_ROWS_PER_PAGE<len(market))
    plate(scene,L['close'],'X','ember')
    footer=pygame.Rect(L['inner'].x,L['panel'].bottom-28,L['inner'].width,23)
    if scene.craft_error_msg: text(scene,scene.craft_error_msg,footer,15,'gold')
    else: text(scene,'Tek tarif özelliği • Doğal özellikler korunur • 10. dalgadan sonra tarif maliyeti artar',footer,14,'steel')
