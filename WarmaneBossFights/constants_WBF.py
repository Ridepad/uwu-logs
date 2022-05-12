from datetime import datetime
import json
import os
import pickle
import zlib
from time import perf_counter

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)

def running_time(f, end="\n"):
    def inner(*args, **kwargs):
        st = perf_counter()
        q = f(*args, **kwargs)
        fin = int((perf_counter() - st) * 1000)
        print(f' Done in {fin:>6,} ms with {f.__module__}.{f.__name__}', end=end)
        return q
    return inner

def get_all_files(ext, dir='.'):
    files = next(os.walk(dir))[2]
    files = sorted(files)
    return [file for file in files if file.rsplit('.', 1)[-1] == ext][::-1]

@running_time
def json_read(path: str):
    if not path.endswith('.json'):
        path = f"{path}.json"
    print("[LOAD JSON]:", path)
    try:
        with open(path) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

@running_time
def json_write(path: str, data, indent=2):
    if not path.endswith('.json'):
        path = f"{path}.json"
    with open(path, 'w') as file:
        json.dump(data, file, default=sorted, indent=indent, separators=(',', ':'))


@running_time
def bytes_write(path: str, data: bytes):
    with open(path, 'wb') as file:
        file.write(data)

@running_time
def bytes_read(path: str):
    with open(path, 'rb') as file:
        return file.read()


@running_time
def zlib_compress(__data, level=7):
    return zlib.compress(__data, level=level)

def pickle_dumps(data):
    return pickle.dumps(data)

@running_time
def zlib_pickle_write(data_raw, path: str):
    data_pickle = pickle_dumps(data_raw)
    comresesed = zlib_compress(data_pickle)
    bytes_write(path, comresesed)

@running_time
def zlib_decompress(data):
    return zlib.decompress(data)

@running_time
def pickle_from_bytes(data):
    return pickle.loads(data)

@running_time
def zlib_pickle_read(path: str):
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return pickle_from_bytes(data)


@running_time
def json_from_bytes(data):
    return json.loads(data)

@running_time
def json_to_bytes(data):
    return json.dumps(data).encode()

@running_time
def zlib_json_read(path: str):
    data_raw = bytes_read(path)
    data = zlib_decompress(data_raw)
    return json_from_bytes(data)

@running_time
def zlib_json_write(data_raw, path: str):
    data_json_encoded = json_to_bytes(data_raw)
    comresesed = zlib_compress(data_json_encoded)
    bytes_write(path, comresesed)


def add_data_to_json(json_name: str, new_data):
    old_data = json_read(json_name)

    combined_data = dict(old_data)
    combined_data.update(new_data)
    combined_data = dict(sorted(combined_data.items()))

    if old_data == combined_data:
        return

    now = datetime.now()
    old_name = now.strftime(f"trash/{json_name}-%Y-%m-%d-%H-%M-%S.json")

    full_name = f"{json_name}.json"
    if os.path.isfile(full_name):
        if os.path.isfile(old_name):
            os.remove(old_name)
        os.rename(full_name, old_name)

    json_write(full_name, combined_data)


CATEGORIES = {
    81: ['411', '412', '424', '430', '664', '684', '729', '880', '881', '883', '884', '1705', '2359', '3357', '3496', '4079', '4496', '4625', '4782', '4785'],
    92: ['6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '545', '546', '556', '557', '558', '559', '621', '705', '889', '890', '891', '892', '964', '1017', '1020', '1021', '1165', '1176', '1177', '1178', '1180', '1181', '1187', '1206', '1244', '1248', '1250', '1254', '1832', '1833', '1956', '2076', '2077', '2078', '2084', '2097', '2141', '2142', '2143', '2516', '2536', '2537', '2556', '2557', '2716'],
    95: ['229', '230', '231', '238', '239', '245', '246', '247', '388', '389', '396', '509', '512', '513', '515', '516', '603', '604', '610', '611', '612', '613', '614', '615', '616', '617', '618', '619', '700', '701', '714', '727', '869', '870', '907', '908', '909', '1005', '1006', '1157', '1175', '2016', '2017'],
    96: ['31', '32', '503', '504', '505', '506', '507', '508', '941', '973', '974', '975', '976', '977', '978', '1182', '1576', '1681', '1682'],
    97: ['42', '43', '44', '45', '46'],
    155: ['913', '1038', '1039', '1656', '1657', '1683', '1684', '1691', '1692', '1693', '1707', '1793', '2144', '2145', '2797', '2798', '3456', '3457', '3478', '3656'],
    156: ['252', '259', '273', '277', '279', '1255', '1282', '1295', '1685', '1686', '1687', '1688', '1689', '1690', '4436', '4437'],
    158: ['255', '283', '284', '288', '289', '291', '292', '963', '965', '966', '967', '968', '969', '970', '971', '972', '979', '981', '1040', '1041', '1261'],
    159: ['248', '249', '2416', '2417', '2418', '2419', '2420', '2421', '2422', '2436', '2497', '2576', '2676'],
    160: ['605', '606', '607', '608', '609', '626', '910', '911', '912', '914', '915', '937', '1281', '1396', '1552'],
    161: ['263', '271', '272', '1022', '1023', '1024', '1025', '1026', '1027', '1028', '1029', '1030', '1031', '1032', '1033', '1034', '1035', '1036', '1037', '1145'],
    162: ['293', '295', '303', '1183', '1184', '1185', '1186', '1203', '1260', '1936', '2796'],
    163: ['275', '1786', '1788', '1789', '1790', '1791', '1792'],
    165: ['397', '398', '399', '400', '401', '402', '403', '404', '405', '406', '407', '408', '409', '699', '875', '876', '1159', '1160', '1161', '1162', '1174', '2090', '2091', '2092', '2093'],
    168: ['1283', '1284', '1285', '1286', '1287', '1288', '1289', '1658', '2136', '2137', '2138', '2957', '2958', '3838', '3839', '3840', '3841', '3842', '3843', '3844', '3876', '4016', '4017', '4316', '4476', '4477', '4478', '4602', '4603'],
    169: ['116', '730', '731', '732', '733', '734', '735'],
    170: ['121', '122', '123', '124', '125', '877', '906', '1563', '1777', '1778', '1779', '1780', '1781', '1782', '1783', '1784', '1785', '1795', '1796', '1797', '1798', '1799', '1800', '1801', '1998', '1999', '2000', '2001', '2002', '3296'],
    171: ['126', '127', '128', '129', '130', '144', '150', '153', '306', '560', '726', '878', '905', '1225', '1243', '1257', '1516', '1517', '1556', '1557', '1558', '1559', '1560', '1561', '1836', '1837', '1957', '1958', '2094', '2095', '2096', '3217', '3218'],
    172: ['131', '132', '133', '134', '135', '137', '141'],
    187: ['260', '1188', '1279', '1280', '1291', '1694', '1695', '1696', '1697', '1698', '1699', '1700', '1701', '1702', '1703', '1704', '4624'],
    201: ['518', '519', '520', '521', '522', '523', '524', '762', '942', '943', '945', '948', '953', '1014', '1015'],
    14777: ['627', '760', '761', '765', '766', '768', '769', '770', '771', '772', '773', '774', '775', '776', '777', '778', '779', '780', '781', '782', '802', '841', '858', '859', '868'],
    14778: ['728', '736', '750', '842', '844', '845', '846', '847', '848', '849', '850', '851', '852', '853', '854', '855', '856', '857', '860', '861'],
    14779: ['843', '862', '863', '864', '865', '866', '867', '1311', '1312'],
    14780: ['1263', '1264', '1265', '1266', '1267', '1268', '1269', '1270', '1457', '2256', '2257'],
    14801: ['218', '219', '220', '221', '222', '223', '224', '225', '226', '582', '706', '707', '708', '709', '873', '1151', '1164', '1166', '1167', '1168'],
    14802: ['73', '154', '155', '156', '157', '158', '159', '161', '162', '165', '583', '584', '710', '711', '1153', '1169', '1170'],
    14803: ['208', '209', '211', '212', '213', '214', '216', '233', '587', '783', '784', '1171', '1258'],
    14804: ['166', '167', '168', '199', '200', '201', '202', '203', '204', '206', '207', '712', '713', '872', '1172', '1173', '1251', '1252', '1259', '1502'],
    14805: ['647', '648', '649', '650', '651', '652', '653', '654', '655', '656', '657', '658', '659', '660', '661', '666', '667', '668', '669', '670', '671', '672', '673', '674', '675', '676', '677', '678', '679', '680', '681', '682', '690', '691', '692', '693', '694', '695', '696', '697', '698'],
    14806: ['477', '478', '479', '480', '481', '482', '483', '484', '485', '486', '487', '488', '3778', '4296', '4516', '4517', '4518'],
    14808: ['628', '629', '630', '631', '632', '633', '634', '635', '636', '637', '638', '639', '640', '641', '642', '643', '644', '645', '646', '685', '686', '687', '688', '689', '1307', '2188'],
    14861: ['940', '1676', '1677', '1678', '1680'],
    14862: ['939', '1189', '1190', '1191', '1192', '1193', '1194', '1195', '1262', '1271', '1272', '1273', '1274', '1275', '1276'],
    14863: ['33', '34', '35', '36', '37', '38', '39', '40', '41', '547', '561', '938', '961', '962', '1277', '1356', '1357', '1358', '1359', '1360', '1428', '1596'],
    14864: ['944', '946', '955', '956', '957'],
    14865: ['763', '764', '893', '894', '896', '897', '898', '899', '900', '901', '902', '903', '958', '959', '960', '1638'],
    14866: ['947', '949', '950', '951', '952', '1007', '1008', '1009', '1010', '1011', '1012', '2082', '2083', '4598'],
    14881: ['1308', '1309', '1310', '1757', '1761', '1762', '1763', '1764', '1765', '1766', '2189', '2190', '2191', '2192', '2193', '2194', '2195', '2200'],
    14901: ['1717', '1718', '1721', '1722', '1723', '1727', '1737', '1751', '1752', '1755', '2080', '2085', '2086', '2087', '2088', '2089', '2199', '2476', '2776', '3136', '3137', '3836', '3837', '4585', '4586'],
    14921: ['489', '490', '491', '492', '493', '494', '495', '496', '497', '498', '499', '500', '1296', '1297', '1816', '1817', '1834', '1860', '1862', '1864', '1865', '1866', '1867', '1868', '1871', '1872', '1873', '1919', '2036', '2037', '2038', '2039', '2040', '2041', '2042', '2043', '2044', '2045', '2046', '2056', '2057', '2058', '2150', '2151', '2152', '2153', '2154', '2155', '2156', '2157', '3802', '3803', '3804', '4297', '4298', '4519', '4520', '4521', '4522', '4523', '4524', '4525', '4526'],
    14922: ['562', '564', '566', '568', '572', '574', '576', '578', '622', '624', '1856', '1858', '1869', '1874', '1876', '1996', '1997', '2047', '2049', '2050', '2051', '2146', '2148', '2176', '2178', '2180', '2182', '2184', '2187', '4396', '4402', '4403', '4404', '4817', '4818'],
    14923: ['563', '565', '567', '569', '573', '575', '577', '579', '623', '625', '1857', '1859', '1870', '1875', '1877', '2048', '2052', '2053', '2054', '2139', '2140', '2147', '2149', '2177', '2179', '2181', '2183', '2185', '2186', '4397', '4405', '4406', '4407', '4815', '4816'],
    14941: ['2756', '2758', '2760', '2761', '2762', '2763', '2764', '2765', '2766', '2767', '2768', '2769', '2770', '2771', '2772', '2773', '2777', '2778', '2779', '2780', '2781', '2782', '2783', '2784', '2785', '2786', '2787', '2788', '2816', '2817', '2836', '3676', '3677', '3736', '4596'],
    14961: ['2886', '2888', '2890', '2892', '2894', '2903', '2905', '2907', '2909', '2911', '2913', '2914', '2915', '2919', '2923', '2925', '2927', '2930', '2931', '2933', '2934', '2937', '2939', '2940', '2941', '2945', '2947', '2951', '2953', '2955', '2959', '2961', '2963', '2967', '2969', '2971', '2973', '2975', '2977', '2979', '2980', '2982', '2985', '2989', '2996', '3003', '3004', '3006', '3008', '3009', '3012', '3014', '3015', '3036', '3056', '3058', '3076', '3097', '3138', '3141', '3157', '3158', '3159', '3176', '3177', '3178', '3179', '3180', '3181', '3182', '3316'],
    14962: ['2887', '2889', '2891', '2893', '2895', '2904', '2906', '2908', '2910', '2912', '2916', '2917', '2918', '2921', '2924', '2926', '2928', '2929', '2932', '2935', '2936', '2938', '2942', '2943', '2944', '2946', '2948', '2952', '2954', '2956', '2960', '2962', '2965', '2968', '2970', '2972', '2974', '2976', '2978', '2981', '2983', '2984', '2995', '2997', '3002', '3005', '3007', '3010', '3011', '3013', '3016', '3017', '3037', '3057', '3059', '3077', '3098', '3118', '3161', '3162', '3163', '3164', '3183', '3184', '3185', '3186', '3187', '3188', '3189', '3237'],
    14981: ['3556', '3557', '3558', '3559', '3576', '3577', '3578', '3579', '3580', '3581', '3582', '3596', '3597'],
    15001: ['3797', '3798', '3799', '3800', '3808', '3809', '3810', '3917', '3918', '3936', '3996', '4080'],
    15002: ['3812', '3813', '3814', '3815', '3816', '3817', '3818', '3819', '3916', '3937', '3997'],
    15003: ['3776', '3777', '3845', '3846', '3847', '3848', '3849', '3850', '3851', '3852', '3853', '3854', '3855', '3856', '3857', '3957', '4176', '4177', '4256'],
    15041: ['4527', '4528', '4529', '4530', '4531', '4532', '4534', '4535', '4536', '4537', '4538', '4539', '4577', '4578', '4579', '4580', '4581', '4582', '4583', '4601', '4628', '4629', '4630', '4631', '4636'],
    15042: ['4584', '4597', '4604', '4605', '4606', '4607', '4608', '4610', '4611', '4612', '4613', '4614', '4615', '4616', '4617', '4618', '4619', '4620', '4621', '4622', '4632', '4633', '4634', '4635', '4637']
}

BOSSES_CATS = {
    "Onyxia's Lair": ['Onyxia', ],
    'The Eye of Eternity': ['Malygos', ],
    'The Obsidian Sanctum': ['Sartharion', ],
    'The Ruby Sanctum': ['Baltharus the Warborn', 'General Zarithrian', 'Saviana Ragefire', 'Halion', ],
    'Trial of the Crusader': ['Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions', "Twin Val'kyr", "Anub'arak", ],
    'Vault of Archavon': ['Archavon the Stone Watcher', 'Emalon the Storm Watcher', 'Koralon the Flame Watcher', 'Toravon the Ice Watcher', ],
    'Icecrown Citadel': [
        'Lord Marrowgar', 'Lady Deathwhisper', 'Gunship Battle', 'Deathbringer Saurfang',
        'Festergut', 'Rotface', 'Professor Putricide',
        'Blood Prince Council', "Blood-Queen Lana'thel",
        'Valithria Dreamwalker', 'Sindragosa',
        'The Lich King',
    ],
    'Naxxramas': [
        "Anub'Rekhan", 'Grand Widow Faerlina', 'Maexxna',
        'Noth the Plaguebringer', 'Heigan the Unclean', 'Loatheb',
        'Patchwerk', 'Grobbulus', 'Gluth', 'Thaddius',
        'Instructor Razuvious', 'Gothik the Harvester', 'The Four Horsemen',
        'Sapphiron',
        "Kel'Thuzad",
    ],
    'Ulduar': [
        'Flame Leviathan', 'Ignis the Furnace Master', 'Razorscale', 'XT-002 Deconstructor',
        'Assembly of Iron', 'Kologarn', 'Auriaya', 'Hodir', 'Thorim', 'Freya', 'Mimiron',
        'General Vezax', 'Yogg-Saron', 'Algalon the Observer',
    ],
}

BOSSES = [
    'The Lich King', 'Halion','Deathbringer Saurfang', 'Festergut', 'Rotface', 'Professor Putricide', "Blood-Queen Lana'thel", 'Sindragosa',
    'Lord Marrowgar', 'Lady Deathwhisper', 'Gunship Battle', 'Blood Prince Council', 'Valithria Dreamwalker',
    'Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions', "Twin Val'kyr", "Anub'arak", 
    'Onyxia', 'Malygos', 'Sartharion', 'Baltharus the Warborn', 'General Zarithrian', 'Saviana Ragefire', 
    'Archavon the Stone Watcher', 'Emalon the Storm Watcher', 'Koralon the Flame Watcher', 'Toravon the Ice Watcher',
    "Anub'Rekhan", 'Grand Widow Faerlina', 'Maexxna', 'Noth the Plaguebringer', 'Heigan the Unclean', 'Loatheb', 'Patchwerk',
    'Grobbulus', 'Gluth', 'Thaddius', 'Instructor Razuvious', 'Gothik the Harvester', 'The Four Horsemen', 'Sapphiron', "Kel'Thuzad",
    'Flame Leviathan', 'Ignis the Furnace Master', 'Razorscale', 'XT-002 Deconstructor', 'Assembly of Iron', 'Kologarn', 'Auriaya',
    'Hodir', 'Thorim', 'Freya', 'Mimiron', 'General Vezax', 'Yogg-Saron', 'Algalon the Observer'
]

BOSSES_FROM_HTML = {
    "the-lich-king": "The Lich King",
    "halion": "Halion",
    "deathbringer-saurfang": "Deathbringer Saurfang",
    "festergut": "Festergut",
    "rotface": "Rotface",
    "professor-putricide": "Professor Putricide",
    "blood-queen-lanathel": "Blood-Queen Lana'thel",
    "sindragosa": "Sindragosa",
    "lord-marrowgar": "Lord Marrowgar",
    "lady-deathwhisper": "Lady Deathwhisper",
    "gunship-battle": "Gunship Battle",
    "blood-prince-council": "Blood Prince Council",
    "valithria-dreamwalker": "Valithria Dreamwalker",
    "northrend-beasts": "Northrend Beasts",
    "lord-jaraxxus": "Lord Jaraxxus",
    "faction-champions": "Faction Champions",
    "twin-valkyr": "Twin Val'kyr",
    "anubarak": "Anub'arak",
    "onyxia": "Onyxia",
    "malygos": "Malygos",
    "sartharion": "Sartharion",
    "baltharus-the-warborn": "Baltharus the Warborn",
    "general-zarithrian": "General Zarithrian",
    "saviana-ragefire": "Saviana Ragefire",
    "archavon-the-stone-watcher": "Archavon the Stone Watcher",
    "emalon-the-storm-watcher": "Emalon the Storm Watcher",
    "koralon-the-flame-watcher": "Koralon the Flame Watcher",
    "toravon-the-ice-watcher": "Toravon the Ice Watcher",
    "anubrekhan": "Anub'Rekhan",
    "grand-widow-faerlina": "Grand Widow Faerlina",
    "maexxna": "Maexxna",
    "noth-the-plaguebringer": "Noth the Plaguebringer",
    "heigan-the-unclean": "Heigan the Unclean",
    "loatheb": "Loatheb",
    "patchwerk": "Patchwerk",
    "grobbulus": "Grobbulus",
    "gluth": "Gluth",
    "thaddius": "Thaddius",
    "instructor-razuvious": "Instructor Razuvious",
    "gothik-the-harvester": "Gothik the Harvester",
    "the-four-horsemen": "The Four Horsemen",
    "sapphiron": "Sapphiron",
    "kelthuzad": "Kel'Thuzad",
    "flame-leviathan": "Flame Leviathan",
    "ignis-the-furnace-master": "Ignis the Furnace Master",
    "razorscale": "Razorscale",
    "xt-002-deconstructor": "XT-002 Deconstructor",
    "assembly-of-iron": "Assembly of Iron",
    "kologarn": "Kologarn",
    "auriaya": "Auriaya",
    "hodir": "Hodir",
    "thorim": "Thorim",
    "freya": "Freya",
    "mimiron": "Mimiron",
    "general-vezax": "General Vezax",
    "yogg-saron": "Yogg-Saron",
    "algalon-the-observer": "Algalon the Observer"
}

def icon_cdn(name, size="medium"):
    if size not in ['large', 'medium', 'small']:
        return
    url = "https://wotlk.evowow.com/static/images/wow/icons"
    return f"{url}/{size}/{name}.jpg"


CLASSES = {
  "Death Knight": {
    "": "class_deathknight",
    "Blood": "spell_deathknight_bloodpresence",
    "Frost": "spell_deathknight_frostpresence",
    "Unholy": "spell_deathknight_unholypresence"
  },
  "Druid": {
    "": "class_druid",
    "Balance": "spell_nature_starfall",
    "Feral Combat": "ability_racial_bearform",
    "Restoration": "spell_nature_healingtouch"
  },
  "Hunter": {
    "": "class_hunter",
    "Beast Mastery": "ability_hunter_beasttaming",
    "Marksmanship": "ability_marksmanship",
    "Survival": "ability_hunter_swiftstrike"
  },
  "Mage": {
    "": "class_mage",
    "Arcane": "spell_holy_magicalsentry",
    "Fire": "spell_fire_firebolt02",
    "Frost": "spell_frost_frostbolt02"
  },
  "Paladin": {
    "": "class_paladin",
    "Holy": "spell_holy_holybolt",
    "Protection": "spell_holy_devotionaura",
    "Retribution": "spell_holy_auraoflight"
  },
  "Priest": {
    "": "class_priest",
    "Discipline": "spell_holy_wordfortitude",
    "Holy": "spell_holy_guardianspirit",
    "Shadow": "spell_shadow_shadowwordpain"
  },
  "Rogue": {
    "": "class_rogue",
    "Assassination": "ability_rogue_eviscerate",
    "Combat": "ability_backstab",
    "Subtlety": "ability_stealth"
  },
  "Shaman": {
    "": "class_shaman",
    "Elemental": "spell_nature_lightning",
    "Enhancement": "spell_nature_lightningshield",
    "Restoration": "spell_nature_magicimmunity"
  },
  "Warlock": {
    "": "class_warlock",
    "Affliction": "spell_shadow_deathcoil",
    "Demonology": "spell_shadow_metamorphosis",
    "Destruction": "spell_shadow_rainoffire"
  },
  "Warrior": {
    "": "class_warrior",
    "Arms": "ability_rogue_eviscerate",
    "Fury": "ability_warrior_innerrage",
    "Protection": "ability_warrior_defensivestance"
  }
}

CLASSES_LIST = list(CLASSES)
SPECS_LIST = {name: list(v) for name, v in CLASSES.items()}
# SPECS_LIST = [icon for v in CLASSES.values() for icon in v.values()]
# print(SPECS_LIST[26])
RACES_LIST = ['Blood Elf', 'Draenei', 'Dwarf', 'Gnome', 'Human', 'Night Elf', 'Orc', 'Tauren', 'Troll', 'Undead']
FACTION = {"Horde": 1, "Alliance": 0}
FACTION = ["Alliance", "Horde"]
