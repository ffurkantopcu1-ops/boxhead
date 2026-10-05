"""Eight passive clusters per class; small investments support a distinct notable.

Tuple: key, Turkish theme, four supporting minor stats, notable stats.
All effects use live combat stats; no class-specific active skills are granted.
"""
CLUSTERS = {
 'warrior': [
  ('reach','Geniş Savuruş',[{'meleeRangeFlat':10},{'attack_speed_bonus':.04},{'physDmgMult':.04},{'max_hp':8}],{'meleeRangeFlat':35,'physDmgMult':.08}),
  ('tempo','Cephe Akışı',[{'attack_speed_bonus':.04},{'armor':4},{'physDmgFlat':2},{'speed':.15}],{'attack_speed_bonus':.12,'meleeRangeFlat':20}),
  ('guard','Demir Muhafız',[{'armor':5},{'max_hp':10},{'regen':.3},{'max_hp_pct':3}],{'armor':16,'max_hp_pct':8}),
  ('impact','Ezici Darbe',[{'physDmgFlat':2},{'physDmgMult':.04},{'armorPenFlat':2},{'critChance':.015}],{'physDmgFlat':8,'armorPenFlat':8}),
  ('sustain','Savaşın İçinde',[{'lifesteal':.01},{'regen':.3},{'max_hp':10},{'attack_speed_bonus':.03}],{'lifesteal':.04,'combatRegen':1}),
  ('duelist','Düello',[{'critChance':.02},{'critDmg':.07},{'bossDmgMult':.04},{'armorPenFlat':2}],{'critChance':.07,'bossDmgMult':.15}),
  ('element','Elementli Çelik',[{'fireDmgFlat':2},{'frostDmgFlat':2},{'elementDmgMult':.04},{'aoe_bonus':.05}],{'fireDmgFlat':7,'frostDmgFlat':7,'aoe_bonus':.12}),
  ('stride','Öncü',[{'speed':.15},{'meleeRangeFlat':10},{'dodgeChance':.015},{'max_hp_pct':3}],{'speed':.4,'meleeRangeFlat':25,'dodgeChance':.04})],
 'sniper': [
  ('chain','Sekme Atölyesi',[{'physDmgMult':.04},{'bullet_speed':.4},{'critChance':.02},{'speed':.15}],{'bounce':1,'attack_speed_bonus':.06}),
  ('pierce','Delici Hat',[{'physDmgFlat':2},{'armorPenFlat':2},{'attack_speed_bonus':.04},{'max_hp':8}],{'pierce':2,'physDmgMult':.06}),
  ('mobility','Gezgin Avcı',[{'speed':.15},{'dodgeChance':.02},{'max_hp':10},{'regen':.3}],{'speed':.4,'dodgeChance':.06}),
  ('volley','Çapraz Ateş',[{'attack_speed_bonus':.04},{'bullet_speed':.4},{'physDmgMult':.04},{'critChance':.015}],{'projectileCount':1,'attack_speed_bonus':.04}),
  ('guard','Avcı Sığınağı',[{'max_hp':10},{'armor':4},{'regen':.3},{'lifesteal':.01}],{'max_hp_pct':10,'lifesteal':.03}),
  ('crit','Kusursuz Nişan',[{'critChance':.02},{'critDmg':.07},{'armorPenFlat':2},{'physDmgMult':.04}],{'critChance':.08,'critDmg':.2}),
  ('element','Prizmatik Mermi',[{'fireDmgFlat':2},{'frostDmgFlat':2},{'elementDmgMult':.04},{'dotDmgMult':.04}],{'fireDmgFlat':6,'frostDmgFlat':6,'bounce':1}),
  ('execution','Tek Hedef',[{'bossDmgMult':.05},{'armorPenFlat':2},{'physDmgFlat':2},{'critDmg':.06}],{'bossDmgMult':.2,'armorPenFlat':8})],
 'engineer': [
  ('pierce','Delici Namlu',[{'turretDmg':.04},{'turretRange':15},{'turretRate':.04},{'armor':4}],{'pierce':1,'turretRate':.08}),
  ('flame','Alev Cephesi',[{'fireDmgFlat':2},{'aoe_bonus':.05},{'attack_speed_bonus':.04},{'speed':.15}],{'aoe_bonus':.2,'fireDmgFlat':5}),
  ('guard','Tahkimat',[{'turretMaxHp':15},{'armor':5},{'max_hp':10},{'regen':.3}],{'turretMaxHp':60,'armor':12}),
  ('volley','Çoklu Namlu',[{'turretRate':.04},{'physDmgMult':.04},{'turretRange':15},{'turretDmg':.04}],{'projectileCount':1,'turretRange':25}),
  ('command','Saha Komutası',[{'cooldownReduction':.025},{'speed':.15},{'turretRange':20},{'max_hp':8}],{'turretCharges':1,'turretRange':50}),
  ('fleet','Taret Filosu',[{'turretDmg':.05},{'turretMaxHp':15},{'turretRate':.04},{'regen':.3}],{'turretLimit':1,'turretDmg':.1}),
  ('chain','Sekme Devresi',[{'turretDmg':.04},{'critChance':.015},{'turretRange':20},{'bullet_speed':.4}],{'bounce':1,'turretDmg':.1}),
  ('pilot','Savaş Pilotu',[{'physDmgFlat':2},{'fireDmgMult':.04},{'attack_speed_bonus':.04},{'lifesteal':.01}],{'fireDmgFlat':6,'attack_speed_bonus':.1})],
 'beastmaster': [
  ('pack','Avcı Sürüsü',[{'minionDamage':.04},{'minionRate':.04},{'minionRange':.04},{'max_hp':8}],{'minionCount':1,'minionRate':.06}),
  ('reach','Uzanan Pençe',[{'minionRange':.08},{'minionPhysDmgFlat':1},{'meleeRangeFlat':10},{'speed':.15}],{'minionRange':.3,'minionDamage':.1}),
  ('guard','Sürü Sığınağı',[{'armor':4},{'minionRange':.06},{'max_hp':10},{'regen':.3}],{'armor':12,'minionRange':.2}),
  ('volley','Diken Yağmuru',[{'minionRate':.04},{'minionDamage':.04},{'minionCrit':.015},{'minionRange':.06}],{'minionProjectileCount':1,'minionPierce':1}),
  ('bond','Yaban Bağı',[{'max_hp':10},{'regen':.3},{'speed':.15},{'minionRange':.06}],{'max_hp_pct':10,'regen':1}),
  ('fang','Alfa Dişleri',[{'minionCrit':.02},{'minionPhysDmgFlat':1},{'minionDamage':.05},{'minionRate':.04}],{'minionPhysDmgFlat':5,'minionCrit':.08}),
  ('element','Element Sürüsü',[{'minionFireDmgFlat':1},{'minionFrostDmgFlat':1},{'minionDamage':.04},{'aoe_bonus':.04}],{'minionFireDmgFlat':4,'minionFrostDmgFlat':4,'minionBounce':1}),
  ('whip','Sürü Öncüsü',[{'meleeRangeFlat':10},{'physDmgFlat':2},{'attack_speed_bonus':.04},{'armor':4}],{'meleeRangeFlat':30,'minionRate':.12})],
 'bomber': [
  ('blast','Patlama Çemberi',[{'aoe_bonus':.05},{'physDmgFlat':2},{'fireDmgMult':.04},{'max_hp':8}],{'aoe_bonus':.25,'physDmgFlat':4}),
  ('tempo','Seri Döşeme',[{'attack_speed_bonus':.04},{'speed':.15},{'dmgMult':.035},{'armor':4}],{'attack_speed_bonus':.15,'aoe_bonus':.1}),
  ('guard','Patlama Siperi',[{'armor':5},{'max_hp':10},{'regen':.3},{'max_hp_pct':3}],{'armor':15,'max_hp_pct':8}),
  ('volley','Mayın Tarlası',[{'aoe_bonus':.04},{'attack_speed_bonus':.04},{'physDmgMult':.04},{'speed':.15}],{'projectileCount':1,'aoe_bonus':.1}),
  ('fire','Közler',[{'fireDmgFlat':2},{'fireDmgMult':.04},{'dotDmgMult':.04},{'regen':.3}],{'fireDmgFlat':8,'dotDmgMult':.12}),
  ('siege','Kuşatma',[{'bossDmgMult':.05},{'physDmgFlat':2},{'critChance':.02},{'armorPenFlat':2}],{'bossDmgMult':.2,'physDmgMult':.12}),
  ('crit','Tetik Mekanizması',[{'critChance':.02},{'critDmg':.07},{'attack_speed_bonus':.04},{'dmgMult':.035}],{'critChance':.08,'critDmg':.2}),
  ('mobility','Kaçış Rotası',[{'speed':.15},{'dodgeChance':.02},{'max_hp':10},{'cooldownReduction':.025}],{'speed':.4,'dodgeChance':.06})],
 'alchemist': [
  ('spread','Yayılan Karışım',[{'aoe_bonus':.05},{'poisonDps':1},{'dotDmgMult':.04},{'max_hp':8}],{'aoe_bonus':.25,'poisonDps':3}),
  ('tempo','Hızlı Damıtma',[{'attack_speed_bonus':.04},{'speed':.15},{'poisonDps':1},{'maxEnergyShield':8}],{'attack_speed_bonus':.15,'aoe_bonus':.1}),
  ('guard','Kimyasal Siper',[{'maxEnergyShield':10},{'esRegen':1},{'max_hp':10},{'regen':.3}],{'maxEnergyShield':35,'esRegen':4}),
  ('volley','Çifte Şişe',[{'aoe_bonus':.04},{'attack_speed_bonus':.04},{'dotDmgMult':.04},{'poisonDps':1}],{'projectileCount':1,'aoe_bonus':.1}),
  ('frost','Soğuk Çözelti',[{'frostDmgFlat':2},{'frostDmgMult':.04},{'maxEnergyShield':8},{'elementDmgMult':.04}],{'frostDmgFlat':8,'frostDmgMult':.12}),
  ('venom','Aşındırıcı Zehir',[{'poisonDps':2},{'dotDmgMult':.04},{'dmgMult':.035},{'speed':.15}],{'poisonDps':6,'dotDmgMult':.16}),
  ('fire','Uçucu Karışım',[{'fireDmgFlat':2},{'fireDmgMult':.04},{'aoe_bonus':.04},{'dotDmgMult':.04}],{'fireDmgFlat':8,'fireDmgMult':.12}),
  ('recovery','Panzehir',[{'regen':.3},{'max_hp':10},{'dodgeChance':.02},{'speed':.15}],{'regen':1.2,'max_hp_pct':8})],
 'sorcerer': [
  ('chain','Zincir Büyüsü',[{'elementDmgMult':.04},{'fireDmgFlat':2},{'attack_speed_bonus':.04},{'maxEnergyShield':8}],{'bounce':1,'elementDmgMult':.08}),
  ('pierce','Delici Işın',[{'frostDmgFlat':2},{'bullet_speed':.4},{'critChance':.02},{'speed':.15}],{'pierce':2,'elementDmgMult':.06}),
  ('guard','Astral Siper',[{'maxEnergyShield':10},{'esRegen':1},{'max_hp':10},{'regen':.3}],{'maxEnergyShield':40,'esRegen':4}),
  ('volley','Büyü Yelpazesi',[{'attack_speed_bonus':.04},{'aoe_bonus':.05},{'elementDmgMult':.04},{'bullet_speed':.4}],{'projectileCount':1,'aoe_bonus':.1}),
  ('frost','Kışın Kalbi',[{'frostDmgFlat':2},{'frostDmgMult':.04},{'maxEnergyShield':8},{'dotDmgMult':.04}],{'frostDmgFlat':8,'frostDmgMult':.12}),
  ('fire','Kızıl Yıldız',[{'fireDmgFlat':2},{'fireDmgMult':.04},{'aoe_bonus':.05},{'dotDmgMult':.04}],{'fireDmgFlat':8,'aoe_bonus':.2}),
  ('crit','Arkane Odak',[{'critChance':.02},{'critDmg':.07},{'elementDmgMult':.04},{'bossDmgMult':.05}],{'critChance':.08,'critDmg':.2}),
  ('flow','Büyü Akışı',[{'attack_speed_bonus':.04},{'speed':.15},{'cooldownReduction':.025},{'esRegen':1}],{'attack_speed_bonus':.12,'speed':.35})],
 'bloodwalker': [
  ('reach','Kızıl Hasat',[{'meleeRangeFlat':10},{'physDmgMult':.04},{'lifesteal':.01},{'max_hp':8}],{'meleeRangeFlat':35,'lifesteal':.02}),
  ('tempo','Kan Akışı',[{'attack_speed_bonus':.04},{'physDmgFlat':2},{'regen':.3},{'speed':.15}],{'attack_speed_bonus':.12,'meleeRangeFlat':20}),
  ('guard','Kan Sığınağı',[{'max_hp':10},{'armor':4},{'regen':.3},{'max_hp_pct':3}],{'max_hp_pct':12,'armor':10}),
  ('leech','Açlık',[{'lifesteal':.01},{'physDmgMult':.04},{'max_hp':8},{'attack_speed_bonus':.03}],{'lifesteal':.05,'combatRegen':1}),
  ('crit','Kanlı Neşter',[{'critChance':.02},{'critDmg':.07},{'physDmgFlat':2},{'armorPenFlat':2}],{'critChance':.07,'armorPenFlat':8}),
  ('execution','Son Nefes',[{'bossDmgMult':.05},{'physDmgMult':.04},{'armorPenFlat':2},{'max_hp':8}],{'lowHpExec':.08,'bossDmgMult':.15}),
  ('venom','Zehirli Kan',[{'poisonDps':2},{'dotDmgMult':.04},{'aoe_bonus':.04},{'lifesteal':.01}],{'poisonDps':6,'dotDmgMult':.15}),
  ('stride','Kızıl Adım',[{'speed':.15},{'meleeRangeFlat':10},{'dodgeChance':.02},{'regen':.3}],{'speed':.4,'dodgeChance':.06})],
 'ninja': [
  ('reach','Ufuk Kesen',[{'meleeRangeFlat':10},{'physDmgMult':.04},{'critChance':.02},{'max_hp':8}],{'meleeRangeFlat':35,'attack_speed_bonus':.06}),
  ('tempo','Akıcı Bıçak',[{'attack_speed_bonus':.04},{'physDmgFlat':2},{'dodgeChance':.015},{'speed':.15}],{'attack_speed_bonus':.12,'meleeRangeFlat':20}),
  ('guard','Gölge Siperi',[{'dodgeChance':.02},{'max_hp':10},{'regen':.3},{'armor':4}],{'dodgeChance':.06,'max_hp_pct':8}),
  ('crit','Suikast',[{'critChance':.02},{'critDmg':.07},{'physDmgFlat':2},{'armorPenFlat':2}],{'critChance':.08,'critDmg':.2}),
  ('leech','Dövüş Ritmi',[{'lifesteal':.01},{'attack_speed_bonus':.04},{'max_hp':8},{'regen':.3}],{'lifesteal':.04,'combatRegen':1}),
  ('execution','Sessiz Son',[{'bossDmgMult':.05},{'armorPenFlat':2},{'physDmgMult':.04},{'critChance':.015}],{'bossDmgMult':.2,'armorPenFlat':8}),
  ('venom','Zehirli Bıçak',[{'poisonDps':2},{'dotDmgMult':.04},{'meleeRangeFlat':8},{'dodgeChance':.015}],{'poisonDps':6,'dotDmgMult':.15}),
  ('stride','Rüzgâr Adımı',[{'speed':.15},{'dodgeChance':.02},{'meleeRangeFlat':10},{'max_hp':8}],{'speed':.4,'meleeRangeFlat':25})],
}

# Mechanical trade-offs, accessible to any class that pays for the route.
KEYSTONES = {
 'warrior':[('Çelik Ufuk',{'meleeRangeMult':.35,'attack_speed_bonus':-.12}),('Demir Yemin',{'armor':50,'max_hp_pct':15,'dodgeChance':-.15})],
 'sniper':[('Parçalanan Salvo',{'projectileCount':2,'dmgMult':-.2}),('Son Mermi',{'critChance':.15,'bossDmgMult':.3,'attack_speed_bonus':-.2})],
 'engineer':[('Dağıtık Ağ',{'turretLimit':2,'turretDmg':-.2}),('Aşırı Devir',{'turretRate':.5,'turretMaxHp':-60})],
 'beastmaster':[('Kalabalık Sürü',{'minionCount':2,'minionDamage':-.2}),('Cam Dişler',{'minionDamage':.4,'minionRange':-.3})],
 'bomber':[('Kuşatma Alanı',{'aoe_bonus':.5,'attack_speed_bonus':-.18}),('Çifte Tetik',{'projectileCount':2,'dmgMult':-.2})],
 'alchemist':[('Yoğun Çözelti',{'dotDmgMult':.4,'aoe_bonus':-.2}),('Uçucu Yayılım',{'aoe_bonus':.45,'dotDmgMult':-.15})],
 'sorcerer':[('Yankılanan Büyü',{'bounce':2,'elementDmgMult':-.15}),('Kırılgan Yıldız',{'elementDmgMult':.35,'max_hp_pct':-20})],
 'bloodwalker':[('Kan Banyosu',{'lifesteal':.15,'max_hp_pct':20,'dmgMult':-.15}),('Kızıl Ufuk',{'meleeRangeMult':.35,'armor':-25})],
 'ninja':[('Gölge Ufku',{'meleeRangeMult':.35,'max_hp_pct':-15}),('Keskin Bedel',{'critChance':.15,'critDmg':.4,'armor':-25})],
}

# Neighbor regions share useful passives, never class-exclusive active skills.
SHARED = [
 ('Silah Ustalığı',[{'physDmgMult':.04},{'critChance':.02},{'attack_speed_bonus':.04},{'max_hp':8}],{'physDmgMult':.1,'armorPenFlat':6}),
 ('Balistik',[{'bullet_speed':.4},{'physDmgMult':.04},{'speed':.15},{'critChance':.02}],{'pierce':1,'turretRange':30}),
 ('Komuta',[{'minionDamage':.03,'turretDmg':.03},{'minionRange':.06,'turretRange':15},{'max_hp':8},{'armor':4}],{'minionRate':.1,'turretRate':.1}),
 ('Saha Kontrolü',[{'aoe_bonus':.04},{'max_hp':8},{'speed':.15},{'regen':.3}],{'aoe_bonus':.15,'minionRange':.15}),
 ('Yanıcı Karışım',[{'dotDmgMult':.04},{'aoe_bonus':.04},{'fireDmgMult':.04},{'regen':.3}],{'fireDmgFlat':5,'dotDmgMult':.1}),
 ('Element Dokuma',[{'elementDmgMult':.04},{'dotDmgMult':.04},{'maxEnergyShield':8},{'esRegen':1}],{'elementDmgMult':.1,'maxEnergyShield':20}),
 ('Yaşam ve Mana',[{'max_hp':8},{'maxEnergyShield':8},{'regen':.3},{'esRegen':1}],{'max_hp_pct':8,'maxEnergyShield':25}),
 ('Kanlı Çeviklik',[{'physDmgMult':.04},{'attack_speed_bonus':.04},{'critChance':.02},{'lifesteal':.01}],{'attack_speed_bonus':.1,'lifesteal':.03}),
 ('Çelik Adımlar',[{'meleeRangeFlat':8},{'dodgeChance':.015},{'physDmgMult':.04},{'speed':.15}],{'meleeRangeFlat':25,'armor':10}),
]
