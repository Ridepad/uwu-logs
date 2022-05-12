from constants import running_time

casts = {
    '0xF130008EF5001232': {
        'Faerie Fire': [(False, 0.341), (True, 185.145), (False, 163.901), (True, 299.979), (False, 238.773)],
        'Earth and Moon': [(False, 2.932), (True, 0.555), (False, 0.415), (True, 0.524), (False, 0.433), (True, 0.7), (False, 0.443), (True, 0.477), (False, 0.69), (True, 0.393), (False, 0.873), (True, 0.251), (False, 0.639), (True, 0.625), (False, 0.421), (True, 0.766), (False, 2.422), (True, 0.0), (False, 2.25), (True, 0.942), (False, 0.143), (True, 1.062), (False, 0.165), (True, 1.165), (False, 3.523), (True, 0.307), (False, 0.943), (True, 0.356), (False, 0.837), (True, 0.349), (False, 0.88), (True, 0.322), (False, 0.882), (True, 1.181), (False, 6.323), (True, 0.714), (False, 0.516), (True, 1.643), (False, 1.781), (True, 0.803), (False, 0.913), (True, 0.736), (False, 0.531), (True, 1.075), (False, 0.529), (True, 1.958), (False, 1.233), (True, 0.532), (False, 1.109), (True, 0.525), (False, 1.193), (True, 2.016), (False, 1.253), (True, 0.23), (False, 1.283), (True, 0.615), (False, 1.01), (True, 0.087), (False, 4.303), (True, 0.247), (False, 0.988), (True, 0.455), (False, 0.524), (True, 0.641), (False, 0.583), (True, 0.493), (False, 0.53), (True, 2.338), (False, 1.906), (True, 0.126), (False, 0.873), (True, 0.105), (False, 0.91), (True, 0.196), (False, 0.914), (True, 0.174), (False, 2.716), (True, 0.538), (False, 1.058), (True, 0.507), (False, 1.012), (True, 1.359), (False, 0.198), (True, 1.382), (False, 0.207), (True, 1.364), (False, 1.685), (True, 3.088), (False, 4.937), (True, 0.765), (False, 0.456), (True, 0.58), (False, 0.492), (True, 0.761), (False, 0.441), (True, 0.696), (False, 0.38), (True, 0.832), (False, 0.858), (True, 1.463), (False, 0.35), (True, 1.515), (False, 0.687), (True, 0.334), (False, 0.642), (True, 1.354), (False, 0.967), (True, 1.561), (False, 0.469), (True, 1.287), (False, 0.39), (True, 13.717), (False, 59.95), (True, 4.057), (False, 0.776), (True, 1.323), (False, 0.375), (True, 1.152), (False, 0.504), (True, 0.91), (False, 2.732), (True, 0.483), (False, 0.601), (True, 0.512), (False, 19.028), (True, 0.182), (False, 0.978), (True, 0.152), (False, 0.813), (True, 1.11), (False, 1.36), (True, 0.808), (False, 0.91), (True, 0.734), (False, 0.828), (True, 0.927), (False, 0.701), (True, 0.847), (False, 0.884), (True, 0.727), (False, 0.853), (True, 0.836), (False, 0.887), (True, 0.708), (False, 0.848), (True, 0.867), (False, 0.868), (True, 1.575), (False, 0.754), (True, 0.602), (False, 0.613), (True, 0.598), (False, 0.374), (True, 0.671), (False, 0.38), (True, 0.724), (False, 25.787), (True, 0.625), (False, 0.115), (True, 0.859), (False, 0.057), (True, 1.652), (False, 0.176), (True, 1.478), (False, 0.93), (True, 1.72), (False, 1.282), (True, 0.312), (False, 1.481), (True, 0.143), (False, 1.413), (True, 1.039), (False, 0.546), (True, 1.223), (False, 0.34), (True, 2.253), (False, 0.528), (True, 0.632), (False, 17.588), (True, 1.533), (False, 0.712), (True, 0.394), (False, 1.662), (True, 0.084), (False, 1.473), (True, 0.157), (False, 1.536), (True, 0.172), (False, 1.417), (True, 0.13), (False, 1.541), (True, 0.193), (False, 1.37), (True, 3.003), (False, 0.357), (True, 1.317), (False, 0.229), (True, 1.387), (False, 1.163), (True, 0.39), (False, 0.67), (True, 1.099), (False, 0.84), (True, 1.004), (False, 18.25), (True, 0.945), (False, 0.038), (True, 0.891), (False, 133.744), (True, 0.921), (False, 0.236), (True, 15.239), (False, 1.014), (True, 1.013), (False, 0.485), (True, 1.501), (False, 0.155), (True, 1.479), (False, 0.184), (True, 1.453), (False, 4.262), (True, 0.3), (False, 0.54), (True, 1.571), (False, 0.681), (True, 0.408), (False, 0.751), (True, 0.359), (False, 1.136), (True, 1.033), (False, 1.148), (True, 1.104), (False, 0.106), (True, 1.009), (False, 0.069), (True, 1.697), (False, 0.445), (True, 1.2), (False, 1.539), (True, 0.116), (False, 1.566), (True, 0.127), (False, 1.42), (True, 0.179), (False, 1.433), (True, 0.173), (False, 1.527), (True, 0.165), (False, 55.976), (True, 2.463), (False, 0.31), (True, 0.656), (False, 0.493), (True, 0.553), (False, 0.42), (True, 1.043), (False, 0.467), (True, 1.017), (False, 3.515), (True, 1.216), (False, 0.191), (True, 1.277), (False, 0.381), (True, 1.082), (False, 0.368), (True, 6.875), (False, 1.924), (True, 0.674), (False, 2.798), (True, 5.413), (False, 0.388), (True, 1.146), (False, 0.037), (True, 1.349), (False, 0.731), (True, 0.385), (False, 2.125), (True, 0.711), (False, 0.538), (True, 0.696), (False, 0.523), (True, 0.347), (False, 1.044), (True, 0.163), (False, 1.024), (True, 1.234), (False, 1.346), (True, 0.882), (False, 0.335), (True, 1.062), (False, 0.132), (True, 1.103), (False, 0.189), (True, 13.284), (False, 41.599), (True, 2.97), (False, 164.836), (True, 1.187), (False, 2.126), (True, 1.921), (False, 0.05), (True, 1.572), (False, 0.586), (True, 0.941), (False, 1.798), (True, 0.997), (False, 0.428), (True, 0.867), (False, 0.65), (True, 0.874), (False, 0.685), (True, 0.679), (False, 0.862), (True, 0.618), (False, 0.859), (True, 0.69), (False, 0.894), (True, 0.651), (False, 1.031), (True, 1.316), (False, 0.168), (True, 0.934), (False, 0.756), (True, 0.647), (False, 1.385), (True, 1.253), (False, 0.449)],
        'Languish': [(False, 2.934), (True, 58.422), (False, 0.417), (True, 55.02), (False, 67.985), (True, 15.847), (False, 16.6), (True, 20.131), (False, 0.032), (True, 7.264), (False, 22.478), (True, 4.757), (False, 1.142), (True, 16.333), (False, 14.167), (True, 19.769), (False, 1.121), (True, 5.938), (False, 15.255), (True, 4.009), (False, 132.757), (True, 6.28), (False, 9.982), (True, 7.202), (False, 3.33), (True, 10.825), (False, 0.64), (True, 14.219), (False, 52.094), (True, 10.421), (False, 0.509), (True, 12.647), (False, 5.738), (True, 4.013), (False, 1.379), (True, 21.205), (False, 50.888), (True, 4.041), (False, 165.787), (True, 21.679), (False, 2.882)],
        'Moonfire': [(False, 9.95), (True, 24.042), (False, 7.713), (True, 24.011), (False, 6.883), (True, 24.029), (False, 11.384), (True, 21.039), (False, 52.868), (True, 24.026), (False, 13.305), (True, 24.044), (False, 19.03), (True, 24.008), (False, 18.789), (True, 24.022), (False, 17.972), (True, 14.995), (False, 115.889), (True, 15.029), (False, 0.486), (True, 23.998), (False, 3.9), (True, 24.037), (False, 38.156), (True, 48.051), (False, 236.002), (True, 20.416), (False, 0.065)],
        'Insect Swarm': [(False, 58.777), (True, 14.032), (False, 16.122), (True, 14.016), (False, 77.865), (True, 27.561), (False, 26.728), (True, 14.027), (False, 11.964), (True, 14.039), (False, 25.553), (True, 14.017), (False, 6.155), (True, 14.026), (False, 13.359), (True, 14.024), (False, 114.713), (True, 14.007), (False, 3.613), (True, 25.629), (False, 61.973), (True, 25.532), (False, 0.955), (True, 14.032), (False, 16.186), (True, 14.013), (False, 235.221)],
        'Hurricane': [(False, 198.983), (True, 0.529), (False, 0.579), (True, 0.454), (False, 0.522), (True, 0.538), (False, 0.485), (True, 0.564), (False, 0.548), (True, 0.493), (False, 0.536), (True, 0.781), (False, 0.246), (True, 0.723), (False, 0.344), (True, 0.687), (False, 0.355), (True, 0.681), (False, 0.358), (True, 0.529), (False, 0.546), (True, 0.55), (False, 0.536), (True, 0.525), (False, 0.578), (True, 0.446), (False, 0.561), (True, 0.491), (False, 0.57), (True, 0.505), (False, 0.567), (True, 0.491), (False, 0.57), (True, 0.497), (False, 0.597), (True, 0.454), (False, 0.581), (True, 0.489), (False, 0.633), (True, 0.367), (False, 65.82), (True, 0.519), (False, 0.596), (True, 0.483), (False, 0.546), (True, 0.512), (False, 0.568), (True, 0.464), (False, 1.426), (True, 0.52), (False, 0.569), (True, 0.444), (False, 0.572), (True, 0.476), (False, 0.606), (True, 0.457), (False, 0.552), (True, 0.518), (False, 0.328), (True, 0.5), (False, 0.552), (True, 0.51), (False, 0.549), (True, 0.483), (False, 0.591), (True, 0.473), (False, 0.598), (True, 0.501), (False, 0.602), (True, 0.462), (False, 0.528), (True, 0.467), (False, 0.622), (True, 0.476), (False, 0.546), (True, 0.478), (False, 0.562), (True, 0.484), (False, 21.913), (True, 0.509), (False, 0.567), (True, 0.465), (False, 0.552), (True, 0.466), (False, 0.59), (True, 0.478), (False, 0.615), (True, 0.448), (False, 0.618), (True, 0.066), (False, 0.0), (True, 0.542), (False, 0.575), (True, 0.433), (False, 0.601), (True, 0.438), (False, 0.585), (True, 0.508), (False, 0.525), (True, 0.523), (False, 0.626), (True, 0.482), (False, 0.559), (True, 0.473), (False, 0.562), (True, 0.792), (False, 0.31), (True, 0.763), (False, 0.579), (True, 0.487), (False, 0.555), (True, 0.046), (False, 544.439)]
    },
    '0xF13000933F0012C0': {
        'Typhoon': [(False, 28.872), (True, 2.551), (False, 856.716)]
    },
    '0xF13000933F0012BE': {
        'Typhoon': [(False, 28.903), (True, 6.057), (False, 853.179)]
    },
    '0xF1300093420012C5': {
        'Typhoon': [(False, 28.903), (True, 6.057), (False, 23.817), (True, 6.01), (False, 25.826), (True, 1.431), (False, 796.095)]
    },
    '0xF13000933F0012D3': {
        'Typhoon': [(False, 58.654), (True, 6.03), (False, 823.455)]
    },
    '0xF13000933F0012D5': {
        'Typhoon': [(False, 58.654), (True, 6.03), (False, 823.455)]
    },
    '0xF13000933F0012D2': {
        'Typhoon': [(False, 58.716), (True, 6.031), (False, 823.392)]
    },
    '0xF13000933F0012E4': {
        'Typhoon': [(False, 90.669), (True, 6.015), (False, 791.455)]
    },
    '0xF13000933F0012E5': {
        'Typhoon': [(False, 90.669), (True, 6.015), (False, 791.455)]
    },
    '0xF13000933F0012E6': {
        'Typhoon': [(False, 90.669), (True, 6.015), (False, 791.455)]
    },
    '0xF1300093420012EB': {
        'Typhoon': [(False, 90.732), (True, 6.002), (False, 791.405)],
        'Insect Swarm': [(False, 121.547), (True, 7.893), (False, 758.699)]
    },
    '0xF13000933F0012F0': {
        'Typhoon': [(False, 117.882), (True, 2.011), (False, 768.246)],
        'Hurricane': [(False, 118.595), (True, 1.298), (False, 768.246)]
    },
    '0xF13000933F0012EE': {
        'Typhoon': [(False, 117.951), (True, 4.617), (False, 765.571)],
        'Hurricane': [(False, 118.595), (True, 2.908), (False, 766.636)]
    },
    '0xF13000933F0012EF': {
        'Typhoon': [(False, 117.987), (True, 6.01), (False, 764.142)],
        'Hurricane': [(False, 118.595), (True, 2.908), (False, 766.636)],
        'Earth and Moon': [(False, 124.653), (True, 1.25), (False, 762.236)],
        'Languish': [(False, 125.903), (True, 0.0), (False, 762.236)]
    },
    '0xF130008F5D0012FA': {
        'Moonfire': [(False, 125.943), (True, 18.038), (False, 744.158)],
        'Languish': [(False, 128.216), (True, 4.048), (False, 0.18), (True, 14.709), (False, 740.986)],
        'Earth and Moon': [(False, 128.216), (True, 0.642), (False, 2.466), (True, 1.549), (False, 0.569), (True, 0.338), (False, 0.732), (True, 0.243), (False, 0.899), (True, 0.217), (False, 0.853), (True, 1.308), (False, 0.886), (True, 1.246), (False, 0.852), (True, 0.653), (False, 0.749), (True, 0.752), (False, 0.125), (True, 1.488), (False, 0.595), (True, 1.775), (False, 740.986)],
        'Insect Swarm': [(False, 128.274), (True, 14.037), (False, 745.828)]
    },
    '0xF130008F5D001302': {
        'Moonfire': [(False, 144.147), (True, 24.068), (False, 719.924)],
        'Earth and Moon': [(False, 146.831), (True, 0.289), (False, 1.173), (True, 0.333), (False, 1.186), (True, 0.316), (False, 1.217), (True, 1.223), (False, 0.319), (True, 1.696), (False, 1.257), (True, 0.594), (False, 0.907), (True, 0.242), (False, 1.372), (True, 0.785), (False, 0.992), (True, 0.111), (False, 1.552), (True, 0.529), (False, 2.65), (True, 0.76), (False, 0.281), (True, 0.804), (False, 0.274), (True, 0.867), (False, 0.149), (True, 0.425), (False, 719.005)],
        'Languish': [(False, 146.831), (True, 17.947), (False, 0.788), (True, 7.166), (False, 715.407)],
        'Insect Swarm': [(False, 162.429), (True, 11.498), (False, 714.212)]
    },
    '0xF130008F5D001306': {
        'Earth and Moon': [(False, 169.59), (True, 1.199), (False, 1.134), (True, 1.394), (False, 0.961), (True, 0.625), (False, 0.418), (True, 1.261), (False, 0.963), (True, 0.702), (False, 0.317), (True, 2.517), (False, 707.058)],
        'Languish': [(False, 169.59), (True, 12.965), (False, 705.584)],
        'Moonfire': [(False, 177.444), (True, 15.022), (False, 695.673)],
        'Insect Swarm': [(False, 178.564), (True, 14.032), (False, 695.543)],
        'Hurricane': [(False, 198.983), (True, 0.529), (False, 0.579), (True, 0.454), (False, 0.522), (True, 0.538), (False, 0.485), (True, 0.564), (False, 0.548), (True, 0.497), (False, 0.532), (True, 0.781), (False, 0.298), (True, 0.671), (False, 0.569), (True, 0.462), (False, 2.469), (True, 0.55), (False, 0.536), (True, 0.525), (False, 0.578), (True, 0.227), (False, 676.242)]
    },
    '0xF150008F0100131A': {
        'Hurricane': [(False, 198.983), (True, 9.952), (False, 0.546), (True, 5.302), (False, 673.356)],
        'Typhoon': [(False, 215.156), (True, 6.028), (False, 666.955)]
    },
    '0xF150008F0100131D': {
        'Hurricane': [(False, 200.043), (True, 8.892), (False, 0.58), (True, 4.732), (False, 673.892)]
    },
    '0xF150008F0100131C': {
        'Hurricane': [(False, 202.688), (True, 6.247), (False, 0.546), (True, 10.008), (False, 668.65)],
        'Typhoon': [(False, 215.048), (True, 6.055), (False, 667.036)]
    },
    '0xF150008F01001338': {
        'Hurricane': [(False, 285.325), (True, 3.973), (False, 1.125), (True, 5.042), (False, 0.0), (True, 9.47), (False, 583.204)]
    },
    '0xF150008F01001339': {
        'Hurricane': [(False, 285.325), (True, 3.973), (False, 1.125), (True, 5.042), (False, 0.0), (True, 7.392), (False, 585.282)]
    },
    '0xF150008F0100133B': {
        'Hurricane': [(False, 285.887), (True, 3.411), (False, 1.125), (True, 5.042), (False, 0.0), (True, 7.392), (False, 585.282)]
    },
    '0xF150008F01001340': {
        'Hurricane': [(False, 327.371), (True, 5.365), (False, 0.011), (True, 9.531), (False, 545.861)],
        'Typhoon': [(False, 339.747), (True, 5.984), (False, 542.408)]
    },
    '0xF150008F01001341': {
        'Hurricane': [(False, 328.369), (True, 4.367), (False, 0.011), (True, 6.859), (False, 0.812), (True, 3.282), (False, 544.439)],
        'Typhoon': [(False, 339.934), (True, 6.016), (False, 542.189)]
    },
    '0xF150008F01001342': {
        'Hurricane': [(False, 329.455), (True, 3.281), (False, 0.0), (True, 10.964), (False, 544.439)],
        'Typhoon': [(False, 339.513), (True, 5.999), (False, 542.627)]
    },
    '0xF130008F5D001343': {
        'Earth and Moon': [(False, 360.655), (True, 2.519), (False, 2.739), (True, 0.246), (False, 1.361), (True, 1.016), (False, 1.538), (True, 0.206), (False, 2.872), (True, 0.705), (False, 0.702), (True, 0.163), (False, 1.479), (True, 0.491), (False, 0.945), (True, 0.125), (False, 2.267), (True, 0.942), (False, 507.168)],
        'Languish': [(False, 360.655), (True, 4.058), (False, 1.168), (True, 18.17), (False, 504.088)],
        'Moonfire': [(False, 367.582), (True, 24.009), (False, 496.548)],
        'Insect Swarm': [(False, 377.701), (True, 14.045), (False, 496.393)]
    },
    '0xF130008F5D001353': {
        'Earth and Moon': [(False, 381.176), (True, 2.052), (False, 1.144), (True, 1.463), (False, 0.679), (True, 0.484), (False, 0.627), (True, 1.53), (False, 1.763), (True, 0.621), (False, 0.49), (True, 1.065), (False, 1.059), (True, 0.457), (False, 0.687), (True, 0.721), (False, 0.322), (True, 1.203), (False, 490.596)],
        'Languish': [(False, 382.326), (True, 12.655), (False, 1.359), (True, 5.05), (False, 486.749)]
    },
    '0xF130008F5D00135A': {
        'Moonfire': [(False, 398.079), (True, 24.014), (False, 466.046)],
        'Earth and Moon': [(False, 398.655), (True, 7.751), (False, 0.623), (True, 0.421), (False, 1.012), (True, 0.18), (False, 1.361), (True, 1.252), (False, 0.273), (True, 0.73), (False, 0.754), (True, 0.345), (False, 2.461), (True, 0.601), (False, 0.703), (True, 0.378), (False, 0.734), (True, 0.31), (False, 0.876), (True, 0.158), (False, 0.99), (True, 1.319), (False, 466.252)],
        'Languish': [(False, 402.668), (True, 14.362), (False, 0.077), (True, 5.55), (False, 465.482)],
        'Insect Swarm': [(False, 413.075), (True, 9.582), (False, 465.482)]
    },
    '0xF130008F5D001369': {
        'Languish': [(False, 423.817), (True, 5.117), (False, 57.57), (True, 10.289), (False, 391.346)],
        'Earth and Moon': [(False, 423.844), (True, 62.889), (False, 0.935), (True, 0.646), (False, 399.825)],
        'Moonfire': [(False, 423.939), (True, 464.2)],
        'Insect Swarm': [(False, 475.47), (True, 14.057), (False, 398.612)]
    },
    '0xF13000991600138A': {
        'Typhoon': [(False, 433.567), (True, 0.0), (False, 454.572)]
    },
    '0xF13000991600138D': {
        'Typhoon': [(False, 433.599), (True, 0.663), (False, 453.877)],
        'Moonfire': [(False, 433.91), (True, 0.352), (False, 453.877)]
    },
    '0xF13000991600138C': {
        'Typhoon': [(False, 433.778), (True, 0.7), (False, 453.661)]
    },
    '0xF130009916001386': {
        'Typhoon': [(False, 433.96), (True, 0.417), (False, 453.762)]
    },
    '0xF130009916001384': {
        'Moonfire': [(False, 435.325), (True, 0.272), (False, 452.542)]
    },
    '0xF1300099160013AD': {
        'Moonfire': [(False, 445.215), (True, 0.0), (False, 442.924)]
    },
    '0xF1300099160013AC': {
        'Moonfire': [(False, 446.471), (True, 0.345), (False, 441.323)]
    },
    '0xF1300099160013AA': {
        'Moonfire': [(False, 448.204), (True, 0.905), (False, 439.03)]
    },
    '0xF1300099160013BF': {
        'Moonfire': [(False, 450.905), (True, 1.488), (False, 435.746)]
    },
    '0xF1300099160013D2': {
        'Moonfire': [(False, 456.562), (True, 0.97), (False, 430.607)]
    },
    '0xF1300099160013D3': {
        'Typhoon': [(False, 462.467), (True, 3.226), (False, 422.446)],
        'Moonfire': [(False, 463.786), (True, 1.907), (False, 422.446)]
    },
    '0xF1300099160013C1': {
        'Moonfire': [(False, 466.992), (True, 0.569), (False, 420.578)]
    },
    '0xF1300099160013EA': {
        'Moonfire': [(False, 468.303), (True, 1.833), (False, 418.003)]
    },
    '0xF1300099160013E8': {
        'Moonfire': [(False, 470.653), (True, 417.486)]
    },
    '0xF130009916001400': {
        'Moonfire': [(False, 473.188), (True, 414.951)]
    },
    '0xF13000991600145F': {
        'Typhoon': [(False, 540.124), (True, 0.0), (False, 348.015)]
    },
    '0xF13000991600142C': {
        'Typhoon': [(False, 540.187), (True, 2.09), (False, 345.862)]
    },
    '0xF130009916001460': {
        'Typhoon': [(False, 540.231), (True, 2.411), (False, 345.497)]
    },
    '0xF13000991600145A': {
        'Typhoon': [(False, 540.231), (True, 2.046), (False, 345.862)],
        'Moonfire': [(False, 540.543), (True, 3.018), (False, 344.578)]
    },
    '0xF130009916001428': {
        'Typhoon': [(False, 540.231), (True, 2.484), (False, 345.424)]
    },
    '0xF130009916001456': {
        'Typhoon': [(False, 540.231), (True, 2.209), (False, 345.699)]
    },
    '0xF130009916001423': {
        'Typhoon': [(False, 540.286), (True, 2.038), (False, 345.815)]
    },
    '0xF13000991600142B': {
        'Typhoon': [(False, 540.409), (True, 2.637), (False, 345.093)]
    },
    '0xF130009916001426': {
        'Typhoon': [(False, 540.409), (True, 1.346), (False, 346.384)]
    },
    '0xF130009916001430': {
        'Typhoon': [(False, 540.445), (True, 1.832), (False, 345.862)],
        'Moonfire': [(False, 541.762), (True, 0.828), (False, 345.549)]
    },
    '0xF13000991600142F': {
        'Typhoon': [(False, 540.445), (True, 3.361), (False, 344.333)]
    },
    '0xF13000991600143C': {
        'Typhoon': [(False, 540.445), (True, 2.197), (False, 345.497)]
    },
    '0xF130009916001459': {
        'Typhoon': [(False, 540.445), (True, 0.255), (False, 347.439)]
    },
    '0xF130009916001420': {
        'Typhoon': [(False, 540.487), (True, 0.0), (False, 347.652)]
    },
    '0xF13000991600141E': {
        'Typhoon': [(False, 540.487), (True, 2.181), (False, 345.471)]
    },
    '0xF13000991600145D': {
        'Typhoon': [(False, 540.487), (True, 1.48), (False, 346.172)]
    },
    '0xF130009916001425': {
        'Typhoon': [(False, 540.587), (True, 6.057), (False, 341.495)]
    },
    '0xF13000991600142A': {
        'Typhoon': [(False, 540.587), (True, 3.273), (False, 344.279)]
    },
    '0xF13000991600142E': {
        'Typhoon': [(False, 540.816), (True, 1.037), (False, 346.286)]
    },
    '0xF13000991600145E': {
        'Moonfire': [(False, 543.106), (True, 0.754), (False, 344.279)]
    },
    '0xF130009916001482': {
        'Moonfire': [(False, 551.153), (True, 12.035), (False, 324.951)]
    },
    '0xF130009916001483': {
        'Moonfire': [(False, 552.325), (True, 3.053), (False, 332.761)]
    },
    '0xF130009916001493': {
        'Moonfire': [(False, 556.442), (True, 0.927), (False, 330.77)]
    },
    '0xF13000991600149F': {
        'Typhoon': [(False, 565.95), (True, 2.365), (False, 319.824)]
    },
    '0xF13000991600149B': {
        'Typhoon': [(False, 566.073), (True, 4.258), (False, 317.808)],
        'Moonfire': [(False, 568.123), (True, 2.208), (False, 317.808)]
    },
    '0xF13000991600149D': {
        'Typhoon': [(False, 566.128), (True, 6.025), (False, 315.986)],
        'Moonfire': [(False, 570.331), (True, 2.041), (False, 315.767)]
    },
    '0xF1300099160014BC': {
        'Moonfire': [(False, 572.691), (True, 1.417), (False, 314.031)]
    },
    '0xF1300099160014CE': {
        'Moonfire': [(False, 573.856), (True, 1.648), (False, 312.635)]
    },
    '0xF1300099160014D5': {
        'Moonfire': [(False, 576.473), (True, 311.666)],
        'Insect Swarm': [(False, 580.544), (True, 307.595)]
    },
    '0xF1300093A70014FA': {
        'Typhoon': [(False, 595.309), (True, 6.018), (False, 286.812)]
    },
    '0xF1300093A70014F4': {
        'Typhoon': [(False, 595.433), (True, 5.995), (False, 286.711)]
    },
    '0xF1300093A70014F2': {
        'Typhoon': [(False, 595.501), (True, 6.073), (False, 286.565)]
    },
    '0xF1300093A70014F8': {
        'Typhoon': [(False, 595.501), (True, 6.073), (False, 286.565)]
    },
    '0xF13000991600155B': {
        'Typhoon': [(False, 648.921), (True, 0.064), (False, 239.154)]
    },
    '0xF130009916001511': {
        'Typhoon': [(False, 649.028), (True, 5.861), (False, 233.25)]
    },
    '0xF130009916001568': {
        'Typhoon': [(False, 649.086), (True, 4.913), (False, 234.14)]
    },
    '0xF130009916001563': {
        'Typhoon': [(False, 649.086), (True, 5.778), (False, 233.275)]
    },
    '0xF130009916001562': {
        'Typhoon': [(False, 649.086), (True, 2.785), (False, 236.268)]
    },
    '0xF13000991600151C': {
        'Typhoon': [(False, 649.086), (True, 6.037), (False, 233.016)]
    },
    '0xF130009916001539': {
        'Typhoon': [(False, 649.086), (True, 5.778), (False, 233.275)]
    },
    '0xF130009916001538': {
        'Typhoon': [(False, 649.086), (True, 4.231), (False, 234.822)]
    },
    '0xF130009916001557': {
        'Typhoon': [(False, 649.086), (True, 6.037), (False, 233.016)]
    },
    '0xF13000991600150F': {
        'Typhoon': [(False, 649.141), (True, 3.422), (False, 235.576)]
    },
    '0xF130009916001518': {
        'Typhoon': [(False, 649.141), (True, 5.723), (False, 233.275)]
    },
    '0xF130009916001558': {
        'Typhoon': [(False, 649.141), (True, 1.719), (False, 237.279)]
    },
    '0xF130009916001517': {
        'Typhoon': [(False, 649.188), (True, 3.398), (False, 235.553)]
    },
    '0xF130009916001524': {
        'Typhoon': [(False, 649.188), (True, 3.398), (False, 235.553)]
    },
    '0xF130009916001567': {
        'Typhoon': [(False, 649.231), (True, 3.73), (False, 235.178)]
    },
    '0xF130009916001566': {
        'Typhoon': [(False, 649.231), (True, 3.355), (False, 235.553)]
    },
    '0xF13000991600151D': {
        'Typhoon': [(False, 649.231), (True, 2.688), (False, 236.22)]
    },
    '0xF130009916001510': {
        'Typhoon': [(False, 649.273), (True, 5.046), (False, 233.82)]
    },
    '0xF130009916001519': {
        'Moonfire': [(False, 649.481), (True, 0.486), (False, 238.172)]
    },
    '0xF13000991600151B': {
        'Moonfire': [(False, 650.482), (True, 1.207), (False, 236.45)]
    },
    '0xF13000991600157B': {
        'Moonfire': [(False, 652.717), (True, 3.389), (False, 232.033)]
    },
    '0xF13000991600155A': {
        'Moonfire': [(False, 654.646), (True, 1.072), (False, 232.421)]
    },
    '0xF130009916001570': {
        'Moonfire': [(False, 657.202), (True, 0.063), (False, 230.874)]
    },
    '0xF13000991600158D': {
        'Moonfire': [(False, 658.334), (True, 6.024), (False, 223.781)]
    },
    '0xF130009916001588': {
        'Moonfire': [(False, 659.371), (True, 1.204), (False, 227.564)]
    },
    '0xF130009916001578': {
        'Moonfire': [(False, 660.387), (True, 1.188), (False, 226.564)]
    },
    '0xF1300099160015D2': {
        'Typhoon': [(False, 684.03), (True, 0.166), (False, 203.943)]
    },
    '0xF1300099160015A2': {
        'Typhoon': [(False, 684.09), (True, 0.617), (False, 203.432)]
    },
    '0xF1300099160015EF': {
        'Typhoon': [(False, 684.09), (True, 204.049)]
    },
    '0xF1300099160015E6': {
        'Typhoon': [(False, 684.134), (True, 2.331), (False, 201.674)],
        'Moonfire': [(False, 685.184), (True, 1.281), (False, 201.674)]
    },
    '0xF1300099160015DC': {
        'Typhoon': [(False, 684.247), (True, 2.152), (False, 201.74)]
    },
    '0xF1300099160015B2': {
        'Typhoon': [(False, 684.504), (True, 203.635)]
    },
    '0xF1300099160015D3': {
        'Typhoon': [(False, 684.575), (True, 203.564)]
    },
    '0xF1300099160015E7': {
        'Typhoon': [(False, 684.575), (True, 203.564)],
        'Moonfire': [(False, 687.558), (True, 200.581)]
    },
    '0xF1300099160015DD': {
        'Typhoon': [(False, 684.607), (True, 203.532)]
    },
    '0xF1300099160015DA': {
        'Typhoon': [(False, 684.607), (True, 203.532)]
    },
    '0xF1300099160015B1': {
        'Typhoon': [(False, 684.651), (True, 203.488)]
    }
}

import numpy as np
from itertools import groupby

def to_ms(uptime: list):
    applied: bool
    _length: float
    w = []
    for applied, _length in uptime:
        w.extend([applied] * int(_length*1000))
    return w

def join_ms(uptime: list):
    applied: bool
    applied_last: bool
    s = 0
    tmp = []
    applied_last = uptime[0]
    for applied in uptime:
        if applied == applied_last:
            s += 1
        else:
            tmp.append((not applied, s))
            applied_last = applied
            s = 1
    tmp.append((applied, s))
    tmp = [(x,y/1000) for x,y in tmp]
    return tmp

def apply_or(final, c):
    return [x or y for x, y in zip(final, c)]


@running_time
def combine(all_cases):
    final = [False] * int(sum(x[1] for x in q1) * 1000)
    for c in all_cases:
        c = to_ms(c)
        final = apply_or(final, c)
    return join_ms(final)


def find_trues(final):
    slices = np.ma.clump_masked(np.ma.masked_where(final, final))
    return [(s.start, s.stop - 1) for s in slices]

def to_ms_numpy(uptime: list):
    func = [np.zeros, np.ones]
    a = [func[applied](int(_length * 1000), dtype=int) for applied, _length in uptime]
    return np.concatenate(a)

def condense(trues, dur):
    start = trues[0][0]
    if start != 0:
        yield False, start / 1000
    
    for (s1,f1), (s2,f2) in zip(trues, trues[1:]):
        yield  True, (f1-s1+1) / 1000
        yield False, (s2-f1-1) / 1000
    
    yield True, (f2-s2+1) / 1000

    end = dur-f2-1
    if end != 0:
        yield False, end / 1000

@running_time
def combine_numpy2(all_cases):
    dur = int(sum(x[1] for x in all_cases[0]) * 1000)
    final = np.zeros(dur, dtype=int)
    for uptime in all_cases:
        c = to_ms_numpy(uptime)
        final = np.logical_or(final, c)
    trues = find_trues(final)
    return condense(trues, dur)
# q1 = [(False, 21.547), (True, 7.893), (False, 58.699)]
# q2 = [(False, 28.274), (True, 14.037), (False, 45.828)]
# q3 = [(False, 47.832), (True, 8.723), (False, 31.584)]
q1 = [
    (False, 58.777), (True, 14.032), (False, 16.122), (True, 14.016), (False, 77.865), (True, 27.561), (False, 26.728), (True, 14.027),
    (False, 11.964), (True, 14.039), (False, 25.553), (True, 14.017), (False, 6.155), (True, 14.026), (False, 13.359), (True, 14.024), (False, 114.713),
    (True, 14.007), (False, 3.613), (True, 25.629), (False, 61.973), (True, 25.532), (False, 0.955), (True, 14.032), (False, 16.186), (True, 14.013), (False, 235.221)]
q2 = [(False, 121.547), (True, 7.893), (False, 758.699)]
q3 = [(False, 128.274), (True, 14.037), (False, 745.828)]

# all_cases = [q1, q2, q3]
all_cases = []
for guid, spells in casts.items():
    if 'Insect Swarm' in spells:
        x = spells["Insect Swarm"]
        all_cases.append(x)
final1 = combine(all_cases)
final2 = combine_numpy2(all_cases)
final2 = list(final2)
print(final1)
print(final2)
print(final1==final2)

print(f'{sum(x[1] for x in q1):.3f}')
print(f'{sum(x[1] for x in final1):.3f}')
print(f'{sum(x[1] for x in final2):.3f}')


# q1 = [
#     (False, 58.777), (True, 14.032), (False, 16.122), (True, 14.016), (False, 77.865), (True, 27.561), (False, 26.728), (True, 14.027),
#     (False, 11.964), (True, 14.039), (False, 25.553), (True, 14.017), (False, 6.155), (True, 14.026), (False, 13.359), (True, 14.024), (False, 114.713),
#     (True, 14.007), (False, 3.613), (True, 25.629), (False, 61.973), (True, 25.532), (False, 0.955), (True, 14.032), (False, 16.186), (True, 14.013), (False, 235.221)]
# q2 = [(False, 121.547), (True, 7.893), (False, 758.699)]
# q3 = [(False, 128.274), (True, 14.037), (False, 745.828)]
