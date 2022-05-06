"""
Converter for Roman Numeral chord annotations based on Music21.
"""
from typing import Tuple

from music21 import roman, pitch, note

from choco.converters.harte_utils import simplify_harte, calculate_interval, convert_root, order_grades


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

    try:
        chord = roman.RomanNumeral(roman_notation, key)
    except (pitch.PitchException, roman.RomanException):
        pass
        # raise ValueError('Impossible to convert the given Roman Numeral.')
    else:
        # process the bass and the root notes
        raw_root, bass = note.Note(chord.root()), note.Note(chord.bass())
        bass_interval = calculate_interval(raw_root, bass, simple=True)
        bass_interval = f'/{bass_interval}' if bass_interval != '1' else ''
        root = convert_root(chord.bass())

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
