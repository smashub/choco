"""
Make use of the jams library interface to enable conversion from leadsheet
encoding to harte encoding.

Leadsheet encoding is usually of the form <root note><intervals shorthand>
i.e. Cmaj7, C#m, D 7, Bb min7 b5
We can proceed by extracting the root note, which can be done by matching
the pattern ^([A-G]\s?(b*|#*)\s?)
from here we can to define the rules to extract each different shorthand.

Notes:
    - We assume that the leadsheet chord embedding doesn't contain any text before
      the root note. Some little preprocessing might prevent unwanted errors.
    - When we have alterations to harte shorthands we are going to add also redundant
      intervals (e.g. Dmsus2 [0, 2, b3, 5] (2 == b3) -> D:min(*b3, *3, 2))
      This can be fixed by making use of chord to intervals converted [1]
      and remove redundancies from intervals.
      [1] https://github.com/bzamecnik/chord-labels 
    - Ambiguous chords: G7+, polychords (i.e. E4,G4), E-/B- (polychord or whole chord as bass?)
"""
from typing import List, Any, Tuple, Union
from collections import OrderedDict
from itertools import chain
import re
import argparse

class RegexOrderedDict(OrderedDict):
  """
  Simple extension of an OrderedDict in which keys are regex patterns
  and a value is retrieved if it matches with a key.
  Note that the data structure access complexity isn't O(1) but O(n).
  """
  def get(self, k: str, match_one: bool = True) -> Union[Tuple[str, Any], List[Tuple[str, Any]]]:
    """Match the provided key with all the patterns that makes up the dictionary

    Parameters
    ----------
    k : str
        string used to perform pattern matching
    match_one : bool, optional
        If True stops at the first matched pattern, by default True

    Returns
    -------
    Union[Tuple[str, Any], List[Tuple[str, Any]]]
        A tuple containing the matched regex and the corresponding value. If match_one 
        is False then a list of all the matched regex and values is returned.
    """
    items = ((pattern, value) for pattern, value in self.items() if re.search(pattern, k))
    return next(items) if match_one else list(items) 
    
ROOT_NOTE_RE = re.compile(r'^([A-G]\s?([b|#]*))')

def _extract_root(leadsheet: str) -> Tuple[str, str]:
  """Extract the root note from a leadsheet notation.

  Parameters
  ----------
  leadsheet : str
      leadsheet chord

  Returns
  -------
  Tuple[str, str]
      tuple in the form (root note, rest of the notation)
  """
  try:
    root = ROOT_NOTE_RE.match(leadsheet).group()
  except:
    raise SyntaxError(f"No root found in {leadsheet}")

  leadsheet = ROOT_NOTE_RE.sub("", leadsheet)
  # remove spaces from leadsheet notation
  leadsheet = leadsheet.replace(" ", "")

  return root, leadsheet

# regex to map leadsheet annotation to harte shorthands
# we will put the most expressive annotations first (e.g. maj7 wrt maj)
# so that we will be able to stop at the first matched regex using an OrderedDict
# i.e. Dmaj7 will only match maj7 and avoid matching maj while Dmaj will match maj
HARTE_SHORTHANDS_RE = RegexOrderedDict({
  '([Mm]i|[Mm]in|m(?!a)|\-)\(?([Mm]a|[Mm]aj|M)7\)?': 'minmaj7',
  '(([Mm]a|[Mm]aj|M)7|Δ)': 'maj7', # Ma7, ma7, Maj7, maj7, M7, Δ -> maj7
  '([Mm]i|[Mm]in|m(?!a)|\-)7': 'min7',  # Min7, min7, m7, -7 -> min7
  'dim7': 'dim7',
  '(mi7b5|-7b5|ø7?|o7?)': 'hdim7',
  '7': '7',
  '([Mm]i|[Mm]in|m(?!a)|\-)6': 'min6',
  '([Mm]a|[Mm]aj|M)?6': 'maj6',
  '([Mm]i|[Mm]in|m(?!a)|\-)9': 'min9',
  '([Mm]a|[Mm]aj|M)?9': 'maj9',
  '6': '6',
  '(min|Min|mi|m(?!a)|\-)': 'min', # minor triad
  '(dim|°)': 'dim', # dimished triad
  '(aug|\+)': 'aug', # augmented triad
  '(Sus|sus)\s*4?': 'sus4', # sus 4
  '': 'maj'
})

def _extract_harte_shorthand(leadsheet: str) -> Tuple[List[str], str]:
  """Extract harte shorthand

  Parameters
  ----------
  leadsheet : str
      leadsheet chord

  Returns
  -------
  Tuple[str, str]
      tuple in the form (harte shorthand, rest of the notation)
  """
  try:
    # map leadsheet to harte shorthand where possible
    matched_pattern, harte_shorthand = HARTE_SHORTHANDS_RE.get(leadsheet, match_one = True)
    # remove matched part
    leadsheet = re.sub(matched_pattern, "", leadsheet)
  except:
    # no shorthand found
    harte_shorthand = "NA"

  return harte_shorthand, leadsheet

# regex to map leadsheet annotation to single intervals which do not constitute an harte shorthand
INTERVALS_RE = RegexOrderedDict({
  '5|power': ['*3'], # power chords, missing fifth
  # all extra notes that can be added to a triad
  'add\s*2': ['2'],
  'add\s*b2': ['b2'],
  'add\s*#2': ['#2'],
  'add\s*4': ['4'],
  'add\s*b4': ['b4'],
  'add\s*#4': ['#4'],
  'add\s*9': ['9'],
  'add\s*b9': ['b9'],
  'add\s*#9': ['#9'],
  'add\s*11': ['11'],
  'add\s*b11': ['b11'],
  'add\s*#11': ['#11'],
  'add\s*13': ['13'],
  'add\s*b13': ['b13'],
  'add\s*#13': ['#13'],

  'sus2': ['2', '*b3', '*3'], # sus2 needs major (minor) third removed
})

def _extract_harte_additional_intervals(leadsheet: str) -> Tuple[List[str], str]:
  """Extract harte additional (or missing) intervals

  Parameters
  ----------
  leadsheet : str
      leadsheet chord

  Returns
  -------
  Tuple[List[str], str]
      tuple in the form (intervals, rest of the notation)
  """
  matched_intervals = INTERVALS_RE.get(leadsheet, match_one = False)
  if len(matched_intervals) > 0:
    patterns, intervals = tuple(zip(*matched_intervals))
  else:
    patterns, intervals = [], []
  
  # get all matched intervals -> flatten in single list -> remove duplicates -> sort by name
  intervals = sorted(list(set(chain(*intervals))))

  # remove matched patterns form leadsheet notation
  for pattern in patterns:
    leadsheet = re.sub(pattern, "", leadsheet)

  return intervals, leadsheet

BASS_NOTE_RE = re.compile(r'(/|\\)([A-G]\s?([b|#]*))')

def _extract_bass_notation(leadsheet: str) -> Tuple[str, str]:
  """Extract harte additional (or missing) intervals

  Parameters
  ----------
  leadsheet : str
      leadsheet chord

  Returns
  -------
  Tuple[str, str]
      tuple in the form (designated bass note, rest of the notation)
  """
  try:
    bass = BASS_NOTE_RE.match(leadsheet).group(2)
  except:
    raise SyntaxError(f"No designated bass found in {leadsheet}")

  leadsheet = BASS_NOTE_RE.sub("", leadsheet)
  # remove spaces from leadsheet notation
  leadsheet = leadsheet.replace(" ", "")

  return bass, leadsheet

def convert(leadsheet: str) -> str:
  """Converts from leadsheet notation to harte notation

  Parameters
  ----------
  leadsheet : str
      Leadsheet encoded chord

  Returns
  -------
  str
      Harte encoded chord, using shorthands when applicable
  """
  root, leadsheet = _extract_root(leadsheet)
  harte_shorthand, leadsheet = _extract_harte_shorthand(leadsheet)
  harte_notation = f"{root}:{harte_shorthand}" 
  
  intervals, leadsheet = _extract_harte_additional_intervals(leadsheet)
  if len(intervals) > 0:
    harte_notation += f"({','.join(intervals)})"

  try:
    bass, leadsheet = _extract_bass_notation(leadsheet)
    harte_notation += f"/{bass}"
  except:
    # no bass note - no problemo
    pass
  
  return harte_notation

# **************************************************************************** #
# **************************************************************************** #

if __name__ == "__main__":
  # usage: cat list-of-chords | python leadsheet_to_harte.py > list-of-converted-chords

  from sys import stdin
  chords = stdin.readlines()
  for chord in chords:
    try:
      print(convert(chord.rstrip()))
    except Exception as e:
      print(e)