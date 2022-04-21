"""
Utilities for extracting chord annotations from notated music annotated
using the Band-in-a-Box software.
"""
import math
from typing import Tuple

import biab_converter


def process_biab(biab_path: str) -> Tuple:
    """
    Parameters
    ----------
    biab_path: str
        The absolute path of a Band-in-a-Box file

    Returns
    -------
    metadata : dict
        A dictionary with all the metadata associated to the tune, including
        title, name of composer, etc. (if available). It also includes a boolean
        placeholder recording whether the score has been expanded or not.
    chord_ann : list of tuples
        A list of (Chord, measure, offset) including all chord annotations.
    time_signature_ann : list of tuples
        A list of (time signature, measure, offset=0) for all time signatures.
    key_signature_ann : list of tuples
        A list of (key signature, measure, offset=0) for all key signatures.
    """

    # get the file metadata
    try:
        biab_metadata = biab_converter.biab_meta(biab_path)
        # TODO investigate how to extract artist name from BiaB
        title, metre_nominator, metre_denominator, key, time = biab_metadata
        chord_annotation = biab_converter.biab_chords(biab_path)
    except ValueError:
        raise FileNotFoundError('No file found at the specified path')

    # get the track length information (measured in beats)
    total_length = chord_annotation[-1][0] + chord_annotation[-1][1]

    # recalculate the chord annotations beat-wise
    # initialise measure values
    jams_chords = []
    measure = 0
    offset = 0
    measure_remaining = metre_nominator
    # iterate over precomputed chords
    for chord in chord_annotation:
        chord_start, chord_duration, chord_label = chord
        chord_remaining = chord_duration
        # if space_remaining == 0 or space_remaining == numerator:
        for x in range(math.ceil(chord_duration / metre_nominator)):
            if measure_remaining == metre_nominator:
                measure += 1
                actual_duration = metre_nominator if chord_remaining >= metre_nominator else chord_remaining
            else:
                actual_duration = measure_remaining if chord_remaining > measure_remaining else chord_remaining
            # print(measure, chord_label, offset, actual_duration)
            jams_chords.append([chord_label, measure, float(offset), float(actual_duration)])
            chord_remaining -= actual_duration
            measure_remaining = measure_remaining - actual_duration if measure_remaining - actual_duration > 0 \
                else metre_nominator
            offset = metre_nominator - measure_remaining

    # arrange the metadata information
    meta = {'title': title, 'composers': [], 'expansion': False, 'duration': total_length}
    metric_info = [[f'{metre_nominator}/{metre_denominator}', '0', 0, total_length]]
    key_info = [[key, '0', 0, total_length]]

    return meta, jams_chords, metric_info, key_info
