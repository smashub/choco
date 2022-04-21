"""
Support for parsing JSON data to extract beats, chords, segments, and metadata
information and create a JAMS annotations for the corresponding namespaces.

Notes:
    - Documentation of some functions is missing (TODO).
"""
import os
import json
import logging

import jams

from choco.utils import flatten

logger = logging.getLogger("parsers.json_parser")


def extract_segments(segment_names, beat_times_per_section, duration):
    """
    Extracts segment annotations based on beat times: the beginning of new
    beat is used to define the end of the former beat. For the last beat in
    the annotations, the track duration is considered as the end.
    """
    
    segment_ann = jams.Annotation("segment_open")
    
    section_beats = [beats[0] for beats in beat_times_per_section] + [float(duration)]
    section_intervals = zip(section_beats[:-1], section_beats[1:])  # time intervals

    for segment_name, (start_beat, end_beat) in zip(segment_names, section_intervals):
        segment_ann.append(
            time=start_beat, duration=end_beat-start_beat,
            value=segment_name, confidence=1.0)

    return segment_ann


def extract_beats(beat_times_per_section, bpb):
    """
    Extracts beats annotations based on the time signature.
    """

    beat_ann = jams.Annotation("beat")
 
    for beat_no, beat_time in enumerate(flatten(beat_times_per_section)):
        beat_ann.append(time=beat_time, duration=0.0,
            value=beat_no%bpb + 1, confidence=1.0)

    return beat_ann


def preprocess_key(key_str):
    """
    Simple utility to make sure that the chord symbol is consistent.
    """
    if "min" in key_str and "minor" not in key_str:
        key_str = key_str.replace("min", "minor")
    elif "maj" in key_str and "major" not in key_str:
        key_str = key_str.replace("maj", "major")

    return key_str


def extract_chords(chords_per_segment, beat_times_per_segment, duration, bpb):
    """
    Pre-processing and adding chords based on beats and time signature.
    """

    chord_ann = jams.Annotation("chord")

    # Retrieving section endings to express the end of the last beat in each section
    section_beats = [beats[0] for beats in beat_times_per_segment] + [float(duration)]
    section_end_times = section_beats[1:]  # the start of the first section is not needed

    assert len(section_end_times) == len(chords_per_segment) == len(beat_times_per_segment), \
        "A mismatch was found in the number of sections implied by the annotation data."

    for seg_chords, seg_beat_times, seg_end_time in \
        zip(chords_per_segment, beat_times_per_segment, section_end_times):
        # Isolating chords for each measure
        chord_str = '|'.join(seg_chords)
        chord_str = chord_str.replace('|||', '|')
        chord_str = chord_str.replace(' |', '|')
        chord_per_measure = chord_str.split('|')[1:-1]

        # Checking the consistency of chord-beats annotations
        implied_measures = len(seg_beat_times) / bpb
        expected_measures = len(chord_per_measure)
        if implied_measures != expected_measures:
            # The number of beats do not align with chord annotations
            logger.error("Found {} measures from chords and {} from beats"
                .format(expected_measures, implied_measures))
            # Attempting N-padding for the missing measures, if possible
            if implied_measures < expected_measures:                
                raise ValueError("The chord annotation cannot be resolved. "
                    "Please, correct the annotation and try again.")

        # Align chords to starting and ending beats for each expected measure
        for measure, chords in enumerate(chord_per_measure):

            starting_beat = measure * bpb
            measure_beats = seg_beat_times[starting_beat:starting_beat+bpb]
            # log.info("measure * bpb {}".format(measure*bpb))
            # log.info("len(beat_times) {}".format(len(seg_beat_times)))
            measure_end_time = seg_beat_times[(measure + 1) * bpb] \
                if (measure + 1) * bpb < len(seg_beat_times) else seg_end_time
            measure_timing = measure_beats + [measure_end_time]

            splitted_chords = chords.split()
            beats_per_chord = bpb / len(splitted_chords)
            assert beats_per_chord.is_integer(), \
                "Illegal number of chords per measure!"
            beats_per_chord = int(beats_per_chord)

            for chord_no, chord_label in enumerate(splitted_chords):

                measure_offset = chord_no *  beats_per_chord
                chord_start = measure_timing[measure_offset]
                chord_end = measure_timing[measure_offset+beats_per_chord]
                
                chord_ann.append(
                    time=chord_start, duration=chord_end-chord_start,
                    value=chord_label, confidence=1.0)
        
        if implied_measures > expected_measures:
            logger.warn("Chord sequence right-padded for {} beats!"
                .format(int((implied_measures - expected_measures)*bpb)))
            # The ending time of the last annotation will be the start of this
            padding_start = chord_ann.data[-1].time
            padding_duration = seg_end_time - padding_start
            chord_ann.append(
                time=chord_ann.data[-1].time,
                duration=padding_duration,
                value="N", confidence=1.0)

    return chord_ann


def extract_annotations_from_json(json_path):
    """
    Extract beat, segment, and chord annotations from a JSON file formatted
    according to the conventions adopted in JAAH. This format is not desirable,
    as it entangles multiple annotation types in a nested organisation; hence,
    to be reused, all these annotations need to be interpreted and separated.

    Parameters
    ----------
    json_path : str
        Path to the JSON file containing the audio annotations, as expected.a

    Returns
    -------
    jam : jams.JAMS
        A JAMS file where all annotations have been interpreted and separated.

    """

    with open(json_path, 'rb') as infile:
        json_raw = json.loads(infile.read())

    jam = jams.JAMS()

    metre = json_raw['metre']
    duration = float(json_raw['duration'])
    bpb = int(metre.split('/')[0])  # beats per bar

    # Populating the metadata of the JAMS file
    jam.file_metadata.title = json_raw['title']
    jam.file_metadata.artist = json_raw['artist']
    jam.file_metadata.duration = duration
    jam.file_metadata.identifiers = {"MB": json_raw['mbid']}
    jam.file_metadata.jams_version = jams.__version__
    jam.sandbox.tuning = json_raw['tuning']
    jam.sandbox.metre = metre

    if "key" in json_raw['sandbox']:
        key = json_raw['sandbox']['key']
        key = key[0] if isinstance(key, list) else key
        key = preprocess_key(key_str=key)
        # Adding key information as a global annotation
        annotation = jams.Annotation(namespace="key_mode")
        annotation.append(time=0, duration=duration, value=key)
        jam.annotations.append(annotation)

    segment_names  = []
    beat_times_per_section = []
    chords_per_section = []

    for segment in json_raw['parts']:
        segment_names.append(segment['name'])
        beat_times_per_section.append(segment['beats'])
        chords_per_section.append(segment['chords'])
    # Extract the annotations for each namespace from the json
    # and append them to the JAMS file.
    jam.annotations.append(extract_segments(
        segment_names, beat_times_per_section, duration))
    jam.annotations.append(extract_beats(
        beat_times_per_section, bpb))
    jam.annotations.append(extract_chords(
        chords_per_section, beat_times_per_section, duration, bpb))

    return jam
