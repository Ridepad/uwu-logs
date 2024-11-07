from c_path import Directories

jf = Directories.static / "talents.json"
jg = Directories.temp / "glyphs.json"
TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE"


class Glyphs(dict[str, str]):
    def __init__(self, glyphs_data: dict[str, str]):
        for i, (glyph_id, glyph_name) in enumerate(glyphs_data.items()):
            letter = TALENTS_ENCODE_STR[i]
            self[glyph_id] = letter
            self[glyph_name] = letter

    def make_string(self, glyphs: set[str]):
        same = set(self) & set(glyphs)
        letters = (
            self[glyph_id]
            for glyph_id in same
        )
        return ''.join(sorted(letters))

class GlyphsByType(dict[str, Glyphs]):
    def __init__(self, glyphs_data: dict[str, dict]):
        for glyph_type, _glyphs in glyphs_data.items():
            self[glyph_type] = Glyphs(_glyphs)

class GlyphsByClass(dict[str, GlyphsByType]):
    def __init__(self, glyphs_data: dict[str, dict]):
        for class_name, glyphs_by_type in glyphs_data.items():
            self[class_name] = GlyphsByType(glyphs_by_type)

    def make_glyph_string(self, class_name: str, glyphs: list[str]):
        class_glyphs = self[class_name]
        # glyphs = defaultdict(set)
        major = class_glyphs["major"].make_string(glyphs)
        minor = class_glyphs["minor"].make_string(glyphs)
        if len(major) < 3 and minor:
            return f"{major}Z{minor}"
        return f"{major}{minor}"


class TalentBySpec:
    def __init__(
        self,
        spec: int,
        talent_index: int,
        level: int,
    ):
        self.tree_index = int(spec)
        self.talent_index = int(talent_index)
        self.level = int(level)

    def __str__(self):
        return " | ".join((
            f"{self.tree_index:>2}",
            f"{self.talent_index:>3}",
            f"{self.level:>2}",
        ))

class TalentsTree:
    def __init__(self, spec_name: str, spec_index: int, nodes: list[list[int]]):
        self.nodes = nodes
        self.spec_name = spec_name
        self.spec_index = spec_index
        self.talent_ids = set(
            spell_id
            for node in nodes
            for spell_id in node
        )

    def get_talent(self, spell_id: int):
        for talent_index, node in enumerate(self.nodes):
            if spell_id in node:
                level = node.index(spell_id) + 1
                return TalentBySpec(
                    self.spec_index,
                    talent_index,
                    level,
                )
        return None

    
    def empty_tree(self):
        return [0] * len(self.nodes)


class TalentsData:
    def __init__(
        self,
        class_name: str,
        prefix: str,
        specs: list[str],
        trees: list[list[int]],
    ):
        self.class_name = class_name
        self.prefix = prefix
        self.trees = [
            TalentsTree(
                spec_name=specs[spec_index],
                spec_index=spec_index,
                nodes=nodes,
            )
            for spec_index, nodes in enumerate(trees)
        ]
    
    def find_spec(self, spell_id: int):
        for talents_tree in self.trees:
            if spell_id in talents_tree.talent_ids:
                return talents_tree.get_talent(spell_id)
                
        print(f"!!! {self.class_name} missing talent: {spell_id:>5}")

    def empty_tree(self, spec_index: int):
        spec_talents = self.trees[spec_index]
        return spec_talents.empty_tree()
    
    def empty_trees(self):
        return {
            tree.spec_index: tree.empty_tree()
            for tree in self.trees
        }

class TalentsDict(dict[str, TalentsData]):
    def __init__(self, data):
        for class_name, class_data in data.items():
            self[class_name] = TalentsData(class_name, **class_data)


TALENTS = TalentsDict(jf.json())
GLYPHS = GlyphsByClass(jg.json())
