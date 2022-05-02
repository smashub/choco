"""
The idea is to extract simple statistics from a JAMS namespace.

"""
import re
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

from parsers.constants import DECOMPOSED_REG

logger = logging.getLogger("choco.stats")


def get_annotation_values(jams_file:str, namespace="chord", unpack=True) -> List:
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
    unpack : bool
        Whether annotation values from related namespaces will be merged.
    
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
        annotations = [data[2] for data in annotation_ns.data]
        if unpack:  # merge annotations if multiple namespaces
            values += annotations 
        else:  # keep all namespaces
            values.append(annotations)
    
    return values


def search_jam(jams_file:str, search_query:str, namespace=None, match_fn=None):
    """
    Perform a simple search of observation values in the given annotation
    namespaces according to the given query and the matching function.

    Parameters
    ----------
    jams_file : str
        Path to the JAMS that needs to be read and processed.
    search_query : str
        A string that will be used as a query for the search operation.
    namespace : str
        Name of the namespace from which annotations will be extracted. If no
        namespace is provided, observations from all namespaces are considered.
    match_fn : fn
        A function that will be used to establish the presence of a match.
    
    Returns
    -------
    matches : set
        A set of annotation observations matching the search query.
 
    """
    if match_fn is None:
        match_fn = lambda x, y: x == y

    observation_values = get_annotation_values(jams_file, namespace)
    matches = [obv for obv in observation_values if match_fn(search_query, obv)]

    return set(matches)


def chord_progression_stats(chords:list):
    """
    Extract simple statistics from a given chord progression, including the
    number of unique chords, the top-3 occurrences (the most frequent ones), and
    whether the progression contains (all or at least one) decomposed chords.

    Parameters
    ----------
    chords : list
        A chord progression encoded as a list of strings.
    
    Returns
    -------
    chprog_stats : dict
        A dictionary containing the computed statistics, indexed by name.

    """
    chord_cnt = Counter(chords)
    chord_top = chord_cnt.most_common()[:3]
    chord_top += [''] * (3 - len(chord_top))
    decomposed = [chord for chord in list(chord_cnt.keys()) \
                if re.match(DECOMPOSED_REG, chord) is not None]

    chprog_stats = {
        "no_of_chords": len(chords),
        "unique_chords": len(chord_cnt),
        "first_most_frequent": chord_top[0],
        "second_most_frequent": chord_top[1],
        "third_most_frequent": chord_top[2],
        "has_decomposed": len(decomposed) > 0,
        "all_decomposed": len(decomposed) == len(chord_cnt),
    }

    return chprog_stats


def extract_chord_stats(jams_dir, out_dir, n_workers=1, **kwargs):
    """
    A simple function to read JAMS files and compute dataset-level statistics
    concerning the relative frequency of chord symbols.

    Parameters
    ----------
    jams_dir : str
        Path to the directory containing dataset's JAMS files.
    out_dir : str
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
    # Global statistics: as if all chords are in the same progression
    all_chords = list(itertools.chain.from_iterable(
        [ann for ann in all_chords if ann is not None]))
    chord_cnt = Counter(all_chords)
    vocab_size = len(chord_cnt)
    no_chords = len(all_chords)

    chord_freq = [[chord, count, count/no_chords,
        re.match(DECOMPOSED_REG, chord) is not None] \
        for chord, count in chord_cnt.most_common()]
    stats_df = pd.DataFrame(
        chord_freq,
        columns=["chord_str", "chord_cnt", "chord_freq", "composite"],
    )

    stats_df.to_csv(os.path.join(out_dir, "chord_stats.csv"), index=None)
    # # Creating a count plot directly from the observations
    # fig, ax = plt.subplots(figsize=(10, .2*vocab_size))
    # sns.countplot(y=all_chords, order=[c[0] \
    #     for c in chord_cnt.most_common()], ax=ax)    
    # plt.tight_layout()  # try to reduce empty spaces in the plot
    # fig.savefig(os.path.join(stats_dir, "chord_cplot.pdf"))

    return chord_freq  #, fig


def search_jams_dataset(jams_dir, query, out_dir=None, namespace=None,
    n_workers=1, **kwargs):
    """
    Search a JAMS dataset for annotations matching a search query in the
    context of the given namespaces. Matches are saved as a CSV file.

    Parameters
    ----------
    jams_dir : str
        Path to the directory containing dataset's JAMS files.
    out_dir : str
        Path to the directory where statistics will be saved.
    query : str
        A string that will be used as a query for the search operation.
    namespace : str
        Name of the namespace from which annotations will be extracted. If no
        namespace is provided, observations from all namespaces are considered.

    Returns
    -------
    chord_freq : dict
        A dictionary containing the relative frequencies of chord symbols.
    fig : plt.Figure
        Handles to the matplotlib Figure object containing the countplot.

    """
    jams_files = glob.glob(os.path.join(jams_dir, "*.jams"))

    all_matches = Parallel(n_jobs=n_workers)\
        (delayed(search_jam)(jam, query, namespace)\
            for jam in tqdm(jams_files))

    comb_matches = list(zip([os.path.basename(j) \
        for j in jams_files], all_matches))
    comb_matches = pd.DataFrame(comb_matches, columns=["jams", "matches"])
    comb_matches = comb_matches[comb_matches["matches"] != set()]

    with pd.option_context('expand_frame_repr', False,
                           'display.max_rows', None): 
        print(comb_matches)  # this is to pretty-print the dataframe

    if len(comb_matches) > 0:
        print(f"No matches found for {query} in {namespace}")
    elif out_dir is not None and out_dir.strip() != "":
        comb_matches.to_csv(os.path.join(
            out_dir, f"matches_{query}.csv"), index=None)

    return comb_matches


command_map = {
    "stats": extract_chord_stats,
    "search": search_jams_dataset,
}

def main():
    """
    Main function to read the arguments and extract stats.
    """

    parser = argparse.ArgumentParser(
        description='Simple extractor of chord stats from JAMS files.')
    
    parser.add_argument('cmd', type=str, choices=list(command_map.keys()),
                        help=f"Either {', '.join(command_map.keys())}.")

    parser.add_argument('input_dir', type=str,
                        help='Directory where JAMS files will be read.')
    parser.add_argument('out_dir', type=str,
                        help='Directory where statistics will be saved.')

    parser.add_argument('--n_workers', action='store', type=int, default=1,
                        help='Number of workers for stats computation.')
    parser.add_argument('--namespace', action='store', type=str,
                        help='Name of the namespace to use for stats/search.')
    parser.add_argument('--search_query', action='store', type=str,
                        help='A textual query to search JAMS annotations.')

    args = parser.parse_args()
    stat_fn = command_map.get(args.cmd)

    stat_fn(
        args.input_dir,
        out_dir=args.out_dir,
        n_workers=args.n_workers,
        query=args.search_query,
        namespace=args.namespace,
    )


if __name__ == "__main__":
    main()