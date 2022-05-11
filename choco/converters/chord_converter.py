"""
Converter for all types of chord annotations into Harte Notation.
"""
import logging
import os
import sys

from converter import Converter
from lark.exceptions import UnexpectedInput
from lark_converter import Parser
from lark_to_harte import Encoder

from polychord_converter import convert_polychord
from prettify_harte import prettify_harte
from roman_converter import convert_roman

sys.path.append(os.path.dirname(os.getcwd()))

ANNOTATION_SUPPORTED = {
    'wikifonia': 'leadsheet_music21',
    'ireal-pro': 'leadsheet_ireal',
    'weimar': 'leadsheet_weimar',
    'nottingham': 'abc_music21',
    'when-in-rome': 'roman_converter',
    'rock-corpus': 'roman_converter',
    'jazz-corpus': 'leadsheet_jazz_corpus',
    'band-in-a-box': 'prettify-harte',
}


class ChordConverter:
    """
    Implements a class for converting chords from different notations to
    the Harte Notation.
    """

    def __init__(self, dataset_name: str) -> None:
        """
        Initialises the ChordConverter class and sets the parameters that will
        be needed in the methods that the class implements.
        Parameters
        ----------
        dataset_name : str
            The name of the dataset that has to be converted. The datasets
            supported are listed in the ANNOTATION_SUPPORTED dictionary.
        """
        self.dataset_name = dataset_name
        if dataset_name in ANNOTATION_SUPPORTED.keys():
            self.annotation_type = ANNOTATION_SUPPORTED[dataset_name]
            if self.annotation_type in ['leadsheet_music21', 'leadsheet_ireal', 'leadsheet_weimar', 'abc_music21',
                                        'leadsheet_jazz_corpus']:
                self.lark_converter = Converter(Parser(self.annotation_type), Encoder())
        else:
            raise ValueError('The annotation type is not supported.\n'
                             f'The supported annotation types are: {", ".join(ANNOTATION_SUPPORTED.keys())}')
        self.chord_metadata = []

    def convert_chords(self, chord: str) -> str:
        """
        Implements a method for converting chords into the Harte Notation
        from different annotation formats.
        Parameters
        ----------
        chord : str
            The chord to be converted.
        """
        converted_chord = chord
        # LARK_CONVERTER
        if self.annotation_type in ['leadsheet_music21', 'leadsheet_ireal', 'leadsheet_weimar', 'abc_music21',
                                    'leadsheet_jazz_corpus']:
            try:
                converted_chord = self.lark_converter.convert(chord)
            except UnexpectedInput as ui:
                try:
                    converted_chord = convert_polychord(chord)
                except ValueError:
                    logging.error(f'Impossible to convert {chord} because the exception {ui} occurred.\n'
                                  'Appending to the generated Jams file the original chord.')
        # ROMAN_CONVERTER
        elif self.annotation_type == 'roman_converter':
            try:
                converted_chord = convert_roman(chord)
            except ValueError:
                logging.error(f'Impossible to convert {chord}.\n'
                              'Appending to the generated Jams file the original chord.')
        # PRETTIFY HARTE
        elif self.annotation_type == 'prettify_harte':
            converted_chord = (chord)

        return prettify_harte(converted_chord)

    def convert_keys(self, key: str) -> str:
        """
        Implements a method for converting key annotations into a
        Harte-supported key information, starting from different
        annotation formats.
        Parameters
        ----------
        key : str
            The key to be converted.
        """
        # IREAL-PRO
        if self.dataset_name in ['ireal-pro']:
            if '-' in key:
                converted_key = key.replace('-', ':minor')
            elif 'maj' in key or 'major' in key:
                converted_key = key.replace('-maj', ':major').replace(' major', ':major').replace(' maj', ':major')
            else:
                converted_key = key + ':major'

        # WIKIFONIA | WHEN-IN-ROME | NOTTINGHAM
        if self.dataset_name in ['wikifonia', 'when-in-rome', 'nottingham']:
            converted_key = key.replace(' ', ':').replace('-', 'b')
        # WEIMAR
        if self.dataset_name == 'weimar':
            converted_key = key.replace('-min', ':minor').replace('-maj', ':major').replace('-mix',
                                                                                            ':mixolydian').replace(
                '-chrom', ':chromatic').replace('-dor', ':dorian')
        # OTHERS
        if self.dataset_name in ['band-in-a-box', 'jazz-corpus', 'rock-corpus']:
            if 'min' in key or 'minor' in key:
                converted_key = key.replace('-min', ':minor').replace(' minor', ':minor').replace(' min', ':minor')
            elif 'maj' in key or 'major' in key:
                converted_key = key.replace('-maj', ':major').replace(' major', ':major').replace(' maj', ':major')
            else:
                converted_key = key + ':major'
        if key == '' or key == '0':
            converted_key = 'N'
        return converted_key
