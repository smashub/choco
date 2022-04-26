# Define a map to move from grammar namespace to the intervals that make up a chord

INTERVAL_MAP = {
  #triads
  "major": ["3", "5"],
  "minor": ["b3", "5"],
  "aug": ["3", "#5"],
  "dim": ["b3", "b5"],
  # seventh
  "major7": ["3", "5", "7"],
  "minor7": ["b3", "5", "b7"],
  "dominant7": ["3", "5", "b7"],
  "minmaj7": ["b3", "5", "7"],
  "dim7": ["b3", "b5", "bb7"],
  "halfdim7": ["b3", "b5", "b7"],
  "augmaj7": ["3", "#5", "7"],
  "augdominant7": ["3", "#5", "b7"],
  "seventh5b": ["3", "b5", "b7"],
  # ninth
  "major9": ["3", "5", "7", "9"],
  "minor9": ["b3", "5", "b7", "9"],
  "dominant9": ["3", "5", "b7", "9"],
  "dominantmin9": ["3", "5", "b7", "b9"],
  "minmaj9": ["b3", "5", "7", "9"],
  "augmaj9": ["3", "#5", "7", "9"],
  "augdominant9": ["3", "#5", "b7", "9"],
  "halfdim9": ["3", "b5", "b7", "9"],
  "halfdimmin9": ["3", "b5", "b7", "b9"],
  "dim9": ["b3", "b5", "bb7", "9"],
  "dimmin9": ["b3", "b5", "bb7", "b9"],
  # eleventh
  "major11": ["3", "5", "7", "9", "11"],
  "minor11": ["b3", "5", "b7", "9", "11"],
  "dominant11": ["3", "5", "b7", "9", "11"],
  "minmaj11": ["b3", "5", "7", "9", "11"],
  "augmaj11": ["3", "#5", "7", "9", "11"],
  "augdominant11": ["3", "#5", "b7", "9", "11"],
  "halfdim11": ["b3", "b5", "b7", "9", "11"],
  "dim11": ["b3", "b5", "bb7", "9", "11"],
  # thirtheenth
  "major13": ["3", "5", "7", "9", "11", "13"],
  "minor13": ["b3", "5", "b7", "9", "11", "13"],
  "dominant13": ["3", "5", "b7", "9", "11", "13"],
  "minmaj13": ["b3", "5", "7", "9", "11", "13"],
  "augmaj13": ["3", "#5", "7", "9", "11", "13"],
  "augdominant13": ["3", "#5", "b7", "9", "11", "13"],
  "halfdim13": ["b3", "b5", "b7", "9", "11", "13"],
  # sixth
  "major6": ["3", "5", "6"],
  "minor6": ["b3", "5", "6"],
  # alt chord
  "alt": ["3", "b5", "#5", "b7", "b9", "#9"],
  # added interval
  "add2": ["2", "3", "5"],
  "add4": ["3", "4", "5"],
  # removed interval
  "no3": ["*3"],
  "no5": ["*5"],
  # sus chords
  "sus4": ["*3", "4", "5"],
  "sus2": ["*3", "2", "5"],
  # power chord
  "power": ["5"],
}