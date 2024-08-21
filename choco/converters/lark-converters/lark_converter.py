"""
Chord converter based on Lark Grammar.
So far, the following converters have been implemented:
    - leadsheet converter (3 flavours)
    - ABC converter
"""

from grammar.abc import abc_music21
from grammar.leadsheet import (
    leadsheet_ireal,
    leadsheet_jazz_corpus,
    leadsheet_music21,
    leadsheet_weimar,
)
from lark_parser import BaseParser


class Parser(BaseParser):
    def __init__(self, dialect: str):
        """
        Build parser with specified dialect

        Parameters
        ----------
        dialect : str
            Leadsheet dialect that needs to be used
        """
        DIALECT_MAP = {
            "leadsheet_music21": leadsheet_music21,
            "leadsheet_weimar": leadsheet_weimar,
            "leadsheet_ireal": leadsheet_ireal,
            "abc_music21": abc_music21,
            "leadsheet_jazz_corpus": leadsheet_jazz_corpus,
        }

        super().__init__(DIALECT_MAP[dialect])
