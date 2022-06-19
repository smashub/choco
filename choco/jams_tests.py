"""
Utilities for JAMS-driven testing and entry point for running tests.

"""
import re
import os

import jams
import pandas as pd

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


def generate_partition_testset(partition_path: str, n_sample : int, seed=1234,
    keep_n=5):
    """
    Generate a full test set for a given ChoCo partition, made of a selection of
    silver JAMS (to be analysed by the annotators) together with a test CSV. 

    Parameters
    ----------
    partition_path : str
        Path to the ChoCo partition, where `choco/meta.csv` is expected and a
        new `test/` folder will be created with the silver JAMS.
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
    meta_path = os.path.join(partition_path, "choco/meta.csv")
    test_meta = generate_partition_testset(
        meta_path, n_sample=n_sample, seed=seed)

    for idx, test_record in test_meta.iterrows():

        jams_path = test_record["jams_path"][3:]

        choco_jams = jams.load(jams_path)
        silver_jams = generate_silver_jams(
            choco_jams, keep_n=keep_n,
            keep_loc=test_record["keep"])
        
        # TODO Save JAMS to disk
        # TODO Add silver path in test meta
    
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