import constants_WBF
import _kill_parser

CLASSES_LIST = constants_WBF.CLASSES_LIST
SPECS_LIST = constants_WBF.SPECS_LIST

def convert_back(report_data):
    for name, class_, spec in zip(report_data['names'], report_data['classes'], report_data['specs']):
        class_name = CLASSES_LIST[class_]
        specs_list = SPECS_LIST[class_name]
        spec_name = specs_list[spec]
        print(f"{name:<12} | {class_name:<12} {spec_name}")


def main2():
    
    report_data = _kill_parser.get_report_info(3629903)
    print(report_data)
    classes = report_data['classes']
    specs = report_data['specs']
    for i, (class_name, spec_name) in enumerate(zip(classes, specs)):
        c_i = CLASSES_LIST.index(class_name)
        specs_list = SPECS_LIST[class_name]
        s_i = specs_list.index(spec_name)
        classes[i] = c_i
        specs[i] = s_i
    print(report_data)
    convert_back(report_data)


main2()