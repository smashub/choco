"""
Module to convert a chord from a variety of different syntaxes to the Harte syntax.
"""

from lark import Tree
from lark_converter import Parser
from lark_encoder import BaseEncoder
from lark_parser import BaseParser
from lark_to_harte import Encoder


class Converter(object):
    def __init__(self, parser: BaseParser, encoder: BaseEncoder):
        """Builds a converter using the specified parser and encoder.

        Parameters
        ----------
        parser : BaseParser
            Parser to parse chord into grammar tree
        encoder : BaseEncoder
            Encoder to encode the grammar tree into a string
        """
        self.encoder = encoder
        self.parser = parser

    def convert(self, chord: str) -> Tree:
        """Convert chord into new encoding by parsing it and passing it to
         the encoder.

        Parameters
        ----------
        chord : str
            Chord initial encoding

        Returns
        -------
        str
            Chord final encoding
        """
        return self.encoder.encode(self.parser.parse(chord))


def initialise_converter(annotation_type: str) -> Converter:
    """Initialises a converter based on the annotation type.

    Parameters
    ----------
    annotation_type : str
        The annotation type to initialise the converter with

    Returns
    -------
    Converter
        The initialised converter
    """
    parser = Parser(annotation_type)
    encoder = Encoder()
    return Converter(parser, encoder)
