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
import math
from typing import Tuple

# import biab_converter

from utils import get_note_index
from py_biab_converter.biab_reader import read_biab_file


# def process_biab_cpp(biab_path: str) -> Tuple:
#     """
#     Parameters
#     ----------
#     biab_path: str
#         The absolute path of a Band-in-a-Box file

#     Returns
#     -------
#     metadata : dict
#         A dictionary with all the metadata associated to the tune, including
#         title, name of composer, etc. (if available). It also includes a boolean
#         placeholder recording whether the score has been expanded or not.
#     chord_ann : list of tuples
#         A list of (Chord, measure, offset) including all chord annotations.
#     time_signature_ann : list of tuples
#         A list of (time signature, measure, offset=0) for all time signatures.
#     key_signature_ann : list of tuples
#         A list of (key signature, measure, offset=0) for all key signatures.
#     """

#     # get the file metadata
#     try:
#         biab_metadata = biab_converter.biab_meta(biab_path)
#         # TODO investigate how to extract artist name from BiaB
#         title, metre_nominator, metre_denominator, key, time = biab_metadata
#         chord_annotation = biab_converter.biab_chords(biab_path)
#     except ValueError:
#         raise FileNotFoundError('No file found at the specified path')

#     # get the track length information (measured in beats)
#     total_length = chord_annotation[-1][0] + chord_annotation[-1][1]

#     # recalculate the chord annotations beat-wise
#     # initialise measure values
#     jams_chords = []
#     measure = 0
#     offset = 0
#     measure_remaining = metre_nominator
#     # iterate over precomputed chords
#     for chord in chord_annotation:
#         chord_start, chord_duration, chord_label = chord
#         chord_remaining = chord_duration
#         # if space_remaining == 0 or space_remaining == numerator:
#         for x in range(math.ceil(chord_duration / metre_nominator)):
#             if measure_remaining == metre_nominator:
#                 measure += 1
#                 actual_duration = metre_nominator if chord_remaining >= metre_nominator else chord_remaining
#             else:
#                 actual_duration = measure_remaining if chord_remaining > measure_remaining else chord_remaining
#             # print(measure, chord_label, offset, actual_duration)
#             jams_chords.append([chord_label, measure, float(offset), float(actual_duration)])
#             chord_remaining -= actual_duration
#             measure_remaining = measure_remaining - actual_duration if measure_remaining - actual_duration > 0 \
#                 else metre_nominator
#             offset = metre_nominator - measure_remaining

#     # arrange the metadata information
#     meta = {'title': title, 'composers': [], 'expansion': False, 'duration': total_length}
#     metric_info = [[f'{metre_nominator}/{metre_denominator}', '0', 0, total_length]]
#     key_info = [[key, '0', 0, total_length]]

#     return meta, jams_chords, metric_info, key_info


def get_note_interval(first_note: str, second_note: str) -> str:
    roots = {1: 'b2', 2: '2', 3: 'b3', 4: '3', 5: '4', 6: 'b5', 7: '5', 8: 'b6', 9: '6', 10: 'b7', 11: '7', 12: '1'}

    note_index_first = get_note_index(first_note)
    note_index_second = get_note_index(second_note)
    interval_degree = note_index_second - note_index_first if note_index_second > note_index_first else (
                                                                12 + note_index_second) - note_index_first
    if interval_degree in roots.keys():
        return roots[interval_degree]


def process_biab_py(biab_path: str) -> Tuple:
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
    chord_info = read_biab_file(biab_path)
    title = chord_info['name']
    metre = chord_info['style']['meter']
    key = chord_info['key']
    tempo = chord_info['tempo']
    chords = chord_info['chords']

    # process chords metre-wise
    jams_chords = []
    root_note = ''
    for i, measure in enumerate(chords):
        offset = 0
        for chord in measure:
            chord_root, chord_attributes = chord[0].split(':')
            chord_root.replace('m', ':min')
            if len(chord_attributes.split('/')) > 1:
                chord_attributes, root_note = chord_attributes.split('/')
                root_note = f'/{get_note_interval(chord_root, root_note)}'
            chord_attributes = f"({chord_attributes.replace('.', ',')})".replace(
                '(3,5)', 'maj'
            ).replace(
                '(b3,5)', 'min'
            ).replace(
                '(3,5,7)', 'maj7')
            harte_chord = ':'.join([chord_root, chord_attributes]) + root_note
            jams_chords.append([harte_chord, i + 1, float(offset), float(chord[1])])
            offset = metre - chord[1]

    total_length = jams_chords[-1][1] * metre
    # organise meta information
    meta = {'title': title, 'composers': [], 'expansion': False, 'duration': total_length}
    metric_info = [[f'{metre}/4', '0', 0, total_length]]
    key_info = [[key, '0', 0, total_length]]

    return meta, jams_chords, metric_info, key_info
