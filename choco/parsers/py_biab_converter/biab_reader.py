__all__ = [
    'read_biab_file']

from py_biab_converter.biabchords import *

root_names = (
    'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B', 'C#', 'D#', 'F#', 'G#', 'A#')


def read_biab_file(filename):
    f = open(filename, 'r', encoding='unicode_escape', errors='backslashreplace')
    version = read_char_as_integer(f)
    if version == 187 or version == 188:
        result = read_biab_file_old_format(f)
    else:
        result = read_biab_file_new_format(f)
    f.close()
    return result


def read_biab_file_old_format(f):
    name = read_old_format_name(f)
    style = read_style(f)
    key = read_key(f)
    tempo = read_tempo(f)
    (sections, chords, chorus) = read_old_format_chart(style['meter'], f)
    return {'name': name, 'style': style, 'key': key, 'tempo': tempo, 'chords': chords, 'chorus': chorus,
            'sections': sections}


def read_old_format_name(f):
    name_len = read_char_as_integer(f)
    name = read_chars_as_string(name_len, f)
    skip_chars(62 - 2 - name_len, f)
    return name.rstrip()


def read_old_format_chart(meter, f):
    sections = read_sections_old_format(f)
    types = read_n_chars_as_integer_list(256, f)
    roots = read_n_chars_as_integer_list(256, f)
    dummy = read_char_as_integer(f)
    chorus = read_chorus_old_format(f)
    chorus_length = chorus['end'] * 4
    bars = make_bars_old_format(types[:chorus_length], roots[:chorus_length])
    return (sections, adjust_for_meter(bars, meter), chorus)


def read_sections_old_format(f):
    sections = read_n_chars_as_integer_list(64, f)
    result = {}
    for bar in range(64):
        section = sections[bar]
        if section != 0:
            name = section_name(section)
            if name:
                result[bar + 1] = name

    return result


def read_chorus_old_format(f):
    begin = read_char_as_integer(f)
    end = read_char_as_integer(f)
    repeats = read_char_as_integer(f)
    return {'begin': begin, 'end': end, 'repeats': repeats + 2}


def make_bars_old_format(types, roots):
    l = len(types) / 4
    result = []
    for bar in range(l):
        i = bar * 4
        result.append(make_bar_old_format(types[i:i + 4], roots[i:i + 4]))

    return result


_last_chord = None


def make_bar_old_format(types, roots):
    global _last_chord
    result = []
    for i in range(4):
        chord_type = types[i]
        chord_root = roots[i]
        if chord_type == 0:
            if result:
                (chord, duration) = result[(-1)]
                result = result[:-1] + [(chord, duration + 1)]
            else:
                result = [
                    (
                        _last_chord, 1)]
        else:
            _last_chord = chord_name(chord_type, chord_root)
            result.append((_last_chord, 1))

    return result


def read_biab_file_new_format(f):
    name = read_new_format_name(f)
    style = read_style(f)
    key = read_key(f)
    tempo = read_tempo(f)
    (sections, chords, chorus) = read_new_format_chart(style['meter'], f)
    return {'name': name, 'style': style, 'key': key, 'tempo': tempo, 'chords': chords, 'chorus': chorus,
            'sections': sections}


def read_new_format_name(f):
    name_len = read_char_as_integer(f)
    name = read_chars_as_string(name_len, f)
    skip_chars(2, f)
    return name.rstrip()


def read_new_format_chart(meter, f):
    sections = read_sections_new_format(f)
    (dummy, types) = read_new_format_chord_types(f)
    (beat, roots) = read_new_format_chord_roots(f)
    chorus = read_chorus_new_format(beat, f)
    return (sections, make_bars_new_format(meter, types, roots), chorus)


def read_sections_new_format(f):
    bar = read_char_as_integer(f)
    result = {}
    while bar < 255:
        bar_type = read_char_as_integer(f)
        if bar_type == 0:
            bar += read_char_as_integer(f)
        else:
            name = section_name(bar_type)
            if name:
                result[bar] = name
            bar += 1

    return result


def read_new_format_chord_types(f):
    beat = 0
    result = []
    while beat < 1020:
        chord_type = read_char_as_integer(f)
        if chord_type == 0:
            duration = read_char_as_integer(f)
            beat += duration
            (chord_type2, duration2) = result[(-1)]
            result = result[:-1] + [(chord_type2, duration2 + duration)]
        else:
            beat += 1
            result.append((chord_type, 1))

    return (
        beat, result)


read_new_format_chord_roots = read_new_format_chord_types


def read_chorus_new_format(beat, f):
    if beat == 1020:
        skip_chars(1, f)
    begin = read_char_as_integer(f)
    end = read_char_as_integer(f)
    repeats = read_char_as_integer(f)
    return {'begin': begin, 'end': end, 'repeats': repeats}


def make_bars_new_format(meter, chord_types, chord_roots):
    l1 = len(chord_types)
    l2 = len(chord_roots)
    if abs(l1 - l2) > 1:
        print(f'Error -> \ntypes: {len(chord_types)}\nroots: {len(chord_roots)}')
        raise ValueError('Inconsistent chord and root list lengths')
    chords = []
    l = min(l1, l2)
    for i in range(l):
        (chord_type, dur1) = chord_types[i]
        (chord_root, dur2) = chord_roots[i]
        if i < l - 1:
            if dur1 != dur2:
                raise ValueError('Inconsistent chord type beat and root beat')
            chords.append((chord_name(chord_type, chord_root), dur1))
        else:
            chords.append((chord_name(chord_type, chord_root), 4))

    return adjust_for_meter(construct_bars(chords), meter)


def construct_bars(chords):
    result = []
    bar = []
    duration = 0
    for (chord_name, dur) in chords:
        while dur > 0:
            new_duration = duration + dur
            if new_duration < 4:
                duration = new_duration
                bar.append((chord_name, dur))
                dur = 0
            elif new_duration == 4:
                bar.append((chord_name, dur))
                result.append(bar)
                bar = []
                duration = 0
                dur = 0
            else:
                partial = 4 - duration
                dur -= partial
                bar.append((chord_name, partial))
                result.append(bar)
                bar = []
                duration = 0

    return result


def read_style(f):
    style_type = read_char_as_integer(f)
    if style_type == 8 or style_type == 17:
        return {'type': style_type, 'meter': 3}
    else:
        return {'type': style_type, 'meter': 4}


def read_key(f):
    key = read_char_as_integer(f)
    if key <= 17:
        return root_names[(key - 1)]
    else:
        return root_names[(key - 18)] + 'm'


def read_tempo(f):
    tempo1 = read_char_as_integer(f)
    tempo2 = read_char_as_integer(f)
    return tempo2 * 256 + tempo1


def chord_name(chord_type, chord_root):
    chord_root_index = chord_root % 18
    chord_bass_index = (chord_root_index - 1 + chord_root // 18) % 12 + 1
    root_name = root_names[(chord_root_index - 1)]
    type_name = biab_chord_type_to_toe(chord_type)
    if chord_root_index == chord_bass_index:
        return root_name + type_name
    else:
        return root_name + type_name + '/' + root_names[(chord_bass_index - 1)]


def read_char_as_integer(f):
    return ord(f.read(1))


def read_chars_as_string(n, f):
    return f.read(n)


def skip_chars(n, f):
    f.read(n)


def read_n_chars_as_integer_list(n, f):
    result = []
    for i in range(n):
        result.append(read_char_as_integer(f))

    return result


def adjust_for_meter(chords, meter):
    def make_3_beats_per_bar(bar):
        beats = 0
        result = []
        while bar:
            (chord_name, dur) = bar[0]
            bar = bar[1:]
            new_beats = beats + dur
            if new_beats < 3:
                beats = new_beats
                result.append((chord_name, dur))
            elif new_beats == 3:
                result.append((chord_name, dur))
                return result
            else:
                result.append((chord_name, 3 - beats))
                return result

    if meter == 4:
        return chords
    elif meter == 3:
        return map(make_3_beats_per_bar, chords)
    else:
        raise ValueError('Unrecognized meter: %d' % meter)


def section_name(section):
    if section == 1:
        return 'A'
    elif section == 2:
        return 'B'
    else:
        return None
    return


if __name__ == '__main__':
    import sys, pprint

    filelist = sys.argv[1:]
    if filelist:
        for f in filelist:
            print(f)
            print(pprint.pprint(read_biab_file(f)))

    else:
        print(pprint.pprint(read_biab_file(filelist)))
