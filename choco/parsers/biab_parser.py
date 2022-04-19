"""
Utilities for extracting chord annotations from notated music annotated
using the Band-in-a-Box software.
"""
import math
from typing import Tuple

import biab_converter

from m21_parser import process_score

# print output sample
print(process_score(
    "/Users/andreapoltronieri/PycharmProjects/choco/partitions/wikifonia/.onbekend, onbekend - Cill Chais.mxl"), '\n')


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
    biab_metadata = biab_converter.biab_meta(biab_path)
    title, metre_nominator, metre_denominator, key, time = biab_metadata

    # offset, lenght, chord = zip(*biab_converter.biab_chords(biab_path))

    # get the chord information
    jams_chords = []
    chord_annotation = biab_converter.biab_chords(biab_path)

    # recalculate the chord annotations beat-wise
    beat = 0
    measure_space = 0
    total_beats = chord_annotation[-1][0] + chord_annotation[-1][1]
    for idx, chord in enumerate(chord_annotation):
        chord_start, length, label = chord
        print(chord)
        remaining_space = metre_denominator - length
        if remaining_space < 0:
            pass
        if measure_space >= metre_denominator:
            measure_space = 0
        for _ in range(math.ceil(length / metre_denominator)):
            chord_measure_length = length / math.ceil(length / metre_denominator)
            measure_space += chord_measure_length
            if measure_space >= metre_denominator:
                beat += 1
            print(beat, chord_measure_length, measure_space)
            jams_chords.append((label, beat, chord_measure_length))

    # arrange the metadata information
    meta = {'title': title, 'composers': None, 'expansion': False, 'duration': total_beats}

    return (meta, jams_chords)


# test the algorithm
process_biab(
    "/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData/All Of You_id_05946_midicons.MGU")
