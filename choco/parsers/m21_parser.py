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
import logging
from typing import List, Tuple

from music21 import converter
from music21.chord import Chord
from music21.key import KeySignature
from music21.meter import TimeSignature
from music21.metadata import Metadata
from music21.stream import Score, Part, Measure

from music21.repeat import Expander, ExpanderException

logger = logging.getLogger("choco.music21_parser")


def process_score(score, expand=True) -> Tuple:
    """
    Extract metadata and chord annotations from a score that can be processed
    via music21. The timing information of chords is currently given in 
    (measure, offset) and the score is first expanded to flatten any repetition.

    Parameters
    ----------
    score : str or `music21.Score`
        The single piece to be processed, either given as a file path reference
        or as a `music21.Score` object that has already been parsed.

    Returns
    -------
    metadata : dict
        A dictionary with all the metadata associated to the tune, including
        title, name of composer, etc. (if available).
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
        logger.warn("No part with chord annotation found, returning none")
    
    chord_part = chord_parts[0]  # safe with the assert
    meta = score.getElementsByClass(Metadata)[0]

    metadata = {
        "title": meta.title,
        "composer": meta.composers,
    }

    # *** ----------------------------------------------- *** #
    # *** XXX From this point on it is the same as in ABC *** #
    # *** ... with the exception of the exander handiling *** #
    # *** ----------------------------------------------- *** #

    if expand:  
        try:  # attempt expanding the score only if requested
            chord_part = Expander(chord_part).process()
            metadata["expansion"] = True
            measure_no = lambda m: m.measureNumberWithSuffix()
        except ExpanderException:
            logger.warn(f"Score {meta.title} has inconsistent repeats")
            measure_no = lambda m: m.measureNumber
            metadata["expansion"] = False            

    measure_offmap = chord_part.measureOffsetMap()

    time_signatures = chord_part.recurse().getElementsByClass(TimeSignature)
    ts_str = lambda x: f"{x.numerator}/{x.denominator}"
    time_signatures_ann = []

    for time_signature in time_signatures.iter():
        time_signature_str = ts_str(time_signature)
        # Add the time signature if it is not duplicated
        if len(time_signatures_ann) == 0 or \
            time_signatures_ann[-1][0] != time_signature_str:
            # Retrieve the measure name
            time_signatures_ann.append((
                time_signature_str,
                measure_no(measure_offmap[time_signature.offset][0]),
                0,
            ))

    key_signatures = chord_part.recurse().getElementsByClass(KeySignature)
    key_signatures_ann = []

    for key_signature in key_signatures.iter():
        key_signature_str = key_signature.name
        # Add the key signature if it is not duplicated
        if len(key_signatures_ann) == 0 or \
            key_signatures_ann[-1][0] != key_signature_str:
            # Retrieve the measure name
            key_signatures_ann.append((
                key_signature_str,
                measure_no(measure_offmap[key_signature.offset][0]),
                0,
            ))

    chord_ann = []

    for measure in chord_part.getElementsByClass(Measure):
        measure_number = measure_no(measure)
        for chord in measure.getElementsByClass(Chord):
            chord_ann.append((chord.figure, measure_number, chord.offset))
    
    return metadata, chord_ann, time_signatures_ann, key_signatures_ann
