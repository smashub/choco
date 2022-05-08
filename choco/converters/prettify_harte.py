"""
Script for prettify a chord annotation in the Harte format.
"""

from harte_utils import simplify_harte


def prettify_harte(harte_chord: str) -> str:
    """
    Utility function that takes a Harte chord as input and
    returns a prettified Harte chord, by converting grades
    in shorthands, where possible.
    Parameters
    ----------
    harte_chord : str
        A valid chord annotated according to the Harte conventions.
    Returns
    -------
    prettified_harte_chord : str
        A harte chord where grades have been simplified using
        shorthands, if possible.
    """
    if ':' in harte_chord:
        base_chord, grades = harte_chord.split(':')
        root = ''
        if '/' in grades:
            grades, root = grades.split('/')
            root = '/' + root
        if grades[0] == '(':
            grades = grades.lstrip('(').rstrip(')').split(',')
            prettified_grades = simplify_harte(grades)
            return base_chord + prettified_grades + root
    return harte_chord


if __name__ == '__main__':
    print(prettify_harte('Cb:(3,5,7,9)'))
