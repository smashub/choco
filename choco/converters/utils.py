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


def get_root_grade(base_chord: str, chord_type: str, root_note: str) -> int:
    chord_types = {
        'min': 'minor',
        'maj': 'major',
        '7': 'major',
    }
    type = chord_types[chord_type] if chord_type in chord_types.keys() else 'major'
    alternate_bass = get_scale(base_chord, type).index(root_note)
    print('#######', alternate_bass)
    return alternate_bass
