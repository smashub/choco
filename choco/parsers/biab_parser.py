"""
Utilities for extracting chord annotations from notated music annotated
using the Band-in-a-Box software.
"""
import math
from typing import Tuple

import biab_converter


# print output sample
# print(process_score(
#     "/Users/andreapoltronieri/PycharmProjects/choco/partitions/wikifonia/.onbekend, onbekend - Cill Chais.mxl"), '\n')


def process_biab(biab_path: str) -> Tuple:
    """
    parameters:
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
        title, metre_nominator, metre_denominator, key, time = biab_metadata
        chord_annotation = biab_converter.biab_chords(biab_path)
    except ValueError:
        raise FileNotFoundError('No file found at the specified path')

    # recalculate the chord annotations beat-wise
    # initialise measure values
    jams_chords = []
    measure = 0
    offset = 0.0
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
            print(measure, chord_label, offset, actual_duration)
            jams_chords.append([chord_label, offset, actual_duration])
            chord_remaining -= actual_duration
            measure_remaining = measure_remaining - actual_duration if measure_remaining - actual_duration > 0 \
                else metre_nominator
            offset = float(metre_nominator - measure_remaining)

    # arrange the metadata information
    meta = {'title': title, 'composers': None, 'expansion': False, 'duration': 0}

    return meta, jams_chords


# test the algorithm
process_biab(
    "/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData/All Of You_id_0594_midicons.MGU")
