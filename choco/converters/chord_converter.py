"""
Converter for all types of chord and key annotations into Harte Notation.
"""

import logging
import os
import sys
from lib2to3.pytree import convert

lark_converters_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "lark-converters")
)
sys.path.append(lark_converters_path)

from converter import initialise_converter  # type: ignore
from converter_utils import robbie_williams_fix
from harte.harte import Harte
from lark.exceptions import UnexpectedInput
from polychord_converter import convert_polychord
from roman_converter import convert_roman

sys.path.append(os.path.dirname(os.getcwd()))

ANNOTATION_SUPPORTED = {
    "wikifonia": "leadsheet_music21",
    "ireal-pro": "leadsheet_ireal",
    "weimar": "leadsheet_weimar",
    "nottingham": "abc_music21",
    "when-in-rome": "roman_converter",
    "rock-corpus": "roman_converter",
    "jazz-corpus": "leadsheet_jazz_corpus",
    "band-in-a-box": "prettify_harte",
    "mozart-piano-sonatas": "roman_converter",
    "schubert-winterreise": "prettify_harte",
    "robbie-williams": "robbie-williams",
    "real-book": "real-book",
}


class ChordConverter:
    """
    Implements a class for converting chords from different notations to
    the Harte Notation.
    """

    def __init__(self, dataset_name: str, handle_error: bool = True) -> None:
        """
        Initialises the ChordConverter class and sets the parameters that will
        be needed in the methods that the class implements.
        Parameters
        ----------
        dataset_name : str
            The name of the dataset that has to be converted. The datasets
            supported are listed in the ANNOTATION_SUPPORTED dictionary.
        handle_error: bool, default = True
            A boolean that indicates whether to raise an error if a chord is not
            converted or return 'N'
        """
        self.dataset_name = dataset_name
        self.handle_error = handle_error
        if dataset_name in ANNOTATION_SUPPORTED.keys():
            self.annotation_type = ANNOTATION_SUPPORTED[dataset_name]
            if self.annotation_type in [
                "leadsheet_music21",
                "leadsheet_ireal",
                "leadsheet_weimar",
                "abc_music21",
                "leadsheet_jazz_corpus",
            ]:
                self.lark_converter = initialise_converter(self.annotation_type)
        else:
            raise ValueError(
                "The annotation type is not supported.\n"
                "The supported annotation types are:"
                f' {", ".join(ANNOTATION_SUPPORTED.keys())}'
            )
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
        if self.annotation_type in [
            "leadsheet_music21",
            "leadsheet_ireal",
            "leadsheet_weimar",
            "abc_music21",
            "leadsheet_jazz_corpus",
        ]:
            if chord in ["N", "NC", ""]:
                return "N"
            try:
                chord = chord.replace("*", "")
                converted_chord = self.lark_converter.convert(chord)
            except UnexpectedInput as ui:
                try:
                    converted_chord = convert_polychord(
                        chord, handle_error=self.handle_error
                    )
                except ValueError:
                    logging.error(
                        f"Impossible to convert {chord} because the exception "
                        f"{ui} occurred.\n"
                        "Appending to the generated Jams file the original "
                        "chord."
                    )
        # ROMAN_CONVERTER
        elif self.annotation_type == "roman_converter":
            try:
                converted_chord = convert_roman(chord)
            except ValueError:
                logging.error(
                    f"Impossible to convert {chord}.\n"
                    "Appending to the generated Jams file the "
                    "original chord."
                )
        # PRETTIFY HARTE
        elif self.annotation_type == "prettify_harte":
            if "?" in chord:
                return "N"
            converted_chord = chord

        # DATASET-SPECIFIC FIXES
        elif self.dataset_name == "robbie-williams":
            converted_chord = robbie_williams_fix(chord)
        return Harte(converted_chord).prettify()

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
        if self.dataset_name in ["ireal-pro"]:
            if "-" in key:
                converted_key = key.replace("-", ":minor")
            elif "maj" in key or "major" in key:
                converted_key = (
                    key.replace("-maj", ":major")
                    .replace(" major", ":major")
                    .replace(" maj", ":major")
                )
            else:
                converted_key = key + ":major"
        # MOZART-PIANO-SONATAS
        if self.dataset_name in ["mozart-piano-sonatas"]:
            if "min" in key:
                converted_key = key.rstrip("min") + ":minor"
            else:
                converted_key = key.rstrip("maj") + ":major"
        # WIKIFONIA | WHEN-IN-ROME | NOTTINGHAM
        if self.dataset_name in ["wikifonia", "when-in-rome", "nottingham"]:
            converted_key = key.replace(" ", ":").replace("-", "b")
        # REAL-BOOK
        if self.dataset_name in ["real-book"]:
            if "m" in key:
                converted_key = key.rstrip("m") + ":minor"
            else:
                converted_key = key + ":major"
        # WEIMAR
        if self.dataset_name in ["weimar", "robbie-williams"]:
            if "-" in key or ":" in key:
                key = key.replace("-", ":")
                converted_key = (
                    key.replace(":min", ":minor")
                    .replace(":maj", ":major")
                    .replace(":mix", ":mixolydian")
                    .replace(":chrom", ":chormatic")
                    .replace(":dor", ":dorian")
                    .replace(":blues", ":blues")
                    .replace(":lyd", ":lydian")
                )
            else:
                converted_key = key + ":major"
        # OTHERS
        if self.dataset_name in [
            "band-in-a-box",
            "jazz-corpus",
            "rock-corpus",
            "schubert-winterreise",
        ]:
            if "min" in key or "minor" in key:
                converted_key = (
                    key.replace(":min", ":minor")
                    .replace("-min", ":minor")
                    .replace(" minor", ":minor")
                    .replace(" min", ":minor")
                )
            elif "maj" in key or "major" in key:
                converted_key = (
                    key.replace(":maj", ":major")
                    .replace("-maj", ":major")
                    .replace(" major", ":major")
                    .replace(" maj", ":major")
                )
            else:
                converted_key = key + ":major"
        if key == "" or key == "0":
            converted_key = "N"
        return converted_key


if __name__ == "__main__":
    # test the ChordConverter class
    converter = ChordConverter("ireal-pro")
    print(converter.convert_chords("G7#11"))
