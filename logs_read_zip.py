import constants

import py7zr

import pylzma 


PATH = './LogsDir/'

def _read(name):
    with open(f'{PATH}/{name}/Logs_cut.txt', 'r') as f:
        _f = f.read()
    return _f

@constants.running_time
def _read2(name):
    with py7zr.SevenZipFile(f'{PATH}/{name}/Archive.7z', 'r') as zip:
        allfiles = zip.getnames()
        for fname, bio in zip.read(allfiles).items():
            print(f'{fname}: {bio.readline()}')

@constants.running_time
def add_to(name):
    with py7zr.SevenZipFile(f'{PATH}/{name}/Archive.7z', 'w') as archive:
        archive.write(f'{PATH}/{name}/Logs_cut.txt')

def main():
    name = '21-10-03--00-09--Lismee'
    # L = _read(name)
    _read2(name)
    # add_to(name)

if __name__ == "__main__":
    main()