"""
Utilities for extracting chord annotations from notated music annotated
using the Band-in-a-Box software.
In this file you can find two different versions of the same code, having
the exact same output:
    - process_biab_cpp implements a parser for Band-in-a-Box files starting
    from a C++ implementation provided by Andrew Choi
    - process_biab_py implements a parser for Band-in-a-Box files starting
    from a Python2 implementation, still provided by Andrew Choi, later
    converted in Python3. This implementation contains more controls for
    checking the integrity of the original BiaB file.
"""
import glob
import math
import os
from typing import Tuple

import biab


def process_biab_cpp(biab_path: str) -> Tuple:
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
        biab_data = biab.biab_data(biab_path)
        metadata, chord_annotation = biab_data
        print(metadata, '\n', chord_annotation)
        title, metre_nominator, metre_denominator, key, tempo = metadata
    except (UnicodeDecodeError, TypeError):
        raise UnicodeDecodeError
    except ValueError:
        raise FileNotFoundError('No file found at the specified path')

    # get the track length information (measured in beats)
    total_length = float(chord_annotation[-1][0]) + float(
        chord_annotation[-1][1])

    # define types
    metre_nominator = int(metre_nominator)
    metre_denominator = int(metre_denominator)

    # recalculate the chord annotations beat-wise
    # initialise measure values
    jams_chords = []
    # iterate over precomputed chords
    for idx, chord in enumerate(chord_annotation, start=1):
        chord_start, chord_duration, chord_label = chord
        jams_chords.append([chord_label, idx, chord_start, chord_duration])

    # arrange the metadata information
    meta = {'title': title, 'composers': [], 'expansion': False,
            'duration': total_length, 'duration_m': jams_chords[-1][1] + 1}
    metric_info = [
        [f'{metre_nominator}/{metre_denominator}', '0', 0, total_length]]
    key_info = [[key, '0', 0, total_length]]

    return meta, jams_chords, metric_info, key_info


def process_biab_cpp_measure(biab_path: str) -> Tuple:
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
        biab_data = biab.biab_data(biab_path)
        metadata, chord_annotation = biab_data
        print(metadata, '\n', chord_annotation)
        title, metre_nominator, metre_denominator, key, tempo = metadata
    except (UnicodeDecodeError, TypeError):
        raise UnicodeDecodeError
    except ValueError:
        raise FileNotFoundError('No file found at the specified path')

    # get the track length information (measured in beats)
    total_length = float(chord_annotation[-1][0]) + float(
        chord_annotation[-1][1])

    # define types
    metre_nominator = int(metre_nominator)
    metre_denominator = int(metre_denominator)

    # recalculate the chord annotations beat-wise
    # initialise measure values
    jams_chords = []
    measure = 0
    offset = 0
    measure_remaining = metre_nominator
    # iterate over precomputed chords
    for chord in chord_annotation:
        chord_start, chord_duration, chord_label = chord
        chord_start, chord_duration = float(chord_start), float(chord_duration)
        chord_remaining = int(chord_duration)
        # if space_remaining == 0 or space_remaining == numerator:
        for x in range(
                math.ceil(float(chord_duration) / float(metre_nominator))):
            if measure_remaining == metre_nominator:
                measure += 1
                actual_duration = metre_nominator \
                    if chord_remaining >= metre_nominator else chord_remaining
            else:
                actual_duration = measure_remaining \
                    if chord_remaining > measure_remaining else chord_remaining
            # print(measure, chord_label, offset, actual_duration)
            jams_chords.append([chord_label, measure - 1, float(offset),
                                float(actual_duration)])
            chord_remaining -= actual_duration
            measure_remaining = measure_remaining - actual_duration \
                if measure_remaining - actual_duration > 0 \
                else metre_nominator
            offset = metre_nominator - measure_remaining

    # arrange the metadata information
    meta = {'title': title, 'composers': [], 'expansion': False,
            'duration': total_length, 'duration_m': jams_chords[-1][1] + 1}
    metric_info = [
        [f'{metre_nominator}/{metre_denominator}', '0', 0, total_length]]
    key_info = [[key, '0', 0, total_length]]

    return meta, jams_chords, metric_info, key_info


if __name__ == '__main__':
    # just for testing purposes
    # print(process_biab_cpp('/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData/April In '
    #                        'Paris_id_07239_allanah.MG1'))

    biab_files = glob.glob(
        os.path.join(
            '/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData',
            "*"))
    for x in biab_files:
        process_biab_cpp(x)
