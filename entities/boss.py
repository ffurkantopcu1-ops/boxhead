"""Echelion: telegraphed arena duel with deliberate melee openings."""
import math
import pygame
from entities.enemy import Enemy
from entities.projectile import segment_hit_fraction

BOSS_DIFF_MULTS = {"Normal": (1.0,1.0), "Hard": (2.5,1.5),
                   "Very Hard": (6.0,2.0), "Nightmare": (6.0,2.0),
                   "Impossible": (15.0,3.0)}

def get_boss_diff_mults(game):
    return BOSS_DIFF_MULTS.get(game.wave.get("current_diff","Normal"),(1.0,1.0))

class AbyssalLord(Enemy):
    NAME = "Echelion • Küllerin Muhafızı"
    # Windup, recovery, raw damage: phases add choices, never faster warnings.
    MOVES = {"cleave": (1.0,1.8,22), "charge": (1.15,2.1,26),
             "ring": (1.2,2.7,18), "slam": (1.35,2.0,28)}
    LABELS = {"cleave":"Kül Biçişi — arkasına geç",
              "charge":"Kırık Mızrak — yana çekil",
              "ring":"Köz Çemberi — açık koridoru kullan",
              "slam":"Yarık Darbesi — içeri veya dışarı gir"}

    def __init__(self,id,x,y,game,wave_level=10):
        super().__init__(id,x,y,game,type="boss",wave_level=wave_level)
        self.game,self.wave_level=game,wave_level
        self.name=self.NAME
        self.radius=55
        self.boss_dmg_mult=get_boss_diff_mults(game)[1]
        self.max_hp=2600*(1.10**wave_level)*get_boss_diff_mults(game)[0]
        self.hp=self.max_hp
        self.invulnerable=False
        self.state="recover"
        self.timer=1.5
        self.move=None
        self.phase=1
        self.attack_index=0
        self.aim=0.0
        self.telegraph_origin=(x,y)
        self.charge_end=(x,y)
        self.owned_projectiles=[]
        self.attacks_resolved=0

    def attack_damage(self,base):
        from logic.progression import base_life, enemy_damage_growth
        expected_level = max(1, round(self.wave_level*1.4))
        growth = math.sqrt(base_life(expected_level)/100) * enemy_damage_growth(self.wave_level)
        return base*(1+0.04*self.wave_level)*growth*self.boss_dmg_mult

    def apply_difficulty(self,diff_name):
        if not hasattr(self,"boss_dmg_mult"): return
        hp_mult,dmg_mult=BOSS_DIFF_MULTS.get(diff_name,(1.0,1.0))
        ratio=self.hp/self.max_hp if self.max_hp>0 else 1
        self.max_hp=2600*(1.10**self.wave_level)*hp_mult
        self.hp=self.max_hp*ratio
        self.boss_dmg_mult=dmg_mult

    def begin_attack(self,game):
        p=game.players[game.local_player_id]
        rotation=("cleave","charge","cleave","ring") if self.phase==1 else (
                  "cleave","slam","charge","ring","cleave","charge")
        self.move=rotation[self.attack_index%len(rotation)]
        self.attack_index+=1
        self.aim=math.atan2(p.y-self.y,p.x-self.x)
        self.telegraph_origin=(self.x,self.y)
        distance=min(480,max(180,math.hypot(p.x-self.x,p.y-self.y)))
        self.charge_end=(max(80,min(4920,self.x+math.cos(self.aim)*distance)),
                         max(80,min(4920,self.y+math.sin(self.aim)*distance)))
        self.state="windup"
        self.timer=self.MOVES[self.move][0]

    def strike_player(self,p,game,base):
        p.take_damage(self.attack_damage(base), source="enemy_attack", attacker_type="boss")

    def resolve_attack(self,game):
        p=game.players[game.local_player_id]
        x,y=self.telegraph_origin
        distance=math.hypot(p.x-x,p.y-y)
        if self.move=="cleave":
            diff=abs((math.atan2(p.y-y,p.x-x)-self.aim+math.pi)%(2*math.pi)-math.pi)
            # Include the player's full footprint at the outer/side edges.
            margin=math.asin(min(1,p.radius/max(distance,1)))
            if distance<=230+p.radius and diff<=math.pi/3+margin:
                self.strike_player(p,game,22)
        elif self.move=="charge":
            # Move over 0.55s; collision follows the entire swept path.
            self.state="charge"
            self.timer=0.55
            self.charge_hit=False
            self.attacks_resolved+=1
            return
        elif self.move=="slam":
            if 130-p.radius<=distance<=330+p.radius:
                self.strike_player(p,game,28)
        elif self.move=="ring":
            # Locked 120-degree opening faces the player; safe melee interior.
            for i in range(12):
                angle=self.aim+i*math.pi/6
                diff=abs((angle-self.aim+math.pi)%(2*math.pi)-math.pi)
                if diff<=math.pi/3+1e-9: continue
                shot=game.projectile_pool.spawn(x+math.cos(angle)*150,y+math.sin(angle)*150,
                       math.cos(angle)*3,math.sin(angle)*3,
                       damage=self.attack_damage(18),radius=7,color=(245,155,65),lifetime=120)
                if shot:
                    shot.boss_owner_id=self.id
                    self.owned_projectiles.append(shot)
        self.attacks_resolved+=1
        game.add_event("shockwave",x,y,radius=230 if self.move=="cleave" else 330,
                       color=(240,145,65),timer=.25)
        self.state="recover"
        self.timer=self.MOVES[self.move][1]

    def update(self,dt,game):
        if self.dead:
            self.clear_projectiles()
            return
        self.effect_manager.update(dt,self,game)
        if self.dead:
            self.clear_projectiles()
            return
        self.phase=1 if self.hp/self.max_hp>.65 else (2 if self.hp/self.max_hp>.30 else 3)
        self.flash_timer=max(0,getattr(self,"flash_timer",0)-max(0,dt))
        remaining=max(0,dt)
        # Consume exact state boundaries, so warnings and cadence ignore FPS.
        for _ in range(16):
            if remaining<=1e-9: break
            step=min(remaining,self.timer)
            if self.state=="charge":
                px,py=self.x,self.y
                frac=step/max(self.timer,1e-9)
                self.x+=(self.charge_end[0]-self.x)*frac
                self.y+=(self.charge_end[1]-self.y)*frac
                p=game.players[game.local_player_id]
                if not self.charge_hit and segment_hit_fraction(px,py,self.x,self.y,p.x,p.y,p.radius+45) is not None:
                    self.strike_player(p,game,26)
                    self.charge_hit=True
            elif self.state=="recover" and self.timer>1.0:
                p=game.players[game.local_player_id]
                distance=math.hypot(p.x-self.x,p.y-self.y)
                if distance>160 and not getattr(self,"is_stunned",False):
                    travel=min(distance-160,80*getattr(self,"speed_mod",1)*step)
                    self.x+=(p.x-self.x)/distance*travel
                    self.y+=(p.y-self.y)/distance*travel
            self.timer=max(0,self.timer-step)
            remaining-=step
            if self.timer<=1e-9:
                if self.state=="recover": self.begin_attack(game)
                elif self.state=="windup": self.resolve_attack(game)
                else:
                    self.state="recover"
                    self.timer=self.MOVES["charge"][1]
        self.x=max(80,min(4920,self.x))
        self.y=max(80,min(4920,self.y))
        self.owned_projectiles=[s for s in self.owned_projectiles if s.active and getattr(s,"boss_owner_id",None)==self.id]

    def clear_projectiles(self):
        for shot in self.owned_projectiles:
            if getattr(shot,"boss_owner_id",None)==self.id: shot.active=False
        self.owned_projectiles.clear()

    def take_damage(self,amount,game,is_crit=False,is_dot=False,from_player=False,is_reflected=False,is_secondary=False,damage_type='physical'):
        # Always attackable; recovery gives a deliberate melee opening.
        result=super().take_damage(amount,game,is_crit,is_dot,from_player,is_reflected=is_reflected,is_secondary=is_secondary,damage_type=damage_type)
        if self.dead: self.clear_projectiles()
        return result

    def draw(self,screen,camera_x,camera_y):
        x,y=int(self.x-camera_x),int(self.y-camera_y)
        if self.state=="windup":
            ox,oy=self.telegraph_origin
            cx,cy=int(ox-camera_x),int(oy-camera_y)
            color=(245,155,65)
            if self.move=="cleave":
                pts=[(cx,cy)]+[(cx+math.cos(self.aim-math.pi/3+i*math.pi/36)*230,
                               cy+math.sin(self.aim-math.pi/3+i*math.pi/36)*230) for i in range(25)]
                pygame.draw.lines(screen,color,True,pts,3)
            elif self.move=="charge":
                ex,ey=self.charge_end[0]-camera_x,self.charge_end[1]-camera_y
                nx,ny=math.sin(self.aim)*45,-math.cos(self.aim)*45
                pygame.draw.lines(screen,color,True,[(cx+nx,cy+ny),(ex+nx,ey+ny),
                                                     (ex-nx,ey-ny),(cx-nx,cy-ny)],3)
            elif self.move=="slam":
                pygame.draw.circle(screen,color,(cx,cy),130,3)
                pygame.draw.circle(screen,color,(cx,cy),330,3)
            else:
                for i in range(41):
                    a=self.aim+math.pi/3+i*(4*math.pi/3)/40
                    b=a+(4*math.pi/3)/40
                    pygame.draw.line(screen,color,(cx+math.cos(a)*150,cy+math.sin(a)*150),
                                      (cx+math.cos(b)*150,cy+math.sin(b)*150),4)
                for a in (self.aim-math.pi/3,self.aim+math.pi/3):
                    pygame.draw.line(screen,(120,220,150),(cx+math.cos(a)*110,cy+math.sin(a)*110),
                                     (cx+math.cos(a)*380,cy+math.sin(a)*380),3)
        # Armored sentinel silhouette; no spinning body during a locked attack.
        outline=(195,145,80) if self.state=="recover" else (240,165,80)
        body=[(x,y-55),(x+44,y-30),(x+55,y+12),(x+28,y+48),
              (x,y+55),(x-28,y+48),(x-55,y+12),(x-44,y-30)]
        pygame.draw.polygon(screen,(135,90,65) if getattr(self,"flash_timer",0)>0 else (38,31,35),body)
        pygame.draw.polygon(screen,outline,body,3)
        for sign in (-1,1):
            pygame.draw.polygon(screen,outline,[(x+sign*22,y-38),(x+sign*42,y-70),(x+sign*37,y-25)])
        pygame.draw.polygon(screen,(95,68,55),[(x,y-30),(x+25,y),(x,y+32),(x-25,y)])
        pygame.draw.line(screen,(250,210,135),(x-15,y-13),(x+15,y-13),4)
        pygame.draw.line(screen,outline,(x,y-6),(x,y+20),3)
        # Spear points along the warning direction.
        ax,ay=math.cos(self.aim),math.sin(self.aim)
        pygame.draw.line(screen,outline,(x+ax*40,y+ay*40),(x+ax*85,y+ay*85),5)
        tip=(x+ax*99,y+ay*99)
        pygame.draw.polygon(screen,(250,210,135),[tip,(x+ax*78-ay*8,y+ay*78+ax*8),
                                                     (x+ax*78+ay*8,y+ay*78-ax*8)])
        import ui_theme
        from ui_elements import render_fit
        label=self.LABELS.get(self.move,"Muhafız hazırlanıyor") if self.state=="windup" else (
              "AÇIK — karşılık ver" if self.state=="recover" else "Kırık Mızrak")
        txt=render_fit(label,20,ui_theme.TEXT_COL,420,bold=True)
        screen.blit(txt,(x-txt.get_width()//2,y+self.radius+20))
