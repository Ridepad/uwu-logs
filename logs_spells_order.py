from collections import defaultdict

SPELLS = {
  "17": {
    "name": "Power Word: Shield",
    "icon": "spell_holy_powerwordshield"
  },
  "66": {
    "name": "Invisibility",
    "icon": "ability_mage_invisibility"
  },
  "71": {
    "name": "Defensive Stance",
    "icon": "ability_warrior_defensivestance"
  },
  "72": {
    "name": "Shield Bash",
    "icon": "ability_warrior_shieldbash"
  },
  "130": {
    "name": "Slow Fall",
    "icon": "spell_magic_featherfall"
  },
  "355": {
    "name": "Taunt",
    "icon": "spell_nature_reincarnation"
  },
  "475": {
    "name": "Remove Curse",
    "icon": "spell_nature_removecurse"
  },
  "498": {
    "name": "Divine Protection",
    "icon": "spell_holy_restoration"
  },
  "526": {
    "name": "Cure Toxins",
    "icon": "spell_nature_nullifypoison"
  },
  "528": {
    "name": "Cure Disease",
    "icon": "spell_holy_nullifydisease"
  },
  "546": {
    "name": "Water Walking",
    "icon": "spell_frost_windwalkon"
  },
  "552": {
    "name": "Abolish Disease",
    "icon": "spell_nature_nullifydisease"
  },
  "586": {
    "name": "Fade",
    "icon": "spell_magic_lesserinvisibilty"
  },
  "642": {
    "name": "Divine Shield",
    "icon": "spell_holy_divineintervention"
  },
  "676": {
    "name": "Disarm",
    "icon": "ability_warrior_disarm"
  },
  "698": {
    "name": "Ritual of Summoning",
    "icon": "spell_shadow_twilight"
  },
  "755": {
    "name": "Health Funnel",
    "icon": "spell_shadow_lifedrain"
  },
  "768": {
    "name": "Cat Form",
    "icon": "ability_druid_catform"
  },
  "770": {
    "name": "Faerie Fire",
    "icon": "spell_nature_faeriefire"
  },
  "781": {
    "name": "Disengage",
    "icon": "ability_rogue_feint"
  },
  "783": {
    "name": "Travel Form",
    "icon": "ability_druid_travelform"
  },
  "871": {
    "name": "Shield Wall",
    "icon": "ability_warrior_shieldwall"
  },
  "883": {
    "name": "Call Pet",
    "icon": "ability_hunter_beastcall"
  },
  "988": {
    "name": "Dispel Magic",
    "icon": "spell_holy_dispelmagic"
  },
  "1038": {
    "name": "Hand of Salvation",
    "icon": "spell_holy_sealofsalvation"
  },
  "1044": {
    "name": "Hand of Freedom",
    "icon": "spell_holy_sealofvalor"
  },
  "1454": {
    "name": "Life Tap",
    "icon": "spell_shadow_burningspirit"
  },
  "1494": {
    "name": "Track Beasts",
    "icon": "ability_tracking"
  },
  "1680": {
    "name": "Whirlwind",
    "icon": "ability_whirlwind"
  },
  "1706": {
    "name": "Levitate",
    "icon": "spell_holy_layonhands"
  },
  "1715": {
    "name": "Hamstring",
    "icon": "ability_shockwave"
  },
  "1719": {
    "name": "Recklessness",
    "icon": "ability_criticalstrike"
  },
  "1742": {
    "name": "Cower",
    "icon": "ability_druid_cower"
  },
  "1766": {
    "name": "Kick",
    "icon": "ability_kick"
  },
  "1776": {
    "name": "Gouge",
    "icon": "ability_gouge"
  },
  "1784": {
    "name": "Stealth",
    "icon": "ability_stealth"
  },
  "1833": {
    "name": "Cheap Shot",
    "icon": "ability_cheapshot"
  },
  "1953": {
    "name": "Blink",
    "icon": "spell_arcane_blink"
  },
  "2139": {
    "name": "Counterspell",
    "icon": "spell_frost_iceshock"
  },
  "2383": {
    "name": "Find Herbs",
    "icon": "inv_misc_flower_02"
  },
  "2457": {
    "name": "Battle Stance",
    "icon": "ability_warrior_offensivestance"
  },
  "2458": {
    "name": "Berserker Stance",
    "icon": "ability_racial_avatar"
  },
  "2484": {
    "name": "Earthbind Totem",
    "icon": "spell_nature_strengthofearthtotem02"
  },
  "2565": {
    "name": "Shield Block",
    "icon": "ability_defend"
  },
  "2580": {
    "name": "Find Minerals",
    "icon": "spell_nature_earthquake"
  },
  "2687": {
    "name": "Bloodrage",
    "icon": "ability_racial_bloodrage"
  },
  "2782": {
    "name": "Remove Curse",
    "icon": "spell_holy_removecurse"
  },
  "2825": {
    "name": "Bloodlust",
    "icon": "spell_nature_bloodlust"
  },
  "2893": {
    "name": "Abolish Poison",
    "icon": "spell_nature_nullifypoison_02"
  },
  "2894": {
    "name": "Fire Elemental Totem",
    "icon": "spell_fire_elemental_totem"
  },
  "3034": {
    "name": "Viper Sting",
    "icon": "ability_hunter_aimedshot"
  },
  "3045": {
    "name": "Rapid Fire",
    "icon": "ability_hunter_runningshot"
  },
  "3411": {
    "name": "Intervene",
    "icon": "ability_warrior_victoryrush"
  },
  "3738": {
    "name": "Wrath of Air Totem",
    "icon": "spell_nature_slowingtotem"
  },
  "4511": {
    "name": "Phase Shift",
    "icon": "spell_shadow_impphaseshift"
  },
  "4987": {
    "name": "Cleanse",
    "icon": "spell_holy_renew"
  },
  "5116": {
    "name": "Concussive Shot",
    "icon": "spell_frost_stun"
  },
  "5118": {
    "name": "Aspect of the Cheetah",
    "icon": "ability_mount_jungletiger"
  },
  "5215": {
    "name": "Prowl",
    "icon": "ability_ambush"
  },
  "5225": {
    "name": "Track Humanoids",
    "icon": "ability_tracking"
  },
  "5229": {
    "name": "Enrage",
    "icon": "ability_druid_enrage"
  },
  "5246": {
    "name": "Intimidating Shout",
    "icon": "ability_golemthunderclap"
  },
  "6346": {
    "name": "Fear Ward",
    "icon": "spell_holy_excorcism"
  },
  "6552": {
    "name": "Pummel",
    "icon": "inv_gauntlets_04"
  },
  "6774": {
    "name": "Slice and Dice",
    "icon": "ability_rogue_slicedice"
  },
  "6795": {
    "name": "Growl",
    "icon": "ability_physical_taunt"
  },
  "6940": {
    "name": "Hand of Sacrifice",
    "icon": "spell_holy_sealofsacrifice"
  },
  "6991": {
    "name": "Feed Pet",
    "icon": "ability_hunter_beasttraining"
  },
  "7384": {
    "name": "Overpower",
    "icon": "ability_meleedamage"
  },
  "7386": {
    "name": "Sunder Armor",
    "icon": "ability_warrior_sunder"
  },
  "8012": {
    "name": "Purge",
    "icon": "spell_nature_purge"
  },
  "8063": {
    "name": "Deviate Fish",
    "icon": "inv_misc_fish_03"
  },
  "8143": {
    "name": "Tremor Totem",
    "icon": "spell_nature_tremortotem"
  },
  "8213": {
    "name": "Cooked Deviate Fish",
    "icon": "inv_misc_fish_03"
  },
  "8643": {
    "name": "Kidney Shot",
    "icon": "ability_rogue_kidneyshot"
  },
  "8647": {
    "name": "Expose Armor",
    "icon": "ability_warrior_riposte"
  },
  "8983": {
    "name": "Bash",
    "icon": "ability_druid_bash"
  },
  "9080": {
    "name": "Hamstring",
    "icon": "ability_shockwave"
  },
  "9512": {
    "name": "Restore Energy",
    "icon": "trade_engineering"
  },
  "9634": {
    "name": "Dire Bear Form",
    "icon": "ability_racial_bearform"
  },
  "10060": {
    "name": "Power Infusion",
    "icon": "spell_holy_powerinfusion"
  },
  "10278": {
    "name": "Hand of Protection",
    "icon": "spell_holy_sealofprotection"
  },
  "10308": {
    "name": "Hammer of Justice",
    "icon": "spell_holy_sealofmight"
  },
  "10890": {
    "name": "Psychic Scream",
    "icon": "spell_shadow_psychicscream"
  },
  "10909": {
    "name": "Mind Vision",
    "icon": "spell_holy_mindvision"
  },
  "11305": {
    "name": "Sprint",
    "icon": "ability_rogue_sprint"
  },
  "11350": {
    "name": "Fire Shield",
    "icon": "spell_fire_immolation"
  },
  "11578": {
    "name": "Charge",
    "icon": "ability_warrior_charge"
  },
  "11688": {
    "name": "Life Tap",
    "icon": "spell_shadow_burningspirit"
  },
  "11719": {
    "name": "Curse of Tongues",
    "icon": "spell_shadow_curseoftounges"
  },
  "11971": {
    "name": "Sunder Armor",
    "icon": "ability_warrior_sunder"
  },
  "12042": {
    "name": "Arcane Power",
    "icon": "spell_nature_lightning"
  },
  "12043": {
    "name": "Presence of Mind",
    "icon": "spell_nature_enchantarmor"
  },
  "12051": {
    "name": "Evocation",
    "icon": "spell_nature_purge"
  },
  "12292": {
    "name": "Death Wish",
    "icon": "spell_shadow_deathpact"
  },
  "12323": {
    "name": "Piercing Howl",
    "icon": "spell_shadow_deathscream"
  },
  "12328": {
    "name": "Sweeping Strikes",
    "icon": "ability_rogue_slicedice"
  },
  "12472": {
    "name": "Icy Veins",
    "icon": "spell_frost_coldhearted"
  },
  "12809": {
    "name": "Concussion Blow",
    "icon": "ability_thunderbolt"
  },
  "13159": {
    "name": "Aspect of the Pack",
    "icon": "ability_mount_whitetiger"
  },
  "13376": {
    "name": "Fire Shield",
    "icon": "spell_fire_immolation"
  },
  "13481": {
    "name": "Tame Beast",
    "icon": "ability_hunter_beasttaming"
  },
  "13737": {
    "name": "Mortal Strike",
    "icon": "ability_warrior_savageblow"
  },
  "13750": {
    "name": "Adrenaline Rush",
    "icon": "spell_shadow_shadowworddominate"
  },
  "13809": {
    "name": "Frost Trap",
    "icon": "spell_frost_freezingbreath"
  },
  "13877": {
    "name": "Blade Flurry",
    "icon": "ability_warrior_punishingblow"
  },
  "14177": {
    "name": "Cold Blood",
    "icon": "spell_ice_lament"
  },
  "14751": {
    "name": "Inner Focus",
    "icon": "spell_frost_windwalkon"
  },
  "15284": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "15286": {
    "name": "Vampiric Embrace",
    "icon": "spell_shadow_unsummonbuilding"
  },
  "15473": {
    "name": "Shadowform",
    "icon": "spell_shadow_shadowform"
  },
  "15487": {
    "name": "Silence",
    "icon": "spell_shadow_impphaseshift"
  },
  "15496": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "15621": {
    "name": "Skull Crack",
    "icon": "spell_frost_stun"
  },
  "16166": {
    "name": "Elemental Mastery",
    "icon": "spell_nature_wispheal"
  },
  "16188": {
    "name": "Nature\'s Swiftness",
    "icon": "spell_nature_ravenform"
  },
  "16190": {
    "name": "Mana Tide Totem",
    "icon": "spell_frost_summonwaterelemental"
  },
  "16589": {
    "name": "Noggenfogger Elixir",
    "icon": "trade_engineering"
  },
  "16857": {
    "name": "Faerie Fire (Feral)",
    "icon": "spell_nature_faeriefire"
  },
  "16979": {
    "name": "Feral Charge - Bear",
    "icon": "ability_hunter_pet_bear"
  },
  "17116": {
    "name": "Nature\'s Swiftness",
    "icon": "spell_nature_ravenform"
  },
  "17334": {
    "name": "Portal Effect: Stormwind",
    "icon": "spell_arcane_portalstormwind"
  },
  "17364": {
    "name": "Stormstrike",
    "icon": "ability_shaman_stormstrike"
  },
  "17609": {
    "name": "Portal Effect: Orgrimmar",
    "icon": "spell_arcane_portalorgrimmar"
  },
  "17627": {
    "name": "Distilled Wisdom",
    "icon": "inv_potion_97"
  },
  "17962": {
    "name": "Conflagrate",
    "icon": "spell_fire_fireball"
  },
  "18499": {
    "name": "Berserker Rage",
    "icon": "spell_nature_ancestralguardian"
  },
  "18562": {
    "name": "Swiftmend",
    "icon": "inv_relics_idolofrejuvenation"
  },
  "18708": {
    "name": "Fel Domination",
    "icon": "spell_nature_removecurse"
  },
  "19028": {
    "name": "Soul Link",
    "icon": "spell_shadow_gathershadows"
  },
  "19263": {
    "name": "Deterrence",
    "icon": "ability_whirlwind"
  },
  "19506": {
    "name": "Trueshot Aura",
    "icon": "ability_trueshot"
  },
  "19746": {
    "name": "Concentration Aura",
    "icon": "spell_holy_mindsooth"
  },
  "19752": {
    "name": "Divine Intervention",
    "icon": "spell_nature_timestop"
  },
  "19801": {
    "name": "Tranquilizing Shot",
    "icon": "spell_nature_drowsy"
  },
  "19879": {
    "name": "Track Dragonkin",
    "icon": "inv_misc_head_dragon_01"
  },
  "19880": {
    "name": "Track Elementals",
    "icon": "spell_frost_summonwaterelemental"
  },
  "19883": {
    "name": "Track Humanoids",
    "icon": "spell_holy_prayerofhealing"
  },
  "19884": {
    "name": "Track Undead",
    "icon": "spell_shadow_darksummoning"
  },
  "19983": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "20066": {
    "name": "Repentance",
    "icon": "spell_holy_prayerofhealing"
  },
  "20166": {
    "name": "Seal of Wisdom",
    "icon": "spell_holy_righteousnessaura"
  },
  "20216": {
    "name": "Divine Favor",
    "icon": "spell_holy_heal"
  },
  "20217": {
    "name": "Blessing of Kings",
    "icon": "spell_magic_magearmor"
  },
  "20230": {
    "name": "Retaliation",
    "icon": "ability_warrior_challange"
  },
  "20252": {
    "name": "Intercept",
    "icon": "ability_rogue_sprint"
  },
  "20271": {
    "name": "Judgement of Light",
    "icon": "spell_holy_righteousfury"
  },
  "20375": {
    "name": "Seal of Command",
    "icon": "ability_warrior_innerrage"
  },
  "20572": {
    "name": "Blood Fury",
    "icon": "racial_orc_berserkerstrength"
  },
  "20736": {
    "name": "Distracting Shot",
    "icon": "spell_arcane_blink"
  },
  "20911": {
    "name": "Blessing of Sanctuary",
    "icon": "spell_nature_lightningshield"
  },
  "21169": {
    "name": "Reincarnation",
    "icon": "spell_nature_reincarnation"
  },
  "21343": {
    "name": "Snowball",
    "icon": "inv_ammo_snowball"
  },
  "22812": {
    "name": "Barkskin",
    "icon": "spell_nature_stoneclawtotem"
  },
  "23133": {
    "name": "Gnomish Battle Chicken",
    "icon": "spell_magic_polymorphchicken"
  },
  "23135": {
    "name": "Heavy Leather Ball",
    "icon": "inv_ammo_bullet_02"
  },
  "23881": {
    "name": "Bloodthirst",
    "icon": "spell_nature_bloodlust"
  },
  "23920": {
    "name": "Spell Reflection",
    "icon": "ability_warrior_shieldreflection"
  },
  "23989": {
    "name": "Readiness",
    "icon": "ability_hunter_readiness"
  },
  "24858": {
    "name": "Moonkin Form",
    "icon": "spell_nature_forceofnature"
  },
  "25046": {
    "name": "Arcane Torrent",
    "icon": "spell_shadow_teleport"
  },
  "25299": {
    "name": "Rejuvenation",
    "icon": "spell_nature_rejuvenation"
  },
  "25646": {
    "name": "Mortal Wound",
    "icon": "ability_criticalstrike"
  },
  "25780": {
    "name": "Righteous Fury",
    "icon": "spell_holy_sealoffury"
  },
  "25898": {
    "name": "Greater Blessing of Kings",
    "icon": "spell_magic_greaterblessingofkings"
  },
  "25899": {
    "name": "Greater Blessing of Sanctuary",
    "icon": "spell_holy_greaterblessingofsanctuary"
  },
  "26297": {
    "name": "Berserking",
    "icon": "racial_troll_berserk"
  },
  "26669": {
    "name": "Evasion",
    "icon": "spell_shadow_shadowward"
  },
  "26889": {
    "name": "Vanish",
    "icon": "ability_vanish"
  },
  "26981": {
    "name": "Rejuvenation",
    "icon": "spell_nature_rejuvenation"
  },
  "27173": {
    "name": "Consecration",
    "icon": "spell_holy_innerfire"
  },
  "28169": {
    "name": "Mutating Injection",
    "icon": "spell_shadow_callofbone"
  },
  "28240": {
    "name": "Poison Cloud",
    "icon": "spell_nature_abolishmagic"
  },
  "28322": {
    "name": "Embalming Cloud",
    "icon": "spell_shadow_corpseexplode"
  },
  "28375": {
    "name": "Decimate",
    "icon": "trade_engineering"
  },
  "28434": {
    "name": "Spider Web",
    "icon": "spell_nature_earthbind"
  },
  "28494": {
    "name": "Insane Strength Potion",
    "icon": "inv_potion_109"
  },
  "28499": {
    "name": "Restore Mana",
    "icon": "trade_engineering"
  },
  "28507": {
    "name": "Haste",
    "icon": "inv_potion_108"
  },
  "28714": {
    "name": "Flame Cap",
    "icon": "inv_misc_herb_flamecap"
  },
  "28730": {
    "name": "Arcane Torrent",
    "icon": "spell_shadow_teleport"
  },
  "29166": {
    "name": "Innervate",
    "icon": "spell_nature_lightning"
  },
  "29858": {
    "name": "Soulshatter",
    "icon": "spell_arcane_arcane01"
  },
  "30449": {
    "name": "Spellsteal",
    "icon": "spell_arcane_arcane02"
  },
  "30823": {
    "name": "Shamanistic Rage",
    "icon": "spell_nature_shamanrage"
  },
  "31224": {
    "name": "Cloak of Shadows",
    "icon": "spell_shadow_nethercloak"
  },
  "31789": {
    "name": "Righteous Defense",
    "icon": "inv_shoulder_37"
  },
  "31801": {
    "name": "Seal of Vengeance",
    "icon": "spell_holy_sealofvengeance"
  },
  "31818": {
    "name": "Life Tap",
    "icon": "spell_holy_righteousnessaura"
  },
  "31821": {
    "name": "Aura Mastery",
    "icon": "spell_holy_auramastery"
  },
  "31842": {
    "name": "Divine Illumination",
    "icon": "spell_holy_divineillumination"
  },
  "31884": {
    "name": "Avenging Wrath",
    "icon": "spell_holy_avenginewrath"
  },
  "32182": {
    "name": "Heroism",
    "icon": "ability_shaman_heroism"
  },
  "32223": {
    "name": "Crusader Aura",
    "icon": "spell_holy_crusaderaura"
  },
  "33206": {
    "name": "Pain Suppression",
    "icon": "spell_holy_painsupression"
  },
  "33357": {
    "name": "Dash",
    "icon": "ability_druid_dash"
  },
  "33697": {
    "name": "Blood Fury",
    "icon": "racial_orc_berserkerstrength"
  },
  "33702": {
    "name": "Blood Fury",
    "icon": "racial_orc_berserkerstrength"
  },
  "33831": {
    "name": "Force of Nature",
    "icon": "ability_druid_forceofnature"
  },
  "33891": {
    "name": "Tree of Life",
    "icon": "ability_druid_treeoflife"
  },
  "34026": {
    "name": "Kill Command",
    "icon": "ability_hunter_killcommand"
  },
  "34074": {
    "name": "Aspect of the Viper",
    "icon": "ability_hunter_aspectoftheviper"
  },
  "34428": {
    "name": "Victory Rush",
    "icon": "ability_warrior_devastate"
  },
  "34433": {
    "name": "Shadowfiend",
    "icon": "spell_shadow_shadowfiend"
  },
  "34477": {
    "name": "Misdirection",
    "icon": "ability_hunter_misdirection"
  },
  "34490": {
    "name": "Silencing Shot",
    "icon": "ability_theblackarrow"
  },
  "34600": {
    "name": "Snake Trap",
    "icon": "ability_hunter_snaketrap"
  },
  "35395": {
    "name": "Crusader Strike",
    "icon": "spell_holy_crusaderstrike"
  },
  "36213": {
    "name": "Angered Earth",
    "icon": "spell_nature_earthquake"
  },
  "36936": {
    "name": "Totemic Recall",
    "icon": "spell_shaman_totemrecall"
  },
  "40504": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "40505": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "42650": {
    "name": "Army of the Dead",
    "icon": "spell_deathknight_armyofthedead"
  },
  "42873": {
    "name": "Fire Blast",
    "icon": "spell_fire_fireball"
  },
  "42891": {
    "name": "Pyroblast",
    "icon": "spell_fire_fireball02"
  },
  "42914": {
    "name": "Ice Lance",
    "icon": "spell_frost_frostblast"
  },
  "42917": {
    "name": "Frost Nova",
    "icon": "spell_frost_frostnova"
  },
  "42921": {
    "name": "Arcane Explosion",
    "icon": "spell_nature_wispsplode"
  },
  "42931": {
    "name": "Cone of Cold",
    "icon": "spell_frost_glacier"
  },
  "42940": {
    "name": "Blizzard",
    "icon": "spell_frost_icestorm"
  },
  "42987": {
    "name": "Replenish Mana",
    "icon": "inv_misc_gem_stone_01"
  },
  "42995": {
    "name": "Arcane Intellect",
    "icon": "spell_holy_magicalsentry"
  },
  "43002": {
    "name": "Arcane Brilliance",
    "icon": "spell_holy_arcaneintellect"
  },
  "43010": {
    "name": "Fire Ward",
    "icon": "spell_fire_firearmor"
  },
  "43012": {
    "name": "Frost Ward",
    "icon": "spell_frost_frostward"
  },
  "43015": {
    "name": "Dampen Magic",
    "icon": "spell_nature_abolishmagic"
  },
  "43017": {
    "name": "Amplify Magic",
    "icon": "spell_holy_flashheal"
  },
  "43020": {
    "name": "Mana Shield",
    "icon": "spell_shadow_detectlesserinvisibility"
  },
  "43039": {
    "name": "Ice Barrier",
    "icon": "spell_ice_lament"
  },
  "43046": {
    "name": "Molten Armor",
    "icon": "ability_mage_moltenarmor"
  },
  "43137": {
    "name": "Zap",
    "icon": "spell_nature_stormreach"
  },
  "43186": {
    "name": "Restore Mana",
    "icon": "trade_engineering"
  },
  "43243": {
    "name": "Shred Armor",
    "icon": "ability_warrior_sunder"
  },
  "43358": {
    "name": "Gut Rip",
    "icon": "ability_druid_disembowel"
  },
  "43771": {
    "name": "Well Fed",
    "icon": "spell_misc_food"
  },
  "44572": {
    "name": "Deep Freeze",
    "icon": "ability_mage_deepfreeze"
  },
  "44781": {
    "name": "Arcane Barrage",
    "icon": "ability_mage_arcanebarrage"
  },
  "45438": {
    "name": "Ice Block",
    "icon": "spell_frost_frost"
  },
  "45470": {
    "name": "Death Strike",
    "icon": "spell_deathknight_butcher2"
  },
  "45524": {
    "name": "Chains of Ice",
    "icon": "spell_frost_chainsofice"
  },
  "45529": {
    "name": "Blood Tap",
    "icon": "spell_deathknight_bloodtap"
  },
  "46584": {
    "name": "Raise Dead",
    "icon": "spell_shadow_animatedead"
  },
  "46924": {
    "name": "Bladestorm",
    "icon": "ability_warrior_bladestorm"
  },
  "46968": {
    "name": "Shockwave",
    "icon": "ability_warrior_shockwave"
  },
  "47193": {
    "name": "Demonic Empowerment",
    "icon": "ability_warlock_demonicempowerment"
  },
  "47241": {
    "name": "Metamorphosis",
    "icon": "spell_shadow_demonform"
  },
  "47436": {
    "name": "Battle Shout",
    "icon": "ability_warrior_battleshout"
  },
  "47437": {
    "name": "Demoralizing Shout",
    "icon": "ability_warrior_warcry"
  },
  "47440": {
    "name": "Commanding Shout",
    "icon": "ability_warrior_rallyingcry"
  },
  "47450": {
    "name": "Heroic Strike",
    "icon": "ability_rogue_ambush"
  },
  "47465": {
    "name": "Rend",
    "icon": "ability_gouge"
  },
  "47476": {
    "name": "Strangulate",
    "icon": "spell_shadow_soulleech_3"
  },
  "47482": {
    "name": "Leap",
    "icon": "spell_shadow_skull"
  },
  "47486": {
    "name": "Mortal Strike",
    "icon": "ability_warrior_savageblow"
  },
  "47488": {
    "name": "Shield Slam",
    "icon": "inv_shield_05"
  },
  "47498": {
    "name": "Devastate",
    "icon": "inv_sword_11"
  },
  "47502": {
    "name": "Thunder Clap",
    "icon": "spell_nature_thunderclap"
  },
  "47520": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "47528": {
    "name": "Mind Freeze",
    "icon": "spell_deathknight_mindfreeze"
  },
  "47568": {
    "name": "Empower Rune Weapon",
    "icon": "inv_sword_62"
  },
  "47585": {
    "name": "Dispersion",
    "icon": "spell_shadow_dispersion"
  },
  "47788": {
    "name": "Guardian Spirit",
    "icon": "spell_holy_guardianspirit"
  },
  "47809": {
    "name": "Shadow Bolt",
    "icon": "spell_shadow_shadowbolt"
  },
  "47813": {
    "name": "Corruption",
    "icon": "spell_shadow_abominationexplosion"
  },
  "47820": {
    "name": "Rain of Fire",
    "icon": "spell_shadow_rainoffire"
  },
  "47823": {
    "name": "Hellfire",
    "icon": "spell_fire_incinerate"
  },
  "47847": {
    "name": "Shadowfury",
    "icon": "spell_shadow_shadowfury"
  },
  "47855": {
    "name": "Drain Soul",
    "icon": "spell_shadow_haunting"
  },
  "47856": {
    "name": "Health Funnel",
    "icon": "spell_shadow_lifedrain"
  },
  "47857": {
    "name": "Drain Life",
    "icon": "spell_shadow_lifedrain02"
  },
  "47860": {
    "name": "Death Coil",
    "icon": "spell_shadow_deathcoil"
  },
  "47864": {
    "name": "Curse of Agony",
    "icon": "spell_shadow_curseofsargeras"
  },
  "47865": {
    "name": "Curse of the Elements",
    "icon": "spell_shadow_chilltouch"
  },
  "47867": {
    "name": "Curse of Doom",
    "icon": "spell_shadow_auraofdarkness"
  },
  "47875": {
    "name": "Master Healthstone",
    "icon": "inv_stone_04"
  },
  "47877": {
    "name": "Master Healthstone",
    "icon": "inv_stone_04"
  },
  "47882": {
    "name": "Use Soulstone",
    "icon": "trade_engineering"
  },
  "47891": {
    "name": "Shadow Ward",
    "icon": "spell_shadow_antishadow"
  },
  "47893": {
    "name": "Fel Armor",
    "icon": "spell_shadow_felarmour"
  },
  "47982": {
    "name": "Blood Pact",
    "icon": "spell_shadow_bloodboil"
  },
  "47983": {
    "name": "Fire Shield",
    "icon": "spell_fire_firearmor"
  },
  "48011": {
    "name": "Devour Magic",
    "icon": "spell_nature_purge"
  },
  "48020": {
    "name": "Demonic Circle: Teleport",
    "icon": "spell_shadow_demoniccircleteleport"
  },
  "48066": {
    "name": "Power Word: Shield",
    "icon": "spell_holy_powerwordshield"
  },
  "48068": {
    "name": "Renew",
    "icon": "spell_holy_renew"
  },
  "48073": {
    "name": "Divine Spirit",
    "icon": "spell_holy_divinespirit"
  },
  "48074": {
    "name": "Prayer of Spirit",
    "icon": "spell_holy_prayerofspirit"
  },
  "48078": {
    "name": "Holy Nova",
    "icon": "spell_holy_holynova"
  },
  "48089": {
    "name": "Circle of Healing",
    "icon": "spell_holy_circleofrenewal"
  },
  "48113": {
    "name": "Prayer of Mending",
    "icon": "spell_holy_prayerofmendingtga"
  },
  "48125": {
    "name": "Shadow Word: Pain",
    "icon": "spell_shadow_shadowwordpain"
  },
  "48156": {
    "name": "Mind Flay",
    "icon": "spell_shadow_siphonmana"
  },
  "48158": {
    "name": "Shadow Word: Death",
    "icon": "spell_shadow_demonicfortitude"
  },
  "48161": {
    "name": "Power Word: Fortitude",
    "icon": "spell_holy_wordfortitude"
  },
  "48162": {
    "name": "Prayer of Fortitude",
    "icon": "spell_holy_prayeroffortitude"
  },
  "48168": {
    "name": "Inner Fire",
    "icon": "spell_holy_innerfire"
  },
  "48169": {
    "name": "Shadow Protection",
    "icon": "spell_shadow_antishadow"
  },
  "48170": {
    "name": "Prayer of Shadow Protection",
    "icon": "spell_holy_prayerofshadowprotection"
  },
  "48173": {
    "name": "Desperate Prayer",
    "icon": "spell_holy_restoration"
  },
  "48263": {
    "name": "Frost Presence",
    "icon": "spell_deathknight_frostpresence"
  },
  "48265": {
    "name": "Unholy Presence",
    "icon": "spell_deathknight_unholypresence"
  },
  "48266": {
    "name": "Blood Presence",
    "icon": "spell_deathknight_bloodpresence"
  },
  "48300": {
    "name": "Devouring Plague",
    "icon": "spell_shadow_devouringplague"
  },
  "48438": {
    "name": "Wild Growth",
    "icon": "ability_druid_flourish"
  },
  "48441": {
    "name": "Rejuvenation",
    "icon": "spell_nature_rejuvenation"
  },
  "48447": {
    "name": "Tranquility",
    "icon": "spell_nature_tranquility"
  },
  "48451": {
    "name": "Lifebloom",
    "icon": "inv_misc_herb_felblossom"
  },
  "48462": {
    "name": "Moonfire",
    "icon": "spell_nature_starfall"
  },
  "48463": {
    "name": "Moonfire",
    "icon": "spell_nature_starfall"
  },
  "48467": {
    "name": "Hurricane",
    "icon": "spell_nature_cyclone"
  },
  "48468": {
    "name": "Insect Swarm",
    "icon": "spell_nature_insectswarm"
  },
  "48469": {
    "name": "Mark of the Wild",
    "icon": "spell_nature_regeneration"
  },
  "48470": {
    "name": "Gift of the Wild",
    "icon": "spell_nature_giftofthewild"
  },
  "48480": {
    "name": "Maul",
    "icon": "ability_druid_maul"
  },
  "48560": {
    "name": "Demoralizing Roar",
    "icon": "ability_druid_demoralizingroar"
  },
  "48562": {
    "name": "Swipe (Bear)",
    "icon": "inv_misc_monsterclaw_03"
  },
  "48564": {
    "name": "Mangle (Bear)",
    "icon": "ability_druid_mangle2"
  },
  "48566": {
    "name": "Mangle (Cat)",
    "icon": "ability_druid_mangle2"
  },
  "48568": {
    "name": "Lacerate",
    "icon": "ability_druid_lacerate"
  },
  "48572": {
    "name": "Shred",
    "icon": "spell_shadow_vampiricaura"
  },
  "48574": {
    "name": "Rake",
    "icon": "ability_druid_disembowel"
  },
  "48577": {
    "name": "Ferocious Bite",
    "icon": "ability_druid_ferociousbite"
  },
  "48638": {
    "name": "Sinister Strike",
    "icon": "spell_shadow_ritualofsacrifice"
  },
  "48659": {
    "name": "Feint",
    "icon": "ability_rogue_feint"
  },
  "48666": {
    "name": "Mutilate",
    "icon": "ability_rogue_shadowstrikes"
  },
  "48668": {
    "name": "Eviscerate",
    "icon": "ability_rogue_eviscerate"
  },
  "48672": {
    "name": "Rupture",
    "icon": "ability_rogue_rupture"
  },
  "48676": {
    "name": "Garrote",
    "icon": "ability_rogue_garrote"
  },
  "48707": {
    "name": "Anti-Magic Shell",
    "icon": "spell_shadow_antimagicshell"
  },
  "48785": {
    "name": "Flash of Light",
    "icon": "spell_holy_flashheal"
  },
  "48788": {
    "name": "Lay on Hands",
    "icon": "spell_holy_layonhands"
  },
  "48792": {
    "name": "Icebound Fortitude",
    "icon": "spell_deathknight_iceboundfortitude"
  },
  "48801": {
    "name": "Exorcism",
    "icon": "spell_holy_excorcism_02"
  },
  "48806": {
    "name": "Hammer of Wrath",
    "icon": "ability_thunderclap"
  },
  "48817": {
    "name": "Holy Wrath",
    "icon": "spell_holy_excorcism"
  },
  "48818": {
    "name": "Consecration",
    "icon": "spell_holy_innerfire"
  },
  "48819": {
    "name": "Consecration",
    "icon": "spell_holy_innerfire"
  },
  "48825": {
    "name": "Holy Shock",
    "icon": "spell_holy_searinglight"
  },
  "48827": {
    "name": "Avenger\'s Shield",
    "icon": "spell_holy_avengersshield"
  },
  "48932": {
    "name": "Blessing of Might",
    "icon": "spell_holy_fistofjustice"
  },
  "48934": {
    "name": "Greater Blessing of Might",
    "icon": "spell_holy_greaterblessingofkings"
  },
  "48936": {
    "name": "Blessing of Wisdom",
    "icon": "spell_holy_sealofwisdom"
  },
  "48938": {
    "name": "Greater Blessing of Wisdom",
    "icon": "spell_holy_greaterblessingofwisdom"
  },
  "48942": {
    "name": "Devotion Aura",
    "icon": "spell_holy_devotionaura"
  },
  "48943": {
    "name": "Shadow Resistance Aura",
    "icon": "spell_shadow_sealofkings"
  },
  "48945": {
    "name": "Frost Resistance Aura",
    "icon": "spell_frost_wizardmark"
  },
  "48947": {
    "name": "Fire Resistance Aura",
    "icon": "spell_fire_sealoffire"
  },
  "48952": {
    "name": "Holy Shield",
    "icon": "spell_holy_blessingofprotection"
  },
  "48982": {
    "name": "Rune Tap",
    "icon": "spell_deathknight_runetap"
  },
  "48990": {
    "name": "Mend Pet",
    "icon": "ability_hunter_mendpet"
  },
  "48996": {
    "name": "Raptor Strike",
    "icon": "ability_meleedamage"
  },
  "49001": {
    "name": "Serpent Sting",
    "icon": "ability_hunter_quickshot"
  },
  "49005": {
    "name": "Mark of Blood",
    "icon": "ability_hunter_rapidkilling"
  },
  "49016": {
    "name": "Hysteria",
    "icon": "spell_deathknight_bladedarmor"
  },
  "49045": {
    "name": "Arcane Shot",
    "icon": "ability_impalingbolt"
  },
  "49050": {
    "name": "Aimed Shot",
    "icon": "inv_spear_07"
  },
  "49067": {
    "name": "Explosive Trap",
    "icon": "spell_fire_selfdestruct"
  },
  "49071": {
    "name": "Aspect of the Wild",
    "icon": "spell_nature_protectionformnature"
  },
  "49206": {
    "name": "Summon Gargoyle",
    "icon": "ability_hunter_pet_bat"
  },
  "49222": {
    "name": "Bone Shield",
    "icon": "inv_chest_leather_13"
  },
  "49231": {
    "name": "Earth Shock",
    "icon": "spell_nature_earthshock"
  },
  "49233": {
    "name": "Flame Shock",
    "icon": "spell_fire_flameshock"
  },
  "49236": {
    "name": "Frost Shock",
    "icon": "spell_frost_frostshock"
  },
  "49238": {
    "name": "Lightning Bolt",
    "icon": "spell_nature_lightning"
  },
  "49271": {
    "name": "Chain Lightning",
    "icon": "spell_nature_chainlightning"
  },
  "49281": {
    "name": "Lightning Shield",
    "icon": "spell_nature_lightningshield"
  },
  "49284": {
    "name": "Earth Shield",
    "icon": "spell_nature_skinofearth"
  },
  "49376": {
    "name": "Feral Charge - Cat",
    "icon": "spell_druid_feralchargecat"
  },
  "49576": {
    "name": "Death Grip",
    "icon": "spell_deathknight_strangulate"
  },
  "49796": {
    "name": "Deathchill",
    "icon": "spell_shadow_soulleech_2"
  },
  "49800": {
    "name": "Rip",
    "icon": "ability_ghoulfrenzy"
  },
  "49895": {
    "name": "Death Coil",
    "icon": "spell_shadow_deathcoil"
  },
  "49909": {
    "name": "Icy Touch",
    "icon": "spell_deathknight_icetouch"
  },
  "49921": {
    "name": "Plague Strike",
    "icon": "spell_deathknight_empowerruneblade"
  },
  "49924": {
    "name": "Death Strike",
    "icon": "spell_deathknight_butcher2"
  },
  "49930": {
    "name": "Blood Strike",
    "icon": "spell_deathknight_deathstrike"
  },
  "49938": {
    "name": "Death and Decay",
    "icon": "spell_shadow_deathanddecay"
  },
  "49941": {
    "name": "Blood Boil",
    "icon": "spell_deathknight_bloodboil"
  },
  "50213": {
    "name": "Tiger\'s Fury",
    "icon": "ability_mount_jungletiger"
  },
  "50334": {
    "name": "Berserk",
    "icon": "ability_druid_berserk"
  },
  "50581": {
    "name": "Shadow Cleave",
    "icon": "ability_warlock_avoidance"
  },
  "50589": {
    "name": "Immolation Aura",
    "icon": "spell_fire_incinerate"
  },
  "50613": {
    "name": "Arcane Torrent",
    "icon": "spell_shadow_teleport"
  },
  "50720": {
    "name": "Vigilance",
    "icon": "ability_warrior_vigilance"
  },
  "50842": {
    "name": "Pestilence",
    "icon": "spell_shadow_plaguecloud"
  },
  "50986": {
    "name": "Sulfuron Slammer",
    "icon": "inv_summerfest_firedrink"
  },
  "51271": {
    "name": "Unbreakable Armor",
    "icon": "inv_armor_helm_plate_naxxramas_raidwarrior_c_01"
  },
  "51294": {
    "name": "Fishing",
    "icon": "trade_fishing"
  },
  "51411": {
    "name": "Howling Blast",
    "icon": "spell_frost_arcticwinds"
  },
  "51425": {
    "name": "Obliterate",
    "icon": "spell_deathknight_classicon"
  },
  "51533": {
    "name": "Feral Spirit",
    "icon": "spell_shaman_feralspirit"
  },
  "51662": {
    "name": "Hunger For Blood",
    "icon": "ability_rogue_hungerforblood"
  },
  "51690": {
    "name": "Killing Spree",
    "icon": "ability_rogue_murderspree"
  },
  "51722": {
    "name": "Dismantle",
    "icon": "ability_rogue_dismantle"
  },
  "51723": {
    "name": "Fan of Knives",
    "icon": "ability_rogue_fanofknives"
  },
  "51886": {
    "name": "Cleanse Spirit",
    "icon": "ability_shaman_cleansespirit"
  },
  "51994": {
    "name": "Earthliving Weapon",
    "icon": "spell_shaman_earthlivingweapon"
  },
  "52150": {
    "name": "Raise Dead",
    "icon": "spell_shadow_animatedead"
  },
  "52610": {
    "name": "Savage Roar",
    "icon": "ability_druid_skinteeth"
  },
  "52985": {
    "name": "Penance",
    "icon": "spell_holy_penance"
  },
  "53000": {
    "name": "Penance",
    "icon": "spell_holy_penance"
  },
  "53023": {
    "name": "Mind Sear",
    "icon": "spell_shadow_mindshear"
  },
  "53201": {
    "name": "Starfall",
    "icon": "ability_druid_starfall"
  },
  "53209": {
    "name": "Chimera Shot",
    "icon": "ability_hunter_chimerashot2"
  },
  "53227": {
    "name": "Typhoon",
    "icon": "spell_frost_stun"
  },
  "53251": {
    "name": "Wild Growth",
    "icon": "ability_druid_flourish"
  },
  "53271": {
    "name": "Master\'s Call",
    "icon": "ability_hunter_masterscall"
  },
  "53307": {
    "name": "Thorns",
    "icon": "spell_nature_thorns"
  },
  "53312": {
    "name": "Nature\'s Grasp",
    "icon": "spell_nature_natureswrath"
  },
  "53338": {
    "name": "Hunter\'s Mark",
    "icon": "ability_hunter_snipershot"
  },
  "53339": {
    "name": "Mongoose Bite",
    "icon": "ability_hunter_swiftstrike"
  },
  "53385": {
    "name": "Divine Storm",
    "icon": "ability_paladin_divinestorm"
  },
  "53395": {
    "name": "Heroic Strike",
    "icon": "ability_rogue_ambush"
  },
  "53401": {
    "name": "Rabid",
    "icon": "ability_druid_berserk"
  },
  "53407": {
    "name": "Judgement of Justice",
    "icon": "ability_paladin_judgementred"
  },
  "53408": {
    "name": "Judgement of Wisdom",
    "icon": "ability_paladin_judgementblue"
  },
  "53434": {
    "name": "Call of the Wild",
    "icon": "ability_druid_kingofthejungle"
  },
  "53563": {
    "name": "Beacon of Light",
    "icon": "ability_paladin_beaconoflight"
  },
  "53595": {
    "name": "Hammer of the Righteous",
    "icon": "ability_paladin_hammeroftherighteous"
  },
  "53601": {
    "name": "Sacred Shield",
    "icon": "ability_paladin_blessedmending"
  },
  "53736": {
    "name": "Seal of Corruption",
    "icon": "spell_holy_sealofvengeance"
  },
  "53750": {
    "name": "Crazy Alchemist\'s Potion",
    "icon": "trade_alchemy"
  },
  "53755": {
    "name": "Flask of the Frost Wyrm",
    "icon": "inv_alchemy_endlessflask_04"
  },
  "53758": {
    "name": "Flask of Stoneblood",
    "icon": "inv_alchemy_endlessflask_05"
  },
  "53760": {
    "name": "Flask of Endless Rage",
    "icon": "inv_alchemy_endlessflask_06"
  },
  "53762": {
    "name": "Indestructible",
    "icon": "inv_alchemy_elixir_empty"
  },
  "53808": {
    "name": "Pygmy Oil",
    "icon": "inv_potion_07"
  },
  "53908": {
    "name": "Speed",
    "icon": "inv_alchemy_elixir_04"
  },
  "53909": {
    "name": "Wild Magic",
    "icon": "inv_alchemy_elixir_01"
  },
  "54043": {
    "name": "Retribution Aura",
    "icon": "spell_holy_auraoflight"
  },
  "54098": {
    "name": "Poison Bolt Volley",
    "icon": "spell_nature_corrosivebreath"
  },
  "54099": {
    "name": "Rain of Fire",
    "icon": "spell_shadow_rainoffire"
  },
  "54121": {
    "name": "Necrotic Poison",
    "icon": "ability_creature_poison_03"
  },
  "54122": {
    "name": "Poison Shock",
    "icon": "spell_nature_acid_01"
  },
  "54362": {
    "name": "Poison",
    "icon": "spell_nature_naturetouchdecay"
  },
  "54428": {
    "name": "Divine Plea",
    "icon": "spell_holy_aspiration"
  },
  "54646": {
    "name": "Focus Magic",
    "icon": "spell_arcane_studentofmagic"
  },
  "54710": {
    "name": "MOLL-E",
    "icon": "inv_misc_enggizmos_13"
  },
  "54757": {
    "name": "Pyro Rocket",
    "icon": "spell_fire_burnout"
  },
  "54758": {
    "name": "Hyperspeed Acceleration",
    "icon": "spell_shaman_elementaloath"
  },
  "54785": {
    "name": "Demon Charge",
    "icon": "ability_warstomp"
  },
  "55001": {
    "name": "Parachute",
    "icon": "spell_magic_featherfall"
  },
  "55198": {
    "name": "Tidal Force",
    "icon": "spell_frost_frostbolt"
  },
  "55233": {
    "name": "Vampiric Blood",
    "icon": "spell_shadow_lifedrain"
  },
  "55262": {
    "name": "Heart Strike",
    "icon": "inv_weapon_shortblade_40"
  },
  "55268": {
    "name": "Frost Strike",
    "icon": "spell_deathknight_empowerruneblade2"
  },
  "55271": {
    "name": "Scourge Strike",
    "icon": "spell_deathknight_scourgestrike"
  },
  "55342": {
    "name": "Mirror Image",
    "icon": "spell_magic_lesserinvisibilty"
  },
  "55360": {
    "name": "Living Bomb",
    "icon": "ability_mage_livingbomb"
  },
  "55503": {
    "name": "Lifeblood",
    "icon": "spell_nature_wispsplodegreen"
  },
  "55694": {
    "name": "Enraged Regeneration",
    "icon": "ability_warrior_focusedrage"
  },
  "56098": {
    "name": "Acid Spit",
    "icon": "spell_nature_corrosivebreath"
  },
  "56186": {
    "name": "Sapphire Owl",
    "icon": "inv_jewelcrafting_azureowl"
  },
  "56222": {
    "name": "Dark Command",
    "icon": "spell_nature_shamanrage"
  },
  "56350": {
    "name": "Saronite Bomb",
    "icon": "spell_fire_selfdestruct"
  },
  "56488": {
    "name": "Global Thermal Sapper Charge",
    "icon": "spell_fire_selfdestruct"
  },
  "56815": {
    "name": "Rune Strike",
    "icon": "spell_deathknight_darkconviction"
  },
  "57337": {
    "name": "Great Feast",
    "icon": "inv_misc_fork&knife"
  },
  "57397": {
    "name": "Fish Feast",
    "icon": "inv_misc_fork&knife"
  },
  "57567": {
    "name": "Fel Intelligence",
    "icon": "spell_shadow_brainwash"
  },
  "57623": {
    "name": "Horn of Winter",
    "icon": "inv_misc_horn_02"
  },
  "57722": {
    "name": "Totem of Wrath",
    "icon": "spell_fire_totemofwrath"
  },
  "57755": {
    "name": "Heroic Throw",
    "icon": "inv_axe_66"
  },
  "57823": {
    "name": "Revenge",
    "icon": "ability_warrior_revenge"
  },
  "57934": {
    "name": "Tricks of the Trade",
    "icon": "ability_rogue_tricksofthetrade"
  },
  "57946": {
    "name": "Life Tap",
    "icon": "spell_shadow_burningspirit"
  },
  "57960": {
    "name": "Water Shield",
    "icon": "ability_shaman_watershield"
  },
  "57994": {
    "name": "Wind Shear",
    "icon": "spell_nature_cyclone"
  },
  "58434": {
    "name": "Volley",
    "icon": "ability_marksmanship"
  },
  "58449": {
    "name": "Strength",
    "icon": "spell_nature_strength"
  },
  "58451": {
    "name": "Agility",
    "icon": "spell_holy_blessingofagility"
  },
  "58656": {
    "name": "Flametongue Totem",
    "icon": "spell_nature_guardianward"
  },
  "58659": {
    "name": "Ritual of Refreshment",
    "icon": "spell_arcane_massdispel"
  },
  "58660": {
    "name": "Conjure Refreshment",
    "icon": "inv_misc_food_32"
  },
  "58704": {
    "name": "Searing Totem",
    "icon": "spell_fire_searingtotem"
  },
  "58734": {
    "name": "Magma Totem",
    "icon": "spell_fire_selfdestruct"
  },
  "58749": {
    "name": "Nature Resistance Totem",
    "icon": "spell_nature_natureresistancetotem"
  },
  "58753": {
    "name": "Stoneskin Totem",
    "icon": "spell_nature_stoneskintotem"
  },
  "58757": {
    "name": "Healing Stream Totem",
    "icon": "inv_spear_04"
  },
  "58790": {
    "name": "Flametongue Weapon",
    "icon": "spell_fire_flametounge"
  },
  "58804": {
    "name": "Windfury Weapon",
    "icon": "spell_nature_cyclone"
  },
  "58875": {
    "name": "Spirit Walk",
    "icon": "ability_tracking"
  },
  "58887": {
    "name": "Ritual of Souls",
    "icon": "spell_shadow_shadesofdarkness"
  },
  "58984": {
    "name": "Shadowmeld",
    "icon": "ability_ambush"
  },
  "59159": {
    "name": "Thunderstorm",
    "icon": "spell_shaman_thunderstorm"
  },
  "59192": {
    "name": "Hateful Strike",
    "icon": "trade_engineering"
  },
  "59547": {
    "name": "Gift of the Naaru",
    "icon": "spell_holy_holyprotection"
  },
  "59658": {
    "name": "Argent Heroism",
    "icon": "spell_holy_mindvision"
  },
  "59752": {
    "name": "Every Man for Himself",
    "icon": "spell_shadow_charm"
  },
  "59757": {
    "name": "Figurine - Monarch Crab",
    "icon": "ability_rogue_fleetfooted"
  },
  "60053": {
    "name": "Explosive Shot",
    "icon": "ability_hunter_explosiveshot"
  },
  "60103": {
    "name": "Lava Lash",
    "icon": "ability_shaman_lavalash"
  },
  "60122": {
    "name": "Baby Spice",
    "icon": "inv_misc_powder_green"
  },
  "60192": {
    "name": "Freezing Arrow",
    "icon": "spell_frost_chillingbolt"
  },
  "60215": {
    "name": "Lavanthor\'s Talisman",
    "icon": "inv_trinket_naxxramas05"
  },
  "60305": {
    "name": "Heart of a Dragon",
    "icon": "spell_shadow_deathpact"
  },
  "60319": {
    "name": "Mark of Norgannon",
    "icon": "ability_hunter_readiness"
  },
  "60346": {
    "name": "Lightning Speed",
    "icon": "inv_alchemy_potion_04"
  },
  "60347": {
    "name": "Mighty Thoughts",
    "icon": "inv_potion_161"
  },
  "60480": {
    "name": "Mark of the War Prisoner",
    "icon": "inv_trinket_naxxramas06"
  },
  "60970": {
    "name": "Heroic Fury",
    "icon": "ability_heroicleap"
  },
  "61006": {
    "name": "Kill Shot",
    "icon": "ability_hunter_assassinate2"
  },
  "61024": {
    "name": "Dalaran Intellect",
    "icon": "achievement_dungeon_theviolethold"
  },
  "61290": {
    "name": "Shadowflame",
    "icon": "ability_warlock_shadowflame"
  },
  "61301": {
    "name": "Riptide",
    "icon": "spell_nature_riptide"
  },
  "61316": {
    "name": "Dalaran Brilliance",
    "icon": "achievement_dungeon_theviolethold_heroic"
  },
  "61336": {
    "name": "Survival Instincts",
    "icon": "ability_druid_tigersroar"
  },
  "61411": {
    "name": "Shield of Righteousness",
    "icon": "ability_paladin_shieldofvengeance"
  },
  "61657": {
    "name": "Fire Nova",
    "icon": "spell_fire_sealoffire"
  },
  "61684": {
    "name": "Dash",
    "icon": "ability_druid_dash"
  },
  "61847": {
    "name": "Aspect of the Dragonhawk",
    "icon": "ability_hunter_pet_dragonhawk"
  },
  "62078": {
    "name": "Swipe (Cat)",
    "icon": "inv_misc_monsterclaw_03"
  },
  "62124": {
    "name": "Hand of Reckoning",
    "icon": "spell_holy_unyieldingfaith"
  },
  "62286": {
    "name": "Tar",
    "icon": "ability_vehicle_oiljets"
  },
  "62299": {
    "name": "Speed Boost",
    "icon": "ability_vehicle_rocketboost"
  },
  "62306": {
    "name": "Hurl Boulder",
    "icon": "ability_vehicle_demolisherflamecatapult"
  },
  "62317": {
    "name": "Devastate",
    "icon": "inv_sword_11"
  },
  "62345": {
    "name": "Ram",
    "icon": "ability_vehicle_siegeengineram"
  },
  "62346": {
    "name": "Steam Rush",
    "icon": "ability_vehicle_siegeenginecharge"
  },
  "62358": {
    "name": "Fire Cannon",
    "icon": "ability_vehicle_siegeenginecannon"
  },
  "62359": {
    "name": "Anti-Air Rocket",
    "icon": "inv_misc_missilesmall_red"
  },
  "62380": {
    "name": "Lesser Flask of Resistance",
    "icon": "inv_potion_118"
  },
  "62490": {
    "name": "Hurl Pyrite Barrel",
    "icon": "ability_vehicle_liquidpyrite_blue"
  },
  "62634": {
    "name": "Mortar",
    "icon": "ability_vehicle_siegeenginecannon"
  },
  "62757": {
    "name": "Call Stabled Pet",
    "icon": "inv_box_petcarrier_01"
  },
  "62974": {
    "name": "Sonic Horn",
    "icon": "ability_vehicle_sonicshockwave"
  },
  "63560": {
    "name": "Ghoul Frenzy",
    "icon": "ability_ghoulfrenzy"
  },
  "63672": {
    "name": "Black Arrow",
    "icon": "spell_shadow_painspike"
  },
  "63818": {
    "name": "Rumble",
    "icon": "spell_nature_earthquake"
  },
  "63978": {
    "name": "Stone Nova",
    "icon": "spell_nature_earthquake"
  },
  "64030": {
    "name": "Antechamber Teleport",
    "icon": "trade_engineering"
  },
  "64205": {
    "name": "Divine Sacrifice",
    "icon": "spell_holy_powerwordbarrier"
  },
  "64395": {
    "name": "Quantum Strike",
    "icon": "ability_warrior_punishingblow"
  },
  "64412": {
    "name": "Phase Punch",
    "icon": "spell_shadow_twistedfaith"
  },
  "64495": {
    "name": "Furious Howl",
    "icon": "ability_hunter_pet_wolf"
  },
  "64638": {
    "name": "Acidic Bite",
    "icon": "ability_creature_poison_01"
  },
  "64707": {
    "name": "Scale of Fates",
    "icon": "inv_spiritshard_02"
  },
  "64712": {
    "name": "Living Flame",
    "icon": "spell_fire_burnout"
  },
  "64763": {
    "name": "Heart of Iron",
    "icon": "ability_rogue_fleetfooted"
  },
  "64800": {
    "name": "Wrathstone",
    "icon": "inv_pet_scorchedstone"
  },
  "64843": {
    "name": "Divine Hymn",
    "icon": "spell_holy_divinehymn"
  },
  "64901": {
    "name": "Hymn of Hope",
    "icon": "spell_holy_symbolofhope"
  },
  "64979": {
    "name": "Anti-Air Rocket",
    "icon": "inv_misc_missilesmall_red"
  },
  "64999": {
    "name": "Meteoric Inspiration",
    "icon": "inv_misc_gem_azuredraenite_01"
  },
  "65543": {
    "name": "Psychic Scream",
    "icon": "spell_shadow_psychicscream"
  },
  "65547": {
    "name": "PvP Trinket",
    "icon": "spell_holy_dispelmagic"
  },
  "65790": {
    "name": "Counterspell",
    "icon": "spell_frost_iceshock"
  },
  "65792": {
    "name": "Frost Nova",
    "icon": "spell_frost_frostnova"
  },
  "65793": {
    "name": "Blink",
    "icon": "spell_arcane_blink"
  },
  "65815": {
    "name": "Curse of Exhaustion",
    "icon": "spell_shadow_grimward"
  },
  "65869": {
    "name": "Disengage",
    "icon": "ability_rogue_feint"
  },
  "65870": {
    "name": "Disengage",
    "icon": "inv_boots_cloth_15"
  },
  "65880": {
    "name": "Frost Trap",
    "icon": "spell_frost_freezingbreath"
  },
  "65924": {
    "name": "Overpower",
    "icon": "ability_meleedamage"
  },
  "65935": {
    "name": "Disarm",
    "icon": "ability_warrior_disarm"
  },
  "65936": {
    "name": "Sunder Armor",
    "icon": "ability_warrior_sunder"
  },
  "65947": {
    "name": "Bladestorm",
    "icon": "ability_warrior_bladestorm"
  },
  "65954": {
    "name": "Hemorrhage",
    "icon": "spell_shadow_lifedrain"
  },
  "65962": {
    "name": "Wound Poison",
    "icon": "inv_misc_herb_16"
  },
  "65970": {
    "name": "Stormstrike",
    "icon": "ability_shaman_stormstrike"
  },
  "65974": {
    "name": "Lava Lash",
    "icon": "ability_shaman_lavalash"
  },
  "65976": {
    "name": "Windfury",
    "icon": "spell_nature_cyclone"
  },
  "66003": {
    "name": "Crusader Strike",
    "icon": "spell_holy_crusaderstrike"
  },
  "66006": {
    "name": "Divine Storm",
    "icon": "ability_paladin_divinestorm"
  },
  "66012": {
    "name": "Freezing Slash",
    "icon": "spell_frost_frostblast"
  },
  "66018": {
    "name": "Strangulate",
    "icon": "spell_shadow_soulleech_3"
  },
  "66020": {
    "name": "Chains of Ice",
    "icon": "spell_frost_chainsofice"
  },
  "66023": {
    "name": "Icebound Fortitude",
    "icon": "spell_deathknight_iceboundfortitude"
  },
  "66071": {
    "name": "Nature\'s Grasp",
    "icon": "spell_nature_natureswrath"
  },
  "66092": {
    "name": "Determination",
    "icon": "spell_shadow_shadowworddominate"
  },
  "66193": {
    "name": "Permafrost",
    "icon": "spell_frost_glacier"
  },
  "66283": {
    "name": "Spinning Pain Spike",
    "icon": "spell_shadow_shadowmend"
  },
  "66407": {
    "name": "Head Crack",
    "icon": "ability_rogue_kidneyshot"
  },
  "66408": {
    "name": "Batter",
    "icon": "ability_kick"
  },
  "66477": {
    "name": "Bountiful Feast",
    "icon": "inv_misc_fork&knife"
  },
  "66494": {
    "name": "Fel Streak",
    "icon": "spell_fire_felhellfire"
  },
  "66613": {
    "name": "Hammer of Justice",
    "icon": "spell_holy_sealofmight"
  },
  "66842": {
    "name": "Call of the Elements",
    "icon": "spell_shaman_dropall_01"
  },
  "66843": {
    "name": "Call of the Ancestors",
    "icon": "spell_shaman_dropall_02"
  },
  "66844": {
    "name": "Call of the Spirits",
    "icon": "spell_shaman_dropall_03"
  },
  "67019": {
    "name": "Flask of the North",
    "icon": "inv_alchemy_endlessflask_05"
  },
  "67029": {
    "name": "Fel Lightning",
    "icon": "spell_fire_felflamebolt"
  },
  "67030": {
    "name": "Fel Lightning",
    "icon": "spell_fire_felflamebolt"
  },
  "67031": {
    "name": "Fel Lightning",
    "icon": "spell_fire_felflamebolt"
  },
  "67047": {
    "name": "Fel Inferno",
    "icon": "spell_fire_felimmolation"
  },
  "67049": {
    "name": "Incinerate Flesh",
    "icon": "ability_warlock_fireandbrimstone"
  },
  "67050": {
    "name": "Incinerate Flesh",
    "icon": "ability_warlock_fireandbrimstone"
  },
  "67051": {
    "name": "Incinerate Flesh",
    "icon": "ability_warlock_fireandbrimstone"
  },
  "67099": {
    "name": "Shivan Slash",
    "icon": "ability_warrior_incite"
  },
  "67108": {
    "name": "Nether Power",
    "icon": "ability_mage_netherwindpresence"
  },
  "67283": {
    "name": "Touch of Darkness",
    "icon": "spell_shadow_chilltouch"
  },
  "67298": {
    "name": "Touch of Light",
    "icon": "ability_paladin_infusionoflight"
  },
  "67309": {
    "name": "Twin Spike",
    "icon": "spell_shadow_painspike"
  },
  "67311": {
    "name": "Twin Spike",
    "icon": "spell_shadow_painspike"
  },
  "67312": {
    "name": "Twin Spike",
    "icon": "ability_paladin_sheathoflight"
  },
  "67314": {
    "name": "Twin Spike",
    "icon": "ability_paladin_sheathoflight"
  },
  "67393": {
    "name": "Eject Passenger",
    "icon": "ability_vehicle_launchplayer"
  },
  "67477": {
    "name": "Impale",
    "icon": "ability_throw"
  },
  "67478": {
    "name": "Impale",
    "icon": "ability_throw"
  },
  "67479": {
    "name": "Impale",
    "icon": "ability_throw"
  },
  "67490": {
    "name": "Runic Mana Injector",
    "icon": "trade_engineering"
  },
  "67574": {
    "name": "Pursued by Anub\'arak",
    "icon": "ability_hunter_snipershot"
  },
  "67643": {
    "name": "Slime Pool",
    "icon": "spell_nature_abolishmagic"
  },
  "67652": {
    "name": "Arctic Breath",
    "icon": "spell_frost_frostnova"
  },
  "67654": {
    "name": "Ferocious Butt",
    "icon": "inv_misc_monsterhorn_07"
  },
  "67656": {
    "name": "Ferocious Butt",
    "icon": "inv_misc_monsterhorn_07"
  },
  "67665": {
    "name": "Whirl",
    "icon": "ability_whirlwind"
  },
  "67683": {
    "name": "Celerity",
    "icon": "ability_rogue_sprint"
  },
  "67684": {
    "name": "Hospitality",
    "icon": "spell_holy_impholyconcentration"
  },
  "67695": {
    "name": "Rage",
    "icon": "ability_warrior_rampage"
  },
  "67699": {
    "name": "Fortitude",
    "icon": "spell_holy_mindvision"
  },
  "67700": {
    "name": "Penetrating Cold",
    "icon": "spell_frost_coldhearted"
  },
  "67738": {
    "name": "Rising Fury",
    "icon": "ability_warrior_strengthofarms"
  },
  "67744": {
    "name": "Volatile Power",
    "icon": "spell_arcane_arcane03"
  },
  "67747": {
    "name": "Rising Fury",
    "icon": "ability_warrior_strengthofarms"
  },
  "67753": {
    "name": "Fortitude",
    "icon": "spell_holy_mindvision"
  },
  "67826": {
    "name": "Jeeves",
    "icon": "inv_pet_lilsmoky"
  },
  "67855": {
    "name": "Permafrost",
    "icon": "spell_frost_glacier"
  },
  "67857": {
    "name": "Permafrost",
    "icon": "spell_frost_glacier"
  },
  "67865": {
    "name": "Trample",
    "icon": "trade_engineering"
  },
  "67900": {
    "name": "Nether Portal",
    "icon": "ability_rogue_envelopingshadows"
  },
  "67903": {
    "name": "Infernal Eruption",
    "icon": "spell_fire_felcano"
  },
  "67929": {
    "name": "Death Coil",
    "icon": "spell_shadow_deathcoil"
  },
  "67931": {
    "name": "Death Coil",
    "icon": "spell_shadow_deathcoil"
  },
  "67935": {
    "name": "Frost Strike",
    "icon": "spell_deathknight_empowerruneblade2"
  },
  "67937": {
    "name": "Frost Strike",
    "icon": "spell_deathknight_empowerruneblade2"
  },
  "67938": {
    "name": "Icy Touch",
    "icon": "spell_deathknight_icetouch"
  },
  "67940": {
    "name": "Icy Touch",
    "icon": "spell_deathknight_icetouch"
  },
  "67994": {
    "name": "Arcane Barrage",
    "icon": "ability_mage_arcanebarrage"
  },
  "67996": {
    "name": "Arcane Barrage",
    "icon": "ability_mage_arcanebarrage"
  },
  "68000": {
    "name": "Arcane Explosion",
    "icon": "spell_nature_wispsplode"
  },
  "68002": {
    "name": "Arcane Explosion",
    "icon": "spell_nature_wispsplode"
  },
  "68019": {
    "name": "Judgement of Command",
    "icon": "ability_warrior_innerrage"
  },
  "68042": {
    "name": "Mind Flay",
    "icon": "spell_shadow_siphonmana"
  },
  "68043": {
    "name": "Mind Flay",
    "icon": "spell_shadow_siphonmana"
  },
  "68044": {
    "name": "Mind Flay",
    "icon": "spell_shadow_siphonmana"
  },
  "68088": {
    "name": "Shadow Word: Pain",
    "icon": "spell_shadow_shadowwordpain"
  },
  "68099": {
    "name": "Fan of Knives",
    "icon": "ability_rogue_fanofknives"
  },
  "68100": {
    "name": "Earth Shock",
    "icon": "spell_nature_earthshock"
  },
  "68102": {
    "name": "Earth Shock",
    "icon": "spell_nature_earthshock"
  },
  "68123": {
    "name": "Legion Flame",
    "icon": "spell_fire_felimmolation"
  },
  "68124": {
    "name": "Legion Flame",
    "icon": "spell_fire_felimmolation"
  },
  "68125": {
    "name": "Legion Flame",
    "icon": "spell_fire_felimmolation"
  },
  "68133": {
    "name": "Corruption",
    "icon": "spell_shadow_abominationexplosion"
  },
  "68135": {
    "name": "Corruption",
    "icon": "spell_shadow_abominationexplosion"
  },
  "68136": {
    "name": "Curse of Agony",
    "icon": "spell_shadow_curseofsargeras"
  },
  "68138": {
    "name": "Curse of Agony",
    "icon": "spell_shadow_curseofsargeras"
  },
  "68147": {
    "name": "Hellfire",
    "icon": "spell_fire_incinerate"
  },
  "68186": {
    "name": "Anub\'arak Scarab Achievement 10",
    "icon": "inv_misc_missilesmall_red"
  },
  "68328": {
    "name": "Portal to Dalaran",
    "icon": "spell_arcane_portalironforge"
  },
  "68510": {
    "name": "Penetrating Cold",
    "icon": "spell_frost_coldhearted"
  },
  "68515": {
    "name": "Anub\'arak Scarab Achievement 25",
    "icon": "inv_misc_missilesmall_red"
  },
  "68755": {
    "name": "Death Grip",
    "icon": "spell_deathknight_strangulate"
  },
  "68761": {
    "name": "Shadowstep",
    "icon": "trade_engineering"
  },
  "68762": {
    "name": "Charge",
    "icon": "ability_warrior_charge"
  },
  "68764": {
    "name": "Charge",
    "icon": "ability_warrior_charge"
  },
  "68782": {
    "name": "Mortal Strike",
    "icon": "ability_warrior_savageblow"
  },
  "68784": {
    "name": "Mortal Strike",
    "icon": "ability_warrior_savageblow"
  },
  "68868": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "69055": {
    "name": "Bone Slice",
    "icon": "ability_warrior_cleave"
  },
  "69200": {
    "name": "Raging Spirit",
    "icon": "ability_warrior_endlessrage"
  },
  "69382": {
    "name": "Light\'s Favor",
    "icon": "spell_holy_healingaura"
  },
  "69401": {
    "name": "Incinerating Blast",
    "icon": "ability_vehicle_demolisherflamecatapult"
  },
  "69409": {
    "name": "Soul Reaper",
    "icon": "ability_rogue_shadowdance"
  },
  "69492": {
    "name": "Shadow Cleave",
    "icon": "ability_warrior_cleave"
  },
  "69652": {
    "name": "Bladestorm",
    "icon": "ability_warrior_bladestorm"
  },
  "69762": {
    "name": "Unchained Magic",
    "icon": "spell_arcane_focusedpower"
  },
  "69776": {
    "name": "Sticky Ooze",
    "icon": "spell_shadow_plaguecloud"
  },
  "69901": {
    "name": "Spell Reflect",
    "icon": "ability_warrior_shieldreflection"
  },
  "69904": {
    "name": "Blink",
    "icon": "spell_arcane_blink"
  },
  "69912": {
    "name": "Plague Strike",
    "icon": "spell_deathknight_empowerruneblade"
  },
  "69916": {
    "name": "Icy Touch",
    "icon": "spell_deathknight_icetouch"
  },
  "69929": {
    "name": "Spirit Stream",
    "icon": "inv_misc_herb_frostlotus"
  },
  "69965": {
    "name": "Thunderclap",
    "icon": "ability_thunderclap"
  },
  "70109": {
    "name": "Permeating Chill",
    "icon": "spell_frost_coldhearted"
  },
  "70117": {
    "name": "Icy Grip",
    "icon": "spell_frost_arcticwinds"
  },
  "70174": {
    "name": "Incinerating Blast",
    "icon": "ability_vehicle_demolisherflamecatapult"
  },
  "70299": {
    "name": "Siphon Essence",
    "icon": "spell_shadow_lifedrain"
  },
  "70309": {
    "name": "Rending Throw",
    "icon": "ability_gouge"
  },
  "70341": {
    "name": "Slime Puddle",
    "icon": "ability_creature_poison_02"
  },
  "70360": {
    "name": "Eat Ooze",
    "icon": "spell_fire_felflamebreath"
  },
  "70423": {
    "name": "Vampiric Curse",
    "icon": "spell_shadow_improvedvampiricembrace"
  },
  "70432": {
    "name": "Blood Sap",
    "icon": "ability_sap"
  },
  "70437": {
    "name": "Unholy Strike",
    "icon": "ability_rogue_rupture"
  },
  "70588": {
    "name": "Suppression",
    "icon": "spell_shadow_shadowembrace"
  },
  "70671": {
    "name": "Leeching Rot",
    "icon": "ability_creature_disease_02"
  },
  "70674": {
    "name": "Vampiric Might",
    "icon": "ability_warlock_improvedsoulleech"
  },
  "70750": {
    "name": "Battle Shout",
    "icon": "ability_warrior_battleshout"
  },
  "70768": {
    "name": "Shroud of the Occult",
    "icon": "spell_shadow_twistedfaith"
  },
  "70769": {
    "name": "Divine Storm!",
    "icon": "ability_paladin_divinestorm"
  },
  "70814": {
    "name": "Bone Slice",
    "icon": "ability_warrior_cleave"
  },
  "70836": {
    "name": "Bone Storm",
    "icon": "ability_gouge"
  },
  "71052": {
    "name": "Frost Aura",
    "icon": "spell_frost_frostshock"
  },
  "71090": {
    "name": "Bubbling Pus",
    "icon": "spell_nature_acid_01"
  },
  "71103": {
    "name": "Combobulating Spray",
    "icon": "inv_misc_slime_01"
  },
  "71106": {
    "name": "Shadow Nova",
    "icon": "spell_shadow_antishadow"
  },
  "71112": {
    "name": "Curse of Agony",
    "icon": "spell_shadow_curseofsargeras"
  },
  "71115": {
    "name": "Massive Stomp",
    "icon": "ability_warstomp"
  },
  "71118": {
    "name": "Blizzard",
    "icon": "spell_frost_icestorm"
  },
  "71119": {
    "name": "Blood Plague",
    "icon": "spell_deathknight_bloodplague"
  },
  "71122": {
    "name": "Consecration",
    "icon": "spell_holy_innerfire"
  },
  "71124": {
    "name": "Curse of Doom",
    "icon": "spell_shadow_auraofdarkness"
  },
  "71127": {
    "name": "Mortal Wound",
    "icon": "ability_criticalstrike"
  },
  "71128": {
    "name": "Fan of Knives",
    "icon": "ability_rogue_fanofknives"
  },
  "71129": {
    "name": "Frost Fever",
    "icon": "spell_deathknight_frostfever"
  },
  "71134": {
    "name": "Holy Wrath",
    "icon": "spell_holy_excorcism"
  },
  "71142": {
    "name": "Rejuvenation",
    "icon": "spell_nature_preservation"
  },
  "71145": {
    "name": "Sinister Strike",
    "icon": "spell_shadow_ritualofsacrifice"
  },
  "71147": {
    "name": "Thunderclap",
    "icon": "ability_thunderclap"
  },
  "71150": {
    "name": "Plague Cloud",
    "icon": "spell_shadow_plaguecloud"
  },
  "71151": {
    "name": "Blast Wave",
    "icon": "spell_holy_excorcism_02"
  },
  "71154": {
    "name": "Rend Flesh",
    "icon": "ability_druid_mangle.tga"
  },
  "71155": {
    "name": "Vampire Rush",
    "icon": "ability_warrior_charge"
  },
  "71159": {
    "name": "Awaken Plagued Zombies",
    "icon": "spell_shadow_raisedead"
  },
  "71164": {
    "name": "Leaping Face Maul",
    "icon": "trade_engineering"
  },
  "71204": {
    "name": "Touch of Insignificance",
    "icon": "ability_hibernation"
  },
  "71221": {
    "name": "Gas Spore",
    "icon": "spell_shadow_creepingplague"
  },
  "71249": {
    "name": "Ice Trap",
    "icon": "spell_frost_chainsofice"
  },
  "71251": {
    "name": "Rapid Shot",
    "icon": "ability_hunter_runningshot"
  },
  "71252": {
    "name": "Volley",
    "icon": "ability_hunter_quickshot"
  },
  "71255": {
    "name": "Choking Gas Bomb",
    "icon": "spell_shadow_mindbomb"
  },
  "71257": {
    "name": "Barbaric Strike",
    "icon": "ability_warrior_bloodbath"
  },
  "71258": {
    "name": "Adrenaline Rush",
    "icon": "ability_rogue_bloodyeye"
  },
  "71264": {
    "name": "Swarming Shadows",
    "icon": "ability_rogue_shadowdance"
  },
  "71274": {
    "name": "Frozen Orb",
    "icon": "spell_frost_frozencore"
  },
  "71289": {
    "name": "Dominate Mind",
    "icon": "inv_belt_18"
  },
  "71300": {
    "name": "Death\'s Embrace",
    "icon": "inv_misc_shadowegg"
  },
  "71302": {
    "name": "Awaken Ymirjar Fallen",
    "icon": "spell_shadow_raisedead"
  },
  "71317": {
    "name": "Glacial Strike",
    "icon": "spell_deathknight_empowerruneblade2"
  },
  "71320": {
    "name": "Frost Nova",
    "icon": "spell_frost_frostnova"
  },
  "71327": {
    "name": "Web",
    "icon": "ability_ensnare"
  },
  "71340": {
    "name": "Pact of the Darkfallen",
    "icon": "spell_shadow_destructivesoul"
  },
  "71357": {
    "name": "Order Whelp",
    "icon": "trade_engineering"
  },
  "71370": {
    "name": "Tail Sweep",
    "icon": "inv_misc_monsterscales_05"
  },
  "71463": {
    "name": "Aether Shield",
    "icon": "spell_holy_powerwordshield"
  },
  "71466": {
    "name": "Hurl Spear",
    "icon": "spell_frost_iceshard"
  },
  "71477": {
    "name": "Vampiric Bite",
    "icon": "inv_misc_monsterfang_01"
  },
  "71503": {
    "name": "Mutated Transformation",
    "icon": "ability_rogue_deviouspoisons"
  },
  "71510": {
    "name": "Blood Mirror",
    "icon": "spell_shadow_improvedvampiricembrace"
  },
  "71552": {
    "name": "Mortal Strike",
    "icon": "ability_warrior_savageblow"
  },
  "71586": {
    "name": "Hardened Skin",
    "icon": "spell_holy_devotionaura"
  },
  "71614": {
    "name": "Ice Lock",
    "icon": "spell_frost_chainsofice"
  },
  "71626": {
    "name": "Delirious Slash",
    "icon": "ability_warlock_everlastingaffliction"
  },
  "71635": {
    "name": "Aegis of Dalaran",
    "icon": "spell_shadow_antimagicshell"
  },
  "71638": {
    "name": "Aegis of Dalaran",
    "icon": "spell_shadow_antimagicshell"
  },
  "71730": {
    "name": "Lay Waste",
    "icon": "achievement_zone_hellfirepeninsula_01"
  },
  "71741": {
    "name": "Mana Void",
    "icon": "inv_enchant_voidsphere"
  },
  "71801": {
    "name": "Rush",
    "icon": "spell_shadow_vampiricaura"
  },
  "71820": {
    "name": "Twilight Bloodbolt",
    "icon": "spell_shadow_felmending"
  },
  "71821": {
    "name": "Twilight Bloodbolt",
    "icon": "spell_shadow_felmending"
  },
  "71924": {
    "name": "Plague Strike",
    "icon": "spell_deathknight_empowerruneblade"
  },
  "71943": {
    "name": "Shadow Resonance",
    "icon": "spell_shadow_rune"
  },
  "72026": {
    "name": "Gut Spray",
    "icon": "spell_shadow_corpseexplode"
  },
  "72110": {
    "name": "Death and Decay",
    "icon": "spell_shadow_deathanddecay"
  },
  "72172": {
    "name": "Call Blood Beast",
    "icon": "ability_creature_cursed_04"
  },
  "72173": {
    "name": "Call Blood Beast",
    "icon": "spell_shadow_rune"
  },
  "72176": {
    "name": "Blood Link",
    "icon": "spell_deathknight_bloodtap"
  },
  "72336": {
    "name": "Amplify Magic",
    "icon": "spell_holy_flashheal"
  },
  "72356": {
    "name": "Call Blood Beast",
    "icon": "spell_shadow_rune"
  },
  "72357": {
    "name": "Call Blood Beast",
    "icon": "spell_shadow_rune"
  },
  "72358": {
    "name": "Call Blood Beast",
    "icon": "spell_shadow_rune"
  },
  "72410": {
    "name": "Rune of Blood",
    "icon": "spell_deathknight_deathstrike"
  },
  "72424": {
    "name": "Life Infusion",
    "icon": "spell_nature_wispsplodegreen"
  },
  "72443": {
    "name": "Boiling Blood",
    "icon": "spell_deathknight_bloodboil"
  },
  "72492": {
    "name": "Necrotic Strike",
    "icon": "spell_deathknight_plaguestrike"
  },
  "72494": {
    "name": "Shadow Cleave",
    "icon": "ability_warrior_cleave"
  },
  "72510": {
    "name": "Mutated Transformation",
    "icon": "ability_rogue_deviouspoisons"
  },
  "72527": {
    "name": "Eat Ooze",
    "icon": "spell_fire_felflamebreath"
  },
  "72571": {
    "name": "Wounding Strike",
    "icon": "ability_warrior_savageblow"
  },
  "72769": {
    "name": "Scent of Blood",
    "icon": "spell_shadow_felmending"
  },
  "72791": {
    "name": "Flames",
    "icon": "spell_fire_sealoffire"
  },
  "72856": {
    "name": "Unbound Plague",
    "icon": "spell_shadow_corpseexplode"
  },
  "72908": {
    "name": "Frostbolt Volley",
    "icon": "spell_frost_frostbolt02"
  },
  "73020": {
    "name": "Vile Gas",
    "icon": "ability_creature_cursed_01"
  },
  "73023": {
    "name": "Mutated Infection",
    "icon": "ability_creature_disease_02"
  },
  "73070": {
    "name": "Incite Terror",
    "icon": "spell_shadow_deathscream"
  },
  "73326": {
    "name": "Tabard of the Lightbringer",
    "icon": "spell_holy_divineprovidence"
  },
  "73799": {
    "name": "Soul Reaper",
    "icon": "ability_rogue_shadowdance"
  },
  "73804": {
    "name": "Explosion",
    "icon": "spell_shadow_shadowfury"
  },
  "73805": {
    "name": "Explosion",
    "icon": "spell_shadow_shadowfury"
  },
  "73914": {
    "name": "Necrotic Plague",
    "icon": "ability_creature_disease_02"
  },
  "74281": {
    "name": "Malleable Goo",
    "icon": "inv_misc_herb_evergreenmoss"
  },
  "74297": {
    "name": "Harvest Souls",
    "icon": "spell_deathknight_strangulate"
  },
  "74367": {
    "name": "Cleave Armor",
    "icon": "ability_warrior_sunder"
  },
  "74502": {
    "name": "Enervating Brand",
    "icon": "ability_creature_cursed_04"
  },
  "74524": {
    "name": "Cleave",
    "icon": "ability_warrior_cleave"
  },
  "74531": {
    "name": "Tail Lash",
    "icon": "ability_criticalstrike"
  },
  "74562": {
    "name": "Fiery Combustion",
    "icon": "ability_mage_livingbomb"
  },
  "74792": {
    "name": "Soul Consumption",
    "icon": "spell_shadow_soulleech_3"
  },
  "75418": {
    "name": "Shockwave",
    "icon": "ability_warrior_shockwave"
  },
  "75490": {
    "name": "Eyes of Twilight",
    "icon": "inv_misc_rubysanctum1"
  },
  "75495": {
    "name": "Eyes of Twilight",
    "icon": "inv_misc_rubysanctum1"
  },
  "75879": {
    "name": "Meteor Strike",
    "icon": "spell_fire_meteorstorm"
  }
}

# flags checkboxes to hide data from chart 
# if spell row empty = hide



# 22-09-09--19-56--Imnotadk--Lordaeron
# 22-04-29--21-04--Nomadra--Lordaeron
# 4/29 23:14:36.536,SPELL_DAMAGE,0x060000000040F817,Nomadra,0xF130008EF5000C6B,The Lich King,48465,Starfire,0x40,20912,0,64,0,0,0,1,nil,nil
# 4/29 23:14:36.716,SPELL_PERIODIC_HEAL,0x06000000003C4477,Wakemeup,0x060000000040F817,Nomadra,15290,Vampiric Embrace,0x20,196,196,0,nil
# 4/29 23:14:37.692,UNIT_DIED,0x0000000000000000,nil,0x060000000040F817,Nomadra
NIL = "0x0000000000000000"


def to_int(s: str):
    minutes, seconds = s.split(":", 1)
    return int(minutes) * 600 + int(seconds.replace('.', ''))

def to_float(s: str):
    minutes, seconds = s[-9:-2].split(":", 1)
    return int(minutes) * 60 + float(seconds)

def get_positive_delta():
    return

def to_str(k: float):
    seconds = k % 60
    minutes = k // 60
    return f"{minutes:0>2.0f}:{seconds:0>4.1f}"

def convert_keys(data: dict[str, int]):
    FIRST_KEY = to_int(list(data)[0])
    for k in list(data):
        new_key = to_int(k) - FIRST_KEY
        if new_key < 0:
            new_key = new_key + 36000
        data[new_key] = data.pop(k)

FLAGS2 = {
    'SPELL_PERIODIC_HEAL',
}
def get_history(logs: list[str], guid):
    def get_delta(current_ts: str):
        new_key = to_float(current_ts) - FIRST_KEY
        if new_key < 0:
            new_key = new_key + 3600
        return new_key
    
    def get_percentage(from_start: float):
        percent_from_start = from_start / FIGHT_DURATION * 100
        return f"{percent_from_start}%"

    history = defaultdict(list)
    flags = set()
    FIRST_KEY = to_float(logs[0].split(",", 1)[0])
    FIGHT_DURATION = get_delta(logs[-1].split(",", 1)[0])

    for line in logs:
        if guid not in line:
            continue
        try:
            # timestamp, flag, sGUID, _, tGUID, _, spell_id, *o = line.split(',')
            timestamp, flag, sGUID, _, tGUID, tName, spell_id, _, _, *o = line.split(',')
            if sGUID != guid:
                continue
            if flag in FLAGS2:
                continue
            # if tGUID[:3] != '0xF':
            #     continue
            # print(o)
            # q.append([timestamp, spell_id, flag, o])
            # q[flag].append([timestamp, spell_id, flag, o])
            _delta = get_delta(timestamp)
            history[spell_id].append([get_percentage(_delta), to_str(_delta), flag, tName, o])
            flags.add(flag)
        except:
            # PARTY_KILL UNIT_DIED
            # print(line)
            continue
    
    return {
        "DATA": history,
        "FLAGS": flags,
    }



def get_spell_name(spellid):
    try:
        return SPELLS[spellid]['name']
    except:
        return ""
# 48468 Insect Swarm
def main():
    import logs_main
    name = "22-04-29--21-04--Nomadra--Lordaeron"
    report = logs_main.THE_LOGS(name)
    enc_data = report.get_enc_data()
    # tlk = "The Lich King"
    # s, f = enc_data[tlk][-2]
    s, f = enc_data["Festergut"][-1]
    logs_slice = report.get_logs(s, f)
    # logs_slice = report.get_logs()
    name = "Nomadra"
    guid = report.name_to_guid(name)
    
    z = get_history(logs_slice, guid)
    # print(z["FLAGS"])
    # return

    for spellid, _asdasd in z['DATA'].items():
        print()
        print(spellid, report.get_spell_name(spellid))
        for ts, flag, target, etc in _asdasd:
            # if flag not in FLAGS2:
                # continue
            print(f"{ts:>18} {flag:<25} {target:<35} {etc}")

    return z

if __name__ == "__main__":
    main()
