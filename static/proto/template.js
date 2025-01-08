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
          major1: 56832,
          major2: 56826,
          major3: 63067,
        },
        Survival: {
          major1: 56826,
          major2: 56832,
          major3: 63068,
        },
        "Beast Mastery": {
          major1: 56830,
          major2: 56826,
          major3: 63067,
        },
      },
    },
  },
  feralDruid: {
    player: {
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
      balanceDruid: {
        options: {
          innervateTarget: {},
        },
      },
      distanceFromTarget: 18,
      glyphs: {
        major1: 54828,
        major2: 54829,
        major3: 54845,
      },
    },
  },
  feral_tankDruid: {
    player: {
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
      mage: {
        options: {
          armor: 2,
          focusMagicPercentUptime: 99,
          focusMagicTarget: {},
        },
      },
      glyphsOverride: {
        Fire: {
          major1: 56368,
          major2: 63091,
          major3: 56382,
        },
        Frost: {
          major1: 42742,
          major2: 50045,
          major3: 42751,
        },
        Arcane: {
          major1: 56363,
          major2: 62210,
          major3: 56382,
        },
      },
      distanceFromTarget: 20,
    },
  },
  retributionPaladin: {
    player: {
      retributionPaladin: {
        options: {
          aura: 3,
        },
      },
      glyphs: {
        major1: 54922,
        major2: 54928,
        major3: 56416,
      },
    },
  },
  protectionPaladin: {
    player: {
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
        major1: 54929,
        major2: 63225,
        major3: 63223,
      },
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
  holyPaladin: {},
  healingPriest: {
    player: {
      healingPriest: {
        options: {
          useShadowfiend: true,
          powerInfusionTarget: {},
          useInnerFire: true,
          rapturesPerMinute: 5,
        },
      },
      glyphs: {
        major1: 55679,
        major2: 63235,
        major3: 55672,
      },
    },
  },
  shadowPriest: {
    player: {
      shadowPriest: {
        options: {
          armor: 1,
        },
      },
      channelClipDelayMs: 100,
      glyphs: {
        major1: 55689,
        major2: 55687,
        major3: 63237,
      },
    },
  },
  smitePriest: {},
  rogue: {
    player: {
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
          major1: 63254,
          major2: 56821,
          major3: 63256,
        },
        Assassination: {
          major1: 63256,
          major2: 63268,
          major3: 63249,
        },
      },
    },
  },
  elementalShaman: {
    player: {
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
        major1: 55451,
        major2: 63280,
        major3: 55453,
      },
      distanceFromTarget: 20,
    },
  },
  enhancementShaman: {
    player: {
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
        major1: 55450,
        major2: 55446,
        major3: 55451,
      },
    },
  },
  restorationShaman: {},
  warlock: {
    player: {
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
          major1: 70947,
          major2: 63320,
          major3: 56246,
        },
        Affliction: {
          major1: 63320,
          major2: 63302,
          major3: 70947,
        },
        Destruction: {
          major1: 56228,
          major2: 56242,
          major3: 56235,
        },
      },
      distanceFromTarget: 25,
      channelClipDelayMs: 150,
    },
  },
  warrior: {
    player: {
      warrior: {
        options: {
          useRecklessness: true,
          shout: 2,
          useShatteringThrow: true,
        },
      },
      glyphsOverride: {
        Fury: {
          major1: 58385,
          major2: 58370,
          major3: 58366,
        },
        Arms: {
          major1: 58385,
          major2: 58386,
          major3: 58368,
        },
      },
    },
  },
  protectionWarrior: {
    player: {
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
        major1: 63329,
        major2: 58353,
        major3: 58375,
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
      deathknight: {
        options: {
          petUptime: 1,
          unholyFrenzyTarget: {},
          drwPestiApply: true,
        },
      },
      glyphsOverride: {
        Frost: {
          major1: 58647,
          major2: 58671,
          major3: 63334,
        },
        Unholy: {
          major1: 58631,
          major2: 58629,
          major3: 58686,
        },
      },
    },
  },
  tankDeathknight: {
    player: {
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
        major1: 59327,
        major2: 58676,
        major3: 63334,
      },
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
};
