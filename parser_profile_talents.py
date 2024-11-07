from c_path import Directories

from parser_talents_data import (
    TALENTS,
    TALENTS_ENCODE_STR,
)


class TalentsParsed:
    def __init__(
        self,
        main_spec_name: str,
        talents_allocated_str: str,
        encoded_string: str,
    ):
        self.main_spec_name = main_spec_name
        self.talents_allocated_str = talents_allocated_str
        self.encoded_string = encoded_string

    def add_glyphs_to_talent_string(self, encoded_glyphs: str):
        if encoded_glyphs:
            self.encoded_string = f"{self.encoded_string}:{encoded_glyphs}"

    def as_list(self):
        return [
            self.main_spec_name,
            self.talents_allocated_str,
            self.encoded_string,
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

