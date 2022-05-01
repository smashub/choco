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
                          '(ø|o|d|maj2|maj4|maj6|maj7|\+?)([b#M0-9+-]{0,})(\[.*\]{0,2})?',
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


def add_chord_grade(grade_list: list, new_grade: list) -> List:
    """
    Auxiliary function that append a chord grade to a list of
    chord grades, sorting the list.
    """
    grade_list.extend(new_grade)
    grade_list.sort(key=lambda x: x[-1])
    return grade_list


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
    chord_type : List
        A list containing all grades that make up the converted chord.
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
        'IT': 6,
        'N': 2,
        'FR': 2,
        'GER': 6,
        'CAD': 1,
    }
    # initialise key index and note index
    if len(key) == 2 and key[1].lower() == 'major' or key[1].lower() == 'minor':
        key_scale = get_scale(key)
    else:
        raise ValueError(
            'The "key" parameter is not set properly.\n'
            'It must be formatted as ["key", "mode"] and the only modes supported are "major" and "minor".')
    # calculate the chord type
    chord_grades = ['3', '5'] if numeral.isupper() else ['b3', '5']
    # calculate the degrees that can be found between the key index and the note index
    roman_numeral = numeral.upper()

    # check if the roman is mapped, else raise an error
    if roman_numeral in romans.keys():
        base_chord = key_scale[romans[roman_numeral] - 1]
    else:
        raise ValueError('The roman numeral is not mapped.')
    # handle alterations
    alteration = alteration if alteration == "#" or alteration == 'b' else ''
    if roman_numeral == 'VII' and key[1] == 'minor':
        alteration += '#'
    if roman_numeral == 'N':
        alteration += 'b'
    if roman_numeral == 'It':
        alteration += 'b'
        add_chord_grade(chord_grades, ['*5', 'b7'])
    if roman_numeral == 'Fr':
        chord_grades = ['3', '4', 'b7']
    if roman_numeral == 'Fr':
        alteration += 'b'
        chord_grades = ['3', 'b5', '#6']
    alteration = alteration.replace('b#', '').replace('#b', '')

    chord_converted = (base_chord + alteration)
    return chord_converted, chord_grades


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
    key, decomposed_chord, roots = processed_chord

    chord_alteration, chord_roman, chord_type, chord_inversion, chord_no_add = decomposed_chord
    # print(chord_inversion)

    types = {
        'ø': (('b3', 'b5', 'b7'), ''),
        'd': (('b3', 'b5', 'bb7'), ''),  # try to use shorthand
        'o': (('b3', 'b5', 'bb7'), ''),  # try to use shorthand
        '+': (('3', '#5'), ''),
        'maj7': (('3', '5', '7'), ''),
        'maj2': (('2', '3', '5'), ''),
        'maj4': (('3', '4', '5'), ''),
        'maj6': (('3', '5', '6'), ''),
    }

    inversions = {
        '5': (('1', '3', '5'), '5'),  # TODO check with musicologists
        '54': (('1', '3', '5'), '5'),  # TODO check with musicologists
        '3': (('1', '3', '5'), '3'),  # TODO check with musicologists
        'b3': (('1', 'b3', '5'), 'b3'),  # TODO check with musicologists
        '53': (('1', '3', '5'), '3'),
        '532': (('1', '3', '4', '5'), '3'),
        '5b3': (('1', '3', 'b5'), '3'),
        '753': (('1', '3', '5'), '3'),
        '63': (('1', '3', '5'), '3'),
        '62': (('1', '3', '4', '5'), '3'),  # TODO check with musicologists
        'b': (('1', '3', '5'), '3'),
        '6': (('1', '3', '5'), '3'),
        '7+6': (('1', '3', '5', '7'), '3'),  # TODO check with musicologists
        '6+': (('1', '3', '5', '7'), '3'),  # TODO check with musicologists
        '64': (('1', '3', '5'), '5'),
        '7': (('3', '5', 'b7'), ''),
        '#7': (('3', '5', '7'), ''),
        '9': (('3', '5', 'b7', 'b9'), ''),
        '7b9': (('3', '5', 'b7', 'b9'), ''),
        '7M9': (('3', '5', 'b7', '9'), ''),
        'b9': (('3', '5', 'b7', 'b9'), ''),
        'b7': (('3', '5', 'b7'), ''),
        '65': (('3', '5', 'b7'), '3'),
        '6-5': (('3', '5', 'b7'), '3'),
        '654': (('3', '5', '6', 'b7'), '3'),
        '6b5': (('3', 'b5', 'b7'), '3'),
        '65M9': (('3', '5', 'b7', '9'), '3'),
        '765': (('3', '5', 'b7'), '3'),
        '6#5': (('3', '5', '7'), '3'),
        '653': (('3', '5', 'b7'), '3'),
        '65b3': (('b3', '5', 'b7'), 'b3'),
        'b7653': (('3', '5', 'b7'), '3'),
        '43': (('3', '5', 'b7'), '5'),
        '43M9': (('3', '5', 'b7', '9'), '5'),
        '4#3': (('3', '5', '7'), '5'),
        '4b3': (('b3', '5', 'b7'), '5'),
        '643': (('3', '5', 'b7'), '5'),
        '64b3': (('3', '5', 'bb7'), '5'),
        '6432': (('3', '5', '6', 'b7'), '5'),
        '64b32': (('3', '5', '6', 'bb7'), '5'),
        '42': (('3', '5', 'b7'), 'b7'),
        '742': (('3', '5', 'b7'), 'b7'),
        '732': (('2', '5', 'b7'), 'b7'),  # TODO check with musicologists
        '642': (('3', '5', 'b7'), 'b7'),
        '6b42': (('b3', '5', '7'), 'b7'),
        '2': (('3', '5', 'b7'), 'b7'),
        '4': (('*3', '5'), ''),
    }

    converted_roman = convert_numeral(chord_roman, chord_alteration, key)
    # disambiguate the semantics of the root list
    roots_validated = []
    for root in roots:
        if root.isnumeric():
            chord_inversion += root
        else:
            roots_validated.append(root)

    # compute the chord types (e.g. diminished)
    if chord_type != '' and chord_type in types.keys():
        grades, root = types[chord_type]
        # print(grades, root)

    # compute chord inversions
    if chord_inversion != '' and chord_inversion in inversions.keys():
        #print(processed_chord)
        print(chord_inversion)
    return converted_roman


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
                # check if the chord is decomposed correctly
                processed_chord = decompose_roman(chord_data[0])
                k = ' '.join(processed_chord[0])
                ch = ''.join(processed_chord[1])
                root = f"/{'/'.join([x for x in processed_chord[2]])}" if len(processed_chord[2]) > 0 else ''
                if f'{k}:{ch}{root}' == chord_data[0]:
                    pass
                # print(processed_chord)
                converted_chord = convert_roman_numeral(processed_chord)
                # print(converted_chord)


if '__main__' == __name__:
    test_roman_conversion('../../partitions/when-in-rome/choco/chord_stats.csv')
    # print(convert_roman_numeral((['F', 'minor'], ('b', 'VII', '', '65'), '')))
