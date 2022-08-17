"""
General python utilities for automating the boring stuff.
"""

import os
import re
import glob
import random
import logging
import numpy as np


def flatten(t):
    return [item for sublist in t for item in sublist]


def stringify_dict(nested_dict:list, sep:str=";"):
    """Create a single string out of a dictionary using custom separators."""
    nested_dict = dict(nested_dict)  # make sure we have a dictionary
    return sep.join([f"({k}: {v})" for k, v in nested_dict.items()]) \
        if len(nested_dict) > 0 else ""


def stringify_list(nested_list:list, sep:str=";"):
    """Create a single string from a list by using custom separators."""
    nested_list = list(nested_list)  # make sure we have a list
    return sep.join(nested_list) if len(nested_list) > 0 else ""


def set_random_state(random_seed):
    # os.environ['PYTHONHASHSEED'] = str(seed_value)
    random.seed(random_seed)
    np.random.seed(random_seed)


def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def is_file(parser, f_arg):
    if not os.path.exists(f_arg):
        return parser.error("File %s does not exist!" % f_arg)
    return f_arg


def is_dir(parser, f_arg):
    if not os.path.isdir(f_arg):
        return parser.error("Directory %s does not exist!" % f_arg)
    return f_arg


def get_class_name(object):
    """Returns the class name of a given object."""
    return object.__class__.__name__


def set_logger(log_name, log_console=True, log_dir=None):
    
    logger_master = logging.getLogger(log_name)
    logger_master.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if log_console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger_master.addHandler(ch)

    if log_dir:
        fh = logging.FileHandler(
            os.path.join(log_dir,
            f'{log_name}.log'))
        fh.setLevel(logging.WARNING)
        fh.setFormatter(formatter)
        logger_master.addHandler(fh)

    return logger_master


def print_recursive_ls(path):
    for root, dirs, files in os.walk(path):
        path = root.split(os.sep)
        print((len(path) - 1) * '---', os.path.basename(root))
        for f in files:
            print(len(path) * '---', f)


def get_directories(root_dir:str, full_path=False):
    if not os.path.isdir:  # sanity check first
        raise ValueError(f"{root_dir} is not a valid folder")
    subdirs = [d for d in os.listdir(root_dir) \
        if os.path.isdir(os.path.join(root_dir, d))]
    return [os.path.join(root_dir, d) for d in subdirs] \
        if full_path else subdirs  # append mother path if needed


def get_files(root_dir:str, ext:str, full_path=False):
    files = [f for f in glob.glob(os.path.join(root_dir, f"*.{ext}"))]
    return [os.path.basename(root_dir, f) for f in files] \
        if not full_path else files  # append mother path if needed


def strip_extension(fname:str, all=False):
    """
    Strip (all, or the main) extension(s) from a given file name.
    """
    return fname.split(".")[0] if all else os.path.splitext(fname)[0]


def note_map():
    return [
        ('C', 'B#', 'Dbb'),
        ('C#', 'Db'),
        ('D', 'C##', 'Ebb'),
        ('D#', 'Eb'),
        ('E', 'D##', 'Fb'),
        ('F', 'E#', 'Gbb'),
        ('F#', 'Gb'),
        ('G', 'F##', 'Abb'),
        ('G#', 'Ab'),
        ('A', 'G##', 'Bbb'),
        ('A#', 'Bb'),
        ('B', 'A##', 'Cb')
    ]


def get_note_index(note_name: str) -> int:
    try:
        return [i for i, n in enumerate(note_map()) if note_name in n][0]
    except IndexError:
        raise IndexError('The note is not indexed, try with enharmonics.')


def pad_substring(string:str, pattern:str, replacement=None, recursive=False):
    """
    Safely pad a sub-string, given its regular expression, and return a copy of
    the padded string. By default, only the first occurrence of the string is
    padded, unless `recursive` is True.

    Parameters
    ----------
    string : str
        The main string that will be searched and replaced for the pattern.
    pattern : str
        A regular expression describing the sub-string that will be padded.
    replacement : str
        An optional string to use as a replacement of the sub-string; if not
        provided, the actual sub-string will be kept to be padded.
    recursive : bool
        If True, all occurrences of the pattern will be recursively padded.

    """
    match = re.search(pattern, string)
    if match is None:  # same string is returned if pattern is not found
        return string

    start, end = match.start(), match.end()
    s = match.group(0) if replacement is None else replacement
    l_padding = " " if start != 0 and string[start-1] != " " else ""
    r_padding = " " if end < len(string) and string[end] != " " else ""
    new_string = string[:start] + l_padding + s + r_padding

    return new_string + string[end:] if not recursive else \
        new_string + pad_substring(string[end:], pattern, replacement, True)
