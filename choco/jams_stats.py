"""
Generates in-depth statistics of the content of a ChoCo datasets. This assumes
that all JAMS files follow ChoCo's schema for audio and score annotations, as
all information are extracted from JAMS.

See also
--------
Example of Audio JAMS
    https://github.com/jonnybluesman/choco/wiki/Examples-of-ChoCo-JAMS#audio-jams
Example of Score JAMS
    https://github.com/jonnybluesman/choco/wiki/Examples-of-ChoCo-JAMS#score-jams

"""
import os
import glob
import argparse

from typing import Union
from itertools import groupby
from collections import Counter

import jams
import joblib
import pandas as pd
import numpy as np
from tqdm import tqdm
from joblib import Parallel, delayed

import namespaces  # keep it here for the new namespaces
from jams_utils import extract_jams_metadata


def zipngram(observations, n=2):
    """Simple utility to extract n-grams from a list"""
    return zip(*[observations[i:] for i in range(n)])


def extract_annotation_stats(annotation:jams.Annotation):
    """
    Computes a series of statistics from a JAMS annotations, including the
    number of observations, the count of their unique values (before and after
    the removal of consecutively repeated occurrences), their possible patterns,
    and basic functionals over the corresponding durations.

    Parameters
    ----------
    annotation : jams.Annotation
        The JAMS annotation from which statistics will be extracted.

    Returns
    -------
    annotation_dict : dict
        A dictionary containing all the extracted annotation-level statistics.
    
    """
    annotation_meta = annotation.annotation_metadata
    annotation_dict = {"namespace": annotation.namespace}
    annotation_dict["ann_type"] = annotation_meta.data_source
    annotation_dict["annotator"] = "Unknown" \
        if annotation_meta.annotator.name == "" \
        else annotation_meta.annotator.name
    annotation_dict["observations"] = len(annotation.data)

    annotation_data = [(o.time, o.duration, o.value, o.confidence) \
                        for o in annotation.data]
    durations = list(map(lambda x: x[1], annotation_data))
    values_all = list(map(lambda x: x[2], annotation_data))
    values_norep = [key for key, _group in groupby(values_all)]

    annotation_dict["observation_cnt_all"] = Counter(values_all)
    annotation_dict["observation_cnt_norep"] = Counter(values_norep)
    annotation_dict["observation_set"] = \
        len(annotation_dict["observation_cnt_all"])
    # Basic observation patterns as n-grams
    annotation_dict["observation_n2g"] = Counter(zipngram(values_norep, n=2))
    annotation_dict["observation_n3g"] = Counter(zipngram(values_norep, n=3))
    annotation_dict["observation_n4g"] = Counter(zipngram(values_norep, n=4))
    annotation_dict["observation_duration_avg"] = np.mean(durations)
    annotation_dict["observation_duration_std"] = np.std(durations)

    return annotation_dict


def extract_jams_stats(jam:Union[str, jams.JAMS]):
    """
    Read a JAMS object and compute relevant statistics along with metadata.

    Parameters
    ----------
    jams_path : Union[str, jams.JAMS]
        Either a JAMS object or a path to the corresponding file to load.

    Returns
    -------
    jams_stats : dict
        A dictionary containing metadata and statistics extracted from the JAMS.
    
    See also
    --------
    `extract_annotation_stats()`, `jams_utils.extract_jams_metadata()`

    """
    # Retrieve metadata expected from a ChoCo JAMS
    jams_stats = extract_jams_metadata(jam, flat_nested=False)
    jam = jams.load(jam, strict=False) if isinstance(jam, str) else jam
    jams_stats["no_annotations"] = len(jam.annotations)  # redundant
    annotation_stats = [extract_annotation_stats(a) for a in jam.annotations]

    return annotation_stats

        
def main():
    """
    Main function implements a simmle CLI for dataset stats extraction.
    """

    parser = argparse.ArgumentParser(
        description='Simple extractor of chord stats from JAMS files.')

    parser.add_argument('dataset_dir', type=str,
                        help='Directory where JAMS files will be read.')

    parser.add_argument('--out_dir', type=str,
                        help='Directory where statistics will be saved.')
    parser.add_argument('--n_workers', action='store', type=int, default=1,
                        help='Number of workers for stats computation.')
    parser.add_argument('--compression', action='store', type=int, default=1,
                        help='Compression rate for saving the stats file.')

    args = parser.parse_args()
    if args.out_dir is not None:  # sanity check and default init
        if not os.path.exists(args.out_dir):
            raise ValueError(f"Directory {args.out_dir} does not exist!")
    else:  # using the same directory of the input dataset
        args.out_dir = os.path.dirname(args.dataset_dir)

    # Extracting JAMS statistics: in parallel
    jams_files = glob.glob(os.path.join(args.dataset_dir, "*.jams"))
    print(f"Found {len(jams_files)} in {args.dataset_dir}")
    jams_stats = Parallel(n_jobs=args.n_workers)\
        (delayed(extract_jams_stats)(jam) for jam in tqdm(jams_files))

    # Save the list of stats in a joblib file for later aggregation
    out_fname = os.path.join(args.out_dir, "jams_stats.joblib")
    with open(out_fname, 'wb') as jobfile:
        joblib.dump(jams_stats, jobfile)
    out_fsize = round(os.path.getsize(out_fname) / 1e6, 2)  # file size in MB
    print(f"Done! JAMS stats written in {out_fname} ({out_fsize}MB)")


if __name__ == "__main__":
    main()