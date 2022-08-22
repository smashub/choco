"""
Utilities for parsing multiple annotation files and returning a single JAMS file
containing all the different annotations in specific namespaces.

Notes
-----
    - Generalise the textual tags for column names in the textual continuous
        annotations (e.g. 'end') as similarly done for the identification
        query in the summative annotations.

"""
import os
import sys
import glob
import logging

import jams
import pandas as pd

sys.path.append(os.path.dirname(os.getcwd()))

logger = logging.getLogger("choco.parsers.multifile_parser")


def process_summative_annotation(summative_anns, namespace_mapping, sum_query,
    jams_tmp=None, duration=None, sep=";", confidence=1.):
    """
    
    Parameters
    ----------
    summative_anns : str or pandas.DataFrame
        ...
    namespace_mapping : dict
        A mapping from global annotation fields in the file (e.g. "key") to
        annotation namespaces in JAMS ("key_mode"). Note that only the mapped
        fields will be parsed as independent global annotations.
    sum_query : dict
        As a summative file provides global annotations for several pieces, a
        query is needed to retrieve the desired entity. The query is given as
        a dictionary, e.g. {"FieldA": "id_001", "FieldB": "sub_id_003"}.
    jams_tmp : jams.JAMS
        A JAMS object that will be extended with the given annotation. If this
        is not provided, a new will be created as long as the full duration of
        the track/score is explicitly specified (for the global annotation).
    duration : float
        Duration of the score/track which is necessary to define the global ann.
    sep : str
        The separator to consider for the raw text files to read.
    default_confidence : float
        A float in (0, 1] indicating the confidence/reliability of annotations.
    """
    if not isinstance(summative_anns, pd.DataFrame):
        summative_anns = pd.read_csv(summative_anns, sep=sep)
    if jams_tmp is None:
        jams_tmp = jams.JAMS()  # new JAMS created
        jams_tmp.file_metadata.duration = duration

    summative_anns = summative_anns.rename(columns=namespace_mapping)
    # Construct the query to identify the specific entry to retrieve
    q = " & ".join([f"{field}=='{val}'" for field, val in sum_query.items()])
    annotation_row = summative_anns.query(q)  # search the piece-specific ann
    if len(annotation_row) != 1:  # bad search
        raise ValueError(f"{len(annotation_row)} entries found for query: {q}")
    # annotation_row = annotation_row.to_dict()

    namespaces = [n for n in namespace_mapping.values() if n in annotation_row]
    for namespace in namespaces:  # only mapped-namespaces will be added
        annotation = jams.Annotation(namespace=namespace)
        annotation.append(
            time=0, duration=jams_tmp.file_metadata.duration,
            value=annotation_row[namespace].values[0], confidence=confidence)
        # Store the new annotation level in the jam
        jams_tmp.annotations.append(annotation)

    return jams_tmp


def process_text_annotation(annotation_file, namespace_mapping, jams_tmp=None,
    ignore_annotations=[], sep=";", confidence=1.):
    """
    
    Parameters
    ----------
    annotation_file : str
        ...
    namespace_mapping : dict
        A dictionary mapping dataset-specific annotation names to actual JAMS
        namespaces (e.g. shorthand to chord_harte).
    jams_tmp : jams.JAMS
        An optional JAMS object that will be extended with the given annotation;
        if no JAMS is provided, a new one will be created and returned.
    ignore_annotations : list
        A list of annotations that should not be converted into a namespace.
    sep : str
        The separator to consider for the raw text files to read.
    default_confidence : float
        A float in (0, 1] indicating the confidence/reliability of annotations.

    Returns
    -------
    jam : jams.JAMS
        The JAMS object that includes the given annotation.

    """
    # Create a fresh new JAMS object if this is the first annotation
    jam = jams.JAMS() if jams_tmp is None else jams_tmp

    annotation_df = pd.read_csv(annotation_file, sep=sep)
    # Renaming columns to match the namespace for the JAMS file
    annotation_df = annotation_df.rename(columns=namespace_mapping)
    # Check whether duration should be inferred from offsets or nullified
    if "end" in annotation_df.columns and "duration" not in annotation_df.columns:
        annotation_df["duration"] = annotation_df["end"] - annotation_df["start"]
    elif "end" not in annotation_df.columns:  # duration is assumed as null
        annotation_df["duration"] = 0.0
    # Check whether confidence is not provided and should be defaulted
    if "confidence" not in annotation_df.columns:
        annotation_df["confidence"] = confidence
    
    inner_namespaces = [cname for cname in annotation_df.columns
        if cname not in ["start", "end", "duration", "confidence"]]
    inner_namespaces = [namespace for namespace in inner_namespaces \
        if namespace not in ignore_annotations]

    for namespace in inner_namespaces:
        # Create the annotation space for the current level
        annotation = jams.Annotation(namespace=namespace)
        # Selecting the portion of the dataframe containing this annotation
        format_annotation_df = annotation_df[
            ["start", "duration", "confidence", namespace]]
        # Append each observation in the dataframe to the annotation
        for _, row in format_annotation_df.iterrows():
            annotation.append(
                time=row["start"], duration=row["duration"],
                value=row[namespace], confidence=row["confidence"])
        # Store the new annotation level in the jam
        jam.annotations.append(annotation)

    return jam


def process_text_annotation_multi(namespace_sources, namespace_mapping,
    sum_query=None, ignore_annotations=[], sep=";", duration=None, confidence=1.):
    """
    Parse annotation data from different sources (fodlers, files) containing
    music annotations of different properties but related to the same pieces.

    Parameters
    ----------
    namespace_sources : dict
        A mapping from general annotation namespaces (e.g. chord, segment) to a
        list of file paths (at least one) providing annotations for the specific
        namespace they are associated with, or a static summative file from
        which the piece-specific entry needs to be retrieved. Please, note that
        a summative annotation is expected to be a global annotation, hence it
        will span for all the duration of the piece.
    namespace_mapping : dict
        A dictionary mapping dataset-specific annotation names to actual JAMS
        namespaces (e.g. shorthand to chord_harte).
    ignore_annotations : list
        A list of annotations that should not be converted into a namespace.
    sep : str
        The separator to consider for the raw text files to read.
    default_confidence : float
        A float in (0, 1] indicating the confidence/reliability of annotations.

    Returns
    -------
    jam : jams.JAMS
        The JAMS object wrapping all the annotations retrieved from given files.

    Notes
    -----
        - For the implementation of the summative feature inclusion, we need to
            ask: which identifier for the piece should be considered, and the
            specific column to use as ID.

    """
    jam = jams.JAMS()  # start creating the JAMS file
    jam.file_metadata.duration = duration  # needed for summative annotations

    for general_namespace, annotation_files in namespace_sources.items():
        # Check whether the annotation is summative or not
        if isinstance(annotation_files, str):
            jam = process_summative_annotation(
                annotation_files, namespace_mapping, sum_query,
                jams_tmp=jam, sep=sep, confidence=confidence
            )
        elif isinstance(annotation_files, list):
            for annotation_file in annotation_files:
                jam = process_text_annotation(
                    annotation_file, namespace_mapping, jams_tmp=jam,
                    ignore_annotations=ignore_annotations,
                    sep=sep, confidence=confidence
                )
    
    return jam


def parse_multiple_annotations_nometa(namespace_sources, namespace_mapping,
    out_dir, ignore_annotations=[], sep=";", confidence=1.):
    """
    Parse annotation data from different sources (folders, files) containing
    music annotations of different properties but related to the same pieces.
    This function does not expect any metadata to guide the parsing process,
    and operates at the dataset level.
    
    Parameters
    ----------
    namespace_sources : dict
        A mapping from annotation namespaces (e.g. chord, segment) to either
        a directory (containing an annotation file per piece), a file (with an
        entry per piece), or a list of the former (when multiple annotators).
    namespace_mapping : dict
        A dictionary mapping dataset-specific annotation names to actual JAMS
        namespaces (e.g. shorthand to chord_harte).
    out_dir : str
        Path to the directory where temporary and final JAMS will be saved.
    ignore_annotations : list
        A list of annotations that should not be converted into a namespace.
    sep : str
        The separator to consider for the raw text files to read.
    confidence : float
        A float in (0, 1] indicating the confidence/reliability of annotations.

    """
    for outer_namespace, outer_namespace_dir  in namespace_sources.items():
        raw_annotations = glob.glob(os.path.join(outer_namespace_dir, "*.csv"))

        for raw_annotation in raw_annotations:  # loopipng through all annotations

            fname = os.path.splitext(os.path.basename(raw_annotation))[0]
            jname = os.path.join(out_dir, fname + ".jams")
            # Check whether a JAMS file already exists for appending this annotation
            if os.path.exists(jname):  # JAMS file already there to be loaded
                jam = jams.load(jname, strict=False)
            else:  # a fresh new JAMS file will be created
                jam = jams.JAMS()

            annotation_df = pd.read_csv(raw_annotation, sep=sep)
            # Renaming columns to match the namespace for the JAMS file
            annotation_df = annotation_df.rename(columns=namespace_mapping)
            # Check whether duration should be inferred from offsets or nullified
            if "end" in annotation_df.columns and "duration" not in annotation_df.columns:
                annotation_df["duration"] = annotation_df["end"] - annotation_df["start"]
            elif "end" not in annotation_df.columns:  # duration is assumed as null
                annotation_df["duration"] = 0.0
            # Check whether confidence is not provided and should be defaulted
            if "confidence" not in annotation_df.columns:
                annotation_df["confidence"] = confidence
            
            inner_namespaces = [cname for cname in annotation_df.columns
                if cname not in ["start", "end", "duration", "confidence"]]
            if len(inner_namespaces) == 1:  # make sure that it takes the namespace
                annotation_df = annotation_df.rename(
                    columns={inner_namespaces[0]: outer_namespace})
                inner_namespaces = [outer_namespace]
            inner_namespaces = [namespace for namespace in inner_namespaces \
                if namespace not in ignore_annotations]
            
            for namespace in inner_namespaces:
                # Create the annotation space for the current level
                annotation = jams.Annotation(namespace=namespace)
                # Selecting the portion of the dataframe containing this annotation
                format_annotation_df = annotation_df[
                    ["start", "duration", "confidence", namespace]]
                # Append each observation in the dataframe to the annotation
                for _, row in format_annotation_df.iterrows():
                    annotation.append(
                        time=row["start"], duration=row["duration"],
                        value=row[namespace], confidence=row["confidence"])
                # Store the new annotation level in the jam
                jam.annotations.append(annotation)

            # Infer the track duration based on the last annotation
            # TODO (or retrieve it from a metadata specification)
            
            # Save the annotation to disk
            jam.save(jname, strict=False)  # either write or overwrite FIXME
