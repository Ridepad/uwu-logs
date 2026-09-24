'''
LOGS_CUT.bin layout. Same rows in the same order as LOGS_CUT.zstd, split into
per-field integer columns behind a report level string dictionary.

Normalized rows are 9 fields wide (see logs_fix):
    timestamp,flag,sGUID,sName,tGUID,tName,spell_id,spell_name,<tail>

    header (once per report)
        magic b"UWUL", u16 version, u32 row_count, u16 block_count
        dicts: events \0 spells \0 strings \0 guids \0 names \0
        block table: per block { global_start_row, ms_base, byte_offset, byte_len }

    block (zstd'd on its own, one per pull, so one boss reads alone)
        ts      u32 ms, stored as deltas, cumsum'd on load
        ev      u8  index into events
        sguid   u8/u16/u32 index into guids
        tguid   u8/u16/u32 index into guids
        spell   u8/u16/u32 index into spells; an entry is id/name/school
        arity   u8  field count of this row's tail
        tail    one signed column per slot, padded to the report's widest
                arity; negative indexes strings, so `nil` / `PARRY` round trip
        namefix sparse (row, guid_slot, name_index) overrides, normally empty

Names live in the guid dict, not in a column: a GUID has one name for the whole
report, except pets and vehicles that log as Unknown until they resolve. Those
rows are restored from namefix, which is what keeps the format byte exact.
'''

import array
from collections import OrderedDict
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, NamedTuple

import numpy
import zstd

MAGIC = b"UWUL"
VERSION = 3

NEW_LINE = b'\n'
COMMA = b','
DICT_END = b'\x00'
SPELL_SEP = b'\x1f'

# 3 matches what LOGS_CUT.zstd used
COMPRESS_LEVEL = 3

# how many blocks may stay rendered as text at once, per report
RENDERED_BLOCK_CACHE = 2

# fixed width, not varints: ~2% bigger on disk, but a column reads straight
# into numpy with no per row decode
TS_DTYPE = numpy.uint32
EV_DTYPE = numpy.uint8
SPINE_WIDTHS = {1: numpy.uint8, 2: numpy.uint16, 4: numpy.uint32}

# same deal, padded to the widest arity in the report; ~20% bigger than varints
TAIL_DTYPES = {1: numpy.int8, 2: numpy.int16, 4: numpy.int32, 8: numpy.int64}

def _tail_width_for(low: int, high: int):
    """Narrowest signed width that holds a column's whole value range."""
    for width, dtype in TAIL_DTYPES.items():
        info = numpy.iinfo(dtype)
        if info.min <= low and high <= info.max:
            return width
    raise ValueError(f"tail value out of range: {low}..{high}")


def _width_for(count: int):
    """Narrowest spine width that can index `count` dictionary entries."""
    if count <= 0x100:
        return 1
    if count <= 0x10000:
        return 2
    return 4

SOURCE_SLOT = 0
TARGET_SLOT = 1

# UNIT_DIED and PARTY_KILL normalize to 6 fields, not 9; index 0 means no spell
NO_SPELL = 0


def _uvarint(buf: bytearray, value: int):
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            buf.append(byte | 0x80)
        else:
            buf.append(byte)
            return

def _zigzag(buf: bytearray, value: int):
    _uvarint(buf, (value << 1) if value >= 0 else (-value << 1) - 1)


class _Reader:
    __slots__ = ("data", "pos")

    def __init__(self, data: bytes, pos: int=0) -> None:
        self.data = data
        self.pos = pos

    def u8(self):
        value = self.data[self.pos]
        self.pos += 1
        return value

    def uvarint(self):
        data = self.data
        pos = self.pos
        value = 0
        shift = 0
        while True:
            byte = data[pos]
            pos += 1
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                self.pos = pos
                return value
            shift += 7

    def zigzag(self):
        value = self.uvarint()
        return (value >> 1) if not value & 1 else -((value + 1) >> 1)

    def blob(self, length: int):
        end = self.pos + length
        chunk = self.data[self.pos:end]
        self.pos = end
        return chunk


class _Interner:
    '''Assigns a stable index to every distinct value, in first seen order.'''
    __slots__ = ("index", "values")

    def __init__(self) -> None:
        self.index: dict[bytes, int] = {}
        self.values: list[bytes] = []

    def __len__(self):
        return len(self.values)

    def add(self, value: bytes):
        try:
            return self.index[value]
        except KeyError:
            pass
        i = self.index[value] = len(self.values)
        self.values.append(value)
        return i

    def to_bytes(self):
        return NEW_LINE.join(self.values) + DICT_END

    @staticmethod
    def from_reader(reader: _Reader):
        data = reader.data
        end = data.index(DICT_END, reader.pos)
        chunk = data[reader.pos:end]
        reader.pos = end + 1
        if not chunk:
            return []
        return chunk.split(NEW_LINE)



class _BlockEncoder:
    '''Builds the columns of one encounter block. Every row goes in via `add`.'''

    def __init__(self, global_start_row: int) -> None:
        self.global_start_row = global_start_row
        # spine, absolute ms; packed to fixed width once the dictionary sizes
        # are known
        self.ms: list[int] = []
        self.ev: list[int] = []
        self.sguid: list[int] = []
        self.tguid: list[int] = []
        self.spell: list[int] = []
        # tail, one column per slot, padded so every column has row_count
        # entries; int32 covers every field the game emits
        self.arity = bytearray()
        self.tail_cols: list[array.array] = []
        self.namefix = bytearray()

    @property
    def row_count(self):
        return len(self.ms)

    @property
    def ms_base(self):
        return self.ms[0]

    def add(
        self, ms: int, ev_i: int, sguid_i: int, tguid_i: int, spell_i: int,
        tail: list[int], namefix: list[tuple[int, int]],
    ):
        '''
        Appends one row. `namefix` is (slot, name_index) for each guid whose
        name differs from the one in the guid dict.
        '''
        row = self.row_count
        for slot, name_index in namefix:
            _uvarint(self.namefix, row)
            self.namefix.append(slot)
            _uvarint(self.namefix, name_index)

        self.ms.append(ms)
        self.ev.append(ev_i)
        self.sguid.append(sguid_i)
        self.tguid.append(tguid_i)
        self.spell.append(spell_i)

        self.arity.append(len(tail))
        while len(self.tail_cols) < len(tail):
            # a new slot back-fills zeros for the rows before this one
            self.tail_cols.append(array.array("i", bytes(4 * row)))
        for column, value in zip(self.tail_cols, tail):
            column.append(value)
        for column in self.tail_cols[len(tail):]:
            column.append(0)

    def tail_bounds(self):
        '''(low, high) per tail column, for choosing the narrowest widths.'''
        return [
            (min(column), max(column)) if len(column) else (0, 0)
            for column in self.tail_cols
        ]

    def to_bytes(self, guid_width: int, spell_width: int, tail_widths: list[int]):
        guid_dtype = SPINE_WIDTHS[guid_width]
        spell_dtype = SPINE_WIDTHS[spell_width]
        # deltas: consecutive lines are ms apart, so the high bytes stay zero
        # and zstd squashes the column. cumsum'd back into offsets on load.
        # a bugged line can step backwards; uint32 wraps and cumsum unwraps it
        ms = numpy.array(self.ms, dtype=numpy.int64)
        deltas = numpy.diff(ms, prepend=ms[:1]).astype(TS_DTYPE)
        spine = b"".join((
            deltas.tobytes(),
            numpy.array(self.ev, dtype=EV_DTYPE).tobytes(),
            numpy.array(self.sguid, dtype=guid_dtype).tobytes(),
            numpy.array(self.tguid, dtype=guid_dtype).tobytes(),
            numpy.array(self.spell, dtype=spell_dtype).tobytes(),
        ))

        tail = []
        for slot, width in enumerate(tail_widths):
            dtype = TAIL_DTYPES[width]
            if slot < len(self.tail_cols):
                column = numpy.frombuffer(self.tail_cols[slot], dtype=numpy.int32)
                tail.append(column.astype(dtype).tobytes())
            else:
                # unused here, but the grid is fixed across the report
                tail.append(numpy.zeros(self.row_count, dtype=dtype).tobytes())

        head = bytearray()
        _uvarint(head, self.row_count)
        _uvarint(head, len(self.namefix))
        return b"".join((
            bytes(head), spine, bytes(self.arity),
            b"".join(tail), bytes(self.namefix),
        ))


class Encoder:
    '''
    Accumulates normalized rows, then emits the LOGS_CUT.bin payload.

    Rows must arrive in file order. Pass `new_block=True` on the first row of
    every encounter; without it the result is a single block, which is valid
    and only gives up the partial read.
    '''

    def __init__(self) -> None:
        self.events = _Interner()
        self.guids = _Interner()
        self.spells = _Interner()
        self.spells.add(b"")  # reserve NO_SPELL at index 0
        self.strings = _Interner()
        # guid index -> name index, the first name seen for that guid
        self.guid_names: list[int] = []
        self.names = _Interner()
        self.blocks: list[_BlockEncoder] = []
        self.row_count = 0

    def _guid(self, guid: bytes, name: bytes):
        '''Returns (guid_index, name_index or None when it matches the dict).'''
        known = self.guids.index.get(guid)
        name_i = self.names.add(name)
        if known is None:
            known = self.guids.add(guid)
            self.guid_names.append(name_i)
            return known, None
        if self.guid_names[known] == name_i:
            return known, None
        return known, name_i

    def add_row(self, ms: int, fields: list[bytes], new_block: bool=False):
        '''
        `fields` is a normalized row split on ',' with maxsplit=8: the 8 fixed
        fields plus the rest of the line as one blob.
        '''
        if new_block or not self.blocks:
            self.blocks.append(_BlockEncoder(self.row_count))

        sguid_i, sname_i = self._guid(fields[2], fields[3])
        tguid_i, tname_i = self._guid(fields[4], fields[5])
        namefix = []
        if sname_i is not None:
            namefix.append((SOURCE_SLOT, sname_i))
        if tname_i is not None:
            namefix.append((TARGET_SLOT, tname_i))

        tail = fields[8].split(COMMA) if len(fields) > 8 else []

        if len(fields) > 7:
            # school is tail[0] and constant per spell, so it rides in the dict
            school = tail[0] if tail else b""
            spell_i = self.spells.add(
                fields[6] + SPELL_SEP + fields[7] + SPELL_SEP + school
            )
        else:
            spell_i = NO_SPELL
        ev_i = self.events.add(fields[1])
        if ev_i > 0xFF:
            raise ValueError(f"more than 256 distinct event types: {ev_i}")

        self.blocks[-1].add(
            ms, ev_i, sguid_i, tguid_i, spell_i,
            [self._tail_value(value) for value in tail], namefix,
        )
        self.row_count += 1

    def _tail_value(self, value: bytes):
        """
        `0x40` and `64` are both valid in the log and must round trip
        separately, so a non negative value is a plain decimal and a negative
        one is -(index + 1) into the string dict: hex schools, `nil`, MISS.
        """
        if value.isdigit():
            return int(value)
        return -self.strings.add(value) - 1

    def to_bytes(self):
        guid_width = _width_for(len(self.guids))
        spell_width = _width_for(len(self.spells))

        # widths come from the whole report, so every block shares the grid
        bounds: list[tuple[int, int]] = []
        for block in self.blocks:
            for slot, (low, high) in enumerate(block.tail_bounds()):
                if slot < len(bounds):
                    was_low, was_high = bounds[slot]
                    bounds[slot] = (min(was_low, low), max(was_high, high))
                else:
                    bounds.append((low, high))
        tail_widths = [_tail_width_for(low, high) for low, high in bounds]

        head = bytearray(MAGIC)
        head += VERSION.to_bytes(2, "little")
        head += self.row_count.to_bytes(4, "little")
        head += len(self.blocks).to_bytes(2, "little")
        head.append(guid_width)
        head.append(spell_width)
        head.append(len(tail_widths))
        head += bytes(tail_widths)

        head += self.events.to_bytes()
        head += self.spells.to_bytes()
        head += self.strings.to_bytes()
        # guids and their names travel together, one entry per guid
        guid_dict = _Interner()
        for i, guid in enumerate(self.guids.values):
            guid_dict.values.append(guid + SPELL_SEP + self.names.values[self.guid_names[i]])
        head += guid_dict.to_bytes()
        # the namefix streams point into the full name dict, which is a superset
        head += self.names.to_bytes()

        payloads = [
            zstd.compress(
                block.to_bytes(guid_width, spell_width, tail_widths), COMPRESS_LEVEL
            )
            for block in self.blocks
        ]

        table = bytearray()
        offset = 0
        for block, payload in zip(self.blocks, payloads):
            _uvarint(table, block.global_start_row)
            _uvarint(table, block.ms_base)
            _uvarint(table, offset)
            _uvarint(table, len(payload))
            offset += len(payload)

        head += len(table).to_bytes(4, "little")
        head += table
        return bytes(head) + b"".join(payloads)


class Dicts(NamedTuple):
    '''
    The report's dictionaries. The spine columns index into these, so a
    consumer builds its lookup table over them once - hundreds of entries,
    not hundreds of thousands. Still unpacks as the old 6-tuple.
    '''
    events: tuple
    guids: tuple
    # the name each guid has for most of the report; see Block.namefix
    guid_names: tuple
    # (spell_id, spell_name) per spell index; index 0 is NO_SPELL
    spells: tuple
    # tail literals: a negative tail value v means strings[-v - 1]
    strings: tuple
    # every name seen, the superset Block.namefix indexes into
    names: tuple

    def decode(self):
        '''The same dictionaries as str.'''
        return Dicts(
            tuple(e.decode() for e in self.events),
            tuple(g.decode() for g in self.guids),
            tuple(n.decode() for n in self.guid_names),
            tuple((i.decode(), n.decode()) for i, n in self.spells),
            tuple(s.decode() for s in self.strings),
            tuple(n.decode() for n in self.names),
        )


@dataclass(frozen=True, slots=True)
class BlockMeta:
    '''One entry of the block table, known without decompressing anything.'''
    index: int
    global_start_row: int
    ms_base: int
    byte_offset: int
    byte_len: int


@dataclass(frozen=True, slots=True, eq=False)
class Block:
    '''
    One decoded encounter block. Built in one go by `_decode_block` and never
    changed afterwards; every column is a read-only numpy array.
    '''
    meta: BlockMeta
    row_count: int
    # ms offsets from meta.ms_base
    ts: numpy.ndarray
    ev: numpy.ndarray
    sguid: numpy.ndarray
    tguid: numpy.ndarray
    spell: numpy.ndarray
    # how many tail slots each row really has; the rest are padding
    arity: numpy.ndarray
    # one signed column per slot, see Dicts.strings for negative values
    tail: tuple
    # row -> (source name index or None, target name index or None) into
    # Dicts.names, for the rows whose names differ from Dicts.guid_names
    namefix: Mapping

    @property
    def global_start_row(self):
        return self.meta.global_start_row

    @property
    def ms_base(self):
        return self.meta.ms_base


def _decode_namefix(data: bytes):
    '''The namefix varint stream -> Block.namefix.'''
    overrides: dict[int, tuple] = {}
    reader = _Reader(data)
    while reader.pos < len(data):
        row = reader.uvarint()
        slot = reader.u8()
        name_i = reader.uvarint()
        source, target = overrides.get(row, (None, None))
        if slot == SOURCE_SLOT:
            source = name_i
        else:
            target = name_i
        overrides[row] = (source, target)
    return MappingProxyType(overrides)


def _decode_block(meta: BlockMeta, raw: bytes, guid_dtype, spell_dtype, tail_widths):
    reader = _Reader(raw)
    rows = reader.uvarint()
    namefix_len = reader.uvarint()

    dtypes = [TS_DTYPE, EV_DTYPE, guid_dtype, guid_dtype, spell_dtype, numpy.uint8]
    dtypes += [TAIL_DTYPES[width] for width in tail_widths]
    columns = []
    pos = reader.pos
    for dtype in dtypes:
        columns.append(numpy.frombuffer(raw, dtype=dtype, count=rows, offset=pos))
        pos += numpy.dtype(dtype).itemsize * rows
    ts_deltas, ev, sguid, tguid, spell, arity, *tail = columns

    # stored as deltas; make it offsets from ms_base
    ts = numpy.cumsum(ts_deltas, dtype=TS_DTYPE)
    ts.flags.writeable = False

    return Block(
        meta=meta, row_count=rows,
        ts=ts, ev=ev, sguid=sguid, tguid=tguid, spell=spell,
        arity=arity, tail=tuple(tail),
        namefix=_decode_namefix(raw[pos:pos + namefix_len]),
    )


class _RenderedBlocks:
    '''Small LRU of blocks rendered as text lines. A pure cache.'''

    def __init__(self, size: int) -> None:
        self.size = size
        self._lines: OrderedDict[int, list[str]] = OrderedDict()

    def get(self, index: int):
        lines = self._lines.get(index)
        if lines is not None:
            self._lines.move_to_end(index)
        return lines

    def put(self, index: int, lines: list[str]):
        self._lines[index] = lines
        while len(self._lines) > self.size:
            self._lines.popitem(last=False)


class ColumnStore:
    '''
    Decoded LOGS_CUT.bin. The header and dictionaries are read up front; a
    block decompresses on first touch, so one encounter never materializes
    the rest of the report.

    Everything set in __init__ stays as it is. The only things that fill in
    later are the two caches, `_decoded` and `_rendered`, and a cache hit
    returns exactly what a miss would have built.
    '''

    def __init__(self, data: bytes) -> None:
        if data[:4] != MAGIC:
            raise ValueError("not a LOGS_CUT.bin payload")
        version = int.from_bytes(data[4:6], "little")
        if version != VERSION:
            raise ValueError(f"unsupported LOGS_CUT.bin version {version}")

        self.row_count = int.from_bytes(data[6:10], "little")
        block_count = int.from_bytes(data[10:12], "little")
        self.guid_dtype = SPINE_WIDTHS[data[12]]
        self.spell_dtype = SPINE_WIDTHS[data[13]]
        tail_slots = data[14]
        self.tail_widths = tuple(data[15:15 + tail_slots])

        reader = _Reader(data, 15 + tail_slots)
        events = _Interner.from_reader(reader)
        # index 0 is the NO_SPELL sentinel; pad it to the (id, name, school) shape
        spell_entries = [
            entry.split(SPELL_SEP) if entry else [b"", b"", b""]
            for entry in _Interner.from_reader(reader)
        ]
        strings = _Interner.from_reader(reader)
        guid_dict = [g.split(SPELL_SEP) for g in _Interner.from_reader(reader)]
        names = _Interner.from_reader(reader)

        # the dictionaries as stored, which byte_lines renders from
        self.raw = Dicts(
            events=tuple(events),
            guids=tuple(g[0] for g in guid_dict),
            guid_names=tuple(g[1] for g in guid_dict),
            spells=tuple((entry[0], entry[1]) for entry in spell_entries),
            strings=tuple(strings),
            names=tuple(names),
        )
        # school is kept apart because it already lives in the tail
        self.spell_schools = tuple(entry[2] for entry in spell_entries)
        # the same as str, which every consumer and the text renderer use
        self.text = self.raw.decode()

        table_len = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
        reader.pos += 4
        table = _Reader(data, reader.pos)
        self.blocks = tuple(
            BlockMeta(
                index, table.uvarint(), table.uvarint(),
                table.uvarint(), table.uvarint(),
            )
            for index in range(block_count)
        )
        self._payloads = data[reader.pos + table_len:]

        self._decoded: dict[int, Block] = {}
        self._rendered = _RenderedBlocks(RENDERED_BLOCK_CACHE)

    def __len__(self):
        return self.row_count

    def block_of(self, row: int):
        '''Global row -> (block index, row offset inside that block).'''
        blocks = self.blocks
        lo = 0
        hi = len(blocks) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if blocks[mid].global_start_row <= row:
                lo = mid
            else:
                hi = mid - 1
        return lo, row - blocks[lo].global_start_row

    def block(self, index: int):
        '''The decoded Block at `index`, decompressed on first use.'''
        block = self._decoded.get(index)
        if block is None:
            meta = self.blocks[index]
            start = meta.byte_offset
            raw = zstd.decompress(self._payloads[start:start + meta.byte_len])
            block = _decode_block(
                meta, raw, self.guid_dtype, self.spell_dtype, self.tail_widths
            )
            self._decoded[index] = block
        return block

    def lines(self, index: int):
        """Rendered lines of one block, cached across views."""
        lines = self._rendered.get(index)
        if lines is None:
            lines = self._render(index)
            self._rendered.put(index, lines)
        return lines

    def _render(self, index: int):
        """Builds the text lines of one block directly as str."""
        block = self.block(index)
        events, guids, guid_names, spells, strings, names = self.text
        namefix = block.namefix

        arity = block.arity.tolist()
        tail_cols = [column.tolist() for column in block.tail]
        ts_col = block.ts.tolist()
        ev_col = block.ev.tolist()
        sguid_col = block.sguid.tolist()
        tguid_col = block.tguid.tolist()
        spell_col = block.spell.tolist()

        join = ",".join
        rendered = []
        ms_base = block.ms_base
        for row in range(block.row_count):
            ms = ms_base + ts_col[row]
            sguid_i = sguid_col[row]
            tguid_i = tguid_col[row]
            spell_i = spell_col[row]

            fix = namefix.get(row)
            if fix is None:
                sname = guid_names[sguid_i]
                tname = guid_names[tguid_i]
            else:
                sname = guid_names[sguid_i] if fix[0] is None else names[fix[0]]
                tname = guid_names[tguid_i] if fix[1] is None else names[fix[1]]

            fields = [
                ms_to_timestamp_str(ms), events[ev_col[row]],
                guids[sguid_i], sname, guids[tguid_i], tname,
            ]
            if spell_i != NO_SPELL:
                fields += spells[spell_i]

            for column in tail_cols[:arity[row]]:
                value = column[row]
                fields.append(str(value) if value >= 0 else strings[-value - 1])

            rendered.append(join(fields))
        return rendered

    def block_ranges(self, start: int=0, stop: int=None):
        """
        (block, lo, hi) per block overlapping [start, stop), lo/hi as offsets
        inside that block. The entry point for working on whole columns.
        """
        if stop is None:
            stop = self.row_count
        index, _ = self.block_of(start)
        for meta in self.blocks[index:]:
            if meta.global_start_row >= stop:
                return
            block = self.block(meta.index)
            lo = max(start - meta.global_start_row, 0)
            hi = min(stop - meta.global_start_row, block.row_count)
            if hi > lo:
                yield block, lo, hi

    # a timestamp has no dictionary behind it, so a needle of only these
    # characters can never be narrowed
    _TIMESTAMP_CHARS = frozenset("0123456789/:. ")

    def substring_lookup(self, needle: str):
        """
        Bool array over the event dict for `needle in line`, or None when any
        other field could match and the caller has to keep its text path.

        A match never spans a comma, so it always lies inside a single field.
        """
        if not needle or self._TIMESTAMP_CHARS.issuperset(needle):
            return None

        text = self.text
        for dictionary in (text.guids, text.guid_names, text.strings, text.names):
            if any(needle in value for value in dictionary):
                return None
        for spell_id, spell_name in text.spells:
            if needle in spell_id or needle in spell_name:
                return None
        return numpy.array([needle in event for event in text.events], dtype=bool)

    def seconds(self):
        """Absolute seconds per row. Decompresses every block."""
        return numpy.concatenate([
            (self.block(meta.index).ts.astype(numpy.int64) + meta.ms_base) // 1000
            for meta in self.blocks
        ])

    def second_offsets(self):
        """First row index of each elapsed second, the shape TIMESTAMP_DATA.json wants."""
        elapsed = self.seconds()
        elapsed -= elapsed[0]
        # timestamps can step backwards on a bugged line; the line based
        # version never rewinds, so neither does this
        numpy.maximum.accumulate(elapsed, out=elapsed)
        total = int(elapsed[-1])
        return numpy.searchsorted(
            elapsed, numpy.arange(1, total + 1), side="left"
        ).tolist()

    def dicts(self):
        """The dictionaries as str, see Dicts."""
        return self.text

    def spell_entries(self):
        """
        [(spell_id, name, school)] in first seen order, header only.

        An id can repeat when its name or school differ between rows; the
        earliest entry is the one a first-occurrence-wins consumer wants.
        """
        return [
            (spell_id.decode(), name.decode(), school.decode())
            for (spell_id, name), school in zip(self.raw.spells, self.spell_schools)
            if spell_id
        ]

    def row_line(self, row: int):
        """
        One rendered line. Uses the already rendered block when there is one,
        otherwise reads the row straight out of the columns.
        """
        index, offset = self.block_of(row)
        rendered = self._rendered.get(index)
        if rendered is not None:
            return rendered[offset]

        block = self.block(index)
        events, guids, guid_names, spells, strings, names = self.text

        sguid_i = int(block.sguid[offset])
        tguid_i = int(block.tguid[offset])
        spell_i = int(block.spell[offset])

        sname = guid_names[sguid_i]
        tname = guid_names[tguid_i]
        fix = block.namefix.get(offset)
        if fix is not None:
            if fix[0] is not None:
                sname = names[fix[0]]
            if fix[1] is not None:
                tname = names[fix[1]]

        fields = [
            ms_to_timestamp_str(block.ms_base + int(block.ts[offset])),
            events[int(block.ev[offset])],
            guids[sguid_i], sname, guids[tguid_i], tname,
        ]
        if spell_i != NO_SPELL:
            fields += spells[spell_i]
        for column in block.tail[:block.arity[offset]]:
            value = int(column[offset])
            fields.append(str(value) if value >= 0 else strings[-value - 1])
        return ",".join(fields)

    def rows(self, index: int):
        '''Yields (ms, fixed_fields, tail_values) per row of one block, as bytes.'''
        block = self.block(index)
        events, guids, guid_names, spells, strings, names = self.raw
        namefix = block.namefix

        arity = block.arity.tolist()
        tail_cols = [column.tolist() for column in block.tail]
        ts_col = block.ts.tolist()
        ev_col = block.ev.tolist()
        sguid_col = block.sguid.tolist()
        tguid_col = block.tguid.tolist()
        spell_col = block.spell.tolist()

        ms_base = block.ms_base
        for row in range(block.row_count):
            ms = ms_base + ts_col[row]
            sguid_i = sguid_col[row]
            tguid_i = tguid_col[row]
            spell_i = spell_col[row]

            fix = namefix.get(row)
            if fix is None:
                sname = guid_names[sguid_i]
                tname = guid_names[tguid_i]
            else:
                sname = guid_names[sguid_i] if fix[0] is None else names[fix[0]]
                tname = guid_names[tguid_i] if fix[1] is None else names[fix[1]]

            fixed = [
                events[ev_col[row]],
                guids[sguid_i], sname,
                guids[tguid_i], tname,
            ]
            if spell_i != NO_SPELL:
                fixed += spells[spell_i]

            values = []
            for column in tail_cols[:arity[row]]:
                value = column[row]
                values.append(
                    str(value).encode() if value >= 0 else strings[-value - 1]
                )

            yield ms, fixed, values


# The log has no year, so the stored integer is a self contained
# month/day/hour/minute/second/millisecond packing of the original text, only
# ever compared against other timestamps from the same report.

_MS_PER_SECOND = 1000
_MS_PER_MINUTE = 60 * _MS_PER_SECOND
_MS_PER_HOUR = 60 * _MS_PER_MINUTE
_MS_PER_DAY = 24 * _MS_PER_HOUR
_MS_PER_MONTH = 32 * _MS_PER_DAY

def timestamp_to_ms(timestamp: bytes):
    '''b"6/25 21:46:32.302" -> packed milliseconds.'''
    date, time = timestamp.split(b" ", 1)
    month, day = date.split(b"/")
    time = time.lstrip(b" ")
    hour, minute, second = time.split(b":")
    whole, _, milli = second.partition(b".")
    return (
        int(month) * _MS_PER_MONTH
        + int(day) * _MS_PER_DAY
        + int(hour) * _MS_PER_HOUR
        + int(minute) * _MS_PER_MINUTE
        + int(whole) * _MS_PER_SECOND
        + int(milli)
    )

def ms_to_timestamp(ms: int):
    '''Inverse of timestamp_to_ms, reproducing the original text exactly.'''
    return ms_to_timestamp_str(ms).encode()

def ms_to_timestamp_str(ms: int):
    month, ms = divmod(ms, _MS_PER_MONTH)
    day, ms = divmod(ms, _MS_PER_DAY)
    hour, ms = divmod(ms, _MS_PER_HOUR)
    minute, ms = divmod(ms, _MS_PER_MINUTE)
    second, milli = divmod(ms, _MS_PER_SECOND)
    return "%d/%d %02d:%02d:%02d.%03d" % (month, day, hour, minute, second, milli)


class LogsView:
    '''
    Sequence of normalized log lines backed by a ColumnStore.

    Exists so the modules that still do `self.LOGS[s:f]` and `line.split(',')`
    keep working untouched. Slicing returns a view, so nothing materializes
    until a caller iterates.
    '''
    __slots__ = ("store", "start", "stop")

    def __init__(self, store: ColumnStore, start: int=0, stop: int=None) -> None:
        self.store = store
        self.start = start
        self.stop = store.row_count if stop is None else stop

    def __len__(self):
        return max(0, self.stop - self.start)

    def __repr__(self) -> str:
        return f"LogsView({self.start}:{self.stop} of {self.store.row_count} rows)"

    def __getitem__(self, item):
        if isinstance(item, slice):
            start, stop, step = item.indices(len(self))
            if step != 1:
                return [self[i] for i in range(start, stop, step)]
            return LogsView(self.store, self.start + start, self.start + stop)

        length = len(self)
        if item < 0:
            item += length
        if not 0 <= item < length:
            raise IndexError(item)
        return self.store.row_line(self.start + item)

    def __iter__(self):
        store = self.store
        row = self.start
        stop = self.stop
        while row < stop:
            index, offset = store.block_of(row)
            lines = store.lines(index)
            end = min(len(lines), offset + stop - row)
            for i in range(offset, end):
                yield lines[i]
            row += end - offset

    def spell_entries(self):
        '''[(spell_id, name, school)] of the whole report, from the header.'''
        return self.store.spell_entries()

    def second_offsets(self):
        '''First row index of each elapsed second, straight from the ts column.'''
        return self.store.second_offsets()

    def block_ranges(self):
        '''(block, lo, hi) per block overlapping this view - raw columns.'''
        return self.store.block_ranges(self.start, self.stop)

    def substring_lookup(self, needle: str):
        '''Event dict bool array for `needle in line`, or None if not reducible.'''
        return self.store.substring_lookup(needle)

    def dicts(self):
        '''(events, guids, guid_names, spells, strings, names) as str lists.'''
        return self.store.dicts()

    def __eq__(self, other) -> bool:
        if isinstance(other, LogsView):
            return list(self) == list(other)
        if isinstance(other, list):
            return list(self) == other
        return NotImplemented


# the text form is `line.split(",")[8:]`, so tail slot n is field 8 + n;
# `_line[9]` and `_line[10]` are the value and the overkill
TAIL_VALUE = 1
TAIL_OVERKILL = 2


def selected_rows(block, lo: int, hi: int, ev_lookup, tail_slots, min_arity: int=0):
    """
    (row offsets, [one int64 array per requested tail slot]) for the rows of
    `block` in [lo, hi) whose event passes `ev_lookup`.

    `min_arity` is how many tail fields the text form needed: reading
    `_line[10]` off a `split(",", 11)` wants 3, unpacking that split into 12
    names wants 4. Pass whichever the loop being replaced used.

    None when a selected row could not have been read the text way - tail too
    short, or a slot holding a literal. Those would have raised there, so the
    caller falls back and the two paths stay identical.
    """
    mask = ev_lookup[block.ev[lo:hi]]
    rows = numpy.flatnonzero(mask)
    if not len(rows):
        empty = numpy.empty(0, dtype=numpy.int64)
        return rows, [empty] * len(tail_slots)
    rows += lo

    need = max(max(tail_slots) + 1, min_arity)
    if len(block.tail) < need or (block.arity[rows] < need).any():
        return None

    values = []
    for slot in tail_slots:
        column = block.tail[slot][rows].astype(numpy.int64)
        if (column < 0).any():
            # a negative slot value indexes the string dict, so the text form
            # of this field is not a number at all
            return None
        values.append(column)
    return rows, values


def group_sums(keys, *value_arrays):
    """
    (unique keys, [summed values per input array]), in first appearance order.

    Sums in int64. The order matters: a caller filling a dict this way gets the
    same insertion order the row-by-row loop it replaces would have.
    """
    if not len(keys):
        return keys, [v for v in value_arrays]

    order = numpy.argsort(keys, kind="stable")
    ordered = keys[order]
    starts = numpy.flatnonzero(
        numpy.concatenate(([True], ordered[1:] != ordered[:-1]))
    )
    sums = [numpy.add.reduceat(v[order], starts) for v in value_arrays]

    first_seen = numpy.minimum.reduceat(order, starts)
    back = numpy.argsort(first_seen, kind="stable")
    return ordered[starts][back], [s[back] for s in sums]


def encode(lines, block_starts=None):
    '''
    Builds the LOGS_CUT.bin payload from normalized lines.

    `lines` is normalized rows as bytes, what logs_fix.normalize yields; blank
    lines are skipped. `block_starts` is an optional sorted iterable of row
    indices that begin a new block - pass the pull boundaries to get partial
    reads, pass nothing to get a single block.
    '''
    encoder = Encoder()
    boundaries = set(block_starts or ())
    row = 0
    for line in lines:
        if not line:
            continue
        fields = line.split(COMMA, 8)
        if len(fields) < 6:
            continue
        encoder.add_row(timestamp_to_ms(fields[0]), fields, row in boundaries)
        row += 1
    return encoder.to_bytes()

def decode(data: bytes):
    return ColumnStore(data)

def block_starts_from_encounters(encounter_data: dict, row_count: int):
    '''
    Turns ENCOUNTER_DATA.json into block boundaries.

    Every pull start and end becomes a boundary, so each pull lands in its own
    block and the trash between pulls in blocks of its own.
    '''
    starts = set()
    for pulls in encounter_data.values():
        for start, end in pulls:
            starts.add(start)
            starts.add(end)
    starts.discard(0)
    return sorted(b for b in starts if 0 < b < row_count)

def byte_lines(store: ColumnStore):
    '''Every row of every block as the normalized bytes line it came from.'''
    join = COMMA.join
    for index in range(len(store.blocks)):
        for ms, fixed, values in store.rows(index):
            yield ms_to_timestamp(ms) + COMMA + join(fixed + values)

def repack(data: bytes, block_starts):
    '''Rewrites a payload with new block boundaries, keeping every row.'''
    return encode(byte_lines(ColumnStore(data)), block_starts)
