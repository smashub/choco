"""
Utility functions related to the generation and interpretation of the
Harte chord notation.
"""

from collections import OrderedDict
from typing import List

from music21 import chord, interval, note


def simplify_harte(harte_grades: List) -> str:
    """
    Utility function that given the grades that constitute a Harte chord
    (as a list) returns a string of Harte complained grades, using
    shorthands, if possible.
    Parameters
    ----------
    harte_grades : List
        A list of the grades as annotated in the Harte format, without
        any shortcut.
    Returns
    -------
    harte_attributes : str
        A list of the attributes formatted in Harte containing all the
        elements except for the bass note, using shorthands if possible.
        The output string has a format such as: :maj7(b9)
    """
    clean_harte_grades = clean_grades(harte_grades)
    shorthand_map = OrderedDict(
        {
            ("3", "5", "b7", "9"): "9",
            ("3", "5", "7", "9"): "maj9",
            ("b3", "5", "b7", "9"): "min9",
            ("3", "5", "b7"): "7",
            ("3", "5", "6"): "maj6",
            ("b3", "5", "6"): "min6",
            ("3", "5", "7"): "maj7",
            ("b3", "b5", "bb7"): "dim7",
            ("b3", "5", "b7"): "min7",
            ("b3", "b5", "b7"): "hdim7",
            ("b3", "5", "7"): "minmaj7",
            ("3", "5"): "maj",
            ("b3", "5"): "min",
            ("b3", "b5"): "dim",
            ("3", "#5"): "aug",
            ("4", "5"): "sus4",
        }
    )
    separator, shorthand = "", ""
    for grades in shorthand_map.keys():
        intersection = set(grades).intersection(clean_harte_grades)
        if len(intersection) == len(grades):
            shorthand = shorthand_map[grades]
            clean_harte_grades = list(set(clean_harte_grades) - intersection)
            if "1" in clean_harte_grades:
                clean_harte_grades.remove("1")
            if "sus" in shorthand and "*3" in clean_harte_grades:
                clean_harte_grades.remove("*3")
            break
    clean_harte_grades = (
        f'({",".join([x for x in sorted(clean_harte_grades, key=lambda p: int("".join([z for z in p if z.isdigit()])))])})'
        if len(clean_harte_grades) > 0 and clean_harte_grades != "(1)"
        else ""
    )
    if len(shorthand) > 0 or len(clean_harte_grades) > 0:
        separator = ":"
    return separator + shorthand + clean_harte_grades


def grammar_rule_to_music21_chord_type(rule: str):
    """Convert grammar rule so that it can be used as key in
    music21.harmony.CHORD_TYPES.

    Parameters
    ----------
    rule : str
        Grammar rule

    Returns
    -------
    str
        music21 CHORD_TYPE rule
    """
    return rule.replace("_", "-")


def calculate_interval(note_1: note, note_2: note, simple: bool = True) -> str:
    """
    Utility function that given two music21 notes returns the interval
    calculated between the two.
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
    mode = "simpleName" if simple is True else "name"
    computed_interval = getattr(interval.Interval(note_1, note_2), mode)
    return convert_intervals(computed_interval).replace("b2", "b9").replace("2", "9")


def convert_intervals(m21_interval: str) -> str:
    """
    Utility function that converts intervals from the music21 format to the
    Harte one.
    Parameters
    ----------
    m21_interval : str
        A string containing an interval as expressed by the music21 notation
        (e.g. 'P4').
    Returns
    -------
    harte:interval : str
        A string containing an interval as expressed by the Harte notation
        (e.g. 'b2').
    """
    substitutions = {
        "M": "",
        "m": "b",
        "P": "",
        "d": "b",
        "A": "#",
    }

    translation = m21_interval.translate(m21_interval.maketrans(substitutions))
    if m21_interval in ["d2", "d3", "d6", "d7"]:
        translation = "b" + translation
    return translation


def convert_root(chord_root: chord) -> str:
    """
    Utility function for cleaning the string of a chord root note and making
    it compliant to the Harte notation.
    Parameters
    ----------
    chord_root : music21.chord.Chord
        A chord expressed by the music21 notation.
    Returns
    -------
    harte_root : str
        The root of the note in the Harte notation.
    """
    root_note = str(chord_root)
    root = "".join(x for x in root_note if not x.isdigit())
    return root.replace("-", "b")


def clean_grades(grades_list: List) -> List:
    """
    Utility function that cleans and orders a list of tones encoded
    according to the Harte notation (containing 'b', '#', and '*').
    Parameters
    ----------
    grades_list : str
        A list of grades in the Harte notation.
        If the characters in input are illegal for the Harte notation,
        an exception is raised.
    Returns
    -------
    sorted_grades : str
        The input grades cleaned (without 1st and 8th grade, with *1
        if not root is listed among grades) sorted from the lower to
        the higher.
    """
    has_third = True if any("3" in g[-1] for g in grades_list) else False
    has_fifth = True if any("5" in g[-1] for g in grades_list) else False
    # add third and fifth if not in grades
    if not has_third:
        grades_list.append("*3")
    if not has_fifth:
        grades_list.append("*5")
    # pretty grades
    try:
        return sorted(
            grades_list,
            key=lambda x: int(x.replace("b", "").replace("#", "").replace("*", "")),
        )
    except ValueError:
        raise ValueError(
            "The list of grades contains non valid characters " "to the Harte notation."
        )
