export const wow_sim_template = {
  player: {
    equipment: {
      items: [],
    },
    healingModel: {},
    bonusStats: {
      stats: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      pseudoStats: [0, 0, 0, 0, 0, 0],
    },
    reactionTimeMs: 200,
    nibelungAverageCasts: 11,
    itemSwap: {},
    glyphs: {},
  },
};
export const spec_overrides = {
  hunter: {
    player: {
      consumes: {
        flask: 2,
        food: 1,
        petFood: 1,
        defaultPotion: 4,
        prepopPotion: 4,
      },
      hunter: {
        options: {
          ammo: 2,
          petType: 31,
          petTalents: {
            cobraReflexes: 2,
            dive: true,
            boarsSpeed: true,
            spikedCollar: 3,
            cullingTheHerd: 3,
            wildHunt: 1,
            spidersBite: 3,
            rabid: true,
            callOfTheWild: true,
          },
          petUptime: 1,
          useHuntersMark: true,
          sniperTrainingUptime: 0.9,
          timeToTrapWeaveMs: 2000,
        },
      },
      glyphsOverride: {
        Marksmanship: {
          major1: 42912,
          major2: 42914,
          major3: 45732,
        },
        Survival: {
          major1: 42914,
          major2: 42912,
          major3: 45733,
        },
        "Beast Mastery": {
          major1: 42902,
          major2: 42914,
          major3: 45732,
        },
      },
    },
  },
  feralDruid: {
    player: {
      consumes: {
        flask: 2,
        food: 13,
        defaultPotion: 4,
        prepopPotion: 4,
      },
      feralDruid: {
        options: {
          latencyMs: 100,
          assumeBleedActive: true,
        },
      },
      glyphs: {
        major1: 40902,
        major2: 45604,
        major3: 40901,
      },
    },
  },
  balanceDruid: {
    player: {
      consumes: {
        flask: 1,
        food: 1,
        defaultPotion: 4,
        prepopPotion: 5,
        fillerExplosive: 1,
      },
      balanceDruid: {
        options: {
          innervateTarget: {},
        },
      },
      distanceFromTarget: 18,
      glyphs: {
        major1: 40921,
        major2: 40923,
        major3: 40916,
      },
    },
  },
  feral_tankDruid: {
    player: {
      consumes: {
        battleElixir: 8,
        guardianElixir: 7,
        food: 3,
        defaultPotion: 3,
        prepopPotion: 3,
        defaultConjured: 5,
        thermalSapper: true,
        fillerExplosive: 1,
      },
      inFrontOfTarget: true,
      feralTankDruid: {
        options: {
          innervateTarget: {},
          startingRage: 20,
        },
      },
      healingModel: {
        hps: 7583.333333333333,
        cadenceSeconds: 2.25,
        burstWindow: 6,
      },
      glyphs: {
        major1: 40899,
        major2: 40896,
        major3: 46372,
      },
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
  restorationDruid: {},
  mage: {
    player: {
      consumes: {
        flask: 1,
        food: 11,
        defaultPotion: 4,
        prepopPotion: 4,
        defaultConjured: 2,
      },
      mage: {
        options: {
          armor: 2,
          focusMagicPercentUptime: 99,
          focusMagicTarget: {},
        },
      },
      glyphsOverride: {
        Fire: {
          major1: 42739,
          major2: 45737,
          major3: 42751,
        },
        Frost: {
          major1: 42742,
          major2: 50045,
          major3: 42751,
        },
        Arcane: {
          major1: 42735,
          major2: 44955,
          major3: 42751,
        },
      },
      distanceFromTarget: 20,
    },
  },
  retributionPaladin: {
    player: {
      consumes: {
        flask: 2,
        food: 13,
        defaultPotion: 4,
        defaultConjured: 1,
      },
      retributionPaladin: {
        options: {
          aura: 3,
        },
      },
      glyphs: {
        major1: 41092,
        major2: 41099,
        major3: 43869,
      },
    },
  },
  protectionPaladin: {
    player: {
      consumes: {
        flask: 4,
        food: 13,
        defaultPotion: 3,
        prepopPotion: 3,
      },
      inFrontOfTarget: true,
      protectionPaladin: {
        options: {
          aura: 3,
        },
      },
      healingModel: {
        hps: 7583.333333333333,
        cadenceSeconds: 2.25,
        burstWindow: 6,
      },
      glyphs: {
        major1: 41100,
        major2: 45747,
        major3: 45745,
      },
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
  healingPriest: {
    player: {
      consumes: {
        flask: 1,
        food: 1,
        defaultPotion: 14,
        prepopPotion: 5,
      },
      healingPriest: {
        options: {
          useShadowfiend: true,
          powerInfusionTarget: {},
          useInnerFire: true,
          rapturesPerMinute: 5,
        },
      },
      glyphs: {
        major1: 42400,
        major2: 45756,
        major3: 42408,
      },
    },
  },
  shadowPriest: {
    player: {
      consumes: {
        flask: 1,
        food: 1,
        defaultPotion: 4,
        prepopPotion: 5,
      },
      shadowPriest: {
        options: {
          armor: 1,
        },
      },
      channelClipDelayMs: 0,
      glyphs: {
        major1: 42407,
        major2: 42415,
        major3: 45757,
      },
    },
  },
  rogue: {
    player: {
      consumes: {
        flask: 2,
        food: 5,
        defaultPotion: 4,
        prepopPotion: 4,
        defaultConjured: 4,
      },
      rogue: {
        options: {
          mhImbue: 2,
          ohImbue: 1,
          startingOverkillDuration: 20,
          honorOfThievesCritRate: 400,
          vanishBreakTime: 0.10000000149011612,
        },
      },
      glyphsOverride: {
        Combat: {
          major1: 45766,
          major2: 42972,
          major3: 45767,
        },
        Assassination: {
          major1: 45767,
          major2: 45768,
          major3: 45761,
        },
      },
    },
  },
  elementalShaman: {
    player: {
      consumes: {
        flask: 1,
        food: 1,
        defaultPotion: 5,
      },
      elementalShaman: {
        options: {
          shield: 1,
          totems: {
            earth: 1,
            air: 3,
            fire: 3,
            water: 1,
            useFireElemental: true,
          },
        },
      },
      glyphs: {
        major1: 41532,
        major2: 45776,
        major3: 41536,
      },
      distanceFromTarget: 20,
    },
  },
  enhancementShaman: {
    player: {
      consumes: {
        flask: 2,
        food: 1,
        defaultPotion: 4,
      },
      enhancementShaman: {
        options: {
          shield: 2,
          syncType: 3,
          imbueMh: 1,
          imbueOh: 2,
          totems: {
            earth: 1,
            air: 2,
            fire: 1,
            water: 1,
          },
        },
      },
      glyphs: {
        major1: 41530,
        major2: 41539,
        major3: 41532,
      },
    },
  },
  restorationShaman: {},
  warlock: {
    player: {
      consumes: {
        flask: 1,
        food: 1,
        petFood: 1,
        defaultPotion: 5,
        prepopPotion: 5,
      },
      warlock: {
        options: {
          armor: 1,
          summon: 4,
          weaponImbue: 1,
          detonateSeed: true,
        },
      },
      glyphsOverride: {
        Demonology: {
          major1: 50077,
          major2: 45785,
          major3: 42459,
        },
        Affliction: {
          major1: 45785,
          major2: 45779,
          major3: 50077,
        },
        Destruction: {
          major1: 42464,
          major2: 42453,
          major3: 42454,
        },
      },
      distanceFromTarget: 25,
      channelClipDelayMs: 150,
    },
  },
  warrior: {
    player: {
      consumes: {
        flask: 2,
        food: 6,
        defaultPotion: 3,
        prepopPotion: 4,
      },
      warrior: {
        options: {
          useRecklessness: true,
          shout: 2,
          useShatteringThrow: true,
        },
      },
      glyphsOverride: {
        Fury: {
          major1: 43423,
          major2: 43432,
          major3: 43414,
        },
        Arms: {
          major1: 43423,
          major2: 43422,
          major3: 43421,
        },
      },
    },
  },
  protectionWarrior: {
    player: {
      consumes: {
        battleElixir: 4,
        guardianElixir: 5,
        food: 13,
        defaultPotion: 3,
        prepopPotion: 3,
        thermalSapper: true,
        fillerExplosive: 1,
      },
      protectionWarrior: {
        options: {
          shout: 2,
        },
      },
      inFrontOfTarget: true,
      healingModel: {
        hps: 7583.333333333333,
        cadenceSeconds: 2.25,
        burstWindow: 6,
      },
      glyphs: {
        major1: 45797,
        major2: 43429,
        major3: 43425,
      },
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
  deathknight: {
    player: {
      consumes: {
        flask: 2,
        food: 13,
        petFood: 1,
        defaultPotion: 4,
        prepopPotion: 4,
        thermalSapper: true,
        fillerExplosive: 1,
      },
      deathknight: {
        options: {
          petUptime: 1,
          unholyFrenzyTarget: {},
          drwPestiApply: true,
        },
      },
      glyphsOverride: {
        Frost: {
          major1: 43543,
          major2: 43547,
          major3: 45805,
        },
        Unholy: {
          major1: 43546,
          major2: 43542,
          major3: 43549,
        },
      },
    },
  },
  tankDeathknight: {
    player: {
      consumes: {
        flask: 4,
        food: 13,
        defaultPotion: 3,
        prepopPotion: 3,
      },
      inFrontOfTarget: true,
      healingModel: {
        hps: 7583.333333333333,
        cadenceSeconds: 2.25,
        burstWindow: 6,
      },
      tankDeathknight: {
        options: {},
      },
      glyphs: {
        major1: 43825,
        major2: 43554,
        major3: 45805,
      },
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
};
