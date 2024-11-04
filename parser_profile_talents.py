from dataclasses import dataclass

from c_path import Directories

jf = Directories.static / "talents.json"
jg = Directories.static / "glyphs.json"
TALENTS_ENCODE_STR = "0zMcmVokRsaqbdrfwihuGINALpTjnyxtgevE"
GLYPHS = jg.json()

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
        # self.specs = specs
        self.prefix = prefix
        # self.trees = TalentsTrees()
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


@dataclass
class TalentsParsed:
    main_spec_name: str
    talents_allocated_str: str
    tree_string: str

    def as_list(self):
        return [
            self.main_spec_name,
            self.talents_allocated_str,
            self.tree_string,
        ]


class Talent:
    def __init__(self, **kwargs):
        self.spell_id = int(kwargs["spell"])
        self.spec = kwargs["spec"] or 0
        self.name = kwargs["name"] or ""

    def __str__(self):
        return " | ".join((
            f"{self.spell_id:>5}",
            f"{self.spec}",
            f"{self.name}",
        ))




def convert_to_string(talents_tree: list[int]):
    if len(talents_tree) & 1:
        talents_tree.append(0)
    
    z = zip(talents_tree[::2], talents_tree[1::2])
    g = (TALENTS_ENCODE_STR[r1 * 6 + r2] for r1, r2 in z)
    s = "".join(g)
    
    if s[-1] == TALENTS_ENCODE_STR[0]:
        return s.rstrip(TALENTS_ENCODE_STR[0]) + "Z"
    return s

def convert_spec_to_string(trees: list[list[int]]):
    tree_gen = (convert_to_string(tree) for tree in trees)
    return "".join(tree_gen).rstrip("Z")
    

class PlayerTalents:
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.class_talents = TALENTS[class_name]
    
    def spec_data(self, trees: list[list[int]]):
        tree_string = convert_spec_to_string(trees)
        tree_string = self.class_talents.prefix + tree_string

        allocated = [sum(tree) for tree in trees]
        spec_index_max_allocated = allocated.index(max(allocated))
        main_spec = self.class_talents.trees[spec_index_max_allocated]
        talents_allocated_str = "/".join(map(str, allocated))
        
        return TalentsParsed(
            main_spec.spec_name,
            talents_allocated_str,
            tree_string,
        )
    
    
class PlayerTalentsWC(PlayerTalents):
    def convert_talents(self, allocated_talents: list[int]):
        trees_d = self.class_talents.empty_trees()
        for spell_id in allocated_talents:
            talent = self.class_talents.find_spec(spell_id)
            if not talent:
                continue
            trees_d[talent.tree_index][talent.talent_index] = talent.level
        return trees_d.values()
    
    def get_talents_data(self, allocated_talents: list[int]):
        trees = self.convert_talents(allocated_talents)
        return self.spec_data(trees)


class PlayerTalentsRG(PlayerTalents):
    def convert_talents(self, allocated_points: str):
        trees: list[list[int]] = []
        for tree in self.class_talents.trees:
            tree_size = len(tree.nodes)
            current_tree = allocated_points[:tree_size]
            allocated_points = allocated_points[tree_size:]
            trees.append(list(map(int, current_tree)))
        return self.spec_data(trees)
    
    def get_talents_data(self, allocated_points: str):
        return self.convert_talents(allocated_points).as_list()
    
    def get_talents_data_list(self, talents: list[str]):
        return [
            self.get_talents_data(allocated_points)
            for allocated_points in talents
        ]


class Glyphs:
    def __init__(self, glyphs: list[int]):
        pass


def main():
    qf = Directories.temp / "test_wc_talents.json"
    q = qf.json()
    data = q["result"]["data"]
    print(data)
    q2 = [Talent(**x).spell_id for x in data]
    # pt = PlayerTalents("Hunter", q2)
    pt = PlayerTalentsWC("Druid", q2)
    z = pt.convert_to_talents_string()
    print(z)


if __name__ == "__main__":
    main()

