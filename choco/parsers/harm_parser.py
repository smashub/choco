"""
Parsing utilities to read and process harmonic annotations in other textual
formats, such as the one proposed by Trevor de Clercq and David Temperley, and
the format introduced by Mark Granroth-Wilding for the JazzCorpus.

"""
import re
import os

import numpy as np

RC_KEY_REG = r"\[\w[b|\#]?\]"
RC_TSG_REG = r"\[\d+\/\d+\]"  # FIXME


def process_harm_expanded(harm_annotation):
    """
    Parse an expanded harmonic annotation, as defined by Trevor and David, to
    extract chord, time signature, and local key annotations together with their
    timing information: [measure, measure offset, duration, value]. This is done
    as the timed-chord annotations released by the authors are temporally not
    consistent due to potential bugs in the `expand6` function.

    Parameters
    ----------
    harm_annotation : str
        String representation of the harmonic annotation or file path.
    
    Returns
    -------
    chords : list of lists
        The chord annotations, where local keys and roman numerals are merged .
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
    for measure_no, measure in enumerate(measures):
        measure = measure.strip()  # remove leading-tailing spaces
        if len(measure) == 0:  # measure has no new elements to process
            chords[-1][-2] += 1; continue  # extend duration of previous chord
        mspan = 1/len([c for c in measure.split() if c!="["])

        measure_offset = 0
        for annotation in measure.split():
            if "[" in annotation:  # key or time sig
                key = re.match(RC_KEY_REG, annotation)
                if key is not None:
                    current_key = key.group(0)[1:-1]
                    max_dur = len(measures) - (measure_no + mspan)
                    keys.append([measure_no, measure_offset, max_dur, current_key])
            else:  # at this stage, either a roman numeral or a dot is expected
                chord = chords[-1][-1] if annotation=="." \
                    else f"{current_key}:{annotation}" 
                chords.append([measure_no, mspan, mspan, chord])
                measure_offset += mspan  # chords advance time

    if len(keys) > 1:  # duration of local keys can be adjusted
        for i, key in enumerate(keys[:-1]):
            start_i = key[0] + key[1]
            start_j = keys[i+1][0] + keys[i+1][1]
            key[-2] = start_j - start_i
    
    return chords, None, keys


def process_multiline_annotation(annotation):
    """
    Parse a multiline textual annotation as defined by Mark Granroth-Wilding.

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

    return hartelike_ann, romanlike_ann, key_ann
