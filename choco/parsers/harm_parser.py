"""
Parsing utilities to read and process harmonic annotations in other textual
formats, such as the one proposed by Trevor de Clercq and David Temperley, and
the format introduced by Mark Granroth-Wilding for the JazzCorpus.

"""
import re
import os
import json
from pathlib import Path
from typing import Union

import numpy as np

RC_KEY_REG = r"\[[A-Z][b|\#]?\]"
RC_TSG_REG = r"\[\d+\/\d+\]"  # FIXME


def process_harm_json(harm_title: str,
                      chord_annotations_file: Union[str, Path],
                      metadata_file: Union[str, Path]):
    """
    Parse harmonic annotations in JSON format as released by Trevor and David,
    stored as a JSON file.

    Parameters
    ----------
    harm_title : str
        The title of the harmonic annotation to be parsed.
    chord_annotations_file : str
        The path to the JSON file containing the chord annotations.
    metadata_file : str
        The path to the JSON file containing the metadata.

    Returns
    -------
    chords : list of lists
        The chord annotations, where local keys and roman numerals are merged.
    time_signatures : list of lists
        The extracted time signatures, with timing information as for chords.
    keys : list of lists
        The extracted local keys, with timing information as for chords.
    """
    chord_annotations = json.load(open(chord_annotations_file, "r"))
    metadata = json.load(open(metadata_file, "r"))

    assert harm_title in chord_annotations.keys()
    assert harm_title in metadata.keys()

    chord_annotation = chord_annotations[harm_title]['harmony']
    time_signature = metadata[harm_title]['meter']
    if isinstance(time_signature, list):
        time_signature = time_signature[0]
    if time_signature == "0" or time_signature == "None":
        time_signature = "4/4"
    numerator, denominator = time_signature.split("/")

    key = metadata[harm_title]['key']
    if isinstance(key, list):
        key = key[0]

    all_chords, all_keys = [], []
    for chord_sequence in chord_annotation[:1]:
        keys, chords = [], []
        measure_no = 1
        for measure in chord_sequence.split('|'):
            chord_offset = 1
            measure = measure.strip()  # remove leading-tailing spaces
            lmeasure = len([c for c in measure.split() if '[' not in c])
            if lmeasure > 0:
                for chord in measure.split(' '):
                    chord_duration = 1 / lmeasure * int(numerator)
                    if chord.startswith("["):
                        if re.match(RC_KEY_REG, chord):
                            key = chord[1:-1]
                            keys.append([measure_no,
                                         chord_offset,
                                         None,
                                         key])
                    else:
                        if chord == "":
                            chords[-1][-2] += int(numerator)
                        elif chord == ".":
                            chords[-1][-2] += chord_duration
                            chord_offset += chord_duration
                        else:
                            key_chord = f'{key}:{chord}' if chord != "R" else "N"
                            chords.append([measure_no,
                                           chord_offset,
                                           chord_duration,
                                           key_chord])
                            chord_offset += chord_duration
                measure_no += 1
        all_chords.append(chords)
        all_keys.append(keys)

    max_duration = max([x[-1][0] * int(numerator) + x[-1][2] for x in all_chords])
    for keys in all_keys:
        for key_idx, key in enumerate(keys):
            if key_idx == len(keys) - 1:
                key[2] = max_duration
            else:
                key[2] = keys[key_idx + 1][1]

    time_signature = [[1, 1, max_duration, time_signature]]

    return all_chords, time_signature, all_keys


def process_harm_expanded(harm_annotation):
    """
    Parse an expanded harmonic annotation, as defined by Trevor and David, to
    extract chord, time signature, and local key annotations together with their
    timing information: [measure, measure offset, duration, value]. This is done
    as the timed-chord annotations released by the authors are temporally not
    consistent due to potential bugs in the `expand6` function. Measure offsets
    are expressed in relation to the position of each chord/key in the measure,
    thus ranging in the [0, 1) interval.

    Parameters
    ----------
    harm_annotation : str
        String representation of the harmonic annotation or file path.
    
    Returns
    -------
    chords : list of lists
        The chord annotations, where local keys and roman numerals are merged.
    time_signatures : list of lists
        The extracted time signatures, with timing information as for chords.
    keys : list of lists
        The extracted local keys, with timing information as for chords.
    
    See also
    --------
    http://rockcorpus.midside.com/harmonic_analyses.html

    Notes
    -----
        - Currently, time signatures are not returned (None is given).
        - Not all special symbols / characters are supported.
        - Chords are repeated when they should be sustained.
    """
    if os.path.isfile(harm_annotation):
        with open(harm_annotation, "r") as sample_exp_file:
            annotation_str = sample_exp_file.readlines()
        annotation_str = [ann_line for ann_line in annotation_str \
            if not ann_line.startswith("Warning")]  # filtration
        assert len(annotation_str) == 1
        annotation_str = annotation_str[0]

    annotation_str = annotation_str.strip()
    measures = annotation_str.split("|")[:-1]  # annotation finishes with "|"

    keys, chords = [], []
    for measure_no, measure in enumerate(measures, start=1):
        measure = measure.strip()  # remove leading-tailing spaces
        if len(measure) == 0:  # empty measure repeating the last occurrence
            if len(chords) > 0:  # extend duration of previous chord, if any
                chords[-1][-2] += 1
            continue  # jump to the next measure
        mspan = 1/len([c for c in measure.split() if "[" not in c])
        # print(measure, mspan)

        measure_offset = 0
        for annotation in measure.split():
            if "[" in annotation:  # key or time sig
                key = re.match(RC_KEY_REG, annotation)
                if key is not None:
                    current_key = key.group(0)[1:-1]
                    max_dur = len(measures) - (measure_no + mspan)
                    keys.append([measure_no, measure_offset, max_dur, current_key])

            elif annotation == "R":  # special non-harmonic characters
                measure_offset += mspan  # silence advances time
                trigger_silence = True

            else:  # at this stage, either a roman numeral or a dot is expected
                if annotation != ".":  # actual chord
                    trigger_silence = False
                    current_chord = f"{current_key}:{annotation}"
                # At this stage: new chord, repeated chord, silent chord
                if not trigger_silence:  # insert chord if not in silence mode
                    chords.append([measure_no, measure_offset,
                                   mspan, current_chord])
                measure_offset += mspan  # advance time

    if len(keys) > 1:  # duration of local keys can be adjusted
        for i, key in enumerate(keys[:-1]):
            start_i = key[0] + key[1]
            start_j = keys[i+1][0] + keys[i+1][1]
            key[-2] = start_j - start_i
    
    return chords, None, keys


def process_multiline_annotation(annotation):
    """
    Parse a multiline textual annotation as defined by Mark Granroth-Wilding.
    Measure offsets are returned as beats (beat offsets).

    Parameters
    ----------
    annotation : list
        A list containing the annotation lines, the last 3 of which are expected
        to have vertical alignment (same length).
    
    Returns
    -------
    hartelike_ann : list
        A list of harte-like chord annotations, where each individual entry is
        organised as [measure, beat offset, duration, chord]. Please, note that
        this annotation level expects chords transposed to C major.
    romanlike_ann : list
        A list of roman-like verbose annotations (e.g. I is Tonic).
    key_ann : list
        A list containing a keys, although only one is expected by the format.

    See also
    --------
    http://jazzparser.granroth-wilding.co.uk/JazzCorpus.html

    """
    key = re.search(r"Main key:\s+(\w[b|#]?)\s(\w+)?", annotation[1])
    scale = "major" if key.group(2) is None else key.group(2)
    key = key.group(1) + " " + scale  # e.g. F minor
    bpb = int(re.search(r"Bar length:\s+(\d+)", annotation[2]).group(1))

    chord_labels = annotation[3].strip().split()
    chord_durations = [int(d) for d in annotation[4].strip().split()]
    chord_roman_descs = annotation[5].strip().split()

    assert len(chord_labels) == len(chord_durations) == len(chord_roman_descs)
    absolute_durs = np.cumsum(chord_durations)

    hartelike_ann, romanlike_ann = [], []
    key_ann = [[1, 1, absolute_durs[-1], key]]

    for chord_label, chord_roman_desc, offset, duration in zip(
        chord_labels, chord_roman_descs, absolute_durs, chord_durations):

        measure, beat = offset // bpb, offset % bpb + 1
        hartelike_ann.append([measure, beat, duration, chord_label])
        romanlike_ann.append([measure, beat, duration,
                              f"{key}:{chord_roman_desc}"])
    
    time_signature_incomplete = [1, 1, bpb*hartelike_ann[-1][0], f"{bpb}/"]

    return hartelike_ann, romanlike_ann, key_ann, time_signature_incomplete


if __name__ == '__main__':
    # test the parser
    process_harm_json('A Change Is Gonna Come',
                      '../../partitions/rock-corpus/raw/chords.json',
                      '../../partitions/rock-corpus/raw/songs.json',)
