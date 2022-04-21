"""
Utilities to parse iReal Pro chart data and extract chord annotations.

"""
import re
import urllib
import logging

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
        Parses iReal urls into human- and machine-readable formats.

        Parameters
        ----------
        url : str
            An url-like string containing one or more tunes.

        Returns
        -------
        tunes : list
            A list of ChoCoTune objects resulting from the parsing.

        """
        url = urllib.parse.unquote(url)
        match = re.match(r'irealb://([^"]+)', url)
        if match is None:
            raise RuntimeError('Provided string is not a valid iReal url!')
        # split url into individual songs along ===
        songs = re.split("===", match.group(1))
        tunes = []
        for i, song in enumerate(songs):
            if song != '':
                try:
                    tune = ChoCoTune(song)
                    tunes.append(tune)
                    logger.info(f"Parsed tune {i}: {tune.title}")
                except Exception as err:
                    logger.warn(f"Cannot import {i} ({tune.title}): {err}")
        
        return tunes


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
    def serialise_ireal_tune(tune):
        chords_pm = tune.measures_as_strings
        chord_seq = " ".join(chords_pm)  # FIXME avoid merged in-measure chords
        # chords = do_something-with_chords(my_tune)  # TODO post-process
        return {
            "title": tune.title,
            "artists": tune.composer,
            "style": tune.style,
            "key": tune.key,
            "transpose": tune.transpose,
            "style": tune.comp_style,
            "tempo": tune.bpm,
            "repeats": tune.repeats,
            "time_signature": tune.time_signature,
            'chords': chord_seq
        }

    parsed_charts = []
    tunes = ChoCoTune.parse_ireal_url(annotation_data)

    if len(tunes) > 0:
        for tune in tunes:
            tune_dict = serialise_ireal_tune(tune)
            parsed_charts.append(tune_dict)

    return parsed_charts
