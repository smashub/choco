"""
Implementation of a converter that takes in input a chord annotated using
the Roman Numeral notation, and converts it into the Harte notation.
"""
import csv
import re
from typing import Tuple

from choco.utils import get_note_index, note_map


def decompose_roman(roman_chord: str) -> Tuple:
    """
    Converts a Roman Numeral chord into Harte Notation, taking into consideration
    the key context in which the chord is played.
    Parameters
    ----------
    roman_chord : str
        The single chord to be converted given as a string.
        The string, according to the implementation of m21_parser and
        related code, is composed by two sections, colon separated:
        [key]:[roman_chord]
    Returns
    -------
    decomposed_chord : Tuple
        Returns a tuple containing the constituent elements of the Roman Chord,
        namely:
        - a list containing the key and the mode in which the chord is played
        - a tuple containing the chord decomposed, which contains elements in this order:
            * any alteration that can be found before the chord notation
            * the roman chord notation itself
            * any alteration to the chord (e.g. inversions: 46)
            * any added or removed note (between square brackets)
        - a list of root notes (originally indicated after the slash "/")
    """
    # preprocess the input chord for removing dataset errors
    if roman_chord == 'Bb major:V7IV':
        roman_chord = roman_chord.replace('V7IV', 'V7/IV')
    if bool(re.search(':$', roman_chord)):
        roman_chord = re.sub(':$', '', roman_chord)

    # decompose the chord into its parts
    key, chord = roman_chord.split(':')
    key, mode = key.split(' ')
    root = ''
    if '/' in roman_chord:
        chord, *root = chord.split('/')

    # extract from chord the grade
    roman_re = re.compile('^([#b+-]{0,3})(It|N|Cad|N6|Fr|Ger|IX|IV|V?I{0,3})?'
                          '(ø|o|d|maj2|maj4|maj6|maj7|\+?)([b#M0-9+-]{0,9})(\[.*\]{0,2})?',
                          flags=re.ASCII | re.IGNORECASE)
    chord_filtered = roman_re.findall(chord)
    final = [key, mode], chord_filtered[0], root
    return final


def convert_roman_numeral(roman_numeral: str, alteration: str, key: list) -> str:
    """
    Converts a roman numeral into a base chord. It does not consider any chord
    alteration or modifier to the chord.
    Parameters
    ----------
    roman_numeral : str
        A Roman numeral grade as returned by the decompose_roman function in
        position [1][1]. This function does not consider alterations.
    alteration : str
        A string specifying the alteration that can be found before the roman
        numeral, as returned by the decompose_roman function in position [1][0].
    key : list
        The key in which the chord takes place. The key has to be provided
        as a list made of two elements, namely the key itself and the mode
        (only major and minor supported soi far).
    Returns
    -------
    base_note : str
        A string indicating the base chord (as described by the Harte notation),
        without any alteration or modifier.
    """
    scales = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
    }

    romans = {
        'I': 1,
        'II': 2,
        'III': 3,
        'IV': 4,
        'V': 5,
        'VI': 6,
        'VII': 7,
        'VIII': 8,
        'IX': 9,
        'X': 10,
    }

    def get_next_character(character: str) -> str:
        if character == 'G':
            return 'A'
        return chr(ord(character) + 1)

    def get_scale(note: str):
        scale = []
        note_index = get_note_index(note)
        enharmonic = note_map()[get_note_index(note)].index(note)
        for i, x in enumerate(scales[key[1]]):
            if x + note_index < 11:
                scale_note = note_map()[x + note_index]
            else:
                scale_note = note_map()[note_index - 12 + x]
            enharmonic = enharmonic if i == 0 else \
            [i for i, n in enumerate(scale_note) if get_next_character(scale[-1][0]) == n[0]][0]
            scale.append(scale_note[enharmonic])

        return scale

    # TODO: add filter for input romans and handling for special chords

    # initialise key index and note index
    if len(key) == 2 and key[1].lower() == 'major' or key[1].lower() == 'minor':
        key_scale = get_scale(key[0])
    else:
        raise ValueError(
            'The "key" parameter is not set properly.\n'
            'It must be formatted as ["key", "mode"] and the only modes supported are "major" and "minor".')
    # calculate the chord type
    chord_type = ':maj' if roman_numeral.isupper() else ':min'
    # calculate the degrees that can be found between the key index and the note index
    roman_numeral = roman_numeral.upper()

    alteration = alteration if alteration == "#" or alteration == 'b' else ''

    return key_scale[romans[roman_numeral] - 1] + alteration + chord_type


def test_roman_conversion(stats_file):
    """
    Tests the chord converter using the statistics file generated by stats.py.
    TODO: move this function in a separated file
    """
    with open(stats_file) as csv_file:
        stats = csv.reader(csv_file, delimiter=',')

        for i, chord_data in enumerate(stats):
            if i != 0:
                processed_chord = decompose_roman(chord_data[0])
                # print(processed_chord)
                converted_chord = convert_roman_numeral(processed_chord[1][1], processed_chord[1][0], processed_chord[0])
                print(converted_chord)


if '__main__' == __name__:
    test_roman_conversion('../../partitions/when-in-rome/choco/chord_stats.csv')
    # print(convert_roman_numeral('ii', '#', ['G#', 'minor']))
