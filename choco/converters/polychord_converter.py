"""
Converter for Polychord, i.e. listing of notes that are the constituent of
a chord.
Used for converting polychords that can be found in some Leadsheet datasets.
"""

from music21 import note, chord, pitch

from harte_utils import convert_root, calculate_interval, simplify_harte


def convert_polychord(polychord: str, handle_error: bool = True) -> str:
    """
    Utility function that given a polychord (a string composed by a list of comma
    separated notes) returns a cleaned list object of the chord notes.
    Parameters
    ----------
    polychord : str
        A polychord, encoded as a string of comma separated notes.
    handle_error: bool, default = True
        A boolean that indicates whether to raise an error if a chord is not
        converted or return 'N'
    Returns
    -------
    cleaned_list : list
        A list of the chord notes.
    """
    if polychord in ['NF', 'N.C.', 'Chord Symbol Cannot Be Identified']:
        return 'N'
    # convert the polychord
    try:
        polychord = polychord.split(',')
        if handle_error is False:
            assert len(polychord) > 1, ValueError('Not a Polychord.')
        chord_object = chord.Chord(polychord)
    except (ValueError, pitch.PitchException, pitch.AccidentalException):
        if handle_error is False:
            raise ValueError('Impossible to convert Polychord.')
        else:
            return 'N'
    # get root and bass information
    root, bass = chord_object.root(), chord_object.bass()
    converted_root = convert_root(root)
    bass_interval = calculate_interval(root, bass, simple=True)
    bass_interval = f'/{bass_interval}' if bass_interval != '1' else ''
    # get chord tones
    chord_intervals = [calculate_interval(note.Note(root), note.Note(x), simple=True) for x in chord_object.pitchNames]
    if '1' in chord_intervals:
        chord_intervals.remove('1')
    elif '8' in chord_intervals:
        chord_intervals.remove('8')
    formatted_intervals = simplify_harte(chord_intervals)

    return str(converted_root + formatted_intervals + bass_interval)


if '__main__' == __name__:
    print(convert_polychord('c,'))
