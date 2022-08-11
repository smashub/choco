"""
The Jamifier creates JAMS files out of your dataset, as long as the way content
is organised in files/folders reflect one of our archetypes.

Notes:
    - Work in progress, after the lesson learned from the other collections.
    - The Jamifier should be in the `/choco/choco` as main entry point.
"""

import os
import logging

import jams
import music21
import pandas as pd

from m21_parser import process_romantext, process_score
from dcmlab_parser import process_dcmlab_record
from jams_score import append_listed_annotation
from jams_utils import register_jams_meta

logger = logging.getLogger("choco.parsers.jamifier")

# **************************************************************************** #
# Format jamifier
# **************************************************************************** #

def jamify_romantext(romantext, **meta_ext):
    """
    Parameters
    ----------
    romantext : str or music21.stream.Score
        The RomanText annotation given either as a file path or music21 score.
    
    Returns
    -------
    metadata : dict
        A dictionary with the metadata that were found in the score.
    jam : jams.JAMS
        The JAMS object encapsulating the given RomanText annotation.

    """
    metadata, chords, time_signatures, local_keys = process_romantext(
        romantext, **meta_ext)

    jam = jams.JAMS()
    jam = append_listed_annotation(
        jam, "chord_m21", chords, offset_type="beat")
    jam = append_listed_annotation(
        jam, "key_mode", local_keys, offset_type="beat")

    register_jams_meta(
        jam, jam_type="score",
        title=metadata["title"],
        composers=metadata["composers"],
        duration=metadata["duration_m"],
        # expanded=None,  # still unclear TODO
    )

    return metadata, jam


def jamify_dcmlab(dcmlab_df: pd.DataFrame):
    """
    Parameters
    ----------
    dcmlab_df : pd.DataFrame
        A pandas dataframe encoding a DCMLab harmonic annotation.

    Returns
    -------
    metadata : dict
        A dictionary with the metadata that were found in the score.
    jam : jams.JAMS
        The JAMS object encapsulating the given RomanText annotation.

    Notes:
        - Metadata extraction not yet implemented.

    """
    chords_roman, chords_numeral, time_signatures, local_keys = \
        process_dcmlab_record(dcmlab_df)

    jam = jams.JAMS()
    jam = append_listed_annotation(jam, "chord_roman", chords_roman)
    jam = append_listed_annotation(jam, "chord_roman", chords_numeral)
    jam = append_listed_annotation(jam, "key_mode", local_keys)

    return None, jam


def jamify_m21(score: music21.stream.Score):
    """
    Parameters
    ----------
    score : music21.stream.Score
        A `music21` score from which annotations will be extracted.

    Returns
    -------
    metadata : dict
        A dictionary with the metadata that were found in the score.
    jam : jams.JAMS
        The JAMS object encapsulating the given score annotation.

    """
    meta, chords, time_signatures, keys = process_score(score)

    jam = jams.JAMS()
    jam = append_listed_annotation(
        jam, "chord_m21", chords, offset_type="beat", reversed=True)
    jam = append_listed_annotation(
        jam, "key_mode", keys, offset_type="beat", reversed=True)

    register_jams_meta(
        jam, jam_type="score",
        title=meta["title"],
        composers=meta["composers"],
        duration=meta["duration_m"],
        expanded=meta["expanded"],
    )

    return meta, jam
