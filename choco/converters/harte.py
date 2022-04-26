from lark import Transformer
from lark.visitors import Interpreter
from itertools import chain
import re
try:
  # import when single calling the script
  from intervals import INTERVAL_MAP
except ImportError:
  # import when called by pytest
  from .intervals import INTERVAL_MAP

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
    "sus4": "sus4",
    "add4": "(4)"
  }
HARTE_SHORTHAND_MAP_INVERSE = {v:k for k,v in HARTE_SHORTHAND_MAP.items()}

class HarteInterpreter(Interpreter):
  """
  Interpreter to convert Lark tree into Harte notation 
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
    return "".join(self.visit_children(interval_contents))

  def addedintervals(self, interval_contents):
    """Parse added intervals, putting them into a list

    Parameters
    ----------
    interval_contents :
        Interval alterations
    """
    return list(interval_contents)

  def _find_rules(self, tree, names):
    if type(names) is not list:
      names = [names]
    matching = list(filter(lambda c: c.data.value in names, tree))
    return matching if len(matching) != 0 else []

  def _find_rule(self, tree, name):
    rules = self._find_rules(tree, name)
    return rules[0] if len(rules) > 0 else None

  def chord(self, chord_constituents):
    """Parse chord by concatenating all of its constituents

    Parameters
    ----------
    chord_constituents :
        Parts of the chord (e.g. [C#, min, add9])
    """
    # parse root
    root = self._find_rule(chord_constituents.children, "root")
    root = self.visit_children(root)[0]
    
    # parse alternate bass
    alternate_bass = self._find_rule(chord_constituents.children, "slash")
    alternate_bass = self.visit_children(alternate_bass)[0] if alternate_bass is not None \
                     else None
    
    # parse main shorthand if possible else decompose it into intervals
    intervals = set()
    main_shorthand = self._find_rule(chord_constituents.children, "mainshorthand")
    main_shorthand = self.visit_children(main_shorthand)[0]
    if type(main_shorthand) is str:
      # shortahand has been recognized as harte shorthand
      main_shorthand_intervals = INTERVAL_MAP[HARTE_SHORTHAND_MAP_INVERSE[main_shorthand]]
    elif type(main_shorthand) is list:
      # main shorthand has been decomposed into list of intervals
      # hence set the main shorthand to empty
      intervals = intervals.union(main_shorthand)
      main_shorthand_intervals = []
      main_shorthand = ""
    
    # parse auxiliary shorthands
    aux_shorthands = self._find_rules(chord_constituents.children, "auxshorthand")
    aux_shorthands = [self.visit(ar)[0] for ar in aux_shorthands] if aux_shorthands is not None \
                     else []
    aux_intervals = list(chain(*[
      INTERVAL_MAP[HARTE_SHORTHAND_MAP_INVERSE[aux]] if type(aux) is not list else aux 
      for aux in aux_shorthands
    ]))
    # add auxiliary intervals
    intervals = intervals.union(aux_intervals)
    
    # sus chord exception handling: if a chord contains a third (minor or major)
    # and the key sus{2,4} is present then the third need to be added as removed
    if "sus" in main_shorthand or any("sus" in x for x in aux_shorthands):
      intervals.add("*3")

    # parse intervals specialization
    intervals_spec = self._find_rules(chord_constituents.children, "intervalspec")
    intervals_spec = [self.visit(ic)[0] for ic in intervals_spec] if intervals_spec is not None \
                     else []
    # remove from intervals those intervals that have been specialized
    intervals = intervals.difference(
      list(map(lambda x: re.sub("(b|#|\*)", "", x), intervals_spec)))
    intervals = intervals.union(intervals_spec)
    
    # remove redundant intervals already represented by the main shorthand
    intervals = intervals.difference(main_shorthand_intervals)
    # cancel out removed intervals i.e C:(*3, 3) -> C
    to_remove = list(filter(lambda x: "*" in x, intervals))
    to_remove = list(chain(*[[tr.replace("*", ""), tr] for tr in to_remove]))
    intervals = intervals.difference(to_remove)
    
    # build str repr for intervals
    sorted_intervals = sorted(list(intervals), 
                              key=lambda x: int(re.sub("(b|#|\*)", "", x)))
    intervals_str = f"({','.join(sorted_intervals)})" \
                    if len(sorted_intervals) > 0 else ""
    alternate_bass_str = f"/{alternate_bass}" if alternate_bass is not None else ""
    
    return f"{root}:{main_shorthand}{intervals_str}{alternate_bass_str}"

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
    elif name in INTERVAL_MAP:
      return lambda *args: INTERVAL_MAP.get(name)
    
    return super().__getattribute__(name)

_transform = HarteInterpreter().visit

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
  return _transform(grammar_parsed_chord)

if __name__ == "__main__":
  from sys import argv
  from leadsheet import parse
  print(encode(parse(argv[1])))
  #print(encode(parse("B-sus2/B")))