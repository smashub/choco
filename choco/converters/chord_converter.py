"""
Converter
"""
import logging
import sys
import os

from lark.exceptions import UnexpectedInput

from lark_converters.converter import Converter
from lark_converters.lark_converter import Parser
from lark_converters.lark_to_harte import Encoder
from polychord_converter import convert_polychord
from prettify_harte import prettify_harte
from roman_converter import convert_roman

sys.path.append(os.path.dirname(os.getcwd()))

ANNOTATION_SUPPORTED = {
    'leadsheet_music21': 'lark_converter',
    'leadsheet_ireal': 'lark_converter',
    'leadsheet_weimar': 'lark_converter',
    'abc_music21': 'lark_converter',
    'roman_numerals': 'roman_converter',
    'polychord': 'polychord_converter',
    'prettify_harte': 'prettify_harte',
}


class ChordConverter:
    """

    """

    def __init__(self, annotation_type: str):
        """

        """
        if annotation_type in ANNOTATION_SUPPORTED.keys():
            self.annotation_type = ANNOTATION_SUPPORTED[annotation_type]
            if self.annotation_type == 'lark_converter':
                self.lark_converter = Converter(Parser(annotation_type), Encoder())
        else:
            raise ValueError('The annotation type is not supported.\n'
                             f'The supported annotation types are: {", ".join(ANNOTATION_SUPPORTED.keys())}')
        self.chord_metadata = []

    def convert_chords(self, chord):
        """

        """
        converted_chord = chord
        # LARK_CONVERTER
        if self.annotation_type == 'lark_converter':
            try:
                converted_chord = self.lark_converter.convert(chord)
            except UnexpectedInput as ui:
                try:
                    converted_chord = prettify_harte(convert_polychord(chord))
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
            converted_chord = prettify_harte(chord)

        return converted_chord
