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
from utils import to_freq, stringify_dict

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


def safe_stats(values:list):
    """Returns mean and standard deviation if listed values are not empty."""
    values_filtered = [v for v in values if v is not None]
    return (np.mean(values_filtered), np.std(values_filtered)) \
        if len(values_filtered) > 0 else (None, None)


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
        if "name" not in annotation_meta.annotator \
             or annotation_meta.annotator.name == "" \
        else annotation_meta.annotator.name
    annotation_dict["observations"] = len(annotation.data)

    annotation_data = [(o.time, o.duration, o.value, o.confidence) \
                        for o in annotation.data]
    durations = list(map(lambda x: x[1], annotation_data))
    values_all = list(map(lambda x: x[2], annotation_data))

    if len(values_all) > 0 and isinstance(values_all[0], dict):
        values_all = [stringify_dict(v, sep="_") for v in values_all]
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


def compute_jams_stats(jam:Union[str, jams.JAMS]):
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
    def __init__(self, namespace:str) -> None:
        """
        Create a `ChoCoAnnotationStats` for a specific JAMS namespace.

        Parameters
        ----------
        namespace : str
            The name of the JAMS namespace this extractor is responsible for.

        """
        self.__state = StatsExtractorState.CREATED
        self.__namespace = namespace
        self.__no_annotations = 0  # number of annotation processed so far

        self._annotation_type = Counter()
        self._annotators = {"proportion": None, "cnt": Counter()}
        self._no_observations = {"values": [], "mean": None, "std": None}
        self._no_observations_uniq = {"values": [], "mean": None, "std": None}
        # Observation counts: both absolute (int) and relative (frequencies),
        # where the latter are then divided by __no_annotations at aggregation.
        self._observation_cnt_all_abs = Counter()
        self._observation_cnt_all_rel = Counter()
        self._observation_cnt_norep_abs = Counter()
        self._observation_cnt_norep_rel = Counter()
        # Observation pattern counts: again, both absolute and relative
        self._observation_cnt_2g_abs = Counter()
        self._observation_cnt_2g_rel = Counter()
        self._observation_cnt_3g_abs = Counter()
        self._observation_cnt_3g_rel = Counter()
        self._observation_cnt_4g_abs = Counter()
        self._observation_cnt_4g_rel = Counter()
        # Duration statistics: separated between audio and score types
        self._observation_dur_avgs = {
            "audio": {"values": [], "mean": None, "std": None},
            "score": {"values": [], "mean": None, "std": None},
        }

    @property
    def no_processed_elements(self):
        return self.__no_annotations
    

    def update_annotation_stats(self, choco_annotation_stats):
        """
        Updates the current object with the statistics collected from another
        annotation object, which can potentially have a different namespace.

        Parameters
        ----------
        choco_annotation_stats : ChoCoAnnotationStats
            Another ChoCo annotation stats object that will be merged.

        """
        if choco_annotation_stats.__namespace != self.__namespace:
            logger.warning("Merging stats from different namespace: expected "
                           f"namespace {self.__namespace} (this object) but "
                           f"{choco_annotation_stats.__namespace} was found!")
        # Aggregate number of annotation and annotation types
        self.__no_annotations += choco_annotation_stats.__no_annotations
        self._annotation_type.update(choco_annotation_stats._annotation_type)

        self._annotators["cnt"].update(
            choco_annotation_stats._annotators["cnt"])
        self._no_observations["values"] += \
            choco_annotation_stats._no_observations["values"]
        self._no_observations_uniq["values"] += \
            choco_annotation_stats._no_observations_uniq["values"]
        # Updating observation counts: absolute (int) and relative (frequencies)
        self._observation_cnt_all_abs.update(
            choco_annotation_stats._observation_cnt_all_abs)
        self._observation_cnt_all_rel.update(
            choco_annotation_stats._observation_cnt_all_rel)
        self._observation_cnt_norep_abs.update(
            choco_annotation_stats._observation_cnt_norep_abs)
        self._observation_cnt_norep_rel.update(
            choco_annotation_stats._observation_cnt_norep_rel)
        # Observation pattern counts: again, both absolute and relative
        self._observation_cnt_2g_abs.update(
            choco_annotation_stats._observation_cnt_2g_abs)
        self._observation_cnt_2g_rel.update(
            choco_annotation_stats._observation_cnt_2g_rel)
        self._observation_cnt_3g_abs.update(
            choco_annotation_stats._observation_cnt_3g_abs)
        self._observation_cnt_3g_rel.update(
            choco_annotation_stats._observation_cnt_3g_rel)
        self._observation_cnt_4g_abs.update(
            choco_annotation_stats._observation_cnt_4g_abs)
        self._observation_cnt_4g_rel.update(
            choco_annotation_stats._observation_cnt_4g_rel)
        # Duration statistics: separated between audio and score types
        self._observation_dur_avgs["audio"]["values"] += \
            choco_annotation_stats._observation_dur_avgs["audio"]["values"]
        self._observation_dur_avgs["score"]["values"] += \
            choco_annotation_stats._observation_dur_avgs["score"]["values"]
        # Re-agrgeagte the statistics, if this was done before
        if self.__state == StatsExtractorState.AGGREGATED:
            logger.info("Re-aggregating statistics after merge.")
            self.__state = StatsExtractorState.COMPUTED  # revert state
            self.aggregate_annotation_stats()  # recompute aggregation


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
        if self.__state.value > StatsExtractorState.COMPUTED.value:
            raise InvalidStatsExtractorState("Cannot process new entries now!")
        if annotation_stats["namespace"] != self.__namespace:
            raise ValueError(f"This extractor processes {self.__namespace} but "
                             f"namespace {annotation_stats['namespace']} found.")
        if jams_type not in ["audio", "score"]:  # check annotated content
            raise ValueError(f"Unsupported JAMS type: {jams_type}")

        self._annotation_type.update([annotation_stats["ann_type"]])
        self._annotators["cnt"].update([annotation_stats["annotator"]])
        self._no_observations["values"].append(
            annotation_stats["observations"])
        self._no_observations_uniq["values"].append(
            annotation_stats["observation_set"])

        self._observation_cnt_all_abs.update(
            annotation_stats["observation_cnt_all"])
        self._observation_cnt_all_rel.update(
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
        if self.__state.value < StatsExtractorState.COMPUTED.value:
            raise InvalidStatsExtractorState("Too early to perform aggregation!")
        elif self.__state.value >= StatsExtractorState.AGGREGATED.value:
            logger.info("Annotation statistics have already been aggregated!")
            return  # no need to recompute stats, they are cached
        
        with_annotators = sum([c for name, c in self._annotators["cnt"].items()
                               if name != "Unknown"])  # no. of real annotators
        self._annotators["proportion"] = with_annotators / self.__no_annotations

        self._no_observations["mean"], self._no_observations["std"] = \
            safe_stats(self._no_observations["values"])
        self._no_observations_uniq["mean"], self._no_observations_uniq["std"] = \
            safe_stats(self._no_observations_uniq["values"])

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
            self._observation_dur_avgs[jtype]["mean"], \
            self._observation_dur_avgs[jtype]["std"] = \
                safe_stats(self._observation_dur_avgs[jtype]["values"])

        self.__state = StatsExtractorState.AGGREGATED


class ChoCoDatasetStats(object):

    def __init__(self, namespaces:list="all") -> None:
        """
        Create a stats extractor for a ChoCo dataset: processing and aggregating
        stats at the metadata and content level.

        Parameters
        ----------
        namespaces : list, optional
           List of namespaces to track for stats, by default "all".

        """
        self.__state = StatsExtractorState.CREATED
        self.__namespaces = namespaces

        self._annotation_stats_ext = {ns: ChoCoAnnotationStats(ns) \
            for ns in namespaces} if namespaces != "all" else {}

        self.__no_jams, self.__no_annotations = 0, 0  # JAMS/anns encountered
        # General metadata-level statistics ---------------------------------- |
        self._identifiers = {"sum": 0, "proportion": None, "cnt": Counter()}
        self._durations = {
            "audio": {"values": [], "mean": None, "std": None},
            "score": {"values": [], "mean": None, "std": None}}
        self._composers = {"sum": 0, "proportion": None, "cnt": Counter()}
        self._performers = {"sum": 0, "proportion": None, "cnt": Counter()}


    @property
    def no_processed_elements(self):
        return self.__no_jams, self.__no_annotations


    def process_jams_stats(self, jams_stats:dict):
        """
        Update the current statistics with the given record.

        Parameters
        ----------
        jams_stats : dict
            Compact descriptor of the stats extracted from a single JAMS.

        """
        if self.__state.value > StatsExtractorState.COMPUTED.value:
            raise InvalidStatsExtractorState("Cannot process new entries now!")
        
        # Identifiers: number, counter per service/website
        if len(jams_stats["identifiers"]) > 0:  # just to say that we have them
            self._identifiers["sum"] += 1
        self._identifiers["cnt"].update(list(jams_stats["identifiers"].keys()))
        # Composers: number, set, proportion for JAMS, top-10
        composers = jams_stats["composers"] \
            if jams_stats["composers"] is not None else []
        if composers is not None and len(composers) > 0:
            self._composers["sum"] += 1
        self._composers["cnt"].update(composers)
        # Performers: number, set, proportion for JAMS, top-10
        performers = jams_stats["performers"] \
            if jams_stats["performers"] is not None else []
        if performers is not None and len(performers) > 0:
            self._performers["sum"] += 1
        self._performers["cnt"].update(performers)
        # No. of annotations: count is enough (mostly 2 expected)
        self.__no_annotations += len(jams_stats["annotations"])
        self._durations[jams_stats["type"]]["values"]\
            .append(jams_stats["duration"])  # audio-score dur

        for annotation_stats in jams_stats["annotations"]:
            ns = annotation_stats["namespace"]  # namespace of this annotation
            if self.__namespaces == "all" and ns not in self._annotation_stats_ext:
                # Create a new annotation stats extractor for this new ns
                self._annotation_stats_ext[ns] = ChoCoAnnotationStats(ns)
            if ns in self._annotation_stats_ext:   # safe to proceed now
                self._annotation_stats_ext[ns].process_annotation_stats(
                    annotation_stats, jams_type=jams_stats["type"])

        self.__no_jams += 1  # ideally run as a transaction
        self.__state = StatsExtractorState.COMPUTED  # redundant but useful


    def aggregate_dataset_stats(self):
        """
        Aggregate all the annotation coming from the different JAMS, so that
        they can be consulted. No new jams stats can be processed thereafter.
        """
        if self.__state.value < StatsExtractorState.COMPUTED.value:
            raise InvalidStatsExtractorState("Too early to perform aggregation!")
        elif self.__state.value >= StatsExtractorState.AGGREGATED.value:
            logger.info("JAMS dataset statistics have already been aggregated!")
            return  # no need to recompute stats, they are cached

        self._identifiers["proportion"] = self._identifiers["sum"] / self.__no_jams
        self._composers["proportion"] = self._composers["sum"] / self.__no_jams
        self._performers["proportion"] = self._performers["sum"] / self.__no_jams
        for jtype in ["audio", "score"]:  # aggreagation of durations per type
            self._durations[jtype]["mean"], self._durations[jtype]["std"] = \
                safe_stats(self._durations[jtype]["values"])

        for namespace, ann_stats_ext in self._annotation_stats_ext.items():
            logger.info(f"Aggregating annotation stats for {namespace}")
            ann_stats_ext.aggregate_annotation_stats()

        self.__state = StatsExtractorState.AGGREGATED


def combine_jams_stats(jams_stats:List[dict], namespaces:list="all",
    out_dir:str=None):
    """
    Compute and aggregate stats from a custom ChoCo JAMS dataset. This assumes
    that JAMS-specific stats have been already extracted individually for each
    JAMS file -- as this function operates at the dataset level.

    Parameters
    ----------
    jams_stats : List[dict]
        List of dict-ed stats extracted from each JAMS file.
    namespaces : list, optional
        Annotation namespaces on which the stats extraction will focus.
    out_dir : str, optional
        Path to a directory where the dataset stats will be dumped.

    Returns
    -------
    dataset_sets : ChoCoDatasetStats
        A dataset stats object, encapsulating all the metadata and content stats
        of the collection under analysis, and for the namespaces required.
    
    See also
    --------
    `extract_annotation_stats()`, `ChoCoDatasetStats`

    """
    dataset_stats = ChoCoDatasetStats(namespaces=namespaces)
    for jams_stats in tqdm(jams_stats):  # iterates JAMS-stats
        dataset_stats.process_jams_stats(jams_stats)
    dataset_stats.aggregate_dataset_stats()

    if out_dir:  # dumping stats object to disk, if required
        out_fname = os.path.join(out_dir, "dataset_stats.joblib")
        with open(out_fname, 'wb') as jobfile:
            joblib.dump(dataset_stats, jobfile)

    return dataset_stats


def extract_jams_stats(dataset_dir, out_dir=None, n_jobs=1):
    """
    Independently compute meta- and content- level stats from all the JAMS files
    found in the given directory. Extraction can be performed in parallel, then
    recombined in a single list containing the stats for each JAMS.

    Parameters
    ----------
    dataset_dir : str
        Path to the directory containing the JAMS files to process.
    out_dir : str, optional
        Path to the directory where stats will be saved, if required.
    n_jobs : int, optional
        Number of threads for parallel execution, by default 1.

    Returns
    -------
    jams_stats : list
        A list of JAMS stats for each file, as dictionaries.

    See also
    --------
    `compute_jams_stats()`

    """
    # Extracting JAMS statistics: in parallel
    jams_files = glob.glob(os.path.join(dataset_dir, "*.jams"))
    print(f"Found {len(jams_files)} in {dataset_dir}")
    jams_stats = Parallel(n_jobs=n_jobs)\
        (delayed(compute_jams_stats)(jam) for jam in tqdm(jams_files))

    if out_dir:  # save list of stats in a joblib file for later aggregation
        out_fname = os.path.join(out_dir, "jams_stats.joblib")
        with open(out_fname, 'wb') as jobfile:
            joblib.dump(jams_stats, jobfile)
        out_fsize = round(os.path.getsize(out_fname) / 1e6, 2)  # file size (MB)
        print(f"Done! JAMS stats written in {out_fname} ({out_fsize}MB)")

    return jams_stats



def main():
    """
    Main function implements a simmle CLI for dataset stats extraction.

    Examples
    --------
    ```
    python jams_stats.py extract ../partitions/isophonics/choco/jams \
        --out_dir ../partitions/isophonics/choco --n_workers 4
    ```
    """
    COMMANDS = ["extract", "aggregate", "plot"]

    parser = argparse.ArgumentParser(
        description='Simple extractor of chord stats from JAMS files.')
    parser.add_argument('cmd', type=str, choices=COMMANDS,
                        help=f"Either {', '.join(COMMANDS)}.")

    parser.add_argument('dataset', type=str,
                        help='Directory where JAMS files will be read, or path '
                             'to the JAMS stats previously generated')

    parser.add_argument('--namespaces', type=list,
                        help='A list of namespaces to consider for aggregation; '
                             'if not provided, all namespaces will be used.')

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
        args.out_dir = os.path.dirname(args.dataset)
    
    if args.cmd == "extract":
        print(f"Extracting JAMS statistics from {args.dataset}")
        extract_jams_stats(
            dataset_dir=args.dataset,
            out_dir=args.out_dir,
            n_jobs=args.n_workers,
        )
    elif args.cmd == "aggregate":
        print(f"Aggregating JAMS statistics from {args.dataset}")
        # First read/load the joblib file containing the JAMS stats
        with open(args.dataset, 'rb') as jobfile:
            jams_stats = joblib.load(jobfile)
        # Ready to combine the JAMS stats as per requirements
        combine_jams_stats(
            jams_stats=jams_stats,
            namespaces="all" if args.namespaces is None else args.namespaces,
            out_dir=args.out_dir,
        )
    else:  # trivially, args.cmd == "plot":
        raise NotImplementedError("Plotting not yet available!")


if __name__ == "__main__":
    main()