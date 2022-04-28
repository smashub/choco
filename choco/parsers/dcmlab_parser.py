"""
Utilities for parsing (extended) harmonic annotations in the DCMLab format.

See also
--------
https://github.com/DCMLab/mozart_piano_sonatas
https://github.com/DCMLab/standards

"""
from functools import partial

import pandas as pd

import music21


def process_dcmlab_record(annotation_df: pd.DataFrame):
    """
    Process a DCM harmonic annotation given as a pandas dataframe and extract
    a list of timed-observations per chords, local keys, and time signatures.

    Parameters
    ----------
    annotation_df: pd.DataFrame
        The dataframe wrapping the DCM annotation of a certain score.

    Returns
    -------
    chords_roman : list of lists
        The roman numeral chord annotations, where each observation follows the
        same structure of ChoCo score parsers [measure, beat, duration, value]. 
    chords_numeral : list of lists
        The (plain) numeral chord annotations, a simplification of the former.
    time_signatures : list of lists
        Time signatures annotations, following the same temporal granularity
        of chord annotation (for the sake of alignment).
    local_keys : list of lists
        Local key annotations, following the same temporal granularity
        of chord annotation (for the sake of alignment).

    """
    timing_info, local_keys = [], []

    for i, annotation_record in annotation_df.iterrows():
        # Reconstruct local key from the dataframe annotation
        lkey_relative = annotation_record["localkey"]
        gkey_absolute = annotation_record["globalkey"]
        gkey_scale = music21.scale.MinorScale \
            if annotation_record["globalkey_is_minor"] \
                else music21.scale.MajorScale
        gkey_scale = gkey_scale(gkey_absolute)
        # Resolving the local relative key through music21
        lkey_roman = music21.roman.RomanNumeral(lkey_relative, gkey_scale)
        lkey_absolute = lkey_roman.root().step
        if annotation_record["localkey_is_minor"]:
            lkey_absolute = lkey_absolute + "min"
        # Infer beats per measure (bpm) from time signature
        ts = music21.meter.TimeSignature(annotation_record["timesig"])
        bpm = ts.beatCount

        beat = annotation_record["beat"]
        if "." in beat:  # complex beats need to be decomposed
            beat_int, beat_dec = beat.split(".")
            beat_dec_n, beat_dec_d = beat_dec.split("/")
            beat = int(beat_int) + int(beat_dec_n)/int(beat_dec_d)
        beat = float(beat)  # and in the end make sure we have a float
        # Save timing information: expanded/unrolled measure + beat
        timing_record = [annotation_record["playthrough"], beat, bpm-beat+1]
        if len(timing_info) > 1 and timing_info[-1][0] == timing_record[0]:
            timing_info[-1][2] = timing_record[1] - timing_info[-1][1]
        
        timing_info.append(timing_record)
        local_keys.append([lkey_absolute])

    chords_roman = [[f"{key[0]}:{chord}"] for key, chord \
        in zip(local_keys, list(annotation_df["chord"]))]
    chords_numeral = [[f"{key[0]}:{chord}"] for key, chord \
        in zip(local_keys, list(annotation_df["numeral"]))]
    time_signatures = [[ts] for ts in list(annotation_df["timesig"])]

    lstack = lambda x,y: [x_i + x_j for x_i, x_j in zip(x,y)]
    stack_time = partial(lstack, x=timing_info)

    local_keys = stack_time(y=local_keys)
    chords_roman = stack_time(y=chords_roman)
    chords_numeral = stack_time(y=chords_numeral)
    time_signatures = stack_time(y=time_signatures)

    return chords_roman, chords_numeral, time_signatures, local_keys
