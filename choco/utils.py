"""
General python utilities for automating the boring stuff.
"""

import os
import glob
import random
import logging
import numpy as np


def flatten(t):
    return [item for sublist in t for item in sublist]


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