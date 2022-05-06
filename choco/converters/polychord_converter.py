"""
Converter for Polychord.
"""
from typing import List

from mingus.core import chords


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
    polychord = polychord.split(',')


if '__main__' == __name__:
    pass
