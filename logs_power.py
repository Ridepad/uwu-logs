from collections import defaultdict

POWER_TYPES = {
    '0': 'mana',
    # Mana will range from 0 to the maximum mana a unit has. Player mana pools are calculated based on a base mana pool plus a certain amount given by the Intellect stat. This is the default power type for most non-player units, although there are exceptions. As of World of Warcraft: Legion Legion, mana is used by Druids, Mages, Mistweaver Monks, Paladins, Priests, Shamans and Warlocks.
    '1': 'rage',
    # Rage is used by Warriors and Druids in [Bear Form]. Rage goes from 0 to 100, but may be increased via player talents. Rage degenerates back to 0 out of combat.
    '3': 'energy',
    # Energy is used by Rogues and Druids in [Cat Form]. Energy goes from 0 to 100, but may be increased via player talents.
    '6': 'runic',
    # Runic Power is used by Death Knights. It is gained via certain abilities, and does not degenerate out of combat.
    '2': 'focus',
    # Focus is used by hunter pets. Focus goes from 0 to 100, and has a slow regeneration rate, but certain abilities will generate focus.
    '4': 'happiness',
    # Pet happiness.
    '5': 'runes',
    # Runes are used as a power type for Death Knights. By default, they have 6 runes (1 & 2 are blood, 3 & 4 are frost, 5 & 6 are unholy), but certain talents and abilities may change the type of a rune. Runes can be converted into a Death Rune, which can be used as any other type of rune. While runes are used by Death Knights, it does not appear that the Blizzard UI code uses this spell power type. Rather, runes are managed through the RUNE_POWER_UPDATE event via the GetRuneCooldown() API call.
}

SPELLS = {
  "1539": {
    "name": "Feed Pet",
    "icon": "ability_hunter_beasttraining"
  },
  "2687": {
    "name": "Bloodrage",
    "icon": "ability_racial_bloodrage"
  },
  "5229": {
    "name": "Enrage",
    "icon": "ability_druid_enrage"
  },
  "9174": {
    "name": "Energize",
    "icon": "ability_racial_bloodrage"
  },
  "9512": {
    "name": "Restore Energy",
    "icon": "inv_drink_milk_05"
  },
  "10310": {
    "name": "Lay on Hands",
    "icon": "spell_holy_layonhands"
  },
  "12051": {
    "name": "Evocation",
    "icon": "spell_nature_purge"
  },
  "12964": {
    "name": "Unbridled Wrath",
    "icon": "spell_nature_stoneclawtotem"
  },
  "14181": {
    "name": "Relentless Strikes Effect",
    "icon": "ability_warrior_decisivestrike"
  },
  "16666": {
    "name": "Demonic Rune",
    "icon": "inv_misc_rune_04"
  },
  "16959": {
    "name": "Primal Fury",
    "icon": "ability_racial_cannibalize"
  },
  "17057": {
    "name": "Furor",
    "icon": "spell_holy_blessingofstamina"
  },
  "17099": {
    "name": "Furor",
    "icon": "spell_holy_blessingofstamina"
  },
  "17528": {
    "name": "Mighty Rage",
    "icon": "ability_warrior_innerrage"
  },
  "17530": {
    "name": "Superior Mana Potion",
    "icon": "inv_potion_74"
  },
  "17531": {
    "name": "Major Mana Potion",
    "icon": "trade_engineering"
  },
  "18371": {
    "name": "Drain Soul",
    "icon": "spell_shadow_haunting"
  },
  "20168": {
    "name": "Seal of Wisdom",
    "icon": "spell_holy_righteousnessaura"
  },
  "20268": {
    "name": "Judgement of Wisdom",
    "icon": "ability_paladin_judgementblue"
  },
  "20272": {
    "name": "Illumination",
    "icon": "spell_holy_greaterheal"
  },
  "21400": {
    "name": "Alchemist's Stone",
    "icon": "spell_holy_aspiration"
  },
  "23575": {
    "name": "Water Shield",
    "icon": "ability_shaman_watershield"
  },
  "23602": {
    "name": "Shield Specialization",
    "icon": "spell_nature_stoneclawtotem"
  },
  "23690": {
    "name": "Berserker Rage Effect",
    "icon": "spell_nature_ancestralguardian"
  },
  "23691": {
    "name": "Berserker Rage Effect",
    "icon": "spell_nature_ancestralguardian"
  },
  "25046": {
    "name": "Arcane Torrent",
    "icon": "spell_shadow_teleport"
  },
  "27154": {
    "name": "Lay on Hands",
    "icon": "spell_holy_layonhands"
  },
  "27746": {
    "name": "Nitrous Boost",
    "icon": "inv_potion_17"
  },
  "27869": {
    "name": "Dark Rune",
    "icon": "inv_misc_rune_04"
  },
  "27996": {
    "name": "Spellsurge",
    "icon": "spell_arcane_arcane02"
  },
  "28499": {
    "name": "Endless Mana Potion",
    "icon": "inv_alchemy_endlessflask_04"
  },
  "28730": {
    "name": "Arcane Torrent",
    "icon": "spell_shadow_teleport"
  },
  "29077": {
    "name": "Master of Elements",
    "icon": "spell_fire_masterofelements"
  },
  "29131": {
    "name": "Bloodrage",
    "icon": "ability_racial_bloodrage"
  },
  "29166": {
    "name": "Innervate",
    "icon": "spell_nature_lightning"
  },
  "29442": {
    "name": "Magic Absorption",
    "icon": "spell_nature_astralrecalgroup"
  },
  "29841": {
    "name": "Second Wind",
    "icon": "ability_hunter_harass"
  },
  "29842": {
    "name": "Second Wind",
    "icon": "ability_hunter_harass"
  },
  "30824": {
    "name": "Shamanistic Rage",
    "icon": "spell_nature_shamanrage"
  },
  "31663": {
    "name": "Quick Recovery",
    "icon": "ability_rogue_quickrecovery"
  },
  "31786": {
    "name": "Spiritual Attunement",
    "icon": "spell_holy_revivechampion"
  },
  "31818": {
    "name": "Life Tap",
    "icon": "spell_shadow_burningspirit"
  },
  "31930": {
    "name": "Judgements of the Wise",
    "icon": "ability_paladin_judgementofthewise"
  },
  "32553": {
    "name": "Mana Feed",
    "icon": "spell_shadow_manafeed"
  },
  "33272": {
    "name": "Sporeling Snack",
    "icon": "inv_misc_food_87_sporelingsnack"
  },
  "33737": {
    "name": "Water Shield",
    "icon": "ability_shaman_watershield"
  },
  "34074": {
    "name": "Aspect of the Viper",
    "icon": "ability_hunter_aspectoftheviper"
  },
  "34075": {
    "name": "Aspect of the Viper",
    "icon": "ability_hunter_aspectoftheviper"
  },
  "34650": {
    "name": "Mana Leech",
    "icon": "spell_shadow_shadowmend"
  },
  "34720": {
    "name": "Thrill of the Hunt",
    "icon": "ability_hunter_thrillofthehunt"
  },
  "34952": {
    "name": "Go for the Throat",
    "icon": "ability_hunter_goforthethroat"
  },
  "34953": {
    "name": "Go for the Throat",
    "icon": "ability_hunter_goforthethroat"
  },
  "35548": {
    "name": "Combat Potency",
    "icon": "inv_weapon_shortblade_38"
  },
  "36070": {
    "name": "Power of the Sun King",
    "icon": "inv_mace_48"
  },
  "39104": {
    "name": "Totemic Recall",
    "icon": "spell_shaman_totemrecall"
  },
  "39609": {
    "name": "Mana Tide Totem",
    "icon": "spell_frost_summonwaterelemental"
  },
  "41618": {
    "name": "Bottled Nethergon Energy",
    "icon": "inv_potion_156"
  },
  "42987": {
    "name": "Mana Sapphire",
    "icon": "inv_misc_gem_sapphire_02"
  },
  "43186": {
    "name": "Runic Mana Potion",
    "icon": "inv_alchemy_elixir_02"
  },
  "43771": {
    "name": "Spiced Mammoth Treats",
    "icon": "inv_misc_food_123_roast"
  },
  "44450": {
    "name": "Burnout",
    "icon": "ability_mage_burnout"
  },
  "45529": {
    "name": "Blood Tap",
    "icon": "spell_deathknight_bloodtap"
  },
  "47755": {
    "name": "Rapture",
    "icon": "spell_holy_rapture"
  },
  "48391": {
    "name": "Owlkin Frenzy",
    "icon": "ability_druid_owlkinfrenzy"
  },
  "48540": {
    "name": "Revitalize",
    "icon": "ability_druid_replenish"
  },
  "48541": {
    "name": "Revitalize",
    "icon": "ability_druid_replenish"
  },
  "48542": {
    "name": "Revitalize",
    "icon": "ability_druid_replenish"
  },
  "48543": {
    "name": "Revitalize",
    "icon": "ability_druid_replenish"
  },
  "48788": {
    "name": "Lay on Hands",
    "icon": "spell_holy_layonhands"
  },
  "49088": {
    "name": "Anti-Magic Shell",
    "icon": "spell_shadow_antimagicshell"
  },
  "50163": {
    "name": "Butchery",
    "icon": "ability_racial_bloodrage"
  },
  "50422": {
    "name": "Scent of Blood",
    "icon": "ability_rogue_bloodyeye"
  },
  "50613": {
    "name": "Arcane Torrent",
    "icon": "spell_shadow_teleport"
  },
  "51178": {
    "name": "King of the Jungle",
    "icon": "ability_druid_kingofthejungle"
  },
  "51490": {
    "name": "Thunderstorm",
    "icon": "spell_shaman_thunderstorm"
  },
  "51637": {
    "name": "Focused Attacks",
    "icon": "ability_rogue_focusedattacks"
  },
  "52697": {
    "name": "Noth's Special Brew",
    "icon": "inv_alchemy_enchantedvial"
  },
  "53358": {
    "name": "Chimera Shot - Viper",
    "icon": "ability_hunter_chimerashot2"
  },
  "53398": {
    "name": "Invigoration",
    "icon": "ability_hunter_invigeration"
  },
  "53506": {
    "name": "Moonkin Form",
    "icon": "ability_druid_improvedmoonkinform"
  },
  "53517": {
    "name": "Roar of Recovery",
    "icon": "ability_druid_mastershapeshifter"
  },
  "53750": {
    "name": "Crazy Alchemist's Potion",
    "icon": "trade_alchemy"
  },
  "53753": {
    "name": "Nightmare Slumber",
    "icon": "spell_shadow_mindshear"
  },
  "53761": {
    "name": "Rejuvenation Potion",
    "icon": "trade_alchemy"
  },
  "54131": {
    "name": "Bloodthirsty",
    "icon": "ability_druid_primaltenacity"
  },
  "54425": {
    "name": "Improved Felhunter",
    "icon": "spell_shadow_summonfelhunter"
  },
  "54428": {
    "name": "Divine Plea",
    "icon": "spell_holy_aspiration"
  },
  "54607": {
    "name": "Soul Leech Mana",
    "icon": "spell_shadow_soulleech_3"
  },
  "54833": {
    "name": "Glyph of Innervate",
    "icon": "inv_glyph_majordruid"
  },
  "55382": {
    "name": "Mana Restore",
    "icon": "spell_holy_magicalsentry"
  },
  "55767": {
    "name": "Darkglow Embroidery",
    "icon": "spell_nature_giftofthewaterspirit"
  },
  "56186": {
    "name": "Sapphire Owl",
    "icon": "inv_jewelcrafting_azureowl"
  },
  "57319": {
    "name": "Blessing of Sanctuary",
    "icon": "spell_holy_greaterblessingofsanctuary"
  },
  "57669": {
    "name": "Replenishment",
    "icon": "spell_magic_managain"
  },
  "57776": {
    "name": "Frost Warding",
    "icon": "spell_shadow_teleport"
  },
  "57894": {
    "name": "Glyph of Mend Pet",
    "icon": "inv_glyph_minorhunter"
  },
  "57961": {
    "name": "Water Shield",
    "icon": "ability_shaman_watershield"
  },
  "58227": {
    "name": "Glyph of Shadowfiend",
    "icon": "inv_glyph_minorpriest"
  },
  "58362": {
    "name": "Glyph of Heroic Strike",
    "icon": "inv_glyph_majorwarrior"
  },
  "58883": {
    "name": "Rapid Recuperation",
    "icon": "ability_hunter_rapidregeneration"
  },
  "59072": {
    "name": "Natural Reaction",
    "icon": "ability_druid_replenish"
  },
  "59117": {
    "name": "Soul Leech Mana",
    "icon": "spell_shadow_soulleech_3"
  },
  "59159": {
    "name": "Thunderstorm",
    "icon": "spell_shaman_thunderstorm"
  },
  "59159": {
    "name": "Discerning Eye of the Beast",
    "icon": "inv_jewelry_talisman_08"
  },
  "60242": {
    "name": "Darkmoon Card: Illusion",
    "icon": "inv_inscription_tarotillusion"
  },
  "60538": {
    "name": "Soul of the Dead",
    "icon": "inv_jewelry_talisman_06"
  },
  "61040": {
    "name": "Fingers of the Damned",
    "icon": "trade_engineering"
  },
  "61258": {
    "name": "Runic Return",
    "icon": "ability_hunter_harass"
  },
  "61389": {
    "name": "Glyph of Arcane Shot",
    "icon": "inv_glyph_majorhunter"
  },
  "62473": {
    "name": "Reload Ammo",
    "icon": "ability_vehicle_reloadammo"
  },
  "62705": {
    "name": "Auto-repair",
    "icon": "inv_gizmo_02"
  },
  "63375": {
    "name": "Improved Stormstrike",
    "icon": "spell_shaman_improvedstormstrike"
  },
  "63652": {
    "name": "Rapture",
    "icon": "spell_holy_rapture"
  },
  "63653": {
    "name": "Rapture",
    "icon": "spell_holy_rapture"
  },
  "63654": {
    "name": "Rapture",
    "icon": "spell_holy_rapture"
  },
  "63655": {
    "name": "Rapture",
    "icon": "spell_holy_rapture"
  },
  "64103": {
    "name": "Shadow Affinity",
    "icon": "spell_shadow_shadowward"
  },
  "64180": {
    "name": "Rapid Recuperation",
    "icon": "ability_hunter_rapidregeneration"
  },
  "64181": {
    "name": "Rapid Recuperation",
    "icon": "ability_hunter_rapidregeneration"
  },
  "64372": {
    "name": "Lifebloom",
    "icon": "spell_nature_healingtouch"
  },
  "64904": {
    "name": "Hymn of Hope",
    "icon": "spell_holy_rapture"
  },
  "64913": {
    "name": "Energized",
    "icon": "ability_rogue_deviouspoisons"
  },
  "65247": {
    "name": "Kibler's Bits",
    "icon": "inv_misc_food_49"
  },
  "65724": {
    "name": "Empowered Darkness",
    "icon": "spell_shadow_darkritual"
  },
  "65748": {
    "name": "Empowered Light",
    "icon": "spell_holy_searinglightpriest"
  },
  "67213": {
    "name": "Empowered Darkness",
    "icon": "spell_shadow_darkritual"
  },
  "67214": {
    "name": "Empowered Darkness",
    "icon": "spell_shadow_darkritual"
  },
  "67215": {
    "name": "Empowered Darkness",
    "icon": "spell_shadow_darkritual"
  },
  "67216": {
    "name": "Empowered Light",
    "icon": "spell_holy_searinglightpriest"
  },
  "67217": {
    "name": "Empowered Light",
    "icon": "spell_holy_searinglightpriest"
  },
  "67218": {
    "name": "Empowered Light",
    "icon": "spell_holy_searinglightpriest"
  },
  "67490": {
    "name": "Runic Mana Injector",
    "icon": "inv_gizmo_runicmanainjector"
  },
  "67545": {
    "name": "Empowered Fire",
    "icon": "spell_fire_masterofelements"
  },
  "67666": {
    "name": "Mana Mana",
    "icon": "spell_arcane_arcanepotency"
  },
  "68082": {
    "name": "Glyph of Seal of Command",
    "icon": "inv_glyph_majorpaladin"
  },
  "68285": {
    "name": "Improved Leader of the Pack",
    "icon": "spell_nature_unyeildingstamina"
  },
  "70360": {
    "name": "Eat Ooze",
    "icon": "spell_fire_felflamebreath"
  },
  "70804": {
    "name": "Tricks of the Trade",
    "icon": "ability_rogue_tricksofthetrade"
  },
  "70873": {
    "name": "Emerald Vigor",
    "icon": "spell_nature_elementalshields"
  },
  "71132": {
    "name": "Glyph of Shadow Word: Pain",
    "icon": "inv_glyph_majorpriest"
  },
  "71565": {
    "name": "Replenish Mana",
    "icon": "inv_jewelry_trinket_05"
  },
  "71566": {
    "name": "Replenished",
    "icon": "spell_holy_magicalsentry"
  },
  "71574": {
    "name": "Replenish Mana",
    "icon": "inv_jewelry_trinket_05"
  },
  "71882": {
    "name": "Invigoration",
    "icon": "ability_hunter_invigeration"
  },
  "71887": {
    "name": "Invigoration",
    "icon": "ability_hunter_invigeration"
  },
  "71941": {
    "name": "Twisted Nightmares",
    "icon": "spell_fire_windsofwoe"
  },
  "72527": {
    "name": "Eat Ooze",
    "icon": "spell_fire_felflamebreath"
  }
}


def asidjioasjdso(logs: list[str]):
    z2 = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for line in logs:
        if "_ENERGIZE" not in line:
            continue
        try:
            _, _, _, _, tguid, _, spell_id, _, _, amount, power_type = line.split(',')
            z2[power_type][tguid][spell_id] += int(amount)
        except ValueError:
            pass
    
    return {
      POWER_TYPES[power_type]: data
      for power_type, data in z2.items()
    }
