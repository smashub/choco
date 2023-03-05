"""
Utilities for extracting chord annotations from notated music and symbolic files
that can be processed and loosslessly converted with music21.

```
>>> c = music21.converter.Converter()
>>> for sc in c.defaultSubconverters():
>>> ...     print(sc)
```
<class 'music21.converter.subConverters.ConverterABC'>
<class 'music21.converter.subConverters.ConverterBraille'>
<class 'music21.converter.subConverters.ConverterCapella'>
<class 'music21.converter.subConverters.ConverterClercqTemperley'>
<class 'music21.converter.subConverters.ConverterHumdrum'>
<class 'music21.converter.subConverters.ConverterIPython'>
<class 'music21.converter.subConverters.ConverterLilypond'>
<class 'music21.converter.subConverters.ConverterMEI'>
<class 'music21.converter.subConverters.ConverterMidi'>
<class 'music21.converter.subConverters.ConverterMuseData'>
<class 'music21.converter.subConverters.ConverterMusicXML'>
<class 'music21.converter.subConverters.ConverterNoteworthy'>
<class 'music21.converter.subConverters.ConverterNoteworthyBinary'>
<class 'music21.converter.subConverters.ConverterRomanText'>
<class 'music21.converter.subConverters.ConverterScala'>
<class 'music21.converter.subConverters.ConverterText'>
<class 'music21.converter.subConverters.ConverterTextLine'>
<class 'music21.converter.subConverters.ConverterTinyNotation'>
<class 'music21.converter.subConverters.ConverterVexflow'>
<class 'music21.converter.subConverters.ConverterVolpiano'>
<class 'music21.converter.subConverters.SubConverter'>

See: https://web.mit.edu/music21/doc/moduleReference/moduleConverter.html

Notes
-----
    - Score expansion may produce inconsistent measure numbers: flatten out.
    - The first measure after the expansion may have implicit rests.
    - Handling expansion errors for the construction of the performed score.

"""
import re
import logging
from functools import partial
from typing import List, Tuple, Union

import numpy as np

import music21
from music21 import converter
from music21.chord import Chord
from music21.harmony import ChordSymbol
from music21.key import Key, KeySignature
from music21.meter import TimeSignature
from music21.metadata import Metadata
from music21.stream import Score, Part, Measure, Stream

from music21.repeat import Expander, ExpanderException


logger = logging.getLogger("choco.music21_parser")


class NoChordsInScoreException(Exception):
    """Raised when no part with chords is found in a score"""
    pass

def extract_chord_part(score: Union[str, Score]):
    """
    Extract the chord part from a given score, which is returned with metadata.

    Parameters
    ----------
    score : str or `music21.Score`
        Path to a score that can be parsed by `music21` or reference to the same
        object that was previously processed by this library.

    Returns
    -------
    chord_part : `music21.Part`
        The part of the score that contains chord annotations.
    metadata : dict
        A dictionary containing the basic metadata that were found in the score.

    """
    if isinstance(score, str):  # parse the single tune first
        score = converter.parse(score)
    # Avoid corpus or score libraries (we just need 1 here)
    if not isinstance(score, Score) and len(score) > 1:
        raise ValueError("This function expects a single tune")
    # Extract the chord-annpotated part, assert one
    score_parts = score.getElementsByClass(Part)
    chord_parts = [part for part in score_parts \
        if len(part.recurse().getElementsByClass(Chord)) > 0]
    assert len(chord_parts) <= 2, "Multiple parts with chord annotations found"

    if len(chord_parts) == 0:
        raise NoChordsInScoreException("No part with chord annotation found!")

    chord_part = chord_parts[0]  # safe with the assert
    meta = score.getElementsByClass(Metadata)[0]
    composers = meta.composers if meta.composers is not None \
        else [meta.composer]  # always prefer the full list of composers

    metadata = {
        "title": meta.title,
        "composers": composers,
        "movement": meta.movementName,
    }

    return chord_part, metadata


def preprocess_stream(stream: Stream, expand=True, rename_measures=True):
    """
    Attempt the expansion of a stream by flattening all repetitions. If this is
    not possible, due to inconsistent repeat and markers in the score, the given
    stream is not expanded, hence returned as it is. Additional data structures
    and utility functions are also returned to manipulate the expansion.

    Parameters
    ----------
    stream : music21.Sream
        A stream object (e.g. a score, a part) in `music21` language.
    rename_measures : bool
        Whether measures should be renamed / recounted to start from 1.

    Returns
    -------
    new_stream : music21.Stream
        A new `music21` stream, which can be the same as the one given, if the
        expansion could not be performed.
    expanded : bool
        Whether the expansion was successful.
    measure_offmap : dict
        The measure offset map resulting from the expansion and the renaming.
    measure_no : fn
        A utility function that allows to properly stringify a measure number,
        depending on whether the expansion has been performed.

    """
    if expand:  # attempt expanding the score only if requested
        try:  # expansion can fail in case of inconsistent repeats
            new_stream = Expander(stream).process()
            expanded = True
            measure_no = lambda m: m.measureNumberWithSuffix()
        except ExpanderException:
            expanded = False
            new_stream = stream
            measure_no = lambda m: m.measureNumber

    measure_offmap = new_stream.measureOffsetMap()
    if rename_measures:  # destroy any repetition info and count from 1
        measure_offmap = {offset: [Measure(m)] for m, offset \
                            in enumerate(measure_offmap.keys(), 1)}

    return new_stream, expanded, measure_offmap, measure_no


def beat_left(measure, beat, beat_map, beat_map_acc):
    """
    Compute the number of beat left in the score from the current measure/beat.

    Parameters
    ----------
    measure : int
        Measure number corresponding to the onset to consider (assumed from 1).
    beat : int
        Beat number corresponding to the onset to consider (assumed from 1).
    beat_map : list or np.array
        A list mapping each measure to the corresponding number of beats therein.
    beat_map_acc : list or np.array
        The global beat count at each measure, trivially corresponding to the
        cumulative view of the former, obtained as `np.cumsum(beat_map)`.
    
    Returns
    -------
    beat_left : int
        No. of beats remaining from the given onset to the end of the piece.

    """
    if measure > len(beat_map):
        raise ValueError(f"Measure {measure} exceeds offset map!")
    measure_beats = beat_map[measure-1]  # no. of beats in given measure
    if beat - 1 > measure_beats:  # extra beat as end of measure
        raise ValueError(f"Measure {measure} has {measure_beats} beats; "
                         f"one cannot start at beat {beat}!")

    beat_duration = beat_map_acc[-1]  # duration as total number of beats
    measure_beats_left = measure_beats - beat + 1  # e.g. 3 for b1 in 4/4
    beat_ellapsed =  beat_map_acc[measure-1] - measure_beats_left

    return beat_duration - beat_ellapsed


def beat_duration(m1, b1, m2, b2, beat_map, beat_map_acc=None):
    """
    Compute the number of beats spanning between the given offsets. For this
    function, order is not relevant (onsets can be placed at any place).

    Parameters
    ----------
    m1 : int
        Measure number of the first onset.
    b1 : int
        Beat number of the first onset.
    m2 : int
        Measure number of the second onset.
    b2 : int
        Beat number of the second onset.
    beat_map : list or np.array
        Number of beaats per measure (location 0 for measure 1).
    beat_map_acc : list or np.array, optional
        Global beat count at each measure, by default None.

    Returns
    -------
    beat_duration : int
        The (non-negative) duration, expressed in bets, between the given 
        offsets.

    """
    if beat_map_acc is None:  # redundant
        beat_map_acc = np.cumsum(beat_map)

    beat_left_mb1 = beat_left(m1, b1, beat_map, beat_map_acc)
    beat_left_mb2 = beat_left(m2, b2, beat_map, beat_map_acc)

    return abs(beat_left_mb2 - beat_left_mb1)


def extract_metre(score_part, measure_offmap):
    """
    Reconstruct the meter of the given score and offset map, the latter of which
    is supposed to start from measure number 1.

    Notes
    -----
    - Why chord part + measure offset map if the latter can be derived from the
    former? Because the offset map may be renamed after the expansion; can be
    improved if hard coding the renaming of measures in the actual part.
    - This function assumes that the measure offset map has no measure 0.
    """
    # XXX The number of measures in the score / part can change when re-encoding the 
    # time signatures with their numerator (e.g. 6/8 assumes 2 beats by default!)
    score_measures = list(score_part.getElementsByClass('Measure'))
    beats_per_measure = np.ones(len(score_measures))  # no. of beats per measure
    # Reconstructing metrical information from the score
    time_signatures, current_ts_str = [], ""  # holds the time signatures
    assert measure_offmap[min(measure_offmap.keys())][0].measureNumber != 0, \
        "Measures starting at number 0, expected first time signature at 1."
    for ts in score_part.recurse().getElementsByClass("TimeSignature").iter():
        if ts.ratioString == current_ts_str: continue  # no need to repeat ts
        current_ts_str = ts.ratioString
        measure_onset = measure_offmap[ts.offset][0].measureNumber
        # beat_onset = 1 # assuming ts.beat == 1 to start at the beginning
        beat_onset = ts.beat  # starting beat expected at 1 in most cases
        beat_count = ts.beatCount # 4 beats for 4/4 (but should use ts.numerator)
        time_signatures.append([current_ts_str, measure_onset, beat_onset, None])
        beats_per_measure[measure_onset-1:] = beat_count # updating beat count

    time_signatures = add_beat_durations(time_signatures, beats_per_measure)
    return time_signatures, beats_per_measure


def add_beat_durations(onset_ann, beats_per_measure, beats_per_measure_acc=None):
    """
    Add beat duration to incomplete annotations, where only the start/onset of
    each observation is known (in terms of starting measure and beat). Here,
    duration is assumed to span between consecutive observations; e.g. if B
    follows A, then A is assumed to last until the beginning of B.
    """
    if beats_per_measure_acc is None:
        beats_per_measure_acc = np.cumsum(beats_per_measure)
    end_annotation = [[None, len(beats_per_measure), beats_per_measure[-1]+1]]

    timed_annotation = [[start[0], start[1], start[2], beat_duration(
        end[1], end[2], start[1], start[2],
        beats_per_measure, beats_per_measure_acc)]
        for end, start in zip(onset_ann[1:] + end_annotation, onset_ann)]

    return timed_annotation


def process_score(score, expand=True, rename_measures=True) -> Tuple:
    """
    Extract metadata and chord annotations from a score that can be processed
    via music21. The timing information of chords is currently given in 
    (measure, offset) and the score is first expanded to flatten any repetition,
    assuming that the notation is consistent.

    Parameters
    ----------
    score : str or `music21.Score`
        The single piece to be processed, either given as a file path reference
        or as a `music21.Score` object that has already been parsed.

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
    # Parse the single tune first
    if isinstance(score, str):
        score = converter.parse(score)
    # Avoid corpus or score libraries
    if not isinstance(score, Score) and len(score) > 1:
        raise ValueError("This function expects a single tune")
    # Extract the chord-annpotated part, assert one
    score_parts = score.getElementsByClass(Part)
    chord_parts = [part for part in score_parts \
        if len(part.recurse().getElementsByClass(Chord)) > 0]
    assert len(chord_parts) <= 2, "Multiple parts with chord annotations found"

    if len(chord_parts) == 0:
        raise NoChordsInScoreException("No part with chord annotation found!")

    chord_part = chord_parts[0]  # safe with the assert
    meta = score.getElementsByClass(Metadata)[0]
    composers = meta.composers if meta.composers is not None \
        else [meta.composer]  # always prefer the full list of composers

    metadata = {
        "title": meta.title,
        "composers": composers,
        "movement": meta.movementName,
    }

    # *** ----------------------------------------------- *** #
    # *** Extract all relevant annotations from the score *** #
    # *** ----------------------------------------------- *** #

    if expand:
        try:  # attempt expanding the score only if requested
            chord_part = Expander(chord_part).process()
            metadata["expanded"] = True
            measure_no = lambda m: m.measureNumberWithSuffix()
        except ExpanderException:
            logger.warn(f"Score {meta.title} has inconsistent repeats")
            measure_no = lambda m: m.measureNumber
            metadata["expanded"] = False

    measure_offmap = chord_part.measureOffsetMap()
    if metadata["expanded"] and rename_measures:
        measure_offmap = {offset: [Measure(m)] for m, offset \
                          in enumerate(measure_offmap.keys())}
    chord_part_duration = chord_part.duration.quarterLength
    metadata["duration"] = chord_part_duration  # XXX can be Fractional!
    metadata["duration_m"] = int(measure_no(  # last measure from offset
        measure_offmap[max(measure_offmap.keys())][-1]))

    time_signatures = chord_part.recurse().getElementsByClass(TimeSignature)
    ts_str = lambda x: f"{x.numerator}/{x.denominator}"
    time_signatures_ann = []

    for time_signature in time_signatures.iter():
        time_signature_str = ts_str(time_signature)
        # Add the time signature if it is not duplicated
        if len(time_signatures_ann) == 0 or \
            time_signatures_ann[-1][0] != time_signature_str:
            # Retrieve the measure name
            time_signatures_ann.append([
                time_signature_str,
                measure_no(measure_offmap[time_signature.offset][0]),
                0,  # this is an offset, and not a beat number (+1)
                chord_part_duration-time_signature.offset,
            ])
            if len(time_signatures_ann) > 1:
                time_signatures_ann[-2][3] = time_signature.offset  # update

    key_signatures = chord_part.recurse().getElementsByClass(KeySignature)
    key_signatures_ann = []

    for key_signature in key_signatures.iter():
        # Key can be either explicit (e.g. G major) or implicit as an actual
        # key signature (e.g. 1 sharp); conversion step required.
        if not isinstance(key_signature, Key):
            key_signature = key_signature.asKey()
        key_signature_str = key_signature.name
        # Add the key signature if it is not duplicated
        if len(key_signatures_ann) == 0 or \
            key_signatures_ann[-1][0] != key_signature_str:
            # Retrieve the measure name
            key_signatures_ann.append([
                key_signature_str,
                measure_no(measure_offmap[key_signature.offset][0]),
                0,  # this is an offset, and not a beat number (+1)
                chord_part_duration-key_signature.offset,
            ])
            if len(key_signatures_ann) > 1:
                key_signatures_ann[-2][3] = key_signature.offset  # update

    chord_ann = []

    for i, measure in enumerate(chord_part.getElementsByClass(Measure)):
        measure_number = i if rename_measures else measure_no(measure)
        measure_duration = measure.duration.quarterLength
        for chord in measure.getElementsByClass(Chord):
            # Check the type of given chord annotation
            if isinstance(chord, ChordSymbol):
                chord_str = chord.figure
            else:  # chord as an ordered list of pitches
                chord_str = ",".join([p.nameWithOctave for p in chord.pitches])
            # Add chord annotation and update duration information
            chord_ann.append([chord_str, measure_number, chord.offset,
                              measure_duration-chord.offset])
            if len(chord_ann) > 1 and chord_ann[-2][1] == measure_number:
                chord_ann[-2][3] = chord.offset  # update previous duration

    return metadata, chord_ann, time_signatures_ann, key_signatures_ann


def process_score_beats(score, expand=True, rename_measures=True) -> Tuple:
    """
    A re-implementation of the `process_score` method where timings are given
    in measures and beats rather than measures and `music21` offsets.

    Parameters
    ----------
    score : str or `music21.Score`
        The single piece to be processed, either given as a file path reference
        or as a `music21.Score` object that has already been parsed.

    Returns
    -------
    metadata : dict
        A dictionary with all the metadata associated to the tune, including
        title, name of composers, etc. It also includes a boolean
        placeholder recording whether the score has been expanded or not.
    chord_ann : list of tuples
        A list of (chord, measure, beat) including all chord annotations.
    time_signature_ann : list of tuples
        A list of (time signature, measure, beat) for all time signatures.
    key_signature_ann : list of tuples
        A list of (key signature, measure, beat) for all key signatures.

    Notes
    -----
    - At the moment, `measure_no` is not used, as the actual measure number is
        always enforced in the annotation; this means that Measure 2B, which
        repeats Measure 2, would still receive the expanded measure number.

    """
    # First, extract the chord part, if present
    chord_part, metadata = extract_chord_part(score)
    chord_part, expanded, measure_offmap, measure_no = \
        preprocess_stream(chord_part, expand, rename_measures)
    metadata["expanded"] = expanded  # keep track of expansion
    if expand and not expanded:
        logger.warn(f"Score {metadata['title']} has inconsistent repeats")

    # Reconstructing temporal / metrical information  ************************ #
    # Here, the chord_part retains the original measures, whereas the returned
    # measure offset map holds a mapping to the expanded measures 
    time_signatures, beats_per_measure = extract_metre(chord_part, measure_offmap)
    beats_per_measure_acc = np.cumsum(beats_per_measure)  # duration ellapsed
    # Updating part-level duration as metrical metadata
    metadata["duration_quarter_beats"] = chord_part.duration.quarterLength
    metadata["duration_beats"] = beats_per_measure_acc[-1]
    metadata["duration_measures"] = len(beats_per_measure)

    # Extracting local keys ************************************************** #
    # Decorating the add_beat_duration to use the same beat information
    add_durations = partial(
        add_beat_durations,
        beats_per_measure=beats_per_measure,
        beats_per_measure_acc=beats_per_measure_acc)

    key_signatures_ann = []
    for key_sig in chord_part.recurse().getElementsByClass(KeySignature).iter():
        # Key can be either explicit (e.g. G major) or implicit as an actual
        # key signature (e.g. 1 sharp); conversion step required.
        if not isinstance(key_sig, Key):
            key_sig = key_sig.asKey()
        key_sig_str = key_sig.name
        # Add the key signature if it is not duplicated
        if len(key_signatures_ann) == 0 or \
            key_signatures_ann[-1][0] != key_sig_str:
            key_measure = measure_offmap[key_sig.offset][0].measureNumber
            key_beat = 1 if key_sig.beat is None or np.isnan(float(key_sig.beat)) \
                else key_sig.beat # assume that key changes happen at the start
            key_signatures_ann.append([key_sig_str, key_measure, key_beat, None])
    key_signatures_ann = add_durations(key_signatures_ann)

    # Extracting chords ****************************************************** #
    chord_ann = []
    for i, measure in enumerate(chord_part.getElementsByClass(Measure), 1):
        # measure_number = i if rename_measures else measure_no(measure)
        # measure_duration = measure.duration.quarterLength
        last_onset, chord_overlap = None, []  # for fixing M21 parsing bugs
        for j, chord in enumerate(measure.getElementsByClass(Chord), 1):
            # Check the type of given chord annotation
            if isinstance(chord, ChordSymbol):
                chord_str = chord.figure
            else:  # chord as an ordered list of pitches
                chord_str = ",".join([p.nameWithOctave for p in chord.pitches])
            # Add chord annotation and update duration information
            assert chord.beat is not None and not np.isnan(float(chord.beat)), \
                f"Chord onset unknown or cannot be parsed as float: {chord.beat}"
            chord_ann.append([chord_str, i, chord.beat, None])
            # Record chord happening at the same time for onset fix
            if chord.beat == last_onset:
                chord_overlap.append(j)
            last_onset = chord.beat

        if len(chord_overlap) > 0:
            # logger.warn(f"Resetting onsets for measure {i}")
            chord_overlap = [chord_overlap[0] - 1] + chord_overlap
            new_duration = beats_per_measure[i] / len(chord_overlap)
            new_onsets = np.arange(1, beats_per_measure[i]+1, new_duration)
            for onset, reset_j in zip(new_onsets, reversed(chord_overlap)):
                chord_ann[-reset_j][2] = onset

    chord_ann = add_durations(chord_ann)
    return metadata, chord_ann, time_signatures, key_signatures_ann


def process_romantext(romantext, **meta_kwargs):
    """
    Extract metadata and chord annotations from a RomanText annotation via
    music21. Analogously to the score version, timing information is currently
    given in (measure, beat offset) and the score is first expanded to flatten
    any repetition, assuming that the notation is consistent. Also, duration is
    expressed as quarter length. Although this provides some syntactic sugar,
    Roman chord figures are returned along with local key information.

    Parameters
    ----------
    romantext : str or `music21.Score`
        The single piece to be processed, either given as a file path reference
        or as a `music21.Score` object that has already been parsed.
    
    Returns
    -------
    ...

    Notes
    -----
    - This implementation is quite different than that of the score; this
        is because the converter in m21 does not integrate certain info in
        the score (e.g. local keys/modulations are only in the numerals).

    """
    score = converter.parse(romantext, format='romanText') \
        if isinstance(romantext, str) else romantext
    annotator, ann_tools = extract_romantext_annotator(romantext, **meta_kwargs)
    # Extract the basic metadata that should be provided in the annotation
    chord_part, _ = extract_chord_part(score)
    chord_part, expanded, measure_offmap, measure_no = \
        preprocess_stream(chord_part, expand=True, rename_measures=True)
    time_signatures, beats_per_measure = extract_metre(
        chord_part, measure_offmap)
    meta = score.getElementsByClass(Metadata)[0]
    metadata = {
        "title": meta.title,
        "composers": meta.composers,
        "duration_beats": sum(beats_per_measure),
        "duration_quarter_beats": chord_part.duration.quarterLength,
        "duration_measures": len(beats_per_measure),
        "annotator": annotator if annotator is not None else "",
        "annotation_tools": ann_tools,
    }

    numerals = [x for x in chord_part.recurse().getElementsByClass('RomanNumeral')]
    chord_ann, key_ann = [], []
    for roman_numeral in numerals:
        # Extracting timing information and processing the implied local key
        measure = roman_numeral.getContextByClass('Measure')
        measure_number = measure_offmap[measure.offset][0].measureNumber
        # measure = measure_fn(measure)  # make sure we avoid 0-measures
        offset = roman_numeral.beat
        duration = roman_numeral.quarterLength
        lkey = roman_numeral.key.name.replace('-', 'b')

        chord_ann.append([
            measure_number, offset, duration,
            lkey + ":" + roman_numeral.figure,
        ])

        if len(key_ann) > 0 and key_ann[-1][-1] == lkey:
            key_ann[-1][2] += duration  # update duration
        else:  # an actual modulation: local key change
            key_ann.append([measure_number, offset, duration, lkey])

    return metadata, chord_ann, time_signatures, key_ann


def extract_romantext_annotator(romantext_path, clean_str=False,
    annotation_tool_map:dict={}, annotation_ignore:list=[]):
    """
    Extract annotation information from the RomanText file and attempts
    separating annotator names and annotation tools in the former string.

    Parameters
    ----------
    romantext_path : str
        Path to the text analysis in RomanText to read.
    clean_str : bool
        Whether the annotation string should be processed for disentanbglement.
    
    Returns
    -------
    annotator_str : str
        The annotator string, containing the name only if `clean_str`.
    annotation_tool : str
        Identifier or name of the annotation tool, if specified and recognised.

    """
    with open(romantext_path, "r") as rt_text:
        analysis = "".join(rt_text.readlines())
    # Find the annotator details, all merged in the same line
    annotation_tool = ""  # assumed not available, yet
    annotator_str = re.search("Analyst:(.+)", analysis)
    if annotator_str is not None:  # strip the annotator
        annotator_str = annotator_str.group(1).strip()
    if annotator_str is None or not clean_str:
        return annotator_str, annotation_tool

    for tool_desc, tool_name in annotation_tool_map.items():
        if tool_desc in annotator_str:
            annotation_tool = tool_name
            annotator_str = annotator_str.replace(tool_desc, "")

    for ignore_str in annotation_ignore:
        if ignore_str in annotator_str:  # drop everything after ignore_str
            annotator_str = annotator_str[:annotator_str.find(ignore_str)]

    annotator_str = annotator_str.replace(" and ", ", ")
    return annotator_str, annotation_tool
