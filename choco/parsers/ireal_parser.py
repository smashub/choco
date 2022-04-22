"""
Utilities to parse iReal Pro chart data and extract chord annotations.

"""
import re
import urllib
import logging

import numpy as np
from pyRealParser import Tune

logger = logging.getLogger("choco.ireal_parser")


class ChoCoTune(Tune):

    @classmethod
    def _get_measures(cls, chord_string):
        """
        Splits a chord string into a list of measures, where empty measures are
        discarded. Cleans up the chord string, removes annotations, and handles
        repeats & codas as well.

        Parameters
        ----------
        chord_string: str
            A chord string

        Returns
        -------
        measures : list
            A list of measures, with the contents of every measure as a string

        """
        chord_string = cls._cleanup_chord_string(chord_string)
        chord_string = cls._remove_annotations(chord_string)
        chord_string = cls._fill_long_repeats(chord_string)
        chord_string = cls._fill_codas(chord_string)
        measures = re.split(r'\||LZ|K|Z|{|}|\[|\]', chord_string)
        measures = [m.strip() for m in measures if m.strip() != '']
        measures = cls._fill_single_double_repeats(measures)
        measures = cls._fill_slashes(measures)

        return measures

    @staticmethod
    def parse_ireal_url(url):
        """
        Parse iReal charts (URL) into human- and machine-readable formats.

        Parameters
        ----------
        url : str
            An url-like string containing one or more tunes.

        Returns
        -------
        tunes : list
            A list of ChoCoTune objects resulting from the parsing.
        pname : str
            The name of the playlist if the given charts are bundled.

        """
        url = urllib.parse.unquote(url)
        match = re.match(r'irealb://([^"]+)', url)
        if match is None:
            raise RuntimeError('Provided string is not a valid iReal url!')
        # Split the url into individual charts along the '===' separator
        charts = re.split("===", match.group(1))
        charts = [c for c in charts if c != '']

        tunes, pname = [], None
        for i, chart in enumerate(charts):
            if i == len(charts)-1 and "=" not in chart:
                pname = chart.strip(); break  # fermete
            try:  # attempt parsing of the individual tune
                tune = ChoCoTune(chart)
                tunes.append(tune)
                logger.info(f"Parsed tune {i}: {tune.title}")
            except Exception as err:
                logger.warn(f"Cannot import tune {i}: {err}")

        return tunes, pname


def extract_metadata_from_tune(tune: ChoCoTune, tune_id=None):
    """
    Extract metadata information from an iReal tune, an object resulting from
    parsing an original chart with the `parse_ireal_url` function.

    Parameters
    ----------
    tune : ChoCoTune
        The ChoCoTune instance from which metadata needs to be extracted.
    tune_id : str
        An optional string that can be used for indexing the tune in the dict.
    
    Returns
    -------
    metadata : dict
        A dictionary providing the metadata extracted from the given tune.

    """
    metadata = {
        "id": tune_id,
        "title": tune.title,
        "artists": tune.composer,
        "genre": tune.style,
        "tempo": tune.bpm,
        "time_signature": tune.time_signature,
    }

    return metadata


def extract_annotations_from_tune(tune: ChoCoTune):
    """
    Extract chord and key annotations from a given tune.

    Parameters
    ----------
    tune : ChoCoTune
        The ChoCoTune instance from which music annotations will be extracted.

    Returns
    -------
    chords : list of lists
        A list of chord annotations as tuples: (measure, beat, duration, chord) 
    keys : list of lists
        A list of chord annotations as tuples: (measure, beat, duration, key)

    """
    measures = tune.measures_as_strings
    measure_beats = tune.time_signature[0]
    duration = measure_beats*len(measures)

    chords = []  # iterating and timing chords
    for m, measure in enumerate(measures):
        measure_chords = measure.split()
        chord_dur = measure_beats / len(measure_chords)
        # Creating equal onsets depending on within-measure chords and beats
        onsets = np.cumsum([0]+[d for d in (len(measure_chords)-1)*[chord_dur]])
        chords += [[m, o, chord_dur, c] for o, c in zip(onsets, measure_chords)]
    # Encapsulating key information as a single annotation
    assert len(tune.key.split()) == 1, "Single key assumed for iReal tunes"
    keys = [[0, 0, duration, tune.key]]

    return chords, keys


def process_ireal_annotations(annotation_data):
    """
    Reads and processes raw ireal charts to re-organise the annotations in a
    separate dictionary containing both the metadata and the chord progressions.

    Parameters
    ----------
    annotation_data : str
        A string representing the iReal URL containing chord charts.

    Returns
    -------
    A list of dictionaries -- one for each tune that was found -- is returned.

    """

    raise NotImplementedError
