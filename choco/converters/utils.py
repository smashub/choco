"""
Utility functions for the converter module.
"""
from music21 import scale


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
        'major': 'MajorScale',
        'minor': 'MinorScale',
        'diminished': 'DiminishedScale',
    }
    m21_scale = getattr(scale, scale_type[mode])(note)
    return [str(x)[:-1].replace('-', 'b') for x in m21_scale.getPitches(direction="ascending")]
