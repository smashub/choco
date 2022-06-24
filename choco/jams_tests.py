"""
Utilities for JAMS-driven testing and entry point for running tests.

"""
import argparse
import logging
import os
import re

import jams
import pandas as pd
from utils import is_dir, create_dir

logger = logging.getLogger("choco.tests")

KEEP_STRATEGIES = ["last_n", "first_n"]  # for skimming test JAMS


def select_partition_testset(metadata_path: str, n_sample: int, seed=1234):
    """
    Selelects a test sample from the given partition metadata.

    Parameters
    ----------
    metadata_path : str
        Path to the CSV file with the content metadata of a ChoCo partition.
    n_sample : int
        Number of files to include in the test sample.
    seed : int
        A random seed for sample selection reproducibility.

    Returns
    -------
    test_metadata : pd.Dataframe
        The test data that is part of the sample, with the reduction strategy
        per sample: either `first_n` or `last_n` for the observation to keep.

    """
    meta_df = pd.read_csv(metadata_path)  # reading the mata
    meta_df = meta_df[meta_df['jams_path'].notna()]  # only considering files having a path
    meta_df.columns = meta_df.columns.str.replace(' ', '')
    test_meta = meta_df.sample(n=n_sample, random_state=seed)
    test_meta["keep"] = pd.DataFrame(KEEP_STRATEGIES).sample(
        n=n_sample, replace=True, random_state=seed).values
    test_meta = test_meta[["id", "keep", "jams_path"]]

    return test_meta


def generate_silver_jams(in_jams: jams.JAMS, keep_n=6, keep_loc="first_n"):
    """
    Generate a skimmed version of a given JAMS file with only the first and the
    last `n` observations for each annotation. Please, note that only those
    namespaces with `chord` or `key` substrings in their name are retained.
    
    Parameters
    ----------
    in_jams : jams.JAMS
        The JAMS object to skim for the generation of the silver JAMS.
    keep_n : int
        The number of observation to keep per chord/key annotation.
    keep_loc : str
        Either `first_n` or `last_n` depending on the strategy.
    
    Returns
    -------
    new_jams : jams.JAMS
        The silver JAMS resulting from the skimming process.

    """
    # Sanity checks of the parameters
    if keep_loc not in KEEP_STRATEGIES:
        raise ValueError("Can only keeep leading or trailing observations.")
    if keep_n is not None and not isinstance(keep_n, int):
        raise ValueError("Can only keep all or first/last observations.")

    # Selection of the annotation namespaces: kept in the same order
    new_jams = jams.JAMS(file_metadata=in_jams.file_metadata,
                         sandbox=in_jams.sandbox)  # spawn JAMS with no annotations

    for annotation in in_jams.annotations:
        if re.search("chord|key", annotation.namespace) is not None:
            skimmed_observations = annotation.data[:keep_n] \
                if keep_loc == "first_n" else annotation.data[-keep_n:]

            new_jams.annotations.append(jams.Annotation(
                annotation.namespace, data=skimmed_observations,
                annotation_metadata=annotation.annotation_metadata,
                sandbox=annotation.sandbox, time=annotation.time,
                duration=annotation.duration))

    return new_jams


def generate_partition_testset(partition_path: str, n_sample: int, keep_n=5,
                               seed=1234):
    """
    Generate a full test set for a given ChoCo partition, made of a selection of
    silver JAMS (to be analysed by the annotators) together with a test CSV. 

    Parameters
    ----------
    partition_path : str
        Path to the ChoCo partition, where `meta.csv` is expected. From this path
        and a new `test/` folder will be created with the silver JAMS, at the same
        level of the root partition (i.e. 'choco/partition_name/test/').
    n_sample : int
        Number of test samples to select for the whole partition.
    seed : int
        A random seed for the generation of the sample with pandas.
    keep_n : int
        Number of observations to keep per chord/key annotation.

    Returns
    -------
    test_meta : pd.Dataframe
        A dataframe describing the test set: id, jams_path, silver_path, keep
        strategy (first_n or last_n) per test progression. This dataframe is
        also written to disk in the test folder, together with the silver JAMS.

    """
    meta_path = os.path.join(partition_path, 'meta.csv')
    listed_path = partition_path.split(os.sep)
    assert 'choco' in listed_path, 'The input path is not a valid path.\n' \
                                   'Please provide the path in which the "meta.csv" file can be found in.'
    test_path = create_dir(
        os.path.join(*listed_path[:listed_path.index('choco')], 'test', *listed_path[listed_path.index('choco') + 1:]))
    test_meta = select_partition_testset(
        meta_path, n_sample=n_sample, seed=seed)
    test_meta["silver_path"] = None

    for idx, test_record in test_meta.iterrows():
        # Retriving the current ChoCo's JAMS and renaming the silver
        jams_path = test_record["jams_path"][3:]
        silver_path = os.path.join(
            test_path, test_record["id"] + "_silver.jams")
        # Generating the silver JAMS based on the given specifications
        choco_jams = jams.load(jams_path, validate=False, strict=False)
        silver_jams = generate_silver_jams(
            choco_jams, keep_n=keep_n,
            keep_loc=test_record["keep"])
        # Save the silver JAMS to the testset partition
        silver_jams.save(silver_path, strict=False)
        test_meta.loc[idx, "silver_path"] = silver_path

    test_meta.to_csv(os.path.join(test_path, "test_meta.csv"), index=False)
    return test_meta


def compare_jams(choco_jams: jams.JAMS, gtruth_jams: jams.JAMS):
    """
    Compare a JAMS file produced by ChoCo with a groundtruth JAMS. Checks are
    performed at different levels, focusing on the the metadata, annotations,
    and the additional information appended in the sandbox.

    Parameters
    ----------
    choco_jams : jams.JAMS
        A JAMS file that was produced by ChoCo's jamification process.
    gtruth_jams : jams.JAMS
        A JAMS file that has been manually annotated on the same input.
    
    Returns
    -------
    jams_comparison : dict
        A dictionary containing statistics for each comparison level.

    """
    raise NotImplementedError


def main():
    """
    Entry point to read the arguments and call the conversion scripts.
    """
    parser = argparse.ArgumentParser(
        description='Testing scripts for the JAMification of ChoCo partitions.')

    parser.add_argument('cmd', choices=["create", "test"],
                        help='Either `create` for generating the test samples'
                             ' or `test` for running the JAMS-based tests.')
    parser.add_argument('partition_dir', type=lambda x: is_dir(parser, x),
                        help='Path to the directory of the ChoCo partition in which the "meta.csv" file can be found.')
    # This is useful to avoid the `last_n` strategy from being selected if the
    # content of the partition is symbolic music, hence the 'expansion' of the
    # score into the performed score will not complicate the evaluation process.
    parser.add_argument('type', type=str, choices=["audio", "score"],
                        help='Type of music content in the collection.')

    parser.add_argument('--n_samples', action='store', type=int, default=4,
                        help='Number of test samples to draw from the partition'
                             ', create the test metadata, and skim the JAMS.')
    parser.add_argument('--keep_n', action='store', type=int, default=5,
                        help='Number of chord/key observations per annotation'
                             ' that will be retained for the evaluation.')
    parser.add_argument('--seed', action='store', type=int, default=1234,
                        help='A random seed for reproducible sampling.')

    args = parser.parse_args()

    if args.cmd == "create":
        print("Creating partition test set: this may take a while...")
        generate_partition_testset(
            partition_path=args.partition_dir,
            n_sample=args.n_samples,
            keep_n=args.keep_n,
            seed=args.seed
        )
        print(f"Test set for partition {args.partition_dir} is ready.")

    else:  # XXX this is not ready, yet
        raise NotImplementedError


if __name__ == "__main__":
    main()
