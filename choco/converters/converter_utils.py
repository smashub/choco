"""
Utility functions for the converter module.
"""

import csv
import os
import re
from typing import List

from music21 import interval, note, scale


def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def get_scale(note: str, mode: str):
    """
    Auxiliary function that given the key information (key, mode), returns
    the scale for that key.
    Note: the function only works for minor and major mode.
    Parameters
    ----------
    note : List
        The starting note of the scale
    mode : str
        The scale mode. Please, note that only major and minor are supported
        so far.
    Returns
    -------
    scale : list
        A list of the notes that make up the scale for the given tonality.
    """
    scale_type = {
        "major": "MajorScale",
        "minor": "MinorScale",
        "diminished": "DiminishedScale",
    }
    m21_scale = getattr(scale, scale_type[mode])(note)
    return [
        str(x)[:-1].replace("-", "b")
        for x in m21_scale.getPitches(direction="ascending")
    ]


def get_root_grade(
    base_chord: str, chord_type: str, chord_grades: list, root_note: str
) -> str:
    """
    Utility function that returns the root grade, calculating it on the
    chord degrees.
    """
    root_note = root_note.capitalize()
    chord_types = {
        "min": "minor",
        "maj": "major",
        "7": "major",
        "9": "major",
        "min7": "min",
    }
    shorthands_grades = {
        "aug": ("3", "#5"),
        "dim": ("3", "b5"),
        "maj7": ("3", "5", "7"),
        "minmaj7": ("3", "b5", "7"),
        "dim7": ("b3", "b5", "bb7"),
        "hdim7": ("b3", "b5", "b7"),
        "maj6": ("3", "5", "6"),
        "min6": ("3", "5", "b6"),
        "maj9": ("3", "5", "7", "9"),
        "min9": ("b3", "5", "b7", "9"),
        "sus4": ("4", "5"),
    }

    base_type = chord_types[chord_type] if chord_type in chord_types.keys() else "major"

    chord_scale = get_scale(base_chord, base_type)
    search_note = [x for x in chord_scale if x[0] == root_note.upper()[0]][0]
    note_index = chord_scale.index(search_note) + 1
    modifier, root_attributes = "", ""
    if chord_type in shorthands_grades.keys():
        alternate_bass = [
            y for y in shorthands_grades[chord_type] if int(y[0]) == note_index
        ][0]
        s_interval = interval.ChromaticInterval(alternate_bass).getDiatonic()
    elif len(chord_grades) > 0:
        alternate_bass = [y for y in chord_grades if int(y[0]) == note_index][0]
        g_interval = interval.Interval(
            str(
                interval.ChromaticInterval(int(alternate_bass))
                .getDiatonic()
                .directedName
            )
        )
        g_interval.noteStart = note.Note(base_chord)
    else:
        alternate_bass = note_index
        if search_note != root_note:
            root_attributes = re.search("(b|#)", root_note)
            root_attributes = root_attributes.group(0) if root_attributes else ""
            key_modifier = re.search("(b|#)", search_note)
            key_modifier = key_modifier.group(0) if key_modifier else ""
            if key_modifier == "b":
                modifier = "#"
            elif key_modifier == "#":
                modifier = "b"

    return str(modifier + root_attributes + str(alternate_bass))


def open_stats_file(stats_file_path: str):
    """
    Opens the stats_file, which contains all chord annotations for each dataset.

    Parameters
    -----------
    stats_file_path : str
        The path of the stats_file
    Returns
    -------
    chord_list : List
        A list of all chord occurrences contained in the dataset.
    """
    with open(stats_file_path) as csv_file:
        stats = csv.reader(csv_file, delimiter=",")
        # skip header
        next(stats)
        return [x for x in stats]


def update_chord_list(original_list: List[List], new_list: List) -> List:
    """
    Utility function that checks if a couple of chords [original, converted]
    are present in a list of lists. If so, it increments the number of
    occurrences by one, otherwise it appends the new chord occurrence to the
    original list.
    Parameters
    ----------
    original_list : List[List]
        The original list in which to check for occurrences.
    new_list : List
        The new occurrence
    """
    # check if the chord exists
    for el in original_list:
        if el[0] == new_list[0] and el[1] == new_list[1]:
            el[-1] += new_list[-1]
            return original_list
    # if not found append
    original_list.append(new_list)
    return original_list


def robbie_williams_fix(chord: str) -> str:
    """
    Utility function that fixes a bug in the Robbie Williams dataset.
    Parameters
    ----------
    chord : str
        The chord to fix.
    Returns
    -------
    chord : str
        The fixed chord.
    """
    if chord == "Bb7/3":
        return "Bb:7/3"
    elif chord == "Bb7/5":
        return "Bb:7/5"
    return chord
