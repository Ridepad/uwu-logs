'''
One shot backfill: writes LOGS_CUT.bin next to every existing LOGS_CUT.zstd.
A report only counts as done once the binary renders back to the text form
exactly. --prune is destructive, run it only after a full clean pass.

    python logs_backfill_columnar.py            # write and verify, keep both
    python logs_backfill_columnar.py --check    # verify only, write nothing
    python logs_backfill_columnar.py --prune    # drop verified LOGS_CUT.zstd
'''

import sys
from time import perf_counter

import logs_columnar
from c_path import Directories, FileNames


def verify(report_dir, data: bytes):
    want = report_dir.joinpath(FileNames.logs_cut).zstd_read().splitlines()
    got = logs_columnar.LogsView(logs_columnar.decode(data))
    if len(got) != len(want):
        return False, f"row count {len(got)} != {len(want)}"
    for i, (a, b) in enumerate(zip(got, want)):
        if a != b:
            return False, f"row {i}:\n    got  {a}\n    want {b}"
    return True, None


def backfill_one(report_dir, check_only: bool):
    path_bin = report_dir / FileNames.logs_cut_bin
    path_txt = report_dir / FileNames.logs_cut

    if not path_txt.is_file():
        return "skipped", "no LOGS_CUT.zstd"

    if check_only:
        if not path_bin.is_file():
            return "skipped", "no LOGS_CUT.bin"
        ok, why = verify(report_dir, path_bin.read_bytes())
        return ("verified", None) if ok else ("failed", why)

    rows = path_txt.zstd_read_bytes().split(b"\n")
    data = logs_columnar.encode(row for row in rows if row)

    ok, why = verify(report_dir, data)
    if not ok:
        return "failed", why

    # temp name first, so a crash never leaves a half file in place
    temp = report_dir / f"{FileNames.logs_cut_bin}.tmp"
    temp.write_bytes(data)
    temp.replace(path_bin)
    return "written", f"{path_txt.stat().st_size:,} -> {len(data):,}"


def main(argv: list[str]):
    check_only = "--check" in argv
    prune = "--prune" in argv

    report_dirs = sorted(Directories.logs.directories)
    print(f"{len(report_dirs):,} reports in {Directories.logs}")

    counts = {}
    failures = []
    size_before = size_after = 0
    pc = perf_counter()

    for i, report_dir in enumerate(report_dirs, 1):
        try:
            status, detail = backfill_one(report_dir, check_only)
        except Exception as error:
            status, detail = "failed", f"{type(error).__name__}: {error}"

        counts[status] = counts.get(status, 0) + 1
        if status == "failed":
            failures.append((report_dir.name, detail))
            print(f"  FAILED {report_dir.name}\n    {detail}")
        elif status == "written":
            before, _, after = detail.partition(" -> ")
            size_before += int(before.replace(",", ""))
            size_after += int(after.replace(",", ""))

        if i % 200 == 0 or i == len(report_dirs):
            done = ", ".join(f"{k}={v:,}" for k, v in sorted(counts.items()))
            print(f"  [{i:,}/{len(report_dirs):,}] {done}  {perf_counter()-pc:.0f}s")

    print(f"\n{', '.join(f'{k}={v:,}' for k, v in sorted(counts.items()))}")
    if size_before:
        print(f"LOGS_CUT: {size_before:,} -> {size_after:,} bytes "
              f"({size_before/size_after:.2f}x smaller)")

    if failures:
        print(f"\n{len(failures):,} reports failed; nothing was pruned")
        return 1

    if prune:
        pruned = 0
        for report_dir in report_dirs:
            path_bin = report_dir / FileNames.logs_cut_bin
            path_txt = report_dir / FileNames.logs_cut
            if path_bin.is_file() and path_txt.is_file():
                path_txt.unlink()
                pruned += 1
        print(f"pruned {pruned:,} LOGS_CUT.zstd files")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
