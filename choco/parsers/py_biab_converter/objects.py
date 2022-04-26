__all__ = [
    'Note', 'Interval', 'ChordType', 'Chord', 'ScaleType', 'Scale', 'NOTE_NAMES', 'ALT_NAMES', 'NOTE_SEMI']

import re

from lxml.builder import basestring

NOTE_NAMES = [
    'C', 'D', 'E', 'F', 'G', 'A', 'B']
ALT_NAMES = ['bb', 'b', '', '#', '##']
NOTE_RE = re.compile('([A-G])((##|#|bb|b)?)')
INTERVAL_RE = re.compile('((##|#|bb|b)?)(10|11|12|13|[1-9])')
CHORD_RE = re.compile('([A-G](##|#|bb|b)?)([^/]*)(/([A-G](##|#|bb|b)?))?')
SCALE_RE = re.compile('([A-G](##|#|bb|b)?)([ \t]*)(.*)')
NOTE_SEMI = [
    0, 2, 4, 5, 7, 9, 11]
INTERVAL_SEMI = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21]


class Note:
    __module__ = __name__
    __slots__ = ['note', 'alt']

    def __init__(self, *args):
        if len(args) == 1:
            self._init_from_string(args[0])
        elif len(args) == 2:
            self._init_from_note_and_alt(args[0], args[1])
        else:
            raise TypeError('Wrong number of arguments to Note initializer')

    def _init_from_note_and_alt(self, note, alt):
        if not isinstance(note, int) or note < 0 or note > 6:
            raise ValueError('Note argument not an integer in [0..6]: %s' % note)
        if not isinstance(alt, int) or alt < -2 or alt > 2:
            raise ValueError('Alt argument not an integer in [-2..2]: %s' % alt)
        self.note = note
        self.alt = alt

    def _init_from_string(self, s):
        if not isinstance(s, basestring):
            raise TypeError('Note name argument not a string: %s' % s)
        _m = NOTE_RE.match(s)
        if not _m:
            raise ValueError('Invalid note name: %s' % s)
        if _m.group(0) != s:
            raise ValueError('Extra characters at end of note name: %s' % s)
        self.note = NOTE_NAMES.index(_m.group(1))
        self.alt = ALT_NAMES.index(_m.group(2)) - 2

    def seminote_number(self):
        return (NOTE_SEMI[self.note] + self.alt + 12) % 12

    def __cmp__(self, other):
        if self.note == other.note:
            return cmp(self.alt, other.alt)
        else:
            return cmp(self.note, other.note)

    def __hash__(self):
        return self.note << 3 + self.alt

    def __repr__(self):
        return "Note('%s')" % self.__str__()

    def __str__(self):
        return NOTE_NAMES[self.note] + ALT_NAMES[(self.alt + 2)]

    def __add__(self, other):
        if not isinstance(other, Interval):
            raise TypeError('Value added to Note not an interval: %s' % other)
        note = self.note
        interval = other.interval
        result_note = (note + interval) % 7
        note_semi_incr = (NOTE_SEMI[result_note] - NOTE_SEMI[note]) % 12
        result_semi_incr = (INTERVAL_SEMI[interval] + other.alt) % 12
        result_alt = self.alt + result_semi_incr - note_semi_incr
        if result_alt > 2:
            result_alt -= 12
        if result_alt < -2:
            result_alt += 12
        if result_alt < -2 or result_alt > 2:
            raise ValueError('%s + %s results in invalid note' % (self, other))
        return Note(result_note, result_alt)

    def __sub__(self, other):
        if not isinstance(other, Note):
            raise TypeError('Value subtracted from Note not a note: %s' % other)
        note1 = self.note
        note2 = other.note
        alt1 = self.alt
        alt2 = other.alt
        result_interval = (note1 - note2 + 7) % 7
        note_semi_diff = (NOTE_SEMI[note1] + alt1 - NOTE_SEMI[note2] - alt2 + 12) % 12
        result_alt = note_semi_diff - INTERVAL_SEMI[result_interval]
        if result_alt > 2:
            result_alt -= 12
        if result_alt < -2:
            result_alt += 12
        if result_alt < -2 or result_alt > 2:
            raise ValueError('%s - %s results in invalid interval' % (self, other))
        return Interval(result_interval, result_alt)


class Interval:
    __module__ = __name__
    __slots__ = ['interval', 'alt']

    def __init__(self, *args):
        if len(args) == 1:
            self._init_from_string(args[0])
        elif len(args) == 2:
            self._init_from_interval_and_alt(args[0], args[1])
        else:
            raise TypeError('Wrong number of arguments to Interval initializer')

    def _init_from_interval_and_alt(self, interval, alt):
        if not isinstance(interval, int) or interval < 0 or interval > 12:
            raise TypeError('Interval argument not an integer in [0..12]: %s' % interval)
        if not isinstance(alt, int) or alt < -2 or alt > 2:
            raise TypeError('Alt argument not an integer in [-2..2]: %s' % alt)
        self.interval = interval
        self.alt = alt

    def _init_from_string(self, s):
        if not isinstance(s, basestring):
            raise ValueError('Interval name argument not a string: %s' % s)
        _m = INTERVAL_RE.match(s)
        if not _m:
            raise ValueError('Invalid interval name: %s' % s)
        if _m.group(0) != s:
            raise ValueError('Extra characters at end of interval name: %s' % s)
        self.interval = int(_m.group(3)) - 1
        self.alt = ALT_NAMES.index(_m.group(1)) - 2

    def seminote_number(self):
        return (INTERVAL_SEMI[self.interval] + self.alt + 12) % 12

    def __cmp__(self, other):
        if self.interval == other.interval:
            return cmp(self.alt, other.alt)
        else:
            return cmp(self.interval, other.interval)

    def __hash__(self):
        return self.seminote_number()

    def __repr__(self):
        return "Interval('%s')" % self.__str__()

    def __str__(self):
        return ALT_NAMES[(self.alt + 2)] + str(self.interval + 1)


class NamedIntervalList:
    __module__ = __name__
    __slots__ = ['interval_list']

    def __init__(self, s):
        if not isinstance(s, basestring):
            raise TypeError('Argument not a string: %s' % s)
        if len(s) > 0 and s[0] == ':':
            try:
                inl = s[1:].split('.')
                il = list(map(Interval, inl))
                self.interval_list = il
            except:
                raise ValueError('Invalid interval list: %s' % s)

        else:
            named_interval_list = self.__class__._map.get(s)
            if named_interval_list:
                self.interval_list = named_interval_list.interval_list
            else:
                raise ValueError('Unknown name: %s' % s)

    def define(cls, name, il):
        if not isinstance(name, basestring):
            raise TypeError('Name argument not a string: %s', name)
        if not isinstance(il, basestring):
            raise TypeError('Interval list argument not a string: %s' % il)
        if len(il) == 0 or il[0] != ':':
            raise ValueError('Interval list argument does not begin with a colon: %s' % il)
        named_interval_list = NamedIntervalList(il)
        cls._map[name] = named_interval_list
        cls._reverse_map[named_interval_list._interval_list_string()] = name
        for f in cls.new_definition_callbacks:
            f()

    define = classmethod(define)

    def nth(self, n):
        for alt in [0, 1, -1, 2, -2]:
            i = Interval(n - 1, alt)
            if i in self.interval_list:
                return i

        return None
        return

    def _interval_list_string(self):
        il = map(str, self.interval_list)
        return ':' + ('.').join(il)

    def __str__(self):
        ils = self._interval_list_string()
        name = self.__class__._reverse_map.get(ils)
        if name != None:
            return name
        else:
            return ils
        return


class ChordType(NamedIntervalList):
    __module__ = __name__
    _map = dict()
    _reverse_map = dict()
    new_definition_callbacks = []

    def __repr__(self):
        return "ChordType('%s')" % self.__str__()


class Chord:
    __module__ = __name__
    __slots__ = ['root', 'chord_type', 'bass', 'notes']

    def __init__(self, s):
        if not isinstance(s, basestring):
            raise TypeError('Argument not a string: %s' % s)
        _m = CHORD_RE.match(s)
        if not _m:
            raise ValueError('Invalid chord name: %s' % s)
        if _m.group(0) != s:
            raise ValueError('Extra characters at end of chord name: %s' % s)
        self.root = Note(_m.group(1))
        self.chord_type = ChordType(_m.group(3))
        if _m.group(4):
            self.bass = Note(_m.group(5))
        else:
            self.bass = self.root
        self._compute_notes()

    def _compute_notes(self):
        il = self.chord_type.interval_list
        self.notes = [self.root] + map(lambda x: self.root + x, il)

    def nth(self, n):
        i = self.chord_type.nth(n)
        if i:
            return self.root + i
        else:
            return None
        return

    def __repr__(self):
        return "Chord('%s')" % self.__str__()

    def __str__(self):
        if self.root == self.bass:
            return str(self.root) + str(self.chord_type)
        else:
            return str(self.root) + str(self.chord_type) + '/' + str(self.bass)


class ScaleType(NamedIntervalList):
    __module__ = __name__
    _map = dict()
    _reverse_map = dict()
    new_definition_callbacks = []

    def __repr__(self):
        return "ScaleType('%s')" % self.__str__()


class Scale:
    __module__ = __name__
    __slots__ = ['root', 'scale_type', 'notes']

    def __init__(self, s):
        if not isinstance(s, basestring):
            raise TypeError('Argument not a string: %s' % s)
        _m = SCALE_RE.match(s)
        if not _m:
            raise ValueError('Invalid scale name: %s' % s)
        if _m.group(0) != s:
            raise ValueError('Extra characters at end of scale name: %s' % s)
        self.root = Note(_m.group(1))
        self.scale_type = ScaleType(_m.group(4))
        self._compute_notes()

    def _compute_notes(self):
        il = self.scale_type.interval_list
        self.notes = [self.root] + map(lambda x: self.root + x, il)

    def nth(self, n):
        i = self.scale_type.nth(n)
        if i:
            return self.root + i
        else:
            return None
        return

    def __repr__(self):
        return "Scale('%s')" % self.__str__()

    def __str__(self):
        scale_type_name = str(self.scale_type)
        if scale_type_name.startswith(':'):
            return str(self.root) + scale_type_name
        else:
            return str(self.root) + ' ' + scale_type_name
