
from multiprocessing import Pool
import os
import constants

def main(name):
    d = os.getcwd()
    pth = f"{d}\\LogsDir\\{name}\\GUIDS_DATA"
    guids = constants.pickle_read(pth)
    return {guid[:12] for guid in guids}

if __name__ == '__main__':
    folders = next(os.walk('./LogsDir/'))[1][:12]
    main_set = set()
    for f in folders:
        main_set |= main(f)

    # with Pool(6) as p:
        # m = p.map(main, folders)
    print(main_set)