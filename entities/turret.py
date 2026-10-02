"""Deployable sentry: live stats, deliberate targeting and active support."""
import math
import pygame

class Turret:
    LIFETIME=24.0
    def __init__(self,id,x,y,hp=150,dmg_mult=1.0,fire_rate=1.0,local_stats=None,owner=None):
        self.id,self.x,self.y=id,x,y
        self.owner=owner
        self.local_stats=local_stats or {}
        self.max_hp=max(1,hp)
        self.hp=self.max_hp
        self.dmg_mult,self.fire_rate=dmg_mult,fire_rate
        self.radius=22
        self.armor=20
        self.range=500
        self.dead=False
        self.color=(90,170,165)
        self.fire_timer=0.0
        self.age=0.0
        self.boot_remaining=.5
        self.target=None
        self.angle=0.0
        self.shot_count=0
        self.contact_timers={}
        self.last_damage_age=-10
        self.invulnerable_timer=0 # Legacy reader compatibility.

    def sync_stats(self):
        if not self.owner: return
        stats=self.owner.stats
        maximum=max(1,stats.get("turretMaxHp",150)*getattr(self.owner,"turret_hp_penalty",1))
        if maximum != self.max_hp:
            self.hp=min(maximum,self.hp*maximum/self.max_hp)
            self.max_hp=maximum
        self.dmg_mult=max(.1,min(4,stats.get("turretDmg",1)))
        self.fire_rate=max(.1,min(3,stats.get("turretRate",1)))
        # Range bonuses are pixels; +25 means 525, never 13,000.
        self.range=max(200,min(800,500+stats.get("turretRange",0)))
        self.armor=max(0,min(60,20+stats.get("armor",0)*.25))

    def owner_distance(self):
        return math.hypot(self.owner.x-self.x,self.owner.y-self.y) if self.owner else 0

    def choose_target(self,game):
        def valid(e):
            return e and not e.dead and (not getattr(e,"is_trap",False) or getattr(e,"is_pillar",False)) and math.hypot(e.x-self.x,e.y-self.y)<=self.range+e.radius
        priority=getattr(self.owner,"turret_focus_target",None)
        if getattr(self.owner,"turret_command_active",0)>0 and valid(priority):
            self.target=priority
        elif not valid(self.target):
            choices=[e for e in game.iter_enemies_near(self.x,self.y,self.range+120) if valid(e)]
            self.target=min(choices,key=lambda e:((e.x-self.x)**2+(e.y-self.y)**2,e.id),default=None)
        return self.target

    def take_damage(self,amount,game=None):
        if self.dead or amount<=0: return 0
        damage=min(self.hp,amount*100/(100+self.armor))
        self.hp=max(0,self.hp-damage)
        self.last_damage_age=self.age
        if self.hp<=0: self.dead=True
        return damage

    def update(self,dt,game):
        if self.dead: return
        dt=max(0,dt)
        self.sync_stats()
        available=min(dt,max(0,self.LIFETIME-self.age))
        self.age+=dt
        boot=min(available,self.boot_remaining)
        self.boot_remaining=max(0,self.boot_remaining-available)
        firing_dt=max(0,available-boot)
        # Every touching attacker has its own half-second pressure budget.
        live_ids=set()
        for e in game.iter_enemies_near(self.x,self.y,160):
            if e.dead or getattr(e,"is_trap",False): continue
            if math.hypot(e.x-self.x,e.y-self.y)<self.radius+e.radius:
                live_ids.add(e.id)
                timer=self.contact_timers.get(e.id,.5)-available
                while timer<=1e-9 and not self.dead:
                    self.take_damage(e.dmg*.5,game)
                    timer+=.5
                self.contact_timers[e.id]=timer
        self.contact_timers={nid:t for nid,t in self.contact_timers.items() if nid in live_ids}
        if self.dead: return
        architect=getattr(self.owner,"evolution_passive","")=="heal_turret"
        if architect and self.owner_distance()<=220 and self.age-self.last_damage_age>2:
            self.hp=min(self.max_hp,self.hp+self.max_hp*.025*available)
        boosted=getattr(self.owner,"turret_command_active",0)>0
        cooldown=max(.15,.55/(self.fire_rate*(1.35 if boosted else 1)))
        self.choose_target(game)
        # A sentry left behind cannot farm the map while its owner runs away.
        if self.owner_distance()>750 or not self.target or getattr(self.owner,"hp",1)<=0:
            self.fire_timer=min(cooldown,self.fire_timer+firing_dt)
        else:
            self.angle=math.atan2(self.target.y-self.y,self.target.x-self.x)
            self.fire_timer=min(cooldown*4,self.fire_timer+firing_dt)
            while self.fire_timer>=cooldown-1e-9 and not self.dead:
                self.fire_timer=max(0,self.fire_timer-cooldown)
                self.shoot(game)
        if self.age>=self.LIFETIME:
            self.dead=True
            game.add_event("fx",self.x,self.y,tex="smoke",size=48,color=(125,140,145),timer=.35)

    def shoot(self,game):
        if self.dead or self.boot_remaining>0 or not self.choose_target(game): return False
        stats=getattr(self.owner,"stats",{})
        fleet=sum(not t.dead and t.owner is self.owner and t.owner_distance()<=750 for t in game.turrets)
        network_budget=1/(1+.20*max(0,fleet-2))
        # Shared damage uses half the global bonus. Weapon flats contribute
        # modestly; turret damage/rate remain the main investment channels.
        power=14+max(0,getattr(self.owner,"level",1)-1)*.7
        power+=.25*max(0,stats.get("physDmg",0)+stats.get("physDmgFlat",0))
        power+=.10*max(0,stats.get("fireDamage",0)+stats.get("frostDamage",0))
        damage=power*self.dmg_mult*(1+.5*(stats.get("dmgMult",1)-1))*network_budget
        if self.owner_distance()<=220: damage*=1.20
        count=max(1,min(4,int(stats.get("projectileCount",1))))
        damage/=1+.3*(count-1)
        pierce=max(0,min(4,int(stats.get("pierce",0))))
        bounce=max(0,min(2,int(stats.get("bounce",0))))
        from entities.projectile import Projectile
        self.angle=math.atan2(self.target.y-self.y,self.target.x-self.x)
        # Barrels converge on the target; extra barrels share a damage budget.
        for i in range(count):
            offset=(i-(count-1)/2)*6
            sx=self.x-math.sin(self.angle)*offset
            sy=self.y+math.cos(self.angle)*offset
            a=math.atan2(self.target.y-sy,self.target.x-sx)
            shot=Projectile(game.entity_id_counter,sx,sy,math.cos(a)*10,math.sin(a)*10,
                            max(0,damage),bounce=bounce,pierce=pierce,lifetime=90)
            shot.is_turret_proj=True
            shot.color=(115,215,205)
            game.projectiles.append(shot)
            game.entity_id_counter+=1
        self.shot_count+=1
        # Electrician gets a turret-specific proc, never player on-hit recursion.
        if getattr(self.owner,"evolution_passive","")=="chain_lightning" and self.shot_count%3==0:
            candidates=[e for e in game.iter_enemies_near(self.target.x,self.target.y,180)
                        if not e.dead and e is not self.target and not getattr(e,"is_trap",False)
                        and math.hypot(e.x-self.target.x,e.y-self.target.y)<=180]
            if candidates:
                other=min(candidates,key=lambda e:(e.x-self.target.x)**2+(e.y-self.target.y)**2)
                other.take_damage(damage*.35,game,from_player=True,is_secondary=True)
                game.add_event("lightning",self.target.x,self.target.y,tx=other.x,ty=other.y,timer=.2)
        return True

    def draw(self,screen,camera_x,camera_y):
        x,y=int(self.x-camera_x),int(self.y-camera_y)
        boosted=getattr(self.owner,"turret_command_active",0)>0
        color=(240,185,85) if boosted else (115,195,180)
        pygame.draw.polygon(screen,(32,40,42),[(x-24,y),(x-13,y-22),(x+13,y-22),(x+24,y),(x+13,y+22),(x-13,y+22)])
        pygame.draw.polygon(screen,color,[(x-24,y),(x-13,y-22),(x+13,y-22),(x+24,y),(x+13,y+22),(x-13,y+22)],2)
        pygame.draw.circle(screen,(55,70,70),(x,y),13)
        for offset in (-5,5):
            sx=x-math.sin(self.angle)*offset
            sy=y+math.cos(self.angle)*offset
            pygame.draw.line(screen,color,(sx,sy),(sx+math.cos(self.angle)*30,sy+math.sin(self.angle)*30),5)
        if self.boot_remaining>0:
            pygame.draw.arc(screen,color,(x-30,y-30,60,60),0,math.tau*(1-self.boot_remaining/.5),3)
        import ui_theme
        ui_theme.draw_world_bar(screen,pygame.Rect(x-24,y-34,48,5),self.hp/max(1,self.max_hp),"moss")
        ui_theme.draw_world_bar(screen,pygame.Rect(x-24,y+31,48,3),max(0,1-self.age/self.LIFETIME),"gold")
