
import os
import re

def infer_title_name(file_name, has_number, has_cd="auto", number_sep=" ", isdir=False):

    def split_on_prefix(fname):
        """
        Simple utility to divide a string based on the given conventions.
        """
        splitted_text = fname.split()
        prefix =  splitted_text[0]
        offset = 2 if splitted_text[1]==number_sep else 1
        fname = " ".join(splitted_text[offset:])

        return prefix, fname

    fname = os.path.splitext(file_name)[0] if not isdir else file_name
    has_cd = bool(re.match(r"^CD[0-9]", fname)) if has_cd=='auto' else has_cd
    number_prefix, cd_prefix = None, None  # for now

    if " " not in fname and "_" in fname:
        fname = fname.replace("_", " ")

    if has_cd:  # the CD number is assumed to lead
        cd_prefix, fname = split_on_prefix(fname)
    if has_number:  # the number follows the cd prefix
        number_prefix, fname = split_on_prefix(fname)

    return fname, number_prefix, cd_prefix
