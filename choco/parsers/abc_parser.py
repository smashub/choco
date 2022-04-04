'''
Utilities for pasing chords sequences from ABC files.
'''
import logging
from typing import List, Tuple

from music21 import converter
from music21.chord import Chord
from music21.stream import Score
from music21.repeat import Expander
from music21.key import KeySignature
from music21.meter import TimeSignature

logger = logging.getLogger("choco.abc_parser")


def process_abc_library(abc_library: str) -> List:
    """
    Process a list of tunes stored in an ABC library file, following the
    conventions of the notation, to retrieve metadata and chord annotations.
    Therefore, melodies are ignored and only ABC chords are retained. See
    `process_abc_tune()` for more details.

    Parameters
    ----------
    abc_library : str
        Path to the ABC file containing a library of ABC tunes uniquely
        identified with their 'X' number.
    
    Returns
    -------
    processed_scores : list
        A list containing the metadata and the chord annotation for each tune
        found in the given ABC library file.
    """
    # Step 1: Read the ABC tunes as music21 scores
    scores = converter.parse(abc_library)
    processed_scores = []
    for score in scores:
        logger.info(f"Processing: {score.metadata.title}")
        score_data = process_abc_tune(score)
        if len(score_data[1]) > 0:
            processed_scores.append({
                "metadata": score_data[0],
                "time_signatures": score_data[2],
                "key_signatures": score_data[3],
                'chords': score_data[1],
            })
    return processed_scores


def process_abc_tune(abc_tune) -> Tuple:
    """
    Extract metadata and chord annotations from an ABC tune via music21. The
    timing information of chords is currently given in (measure, offset) and
    the score is first expanded to flatten any repetition.

    Parameters
    ----------
    abc_tune : str or `music21.Score`
        The ABC tune to be processed either given as a file path reference or
        as a `music21.Score` object that has already been parsed.

    Returns
    -------
    metadata : dict
        A dictionary with all the metadata associated to the tune, including
        title, name of composer (if available).
    chord_ann : list of tuples
        A list of (ABCChord, measure, offset) including all chord annotations.
    time_signature_ann : list of tuples
        A list of (time signature, measure, offset=0) for all time signatures.
    key_signature_ann : list of tuples
        A list of (key signature, measure, offset=0) for all key signatures.
    """
    # Parse the single tune first
    if isinstance(abc_tune, str):
        abc_tune = converter.parse(abc_tune)
    # Avoid ABC tune libraries and assert single-part scores
    if not isinstance(abc_tune, Score) and len(abc_tune) > 1:
        raise ValueError("This function expects a single tune")
    assert len(abc_tune) == 2, "Single-part score is assumed"

    meta, part = abc_tune
    metadata = {
        "title": meta.title,
        "composer": meta.composer,                                                                # G minor
    }
    # From original score to performed score
    part_ext = Expander(part).process()
    measure_offmap = part_ext.measureOffsetMap()

    time_signatures = part_ext.recurse().getElementsByClass(TimeSignature)
    ts_str = lambda x: f"{x.numerator}/{x.denominator}"
    time_signatures_ann = []

    for time_signature in time_signatures.iter():
        time_signature_str = ts_str(time_signature)
        # Add the time signature if it is not duplicated
        if len(time_signatures_ann) == 0 or \
            time_signatures_ann[-1][0] != time_signature_str:
            # Retrieve the measure name
            time_signatures_ann.append(
                (time_signature_str,
                measure_offmap[time_signature.offset]\
                    [0].measureNumberWithSuffix(), 0))

    key_signatures = part_ext.recurse().getElementsByClass(KeySignature)
    key_signatures_ann = []

    for key_signature in key_signatures.iter():
        key_signature_str = key_signature.name
        # Add the key signature if it is not duplicated
        if len(key_signatures_ann) == 0 or \
            key_signatures_ann[-1][0] != key_signature_str:
            # Retrieve the measure name
            key_signatures_ann.append(
                (key_signature_str,
                measure_offmap[key_signature.offset]\
                    [0].measureNumberWithSuffix(), 0))

    chord_ann = []
    for measure_ext in part_ext:
        measure_number = measure_ext.measureNumberWithSuffix()
        for chord in measure_ext.getElementsByClass(Chord):
            chord_ann.append((chord.figure, measure_number, chord.offset))
    
    return metadata, chord_ann, time_signatures_ann, key_signatures_ann
