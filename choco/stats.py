"""
The idea is to extract simple statistics from a JAMS namespace.
"""

import os
import glob
import logging
import argparse
import itertools
from collections import Counter
from typing import List

import jams
from tqdm import tqdm
from joblib import Parallel, delayed

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

logger = logging.getLogger("choco.stats")


def get_annotation_values(jams_file:str, namespace="chord") -> List:
    """
    Read a JAMS file and extract the annotation values from the desired
    annotation namespace (e.g. chords, key_mode, see JAMS namespaces). If the
    JAMS is not correctly formatted, hence it cannot be read, None is returned.

    Parameters
    ----------
    jams_file : str
        Path to the JAMS that needs to be read and processed.
    namespace : str
        Name of the namespace from which annotations will be extracted.
    
    Returns
    -------
    values : list
        A list containing all the annotation values from the given namespace.

    Notes
    -----
        - Extend this function to just return a tuple with all timihg info.
    """
    try:  # attempting to read the given JAMS file
        jam = jams.load(jams_file, strict=False)
    except:  # badly formatted JAMS cannot be read
        logger.error(f"Could not read: {jams_file}")
        return None  # for now
    values = []  # accumulating from all namespaces
    for annotation_ns in jam.search(namespace=namespace):
        values += [data[2] for data in annotation_ns.data]

    return values


def extract_chord_stats(jams_dir, stats_dir, n_workers=1):
    """
    A simple function to read JAMS files and compute dataset-level statistics
    concerning the relative frequency of chord symbols.

    Parameters
    ----------
    jams_dir : str
        Path to the directory containing dataset's JAMS files.
    stats_dir : str
        Path to the directory where statistics will be saved.
    
    Returns
    -------
    chord_freq : dict
        A dictionary containing the relative frequencies of chord symbols.
    fig : plt.Figure
        Handles to the matplotlib Figure object containing the countplot.

    """
    jams_files = glob.glob(os.path.join(jams_dir, "*.jams"))

    all_chords = Parallel(n_jobs=n_workers)\
        (delayed(get_annotation_values)(jam) for jam in tqdm(jams_files))
    all_chords = list(itertools.chain.from_iterable(
        [ann for ann in all_chords if ann is not None]))

    chord_cnt = Counter(all_chords)
    vocab_size = len(chord_cnt)
    no_chords = len(all_chords)

    chord_freq = [[chord, count, count/no_chords, "," in chord] \
        for chord, count in chord_cnt.most_common()]
    stats_df = pd.DataFrame(
        chord_freq,
        columns=["chord_str", "chord_cnt", "chord_freq", "composite"],
    )

    stats_df.to_csv(os.path.join(stats_dir, "chord_stats.csv"), index=None)
    # # Creating a count plot directly from the observations
    # fig, ax = plt.subplots(figsize=(10, .2*vocab_size))
    # sns.countplot(y=all_chords, order=[c[0] \
    #     for c in chord_cnt.most_common()], ax=ax)    
    # plt.tight_layout()  # try to reduce empty spaces in the plot
    # fig.savefig(os.path.join(stats_dir, "chord_cplot.pdf"))

    return chord_freq  #, fig


def main():
    """
    Main function to read the arguments and extract stats.
    """

    parser = argparse.ArgumentParser(
        description='Simple extractor of chord stats from JAMS files.')

    parser.add_argument('input_dir', type=str,
                        help='Directory where JAMS files will be read.')
    parser.add_argument('out_dir', type=str,
                        help='Directory where statistics will be saved.')

    # Logging and checkpointing
    parser.add_argument('--n_workers', action='store', type=int, default=1,
                        help='Number of workers for stats computation.')

    args = parser.parse_args()
    extract_chord_stats(
        args.input_dir,
        args.out_dir,
        n_workers=args.n_workers,
    )


if __name__ == "__main__":
    main()