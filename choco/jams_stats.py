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
import logging
import argparse

from enum import Enum
from typing import List, Union
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
from utils import to_freq

logger = logging.getLogger("choco.jams_stats")


class StatsExtractorState(Enum):
        CREATED    = 0  # object created, nothing parsed yet
        COMPUTED   = 1  # elements have been iterated
        AGGREGATED = 2  # aggregations/functionals computed
        EXPORTED   = 3  # stats object have been dumped to disk

class InvalidStatsExtractorState(Exception):
    """Raised when trying to process new entries or saving too early."""
    pass


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
    jams_stats["annotations"] = [extract_annotation_stats(ann) \
                                 for ann in jam.annotations]
    return jams_stats


class ChoCoAnnotationStats(object):
    """
    Incremental extraction and aggregation of content-based statistics from JAMS
    annotation stats. These can be either previously computed, or generated
    directly from JAMS annotation objects.

    See also
    --------
    extract_annotation_stats(), ChoCoDatasetStats()

    """
    __state = StatsExtractorState.CREATED
    __no_annotations = 0  # number of annotation processed so far
    __namespace = ""  # the namespace this stats are responsible for

    _annotation_type = Counter()
    _annotators = {"proportion": None, "cnt": Counter()}
    _no_observations = {"values": [], "mean": None, "std": None}
    _no_observations_unique = {"values": [], "mean": None, "std": None}
    # Observation counts: both absolute (int count) and relative (frequencies)
    _observation_cnt_all_abs = Counter()
    _observation_cnt_all_rel = Counter()  # to divide by __no_annotations
    _observation_cnt_norep_abs = Counter()
    _observation_cnt_norep_rel = Counter()  # to divide by __no_annotations
    # Observation pattern counts: again, both absolute and relative
    _observation_cnt_2g_abs = Counter()
    _observation_cnt_2g_rel = Counter()  # to divide by __no_annotations
    _observation_cnt_3g_abs = Counter()
    _observation_cnt_3g_rel = Counter()  # to divide by __no_annotations
    _observation_cnt_4g_abs = Counter()
    _observation_cnt_4g_rel = Counter()  # to divide by __no_annotations
    # Duration statistics: separated between audio and score types
    _observation_dur_avgs = {
        "audio": {"values": [], "mean": None, "std": None},
        "score": {"values": [], "mean": None, "std": None},
    }

    def __init__(self, namespace:str) -> None:
        """
        Create a `ChoCoAnnotationStats` for a specific JAMS namespace.

        Parameters
        ----------
        namespace : str
            The name of the JAMS namespace this extractor is responsible for.

        """
        self.namespace = namespace
    

    def process_annotation_stats(self, annotation_stats:dict, jams_type:str):
        """
        Process annotations stats to update the accumulated counts. Overall,
        stats are not consistent until they are closed and aggregated.

        Parameters
        ----------
        annotation_stats : dict
            A dictionary containing the stats for a single annotation.
        jams_type : str
            Type of the annotated musical content, either `score` or `audio`.

        """
        if self.__state > StatsExtractorState.COMPUTED:
            raise InvalidStatsExtractorState("Cannot process new entries now!")
        if annotation_stats["namespace"] != self.__namespace:
            raise ValueError(f"This extractor processes {self.__namespace} but "
                             f"namespace {annotation_stats['namespace']} found.")
        if jams_type not in ["audio", "score"]:  # check annotated content
            raise ValueError(f"Unsupported JAMS type: {jams_type}")

        self._annotation_type.update([annotation_stats["ann_type"]])
        self._annotators["cnt"].update(annotation_stats["annotator"])
        self._no_observations["values"].append(
            annotation_stats["observations"])
        self._no_observations_unique["values"].append(
            annotation_stats["observation_set"])
        
        self._observation_cnt_all_abs.update(
            annotation_stats["observation_cnt_all"])
        self._observation_cnt_all_abs.update(
            to_freq(annotation_stats["observation_cnt_all"]))
        self._observation_cnt_norep_abs.update(
            annotation_stats["observation_cnt_norep"])
        self._observation_cnt_norep_rel.update(
            to_freq(annotation_stats["observation_cnt_norep"]))

        self._observation_cnt_2g_abs.update(
            annotation_stats["observation_n2g"])
        self._observation_cnt_2g_rel.update(
            to_freq(annotation_stats["observation_n2g"]))
        self._observation_cnt_3g_abs.update(
            annotation_stats["observation_n3g"])
        self._observation_cnt_3g_rel.update(
            to_freq(annotation_stats["observation_n3g"]))
        self._observation_cnt_4g_abs.update(
            annotation_stats["observation_n4g"])
        self._observation_cnt_4g_rel.update(
            to_freq(annotation_stats["observation_n4g"]))

        self._observation_dur_avgs[jams_type]["values"]\
            .append(annotation_stats["observation_duration_avg"])
        self.__no_annotations += 1  # ideally should execute as transaction
        self.__state = StatsExtractorState.COMPUTED  # redundant but useful


    def aggregate_annotation_stats(self):
        """
        Aggregate all the annotation statistics, so that they can be returned.
        This assumes that no new annotation will be processed, otherwise the
        aggregates would not be consistent.

        """
        if self.__state < StatsExtractorState.COMPUTED:
            raise InvalidStatsExtractorState("Too early to perform aggregation!")
        elif self.__state >= StatsExtractorState.AGGREGATED:
            logger.info("Annotation statistics have already been aggregated!")
            return  # no need to recompute stats, they are cached
        
        with_annotators = sum([c for name, c in self._annotators["cnt"].items()
                               if name != "Unknown"])  # no. of real annotators
        self._annotators["proportion"] = with_annotators / self.__no_annotations

        self._no_observations["mean"] = np.mean(
            self._no_observations["values"])
        self._no_observations["std"] = np.std(
            self._no_observations["values"])
        self._no_observations_unique["mean"] = np.mean(
            self._no_observations_unique["values"])
        self._no_observations_unique["std"] = np.std(
            self._no_observations_unique["values"])

        self._observation_cnt_all_rel = to_freq(
            self._observation_cnt_all_rel, occurrences=self.__no_annotations)
        self._observation_cnt_norep_rel = to_freq(
            self._observation_cnt_norep_rel, occurrences=self.__no_annotations)

        self._observation_cnt_2g_rel = to_freq(
            self._observation_cnt_2g_rel, occurrences=self.__no_annotations)
        self._observation_cnt_3g_rel = to_freq(
            self._observation_cnt_3g_rel, occurrences=self.__no_annotations)
        self._observation_cnt_4g_rel = to_freq(
            self._observation_cnt_4g_rel, occurrences=self.__no_annotations)

        for jtype in ["audio", "score"]:
            self._observation_dur_avgs[jtype]["mean"] = np.mean(
                self._observation_dur_avgs[jtype]["values"])
            self._observation_dur_avgs[jtype]["std"] = np.std(
                self._observation_dur_avgs[jtype]["values"])
        
        self.__state = StatsExtractorState.AGGREGATED


class ChoCoDatasetStats(object):

    __state = StatsExtractorState.CREATED
    __namespaces = None  # either 'all' or a list of valid namespaces
    __no_jams, __no_annotations = 0, 0  # JAMS and annotations encountered
    # General metadata-level statistics -------------------------------------- |
    _identifiers = {"sum": 0, "proportion": None, "cnt": Counter()}
    _durations = {
        "audio": {"values": [], "mean": None, "std": None},
        "score": {"values": [], "mean": None, "std": None}}
    _composers = {"sum": 0, "proportion": None, "cnt": Counter()}
    _performers = {"sum": 0, "proportion": None, "cnt": Counter()}
    # Content-level statistics ----------------------------------------------- |
    _annotation_stats_ext = {}  # holding a ChoCoAnnotationStats per namespace

    def __init__(self, namespaces:list="all") -> None:
        """
        Create a stats extractor for a ChoCo dataset: processing and aggregating
        stats at the metadata and content level.

        Parameters
        ----------
        namespaces : list, optional
           List of namespaces to track for stats, by default "all".

        """
        self.__namespaces = namespaces
        if namespaces != "all": # can create them now
            for ns in namespaces:  # namespace-wise extractor
                self._annotation_stats_ext[ns] = ChoCoAnnotationStats(ns)


    def process_jams_stats(self, jams_stats:dict):
        """
        Update the current statistics with the given record.

        Parameters
        ----------
        jams_stats : dict
            Compact descriptor of the stats extracted from a single JAMS.

        """
        if self.__state > StatsExtractorState.COMPUTED:
            raise InvalidStatsExtractorState("Cannot process new entries now!")
        
        # Identifiers: number, counter per service/website
        if len(jams_stats["identifiers"]) > 0:  # just to say that we have them
            self._identifiers["sum"] += 1  
        self._identifiers["cnt"].update(jams_stats["identifiers"])
        # Composers: number, set, proportion for JAMS, top-10
        if len(jams_stats["composers"]) > 0:
            self._composers["sum"] += 1
        self._composers["cnt"].update(jams_stats["composers"])
        # Performers: number, set, proportion for JAMS, top-10
        if len(jams_stats["performers"]) > 0:
            self._performers["sum"] += 1
        self._performers["cnt"].update(jams_stats["performers"])
        # No. of annotations: count is enough (mostly 2 expected)
        self.__no_annotations += len(jams_stats["annotations"])
        self._durations[jams_stats["type"]]["values"]\
            .append(jams_stats["duration"])  # audio-score dur

        for annotation_stats in jams_stats["annotations"]:
            ns = jams_stats["namespace"]  # the namespace of this annotation
            if self.__namespaces == "all" and ns not in self._annotation_stats_ext:
                self._annotation_stats_ext[ns] = ChoCoAnnotationStats(ns)
            if ns in self.__namespaces:   # safe to proceed with stats ext
                self._annotation_stats_ext[ns].process_annotation_stats(
                    annotation_stats, jams_type=jams_stats["type"])

        self.__no_jams += 1  # ideally run as a transaction
        self.__state = StatsExtractorState.COMPUTED  # redundant but useful


    def aggregate_dataset_stats(self):
        """
        Aggregate all the annotation coming from the different JAMS, so that
        they can be consulted. No new jams stats can be processed thereafter.
        """
        if self.__state < StatsExtractorState.COMPUTED:
            raise InvalidStatsExtractorState("Too early to perform aggregation!")
        elif self.__state >= StatsExtractorState.AGGREGATED:
            logger.info("JAMS dataset statistics have already been aggregated!")
            return  # no need to recompute stats, they are cached

        self._identifiers["proportion"] = self._identifiers["sum"] / self.__no_jams
        self._composers["proportion"] = self._composers["sum"] / self.__no_jams
        self._performers["proportion"] = self._performers["sum"] / self.__no_jams
        # Aggreagation of durations per JAMS type
        for jtype in ["audio", "score"]:
            self._durations[jtype]["mean"] = np.mean(
                self._durations[jtype]["values"])
            self._durations[jtype]["std"] = np.std(
                self._durations[jtype]["values"])

        for namespace, ann_stats_ext in self._annotation_stats_ext.items():
            logger.info(f"Aggregating annotation stats for {namespace}")
            ann_stats_ext.aggregate_annotation_stats()

        self.__state = StatsExtractorState.AGGREGATED


def combine_jams_stats(annotation_stats:List[dict], namespaces:list="all",
    out_dir:str=None):

    dataset_stats = ChoCoDatasetStats(namespaces=namespaces)

    for jams_stats in tqdm(annotation_stats):
        dataset_stats.process_jams_stats(jams_stats)
    dataset_stats.aggregate_dataset_stats()

    if out_dir:
        out_fname = os.path.join(out_dir, "dataset_stats.joblib")
        with open(out_fname, 'wb') as jobfile:
            joblib.dump(dataset_stats, jobfile)
    
    return dataset_stats

        
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