"""
Implementation of a converter that takes in input a chord annotated using
the Roman Numeral notation, and converts it into the Harte notation.
"""
import csv
import re
from typing import Tuple, List

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


def get_next_note(note_name: str) -> str:
    """
    Auxiliary function that given a note name returns the following one.
    Parameters
    ----------
    note_name : str
        The note name without any attribute.
    Returns
    -------
    following_note : str
        A character which is the following note of the given one.
    """
    valid_notes = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    if note_name not in valid_notes:
        quit()
        raise ValueError('The given note is not a valid note.')
    if note_name == 'G':
        return 'A'
    return chr(ord(note_name) + 1)


def get_scale(key: List) -> List:
    """
    Auxiliary function that given the key information [key, mode], returns
    the scale for that key.
    Note: the function only works for minor and major mode.
    Parameters
    ----------
    key : List
        A list of string structured in the following way: [key, mode]
    Returns
    -------
    scale : list
        A list of the notes that make up the scale for the given tonality.
    """
    note, mode = key
    scales = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
    }
    scale = []
    note_index = get_note_index(note)
    enharmonic = note_map()[get_note_index(note)].index(note)
    for i, x in enumerate(scales[mode]):
        if x + note_index < 11:
            scale_note = note_map()[x + note_index]
        else:
            scale_note = note_map()[note_index - 12 + x]
        enharmonic = enharmonic if i == 0 else \
            [i for i, n in enumerate(scale_note) if get_next_note(scale[-1][0]) == n[0]][0]
        scale.append(scale_note[enharmonic])
    return scale


def convert_numeral(numeral: str, alteration: str, key: List):
    """
    Auxiliary function that given a roman numeral and its key information
    returns the base chord. The function only processes the base chord,
    without taking into account modifiers to the chord.
    Parameters
    ----------
    numeral : str
        A roman numeral chord in without any attribute or alteration.
    alteration : str
        A string containing the alterations to the base numeral. If no
        alterations are present it has to be an empty string.
    key: List
        A list of string structured in the following way: [key, mode]
    Returns
    -------
    converted_chord : str
        A chord expressed in a Harte-like notation, without any attribute.
    chord_type : Tuple
        A tuple containing all grades that make up the converted chord.
        The grades are expressed in a Harte-like notation.
    """

    romans = {
        'I': 1,
        'II': 2,
        'III': 3,
        'IV': 4,
        'V': 5,
        'VI': 6,
        'VII': 7,
        'VIII': 1,
        'IX': 9,
        'X': 10,
        'IT': 2,
    }
    # initialise key index and note index
    if len(key) == 2 and key[1].lower() == 'major' or key[1].lower() == 'minor':
        key_scale = get_scale(key)
    else:
        raise ValueError(
            'The "key" parameter is not set properly.\n'
            'It must be formatted as ["key", "mode"] and the only modes supported are "major" and "minor".')
    # calculate the chord type
    chord_type = ('3', '5') if numeral.isupper() else ('b3', '5')
    # calculate the degrees that can be found between the key index and the note index
    roman_numeral = numeral.upper()

    try:
        base_chord = key_scale[romans[roman_numeral] - 1]

    except:
        pass
    # handle alterations
    alteration = alteration if alteration == "#" or alteration == 'b' else ''
    if roman_numeral == 'VII' and chord_type == ('b3', '5'):
        print(alteration)

    if roman_numeral in ['IT', 'GER', 'N', 'CAD', 'FR']:
        return roman_numeral
    chord = (base_chord + alteration).replace('b#', '')
    return chord, chord_type


def convert_roman_numeral(processed_chord: Tuple) -> str:
    """
    Converts a roman numeral into a base chord. It does not consider any chord
    alteration or modifier to the chord.
    Parameters
    ----------
    processed_chord : str
        The output of the function decompose_roman, which is the result of the
        decomposition of a roman numeral.
        Refer to the function for more information.
    Returns
    -------
    chord : str
        A string indicating the base chord (as described by the Harte notation),
        including basic alterations (i.e. # and b, and their combinations).
    root_note : Tuple
        A tuple of strings, in which each string corresponds to a grade of the
        base chord.
    """
    # initialise parameters
    key = processed_chord[0]
    decomposed_chord = processed_chord[1]

    inversions = {
        '63': ((), '3'),
        '6': ((), '3'),
        '64': ((), '5'),
        '65': (('3', '5', '7'), '3'),
        '43': (('3', '5', '7'), '5'),
        '42': (('3', '5', '7'), '7'),
        '4': (('*3', '5'), ''),
        'ø': (('b3', 'b5', 'b7'), ''),
        'd': (('b3', 'b5', 'bb7'), ''),  # try to use shorthand
        'o': (('b3', 'b5', 'bb7'), ''),  # try to use shorthand
        '+': (('3', '#5'), ''),
        'maj7': (('3', '5', '7'), ''),
        'maj2': (('2', '3', '5'), ''),
        'maj4': (('3', '4', '5'), ''),
        'maj6': (('3', '5', '6'), ''),
    }

    converted_roman = convert_numeral(decomposed_chord[1], decomposed_chord[0], key)
    print(converted_roman)
    if decomposed_chord[2] != '' and decomposed_chord[2] in inversions.keys():
        grades, root = inversions[decomposed_chord[2]]
        # print(grades, root)


def simplify_chord(chord_label: str) -> str:
    """
    Simple function that takes a Harte chorde and returns a Harte chord simplified,
    i.e. considering the Harte Notation shorthands.
    Parameters
    ----------
    chord_label : str
        A chord label annotated in Harte.
    Returns
    -------
    chords_simplified_label : str
        A chord label annotated using shortcuts.
    """
    pass


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
                converted_chord = convert_roman_numeral(processed_chord)
                # print(converted_chord)


if '__main__' == __name__:
    # test_roman_conversion('../../partitions/when-in-rome/choco/chord_stats.csv')
    print(convert_roman_numeral((['F', 'minor'], ('', 'V', '65', ''), '')))
