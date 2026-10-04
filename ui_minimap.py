"""A fixed arena overview: terrain and markers use the same world coordinates."""
import pygame
import tile_renderer
import ui_theme
from ui_elements import render_fit


def world_point(rect, x, y, world_size):
    return (round(rect.x + max(0, min(world_size, x)) * rect.width / world_size),
            round(rect.y + max(0, min(world_size, y)) * rect.height / world_size))


def draw(scene, player):
    size = 184
    panel = pygame.Rect(scene.width-size-48, scene.height-size-76, size+24, size+48)
    ui_theme.draw_inset_frame(scene.screen, panel, 'panel_frame_small.png', pad=12)
    rect = pygame.Rect(panel.x+12, panel.y+30, size, size)
    game = scene.logic
    biome = game.wave.get('biome', 'forest')
    tmap = game.tilemap
    world_size = game.arena_size
    key = (tmap.seed, biome, world_size, size)
    if getattr(scene, '_minimap_terrain_key', None) != key:
        terrain = pygame.Surface((size, size)).convert()
        terrain.fill(tile_renderer._palette(biome)['base'])
        tiles = tile_renderer._tiles_for(biome)
        scale = size / world_size
        step = tmap.tile_size
        for tx in range(tmap.tiles_across):
            for ty in range(tmap.tiles_across):
                x, y = round(tx*step*scale), round(ty*step*scale)
                w, h = round((tx+1)*step*scale)-x, round((ty+1)*step*scale)-y
                terrain.blit(pygame.transform.smoothscale(tiles[tmap.variant_at(tx,ty)], (w,h)), (x,y))
        for src, wx, wy, diameter in tile_renderer._map_for(tmap, biome)['landmarks']:
            extent = max(2, round(diameter*scale))
            terrain.blit(pygame.transform.smoothscale(src, (extent,extent)), (round(wx*scale),round(wy*scale)))
        pygame.draw.rect(terrain, ui_theme.COLORS['gold'], terrain.get_rect(), 3)
        scene._minimap_terrain = terrain
        scene._minimap_terrain_key = key
    scene.screen.blit(scene._minimap_terrain, rect)
    old_clip = scene.screen.get_clip()
    scene.screen.set_clip(rect)
    viewport = pygame.Rect(*world_point(rect, scene.camera_x, scene.camera_y, world_size),
                           round(scene.width/scene.zoom_level*size/world_size),
                           round(scene.height/scene.zoom_level*size/world_size))
    pygame.draw.rect(scene.screen, (170,185,162), viewport, 1)
    cleanup = getattr(game, 'wave_cleanup', False)
    for enemy in game.enemies:
        if enemy.dead or getattr(enemy, 'is_trap', False) or getattr(enemy, 'is_pillar', False):
            continue
        pos = world_point(rect, enemy.x, enemy.y, world_size)
        boss = enemy.type in ('boss','crystal_dragon','arachne')
        pygame.draw.circle(scene.screen, (215,95,235) if boss else (245,92,65), pos, 4 if boss else 2)
        if cleanup:
            pygame.draw.circle(scene.screen, ui_theme.readable(ui_theme.COLORS['gold']), pos, 5, 1)
    pos = world_point(rect, player.x, player.y, world_size)
    pygame.draw.circle(scene.screen, (20,20,16), pos, 5)
    pygame.draw.circle(scene.screen, ui_theme.readable(ui_theme.COLORS['gold']), pos, 3)
    scene.screen.set_clip(old_clip)
    title = render_fit('ARENA • SON DÜŞMANLAR' if cleanup else 'ARENA HARİTASI', 14,
                       ui_theme.readable(ui_theme.COLORS['gold']), size, bold=True)
    scene.screen.blit(title, (rect.x, panel.y+10))
