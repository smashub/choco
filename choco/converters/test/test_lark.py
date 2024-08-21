import os
import sys
from typing import List

import pandas as pd

sys.path.append(os.path.dirname(os.getcwd()))
lark_converters_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "lark-converters")
)
sys.path.append(lark_converters_path)
converters_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(converters_path)

from converter import Converter
from converter_utils import open_stats_file
from lark.exceptions import UnexpectedInput
from lark_converter import Parser
from lark_to_harte import Encoder
from polychord_converter import convert_polychord

basedir = os.path.dirname(__file__)
LEADSHEET_CHORD_STATS = os.path.join(
    basedir, "../../../partitions/ireal-pro/choco/forum/chord_stats.csv"
)
ABC_CHORD_STATS = os.path.join(
    basedir, "../../../partitions/nottingham/choco/chord_stats.csv"
)

leadsheet_music21_parser = Parser("leadsheet_ireal")
abc_music21_parser = Parser("abc_music21")
harte_encoder = Encoder()


def save_chord_stats(error_list: List[List]) -> None:
    error_df = pd.DataFrame(
        error_list, columns=["chord", "occurrences_n", "percentage"]
    )
    error_df.sort_values(by=["percentage"], inplace=True, ascending=False)
    error_df.to_csv("error_meta.csv", index=False)


def test_leadsheet_harte_conversion(stats_file: str) -> None:
    """
    Tests the Leadsheet chord converter using the statistics file generated
    by stats.py.
    """
    leadsheet_converter = Converter(leadsheet_music21_parser, harte_encoder)

    all_leadsheet_chord = open_stats_file(stats_file)
    errors = []
    error_meta = []
    f = 0
    for chord_data in all_leadsheet_chord:
        chord = chord_data[0].replace("*", "")
        chord = chord.upper() if len(chord) == 1 else chord
        try:
            converted_chord = leadsheet_converter.convert(chord)
            f += float(chord_data[2])
            # print(f"{chord_data[0].ljust(15)} -> {converted_chord}")
        except Exception as ea:
            try:
                # parser error -> chord couldnt be parsed
                # print(f"{chord_data[0].ljust(15)} -> Parsing error")
                print(f"{chord_data[0].ljust(15)} -> {convert_polychord(chord)}")
                f += float(chord_data[2])
            except Exception as eb:
                print(f"Impossible to convert: {chord_data[0]}")
                errors.append(chord_data[0])
                error_meta.append([chord_data[0], chord_data[1], chord_data[2]])
    save_chord_stats(error_meta)
    print("Chords converted (%): ", f, "\nNot converted: ", len(list(set(errors))))


def test_abc_harte_conversion(stats_file: str) -> None:
    """
    Tests the ABC chord converter using the statistics file generated
     by stats.py.
    """
    abc_converter = Converter(abc_music21_parser, harte_encoder)

    all_abc_chord = open_stats_file(stats_file)

    f = 0
    for chord_data in all_abc_chord:
        try:
            converted_chord = abc_converter.convert(chord_data[0])
            f += float(chord_data[2])
            # print(f"{chord_data[0].ljust(15)} -> {converted_chord}")
        except UnexpectedInput as lark_e:
            # parser error -> chord can't be parsed
            # print(f"{chord_data[0].ljust(15)} -> Parsing error")
            pass
        except Exception as e:
            print(e)
    print(f)


if __name__ == "__main__":
    test_leadsheet_harte_conversion(os.path.join(basedir, LEADSHEET_CHORD_STATS))
    # print(convert_roman_numeral('ii', '#', ['G#', 'minor']))

    # test_abc_harte_conversion(os.path.join(basedir, ABC_CHORD_STATS))
