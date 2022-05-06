"""
Converter for Polychord.
"""
from typing import List

from mingus.core import chords

from music21 import note, chord, interval, pitch
from choco.converters.harte_utils import convert_intervals, convert_root, calculate_interval, simplify_harte


def clean_polychord(polychord: str) -> List:
    """
    Utility function that given a polychord (a string composed by a list of comma
    separated notes) returns a cleaned list object of the chord notes.
    Parameters
    ----------
    polychord : str
        A polychord, encoded as a string of comma separated notes.
    Returns
    -------
    cleaned_list : list
        A list of the chord notes.
    """
    return polychord.split(',')


def convert_polychord(polychord: str) -> str:
    """
    Utility function that given a polychord (a string composed by a list of comma
    separated notes) returns a cleaned list object of the chord notes.
    Parameters
    ----------
    polychord : str
        A polychord, encoded as a string of comma separated notes.
    Returns
    -------
    cleaned_list : list
        A list of the chord notes.
    """
    # convert the polychord
    polychord = polychord.split(',')
    chord_object = chord.Chord(polychord)
    # get root and bass information
    root, bass = chord_object.root(), chord_object.bass()
    converted_root = convert_root(root)
    bass_interval = calculate_interval(root, bass, simple=True)
    bass_interval = f'/{bass_interval}' if bass_interval != '1' else ''
    # get chord tones
    chord_intervals = [calculate_interval(note.Note(root), note.Note(x), simple=True) for x in chord_object.pitchNames]
    formatted_intervals = simplify_harte(chord_intervals)

    return str(converted_root + formatted_intervals + bass_interval)


if '__main__' == __name__:
    print(convert_polychord('C#4,E4,A4'))
