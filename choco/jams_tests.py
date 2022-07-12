"""
Utilities for JAMS-driven testing and entry point for running tests. Also
provides basic testing primitives for JAMS sanity checks and 1-to-1 comparisons
of observations. These can be used for validating JAMS individually, but also
for testing JAMS objects resulting from a manual or (semi-)automatic process.

"""
import os
import re
import math
import argparse
import logging

import jams
import numpy as np
import pandas as pd
from textdistance import levenshtein

from utils import is_dir, create_dir

logger = logging.getLogger("choco.tests")

KEEP_STRATEGIES = ["last_n", "first_n"]  # for skimming test JAMS

sublist = lambda c, i: list(map(lambda x: x[i], c))  # TODO move to utils


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

# ---------------------------------------------------------------------------- #
# Testing utilities for the validation of the JAMification step
# ---------------------------------------------------------------------------- #

def get_nonnull_fields(jams_module):
    """
    Filter the given JAMS section (file_metadata, annotation, sandbox) to
    remove all those null or empty fields. Note that a string containing just
    spaces is considered empty, hence null.

    Parameters
    ----------
    jams_module : JAMS.FileMetadata, JAMS.Annotation_Metadata, JAMS.Sandbox
        An inner section of the JAMS object that needs to be filtered.
    
    Returns
    -------
    meta_fields : dict
        A dictionary with the filtered (non-null) meta fields.

    """
    compact = lambda x: x.strip() if x is not None else None

    names = list(jams_module.keys())  # get all names of the fields found
    # Retrieve all the possible attribute: not elegant but flexible for new def
    meta_fields = {mf: jams_module.__getattribute__(mf) for mf in names \
        if compact(jams_module.__getattribute__(mf)) not in [None, ""]}

    return meta_fields


def get_meta_coverage(gold_meta: dict, pred_meta: dict):
    """
    Compute the level of meta coverage of non-null fields in a section of the
    generated JAMS object. Coverage is intended as the ratio of metadata fields
    that are expected in the JAMS file.

    Parameters
    ----------
    gold_meta : dict
        A dictionary containing all the expected (non-null) metadata fields.
    pred_meta : dict
        A dictionary containing all the generated (non-null) metadata fields.

    Returns
    -------
    coverage : float
        Ratio of expected metadata fields that can be found in `pred_meta`.
    missing_fields : list
        The list of metadata fields that were not found in `pred_meta`.

    """
    expected_fields = set(gold_meta.values())
    predicted_fields = set(pred_meta.values())

    missing_fields = list(expected_fields.difference(predicted_fields))
    return 1 - len(missing_fields) / len(expected_fields), missing_fields


def get_meta_accuracy(gold_meta: dict, pred_meta: dict, soft=True):
    """
    Compute the level of meta accuracy for a section of the JAMS object under
    validation (and only for the common fields). Accuracy ranges from 0 to 1 and
    it its definition depends on the type of field and the comparison behaviour.
    The latter is regulated by the `soft` parameter.

    Parameters
    ----------
    gold_meta : dict
        A dictionary containing all the expected (non-null) metadata fields.
    pred_meta : dict
        A dictionary containing all the generated (non-null) metadata fields.

    Returns
    -------
    accuracies : list
        A list of field-wise accuracies, ranging from 0 (min) to 1 (max).

    """
    accuracies = []
    for field_name, expected_value in gold_meta.items():
        # First check if this is a common field
        if field_name not in pred_meta: continue
        predicted_value = pred_meta[field_name]
        # Perform type and instance checks on the values
        if type(expected_value) != type(predicted_value):
            logger.warn(f"Field {field_name} has inconsistent types. Expected "
                        f"{type(expected_value)}, found {type(predicted_value)}")
            accuracies.append(0)  # a type mismatch will not be resolved
        elif soft & isinstance(expected_value, (int, float)):
            accuracies.append(
                math.abs(expected_value - predicted_value) / expected_value)
        elif soft & isinstance(expected_value, str):
            accuracies.append(levenshtein.\
                normalized_similarity(expected_value, predicted_value))
        else:  # anything that is not a string or number is hammed
            accuracies.append(int(expected_value == predicted_value))
    
    return accuracies


def get_annotation_coverage(gold_annotation, pred_annotation):
    """
    Compute the coverage of a generated annotation with respect to the target
    (expected) annotation. Conversely to accuracy, this notion of coverage does
    not look at the temporal order of the observations; instead, it simply 
    measures the amount of overlap between the observation fields, which is more
    robust to alignment errors (e.g. an extra observation may have been
    inserted, which breaks the expected alignment).

    Parameters
    ----------
    gold_annotation : JAMS.Annotation
        The expected JAMS annotation, used as a gold standard.
    pred_annotation : JAMS.Annotation
        The input JAMS annotation to compare against the gold annotation.

    Returns
    -------
    coverage : dict
        A dictionary with coverage information for each field.

    """
    def cov_fn(i):  # simple implementation of the coverage function
        covered = set(sublist(gold_annotation, i)).\
            intersection(set(sublist(pred_annotation, i)))
        return len(covered) / len(gold_annotation.data)

    coverage = {}
    coverage["time"], coverage["duration"], coverage["value"] = \
        cov_fn(0), cov_fn(1), cov_fn(2)  # same fn different levels

    return coverage


def get_annotation_error(gold_annotation, pred_annotation, agg_fn=np.mean):
    """
    The annotation error results from a 1-to-1 comparison of observations,
    which are thus assumed to be aligned. The latter is reported according to
    the unit of measure of each field: seconds and measure.beats for time and
    duration, text-distance for string values, and so forth.

    Parameters
    ----------
    gold_annotation : JAMS.Annotation
        The expected JAMS annotation, used as a gold standard.
    pred_annotation : JAMS.Annotation
        The input JAMS annotation to compare against the gold annotation.

    Returns
    -------
    errors : dict
        Aggregation of errors for times, durations, and values.

    """
    errors = {"time": [], "duration": [], "value": []}
    for y_gold, y_pred in zip(gold_annotation.data, pred_annotation.data):
        # Time-wise accuracy: distiction between score and audio not needed
        errors["time"].append(math.abs(y_gold.time - y_pred.time))
        errors["duration"].append(math.abs(y_gold.duration - y_pred.duration))
        errors["value"].append(levenshtein.normalized_distance(
            y_gold.value, y_pred.value))  # not similarity

    return {field: agg_fn(errs) for field, errs in errors.items()}


def compare_annotations(gold_annotation, pred_annotation):
    """
    Compare a generated JAMS annotation against a reference for validation.
    Comparison is still focused on coverage and error, but it is reported
    independently for times, durations, and values.

    Parameters
    ----------
    gold_annotation : JAMS.Annotation
        The expected JAMS annotation, used as a gold standard.
    pred_annotation : JAMS.Annotation
        The input JAMS annotation to compare against the gold annotation.

    Returns
    -------
    coverage : dict
        A dictionary with coverage information for each field.
    error : dict
        Aggregation of errors for times, durations, and values.

    """
    if gold_annotation.namespace != pred_annotation.namespace:
        raise ValueError("Cannot compare annotations of different namespace.")

    num_observations = len(gold_annotation.data)
    if len(gold_annotation.data) < num_observations:
        logger.warn("Reference annotation has fewer observation. Using first "
                    "{num_observations} obs to validate the annotation.")
        pred_annotation = pred_annotation[:num_observations]
    

    coverage = get_annotation_coverage(gold_annotation, pred_annotation)    
    error = get_annotation_error(gold_annotation, pred_annotation)

    return coverage, error


class JAMSanityCheck(object):
    """
    Provides functions for validating JAMS objects for internal consistency.

    Notes
    -----
    - Can be made as a test case or should produce warnings / errors at least.

    """
    def __init__(self, jams_path: str, strict=False) -> None:
        """
        Creates a JAMS Sanity Check object from the given file.

        Parameters
        ==========
        jams_path : str
            Path to the JAMS file to be loaded and checked.
        strict : bool
            Whether the builtin JAMS validation should be triggered.

        """
        if not os.path.exists(jams_path):
            raise ValueError(f"No JAMS file at {jams_path}")
        self._jams = jams.load(jams_path, strict=strict)


    def check_annotation_times(self) -> bool:
        """
        Check whether annotation times are less than or equal to the total
        duration of the track / piece, if the latter information is available.

        Returns
        -------
        True if duration are consistent.

        """
        duration = self._jam.file_metadata.duration
        if duration is not None:  # piece duration is available
            annotation_times = [ann.duration <= duration for ann in \
                self.jams.annotations if ann is not None]
            # No annotation duration specified or all consistent
            # XXX Can be improved to include the end of the last obs if no
            # annotation-wise duration is made explicit.
            return annotation_times == [] or all(annotation_times)


    def check_annotation_order(self) -> bool:
        """
        Check wether observation times are temporally ordered in all annotations.
        Please, note that this check is trivial, as this already handled by
        `jams` but still necessary to validate the ordering operator.

        Returns
        -------
        True if annotations are temporally ordered according to the start times.

        """
        for annotation in self._jams.annotations:
            observation_times = [obs[0] for obs in annotation.data]
            if not observation_times[1:] >= observation_times[:-1]:
                return False  # ordering of observations is not indexed
        
        return True


    def check_annotation_uniqueness(self) -> bool:
        """
        Check whether the JAMS object contains duplicated annotations. Two
        annotations are considered the same if they share the same observations
        and they have either: the same annotator, or at least a null annotator.

        Returns
        -------
        True if annotations are unique in the JAMS object. Please, note that
        annotation metadata may still slightly differ.
        """
        duplicates = False
        annotation_hashes = {}  # hash: annotation idx
        for i, annotation in enumerate(self._jams.annotations):

            ann_hash = hash(frozenset(annotation.data))
            siblings = annotation_hashes.get(ann_hash, [])
            for sibling_idx in siblings:  # potential duplicates if not empty
                pdup_ann = self._jams.annotations[sibling_idx]
                # Retrieve and compare annotation metadata
                annotator_a = annotation.annotation_metadata.annotator
                annotator_b = pdup_ann.annotation_metadata.annotator
                if (annotator_a == annotator_b) or \
                    annotator_a is None or annotator_b is None:
                    duplicates = True  # JAMS contains duplicates
                    logger.warn(f"Annotations {i}, {sibling_idx} duplicated.")
                
            siblings.append(i)  # append in any case

        return not duplicates


    def check_supported_metadata(self) -> bool:
        raise NotImplementedError

    
    def run_all_checks(self) -> dict:
        """
        Performs all sanity checks and return the results in a dictionary.

        """
        sanity_checks = {}

        sanity_checks["durations"] = self.check_annotation_times()
        sanity_checks["order"] = self.check_annotation_order()
        sanity_checks["uniqueness"] = self.check_annotation_uniqueness()

        return sanity_checks


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
