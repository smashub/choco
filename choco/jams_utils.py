
from parsers.constants import CHORD_NAMESPACES

def has_chords(jam_file):
    for namespace in CHORD_NAMESPACES:
        if jam_file.search(namespace=namespace):
            return True
    return False