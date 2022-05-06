"""
Converter for Roman Numeral chord annotations based on Music21.
"""
from typing import Tuple, List

from music21 import roman, pitch, chord, interval, note

from choco.converters.utils import simplify_harte


def decompose_roman(roman_chord: str) -> Tuple:
    """
    Utility function that decomposes a Roman Numeral chord in its constituting
    parts, i.e. KEY and the ROMAN NUMERAL itself.
    Parameters
    ----------
    roman_chord : str
        A Roman Chord in its complete Choco-shape (i.e. key_scale:roman_chord).
    Returns
    -------
        A Tuple composed by:
            key : str
                The key note uppercase (if the key is major) or lowercase (if
                the key is minor).
            roman : str
                The roman numeral without the key information.
    Note:
        If the key does not contain the scale (space separated), only the key
        note will be returned, and the scale will be inferred from its case
        (lowercase for minor, major otherwise).
    """
    key, roman = roman_chord.split(':')
    if ' ' in key:
        key_root, mode = key.split(' ')
        key = key_root.upper() if mode == 'major' else key_root.lower()
    return key, roman


def calculate_interval(note_1: note, note_2: note, simple: bool = True) -> str:
    """
    Utility function that given two music21 notes returns the interval calculated
    between the two.
    Parameters
    ----------
    note_1 : music21.note.Note
        The start note from which the interval has to be calculated.
    note_2 : music21.note.Note
        The end note to which the interval has to be calculated.
    simple : bool
        To mode in which to return the function. If true the interval is printed
        in the music21 "simpleName" mode, in the "name" mode if False.
    Returns
    -------
    interval : str
        An interval as convention in the Harte notation (i.e. b for flat and #
        for sharp).
    """
    note_1.octave = 4
    note_2.octave = 5
    mode = 'simpleName' if simple is True else 'name'
    computed_interval = getattr(interval.Interval(note_1, note_2), mode)
    return convert_intervals(computed_interval).replace('b2', 'b9').replace('2', '9')


def convert_intervals(m21_interval: str) -> str:
    """
    Utility function that converts intervals from the music21 format to the Harte one.
    Parameters
    ----------
    m21_interval : str
        A string containing an interval as expressed by the music21 notation (e.g. 'P4').
    Returns
    -------
    harte:interval : str
        A string containing an interval as expressed by the Harte notation (e.g. 'b2').
    """
    substitutions = {
        'M': '',
        'm': 'b',
        'P': '',
        'd': 'b',
        'A': '#',
    }
    return m21_interval.translate(m21_interval.maketrans(substitutions))


def convert_root(chord: chord) -> str:
    """
    Utility function for cleaning the string of a chord root note and making
    it compliant to the Harte notation.
    Parameters
    ----------
    chord : music21.chord.Chord
        A chord expressed by the music21 notation.
    Returns
    -------
    harte_root : str
        The root of the note in the Harte notation.
    """
    root_note = str(chord.root())
    root = ''.join(x for x in root_note if not x.isdigit())
    return root.replace('-', 'b')


def order_grades(grades_list: List) -> List:
    """
    Utility function that orders a list of tones encoded according to
    the Harte notation (containing 'b', '#', and '*').
    Parameters
    ----------
    grades_list : str
        A list of grades in the Harte notation.
        If the characters in input are illegal for the Harte notation,
        an exception is raised.
    Returns
    -------
    sorted_grades : str
        The input grades sorted from the lower to the higher.
    """
    try:
        return sorted(grades_list, key=lambda x: int(x.replace('b', '').replace('#', '').replace('*', '')))
    except ValueError:
        raise ValueError('The list of grades contains non valid characters to the Harte notation.')


def convert_roman(roman_chord: str) -> str:
    """
    The main function for converting chords from Roman Numeral notation to Harte Notation.
    Parameters
    ----------
    roman_chord : str
        A Roman Numeral chord annotated according to Choco's guidelines, i.e.
        key_scale:roman_chord (colon separated).
        Input example: D minor:IV64/ii
    Returns
    -------
    harte_chord : str
        An annotated chord according to Harte Notation specifications, using
        shorthands where possible.
    """
    # get the decomposed chord
    key, roman_notation = decompose_roman(roman_chord.rstrip(':'))
    chord = None

    try:
        chord = roman.RomanNumeral(roman_notation, key)
    except (pitch.PitchException, roman.RomanException):
        pass
        # raise ValueError('Impossible to convert the given Roman Numeral.')
    if chord:
        # process the bass and the root notes
        raw_root, bass = note.Note(chord.root()), note.Note(chord.bass())
        bass_interval = calculate_interval(raw_root, bass, simple=True)
        bass_interval = f'/{bass_interval}' if bass_interval != '1' else ''
        root = convert_root(chord)

        # process the intervals that constitute the chord
        chord_intervals = [calculate_interval(raw_root, note.Note(x), simple=True) for x in chord.pitchNames]
        # deal with the fist grade of the chord
        if '1' in chord_intervals:
            chord_intervals.remove('1')
        elif '8' in chord_intervals:
            chord_intervals.remove('8')
        else:
            chord_intervals.append('*1')

        # order the chord intervals in order to be simplified in shorthand
        ordered_chord_intervals = order_grades(chord_intervals)
        ordered_chord_intervals = simplify_harte(ordered_chord_intervals)

        return root + ordered_chord_intervals + bass_interval


if '__main__' == __name__:
    # test a conversion of a Roman Chord
    print(convert_roman('D minor:i[no3no5]'))
