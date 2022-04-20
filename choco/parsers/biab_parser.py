"""
Utilities for extracting chord annotations from notated music annotated
using the Band-in-a-Box software.
"""
import math
from typing import Tuple

import biab_converter

from m21_parser import process_score

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
    for chord in chord_annotation:
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


def process_biab_2(biab_path):
    # get the file metadata
    biab_metadata = biab_converter.biab_meta(biab_path)
    title, metre_nominator, metre_denominator, key, time = biab_metadata

    # offset, lenght, chord = zip(*biab_converter.biab_chords(biab_path))

    # get the chord information
    jams_chords = []
    # chord_annotation = biab_converter.biab_chords(biab_path)
    chord_annotation = [[4, 4, 'Eb:maj7'], [8, 8, 'Bb:(7,b9)'], [16, 4, 'Bb:(7,b9)']]
    # print(chord_annotation)
    # recalculate the chord annotations beat-wise
    abc = []
    [abc.extend([x[2]] * x[1]) for x in chord_annotation]

    total_beats = chord_annotation[-1][0] + chord_annotation[-1][1]
    for x in range(int(total_beats / metre_nominator) - 1):
        measure_chord = abc[(x * metre_nominator):(x * metre_nominator + metre_nominator)]
        chords = []
        for i, mc in enumerate(measure_chord):
            if [mc, i - 1, ...] not in chords:
                chords.append([mc, i, 1])
            else:
                pass
            offset = i
            length = 1
            # chords[mc] = 0
            # if mc == measure_chord[i + 1]:
            #     length += 1
            jams_chords.append([mc, length, offset])
    # print(jams_chords)


    beat = 0
    measure_space = 0
    space_remaining = metre_nominator
    print(chord_annotation)
    for chord in chord_annotation:
        chord_start, chord_duration, chord_label = chord
        print(chord)

        space_remaining = space_remaining - chord_duration
        print(space_remaining)
        if space_remaining >= 0:
            offset = 0
            jams_chords.append([chord_label, chord_duration])
            print(chord_label, chord_duration)
            if space_remaining == 0:
                space_remaining = metre_nominator

        if space_remaining < 0:
            for x in range(abs(math.ceil(space_remaining / metre_nominator))):
                chord_duration = abs(math.ceil(space_remaining / metre_nominator))
                jams_chords.append([chord_label, chord_duration])
                print(chord_label, chord_duration)


def process_biab_3():
    jams_chords = []
    # chord_annotation = biab_converter.biab_chords(biab_path)
    chord_annotation = [[4, 3, 'Eb:maj7'], [8, 8, 'Bb:(7,b9)'], [16, 4, 'C:(7,b9)']]

    numerator, denominator = 3, 4
    measure = 0
    space_remaining = numerator
    for chord in chord_annotation:
        chord_start, chord_duration, chord_label = chord
        offset = 0
        # space_remaining = numerator - chord_duration - already_used_space

        #if space_remaining:
        chord_remaining = chord_duration
        # if space_remaining == 0 or space_remaining == numerator:
        for x in range(math.ceil(chord_duration / numerator)):
            if space_remaining == 0 or space_remaining == numerator:
                measure += 1
                actual_duration = numerator if chord_remaining >= numerator else chord_remaining
            else:
                print('chord_remaining', chord_remaining)
                actual_duration = space_remaining if chord_remaining > space_remaining else chord_remaining
                print('actual_duration', actual_duration)
            print(measure, chord_label, offset, actual_duration)
            jams_chords.append([chord_label, offset, actual_duration])
            chord_remaining -= actual_duration
            space_remaining = numerator - actual_duration if numerator - actual_duration > 0 else numerator
        print(space_remaining)

        ## deprecated
        if space_remaining == 'asdc':
            for x in range(math.ceil(chord_duration / numerator)):
                actual_duration = space_remaining if chord_remaining > space_remaining else chord_remaining
                print(measure, chord_label, offset, actual_duration)
                jams_chords.append([chord_label, offset, actual_duration])
                chord_remaining -= actual_duration
                space_remaining = space_remaining - actual_duration
                continue


# test the algorithm process_biab_2("/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData/All
# Of You_id_05946_midicons.MGU")

process_biab_3()
