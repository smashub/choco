import re
from typing import List

import music21
from harte_utils import grammar_rule_to_music21_chord_type, calculate_interval
from lark import Transformer, Tree
from lark_encoder import BaseEncoder

HARTE_SHORTHAND_MAP = {
    "major": "maj",
    "minor": "min",
    "augmented": "aug",
    "diminished": "dim",
    "major_seventh": "maj7",
    "minor_seventh": "min7",
    "dominant_seventh": "7",
    "minor_major_seventh": "minmaj7",
    "diminished_seventh": "dim7",
    "half_diminished_seventh": "hdim7",
    "major_sixth": "maj6",
    "minor_sixth": "min6",
    "dominant_ninth": "9",
    "major_ninth": "maj9",
    "minor_ninth": "min9",
    "suspended_fourth": "sus4",
}

MODES = {
    "maj": "major",
    "min": "minor",
    "7": "major",
}

MISSING_INTERVALS = {
    "suspended-ninth": '1,4,5,-7,9',
    "suspended-thirteen": '1,4,5,-7,9,11,13',
    "flat-ninth": '1,3,5,-7,-9',
    "minor-flat-ninth": '1,-3,5,-7,-9',
    "major-sharp-11th": '1,3,5,7,9,#11',
    "augmented-sharp-11th": '1,3,#5,-7,9,#11',
    "sharp-ninth-sharp-11th": '1,3,5,-7,#9,#11',
    "sharp-ninth-13th": '1,3,5,-7,#9,13',
    "flat-13th": '1,3,5,-7,9,-13',
    "sharp-ninth": '1,3,5,-7,#9',
    "major-sharp-ninth": '1,3,5,7,#9',
    "sharp-11th": '1,3,5,b7,9,#11',
    "major-sharp-ninth-sharp-11th": '1,3,5,7,#9,#11',
    "minor-major-sharp-11th": '1,b3,5,7,9,#11',
    "sixth-ninth": '1,3,5,6,9',
    "minor-sixth-ninth": '1,b3,5,6,9',
    "alt": '1,3,b5,b7,b9,b13',
    "flat-ninth-flat-13th": '1,3,5,-7,-9,-13',
    "sixth-ninth-sharp-eleventh": '1,3,5,6,9,#11',
    "minor-augmented": '1,-3,#5',
    "sharp-7th-flat-5th-flat-9th": '1,3,-5,#7,b9',
    "minor-flat-sixth": '1,b3,5,b6',
    "augmented-sharp-ninth": '1,3,#5,-7,#9',
    "flat-ninth-sharp-11th": '1,3,5,-7,-9,#11',
    "suspended-flat-ninth": '1,4,5,-7,-9',
    "major-seventh-flat-five": '1,3,-5,7',
    "seventh-flat-9th-sharp-9th": '1,3,5,7,-9,#9',
    "seventh-flat-9th-sharp-5th": '1,3,#5,7,-9',
    "seventh-sharp-9th-flat-5th": '1,3,-5,-7,b9',
    "major-ninth-sharp-11th": '1,3,5,7,9,#11',
    "diminished-seventh-major-seventh": '1,-3,-5,7',
    "seventh-flat-9th-flat-5th": '1,3,b5,b7,9',
    "flat-ninth-sharp-13th": '1,3,5,-7,-9,#13',
    "flat-13th-sharp-11th": '1,3,5,-7,9,#11,-13',
    "suspended-flat-thirteen": '1,3,5,-7,-13',
    "flat-ninth-13th": '1,3,5,-7,-9,13',
    "sharp-eleventh-13th": '1,3,5,-7,9,#11,13',
    "flat-fifth-9th": '1,3,-5,-7,9',
    "sharp-ninth-sharp-13th": '1,3,5,-7,#9,#13',
    "sharp-ninth-flat-13th": '1,3,5,-7,#9,-13',
}


class HarteTransformer(Transformer):
    NOTE = str
    DEGREE = str

    @staticmethod
    def sharp(_):
        return "#"

    @staticmethod
    def flat(_):
        return "b"

    @staticmethod
    def _join_contents(content: Tree) -> str:
        """Join contents of tree in a single string

        Parameters
        ----------
        content : Tree
            Tree contents

        Returns
        -------
        str
            Contents joined in a single string
        """
        return "".join(content)

    altered_note = _join_contents
    altered_degree = _join_contents
    root = _join_contents

    @staticmethod
    def add_degree(degree: Tree) -> str:
        """Add degree as a single number

        Parameters
        ----------
        degree : Tree
            Leaf content

        Returns
        -------
        str
            Additional degree 
        """
        return degree[0]

    @staticmethod
    def subtract_degree(degree: Tree) -> str:
        """Subtract a degree (appends * in front of it)

        Parameters
        ----------
        degree : Tree
            Leaf content

        Returns
        -------
        str
            Removed degree 
        """
        return "*" + degree[0]

    @staticmethod
    def alter_degree(degree: Tree) -> str:
        """Add degree as a single number

        Parameters
        ----------
        degree : Tree
            Leaf content

        Returns
        -------
        str
            Additional degree 
        """
        return degree[0]

    @staticmethod
    def slash(bass: Tree) -> str:
        """Slash chord annotation with alternative bass

        Parameters
        ----------
        bass : Tree
            Bass content

        Returns
        -------
        str
            Alternative bass notation with "/" in front
        """
        return "/" + bass[0]

    @staticmethod
    def shorthand(shorthand: Tree) -> str:
        """Map shorthand rule to Harte rule using HARTE_SHORTHAND_MAP if applicable.
        If the rule can't be converted to an Harte shorthand we will extract the
        intervals that make up the chords using music21.

        Parameters
        ----------
        shorthand : Tree
            Shorthand rule

        Returns
        -------
        str
            Harte shorthand matching 
        """
        assert len(shorthand) == 1, "Only one shorthand can be defined!"
        shorthand_rule = shorthand[0].data.value
        if shorthand_rule in HARTE_SHORTHAND_MAP:
            harte_shorthand = HARTE_SHORTHAND_MAP[shorthand_rule]
        else:
            # extract intervals making up the rule
            shorthand_rule = grammar_rule_to_music21_chord_type(shorthand_rule)
            if shorthand_rule in music21.harmony.CHORD_TYPES.keys():
                intervals = music21.harmony.CHORD_TYPES[shorthand_rule][0]
            elif shorthand_rule in MISSING_INTERVALS.keys():
                intervals = MISSING_INTERVALS[shorthand_rule]
            else:
                print('ERROR!', shorthand_rule)
                intervals = ''
            # remove root (not used by Harte shorthand)
            intervals = intervals.replace("1,", "").replace("-", "b")
            harte_shorthand = intervals.split(",")

        return harte_shorthand

    @staticmethod
    def _build_chord_repr(root: str, shorthand: str, intervals: List[str], bass: str) -> str:
        """
        Parameters
        ----------
        root : str
        shorthand : str
        intervals : List[str]
        bass : str

        Returns
        -------
        str
            Harte chord representation in the form <root><shorthand?><intervals?><bass?>
        """
        # TODO: implement shorthand detection from intervals
        # sort intervals
        intervals = sorted(
            intervals, key=lambda x: int(re.sub("\*|b|#", "", x)))
        intervals = f"({','.join(intervals)})" if len(intervals) > 0 else ""
        return f"{root}:{shorthand}{intervals}{bass}"

    # @staticmethod
    # def polychord(polychord: Tree) -> str:
    #     """Add degree as a single number
    #
    #     Parameters
    #     ----------
    #     degree : Tree
    #         Leaf content
    #
    #     Returns
    #     -------
    #     str
    #         Additional degree
    #     """
    #     return polychord[0]

    def chord(self, chord_constituents: List) -> str:
        """Parse chord rule

        Parameters
        ----------
        chord_constituents : Tree
            Chord tree

        Returns
        -------
        str
            Harte representation of the parsed tree
        """
        for i, cc in enumerate(chord_constituents):
            if '/' in cc:
                chord_constituents.append(chord_constituents.pop(i))
                break

        # extract root
        assert len(chord_constituents) > 0, "Root missing!"
        root = chord_constituents.pop(0)
        root = root.capitalize()

        # extract shorthand
        assert len(chord_constituents) > 0, "Shorthand missing!"
        shorthand = chord_constituents.pop(0)
        # handle shorthand composed by single intervals
        intervals = set()
        if type(shorthand) is list:
            intervals = set(shorthand)
            shorthand = ""

        # check for alternate bass, if present
        alternate_bass = ""
        if len(chord_constituents) > 0 and "/" in chord_constituents[-1]:
            alternate_bass = chord_constituents.pop(-1)
            alternate_bass = f'''/{calculate_interval(music21.note.Note(root),
                                                      music21.note.Note(alternate_bass.replace('b', '-').replace('/', '')))}'''

        # check for degree modifications
        if len(chord_constituents) > 0:
            intervals = intervals.union(chord_constituents)
        return self._build_chord_repr(root, shorthand, intervals, alternate_bass)


class Encoder(BaseEncoder):
    def __init__(self):
        """
        Initialize base encoder using Harte encoder
        """
        super().__init__(HarteTransformer())
