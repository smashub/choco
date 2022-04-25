from lark import Transformer
from itertools import chain
import re
from choco.converters.intervals import INTERVAL_MAP

HARTE_SHORTHAND_MAP = {
    "major": "maj",
    "minor": "min",
    "aug": "aug",
    "dim": "dim",
    "major7": "maj7",
    "minor7": "min7",
    "dominant7": "7",
    "minmaj7": "minmaj7",
    "dim7": "dim7",
    "halfdim7": "hdim7",
    "major6": "maj6",
    "minor6": "min6",
    "dominant9": "9",
    "major9": "maj9",
    "minor9": "min9",
    "sus4": "sus4"
  }
HARTE_SHORTHAND_MAP_INVERSE = {v:k for k,v in HARTE_SHORTHAND_MAP.items()}

class HarteTransformer(Transformer):
  """
  Transformer to convert Lark tree into Harte notation 
  """
  def root(self, root_contents):
    """Parse root content by concatenating the root note and its alteration(s) 

    Parameters
    ----------
    root_contents :
        Root and alterations i.e. Eb
    """
    return "".join(root_contents)

  def slash(self, alternate_bass):
    """Parse slash chord content by concatenating the note and its alteration(s) 

    Parameters
    ----------
    alternate_bass :
        Note and alterations i.e. Eb
    """
    return "/" + "".join(alternate_bass)

  def addedinterval(self, interval_contents):
    """Parse interval content by concatenating the alteration and the interval 

    Parameters
    ----------
    interval_contents :
        Alteration and interval i.e. b11
    """
    return "".join(interval_contents)

  def addedintervals(self, interval_contents):
    """Parse added intervals, putting them into a list

    Parameters
    ----------
    interval_contents :
        Interval alterations
    """
    return list(interval_contents)

  def chord(self, chord_constituents):
    """Parse chord by concatenating all of its constituents

    Parameters
    ----------
    chord_constituents :
        Parts of the chord (e.g. [C#, min, add9])
    """
    root = chord_constituents.pop(0)
    shorthand = chord_constituents.pop(0)
    shorthand_intervals = INTERVAL_MAP[HARTE_SHORTHAND_MAP_INVERSE[shorthand]]
    # parse alternate bass
    alternate_bass = chord_constituents.pop(-1) if "/" in chord_constituents[-1] else None
    # parse altered intervals
    altered_intervals = chord_constituents.pop(-1)
    # parse remaining shorthands as intervals
    rem_intervals = set(*[chain(INTERVAL_MAP[HARTE_SHORTHAND_MAP_INVERSE[c]]) for c in chord_constituents])

    # sus chord exception handling: if a chord contains a third (minor or major)
    # and the key sus{2,4} is present then the third need to be added as removed
    if any("sus" in c for c in chord_constituents):
      rem_intervals.add("*3")

    # remove intervals represented by the shorthand from the additional ones
    # to be added
    intervals = rem_intervals.difference(shorthand_intervals)
    # take into account altered intervals
    intervals = intervals.union(altered_intervals)

    # build str repr for intervals and alternate bass
    sorted_intervals = sorted(list(intervals), 
                              key=lambda x: int(re.sub("(b|#|\*)", "", x)))
    intervals_str = f"({','.join(sorted_intervals)})" \
                    if len(sorted_intervals) > 0 else ""
    alternate_bass_str = alternate_bass if alternate_bass is not None else ""
    
    return f"{root}:{shorthand}{intervals_str}{alternate_bass_str}"

  def note(self, note):
    """
    Parse note (simply return it)

    Parameters
    ----------
    note :
        Note parsed to be tranformed
    """
    return note
  
  def alter(self, alter):
    """
    Parse alteration (simply return it)

    Parameters
    ----------
    alter :
        Alteration parsed to be tranformed
    """
    return alter
  
  def __getattribute__(self, name):
    """
    Shorthand attributes just turn the mathced rule into the Harte shorthand e.g.
    the major7 rule method would be somtehing like

    def major7(self): return ":maj7"

    To avoid repetition and improve readability the dictionary HARTE_SHORTHAND_MAP
    has been defined.
    Whenever the requested method matches with one of the dict keys the corresponding
    value is returned. 
    """
    if name in HARTE_SHORTHAND_MAP:
      return lambda *args: HARTE_SHORTHAND_MAP.get(name)
    
    return super().__getattribute__(name)

harte_transformer = HarteTransformer()

def encode(grammar_parsed_chord):
  """Encode chord in harte form

  Parameters
  ----------
  grammar_parsed_chord :
      Chord parsed from Lark grammar

  Returns
  -------
  str
      Chord in Harte encoding
  """
  return harte_transformer.transform(grammar_parsed_chord)