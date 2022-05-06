"""
Converter for Polychord.
"""
from typing import List

from mingus.core import chords

from music21 import note, chord, interval, pitch


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


def convert_polychord(polychord: str):
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
    chord_obj = chord.Chord(polychord)

    root, bass = chord_obj.root(), chord_obj.bass()
    print(chord_obj, root, bass)


if '__main__' == __name__:
    convert_polychord('')
