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
    w, h = min(1180, scene.width - 72), min(680, scene.height - 76)
    panel = pygame.Rect((scene.width-w)//2, (scene.height-h)//2, w, h)
    inner = panel.inflate(-72, -68)
    side = int(inner.width * .29)
    mid = inner.width - 2 * side - 32
    lx, rx = inner.x, inner.right - side
    top, bottom = inner.y + 54, inner.bottom - 90
    rh = max(32, (bottom-top)//scene.ORB_ROWS_PER_PAGE)
    mh = max(46, (bottom-top)//scene.MARKET_ROWS_PER_PAGE)
    orbs = [pygame.Rect(lx, top+i*rh, side, rh-4) for i in range(scene.ORB_ROWS_PER_PAGE)]
    markets = [pygame.Rect(rx, top+i*mh, side, mh-5) for i in range(scene.MARKET_ROWS_PER_PAGE)]
    item = pygame.Rect(lx+side+16, top, mid, bottom-top)
    return dict(orb_mode=pygame.Rect(lx,inner.y+28,side//3-4,23), recipe_mode=pygame.Rect(lx+side//3+2,inner.y+28,side//3-4,23), advanced_mode=pygame.Rect(lx+2*side//3+4,inner.y+28,side//3-4,23), panel=panel, inner=inner, item=item,
                close=pygame.Rect(inner.right-40, inner.y-4, 40, 36),
                orb_rows=orbs, orb_use=[pygame.Rect(r.right-72,r.y+3,64,r.height-6) for r in orbs],
                mkt_rows=markets, mkt_buy=[pygame.Rect(r.right-70,r.y+8,62,r.height-16) for r in markets],
                take_back=pygame.Rect(item.x,bottom+10,mid,34),
                apply=pygame.Rect(item.x,bottom+50,mid,34),
                orb_prev=pygame.Rect(lx,bottom+12,side//2-4,32),
                orb_next=pygame.Rect(lx+side//2+4,bottom+12,side//2-4,32),
                mkt_prev=pygame.Rect(rx,bottom+12,side//2-4,32),
                mkt_next=pygame.Rect(rx+side//2+4,bottom+12,side//2-4,32))


def draw_craft(scene):
    from scenes.game_scene import ITEM_STAT_LABEL, _fmt_stat_val
    scene._overlay_surface.fill((0,0,0,225))
    scene.screen.blit(scene._overlay_surface,(0,0))
    L = craft_layout(scene)
    import ui_gothic_tabs
    ui_gothic_tabs.hall(scene.screen,L['panel'])
    item = scene.crafting_target
    if not item:
        return
    p = scene.logic.players[scene.logic.local_player_id]
    text(scene,'ATÖLYE • Eşya → İşlem → Uygula',pygame.Rect(L['inner'].x,L['inner'].y,L['inner'].width-60,30),24)
    from logic.crafting import recipes, recipe_cost, recipe_tier, advanced_recipes
    from logic.affix_rules import bench_value, item_level
    recipe_mode = getattr(scene,'_craft_recipe_mode',False)
    plate(scene,L['orb_mode'],'ORBLAR','night')
    plate(scene,L['recipe_mode'],'TARİFLER','gold')
    plate(scene,L['advanced_mode'],'İŞÇİLİK','arcane')
    owned = [it for it in p.inventory if it.get('type') == 'orb']
    options = (advanced_recipes(item,p) if getattr(scene,'_craft_advanced_mode',False) else recipes(item)) if recipe_mode else owned
    page = getattr(scene,'_recipe_page',0) if recipe_mode else scene.orb_inv_page
    chosen = getattr(scene,'_selected_recipe',None) if recipe_mode else getattr(scene,'_selected_craft_orb',None)
    if not recipe_mode and chosen is not None and not any(it is chosen for it in owned):
        chosen = scene._selected_craft_orb = None
    scene.craft_orb_use_rects = []
    scene.craft_recipe_rects = []
    for i,r in enumerate(L['orb_rows']):
        idx = page*scene.ORB_ROWS_PER_PAGE+i
        if idx >= len(options): break
        option=options[idx]; btn=L['orb_use'][i]
        selected=chosen is not None and ((chosen.get('id')==option.get('id')) if recipe_mode else chosen is option)
        ui_theme.draw_plate(scene.screen,r,'hover' if selected else 'normal')
        label=(option['name']+' · '+('İŞ' if option.get('operation') else ('P' if option['side']=='prefixes' else 'S'))) if recipe_mode else f"{option['name'].split(' (')[0]} ×{option.get('stack',1)}"
        text(scene,label,pygame.Rect(r.x+16,r.y+8,btn.left-r.x-26,24),16,'steel')
        plate(scene,btn,'SEÇ','moss')
        if recipe_mode: scene.craft_recipe_rects.append((option,btn))
        else: scene.craft_orb_use_rects.append((idx,btn))
    if not options:
        text(scene,'Orb yok. Sağdan satın alabilirsin.',L['orb_rows'][0],17,'steel')
    plate(scene,L['orb_prev'],'GERİ','night',page>0)
    plate(scene,L['orb_next'],'İLERİ','night',(page+1)*scene.ORB_ROWS_PER_PAGE<len(options))
    c=ui_theme.draw_inset_frame(scene.screen,L['item'],'panel_frame_small.png',pad=26)
    icon_box=pygame.Rect(c.centerx-30,c.y,60,60)
    ui_theme.draw_item_slot(scene.screen,icon_box,item.get('rarity'),True)
    icon=ImageLoader.get_item_icon(item.get('icon_id',''),(48,48))
    if icon: scene.screen.blit(icon,(icon_box.x+6,icon_box.y+6))
    text(scene,item['name'],pygame.Rect(c.x,c.y+65,c.width,24),20)
    limits={'Normal':0,'Magic':1,'Rare':2,'Unique':3}
    limit=limits.get(item.get('rarity'),0)+(1 if item.get('is_corrupted') else 0)
    text(scene,f"Prefix {len(item.get('prefixes',[]))}/{limit} • Suffix {len(item.get('suffixes',[]))}/{limit}",pygame.Rect(c.x,c.y+91,c.width,24),16,'steel')
    lines=[]
    for stat,val in item.get('itemBase',{}).items():
        lines.append((f"{ITEM_STAT_LABEL.get(stat,stat)}: {_fmt_stat_val(stat,val)}",'steel'))
    for group,title in (('prefixes','P'),('suffixes','S')):
        for a in item.get(group,[]):
            lines.append((f"{'Sabit' if a.get('fractured') else ('Tarif' if a.get('crafted') else title)} · T{a.get('tier',3)}  {_fmt_stat_val(a['stat'],a['val'])} {ITEM_STAT_LABEL.get(a['stat'],a['stat'])}",'moss'))
    desc_top=c.bottom-76
    y=c.y+117
    prev=scene.screen.get_clip();scene.screen.set_clip(pygame.Rect(c.x,y,c.width,max(0,desc_top-y-8)))
    step=max(16,min(22,(desc_top-y-8)//max(1,len(lines))))
    for label,key in lines:
        text(scene,label,pygame.Rect(c.x,y,c.width,step),min(17,step),key);y+=step
    scene.screen.set_clip(prev)
    if recipe_mode:
        if chosen:
            tier=recipe_tier(scene.logic.wave.get('level',1),item)
            value=bench_value(chosen,tier) if not chosen.get('operation') else 0
            desc=chosen['desc'] if chosen.get('operation') else f"Kesin sonuç: {_fmt_stat_val(chosen['stat'],value)} {ITEM_STAT_LABEL.get(chosen['stat'],chosen['stat'])}. Tek tarif özelliğini değiştirir; doğal özellikler korunur."
        else: desc='Söküm, hedefli çıkarma, geliştirme, sabitleme veya aktarım seç. Seçmek kaynak harcamaz.' if getattr(scene,'_craft_advanced_mode',False) else 'Bir özellik seç. Eşya başına tek tarif özelliği; doğal özellikler korunur.'
    else:
        desc=chosen.get('desc','') if chosen else 'Soldan bir işlem seç. Seçmek orbu tüketmez.' 
    if item.get('is_corrupted'): desc='Mühürlü eşya: değiştirilemez.'
    font=scene.font_desc
    for j,line in enumerate(wrap_text(font,desc,c.width)[:3]):
        scene.screen.blit(font.render(line,True,ui_theme.TEXT_COL),(c.x,desc_top+j*20))
    plate(scene,L['take_back'],'ÇANTAYA DÖN','night')
    cost_label = ('SÖK • EŞYAYI PARÇALA' if chosen['id']=='salvage' else f"UYGULA • {chosen['cost']} ÖZ") if recipe_mode and chosen and chosen.get('operation') else (f"UYGULA • {recipe_cost(scene.logic.wave.get('level',1),item)} G" if recipe_mode else 'UYGULA • 1 ORB')
    text(scene,f"Eşya Sv. {item_level(item)} • İşçilik özü: {getattr(p,'craft_dust',0)}",pygame.Rect(L['inner'].right-360,L['inner'].y+2,310,22),16,'moss')
    plate(scene,L['apply'],cost_label,'moss',chosen is not None and not item.get('is_corrupted'))
    market=scene.logic.orb_market
    for i,r in enumerate(L['mkt_rows']):
        idx=scene.orb_market_page*scene.MARKET_ROWS_PER_PAGE+i
        if idx>=len(market): break
        orb=market[idx];btn=L['mkt_buy'][i]
        ui_theme.draw_plate(scene.screen,r,'normal')
        text(scene,orb['name'].split(' (')[0],pygame.Rect(r.x+16,r.y+8,btn.left-r.x-22,20),16,'steel')
        amount=sum(it.get('stack',1) for it in owned if it['orb_id']==orb['orb_id'])
        text(scene,f"{orb['price']} G • Sende {amount}",pygame.Rect(r.x+16,r.y+30,btn.left-r.x-22,20),15)
        plate(scene,btn,'AL','moss',p.gold>=orb['price'])
    plate(scene,L['mkt_prev'],'GERİ','night',scene.orb_market_page>0)
    plate(scene,L['mkt_next'],'İLERİ','night',(scene.orb_market_page+1)*scene.MARKET_ROWS_PER_PAGE<len(market))
    text(scene,f"ALTIN: {p.gold:,}",pygame.Rect(L['mkt_prev'].x,L['apply'].y,L['mkt_rows'][0].width,24),18)
    plate(scene,L['close'],'X','ember')
    if scene.craft_error_msg:
        text(scene,scene.craft_error_msg,pygame.Rect(L['panel'].x+40,L['panel'].bottom-27,L['panel'].width-80,24),16,'blood')
