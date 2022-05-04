"""
Converter for Polychord.
"""
from typing import List

from mingus.core import chords


def clean_polychord(polychord: str) -> List:
    cleaned_polychord = ''.join([i.replace('-', 'b') for i in polychord if not i.isdigit()]).split(',')

    print(chords.determine(cleaned_polychord, shorthand=True), '\n')
