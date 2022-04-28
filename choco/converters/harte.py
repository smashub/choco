from lark import Lark, Transformer, Tree
from lark.visitors import Interpreter
from itertools import chain
import music21
from typing import List
import re
from encoder import BaseEncoder

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


def grammar_rule_to_music21_chord_type(rule: str):
    """Convert grammar rule so that it can be used as key in
    music21.harmony.CHORD_TYPES.
    TODO: Move it to different file,

    Parameters
    ----------
    rule : str
        Grammar rule

    Returns
    -------
    str
        music21 CHORD_TYPE rule
    """
    return rule.replace("_", "-")


class HarteTransformer(Transformer):
    NOTE = str
    DEGREE = str
    def sharp(self, _): return "#"
    def flat(self, _): return "b"

    def _join_contents(self, content: Tree) -> str:
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

    def add_degree(self, degree: Tree) -> str:
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

    def subtract_degree(self, degree: Tree) -> str:
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

    def alter_degree(self, degree: Tree) -> str:
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

    def slash(self, bass: Tree) -> str:
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

    def shorthand(self, shorthand: Tree) -> str:
        """Map shortand rule to Harte rule using HARTE_SHORTHAND_MAP if applicable.
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
            intervals = music21.harmony.CHORD_TYPES[shorthand_rule][0]
            # remove root (not used by Harte shorthand)
            intervals = intervals.replace("1,", "").replace("-", "b")
            harte_shorthand = intervals.split(",")

        return harte_shorthand

    def _build_chord_repr(self, root: str, shorthand: str, intervals: List[str], bass: str) -> str:
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

    def chord(self, chord_constituents: Tree) -> str:
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
        # extract root
        assert len(chord_constituents) > 0, "Root missing!"
        root = chord_constituents.pop(0)

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
