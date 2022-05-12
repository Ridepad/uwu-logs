import pandas
import  main_db
import constants_WBF
import _kill_parser

def correct(s):
    db_n = f"kill_db/data_kills_{s}-{s+1}.pickle"
    print(db_n)
    df = main_db.df_read(db_n)
    a = []
    for row, data in df.iterrows():
        dur = data['duration']
        if dur < 2:
            a.append(row)
    print(f"{len(a)=}")
    # _kill_parser.main_parser(s*100, redo=a)


def __main():
    for x in range(33, 36):
        correct(x)

if __name__ == "__main__":
    __main()