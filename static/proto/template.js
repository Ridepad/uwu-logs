export const wow_sim_template = {
  player: {
    equipment: {
      items: [],
    },
    healingModel: {},
    bonusStats: {
      stats: [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      ],
      pseudoStats: [0, 0, 0, 0, 0, 0],
    },
    reactionTimeMs: 200,
    nibelungAverageCasts: 11,
    itemSwap: {},
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
    },
  },
  feralTankDruid: {
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
    },
    tanks: [
      {
        type: 1,
      },
    ],
  },
};
