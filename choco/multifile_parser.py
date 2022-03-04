"""
Utilities for parsing multiple annotation files and returning a single JAMS
file containing the all the different annotations in specific namespaces.
Currently works for Schubert, but can be easily adapted/generalised.

Notes
    - This code will be generalised, re-organised and improved for reuse!
    - Some annotations are not supported in JAMS, and should be added (e.g.
        measure-bar annotations are not supported at the current time).
"""
import os
import glob
import json

import jams
import pandas as pd
import numpy as np


rawdata_dir = "../raw/"
metadata_dir = "../metadata/"
annotations_dir = "../annotations/"

schubert_raw = os.path.join(rawdata_dir, "schubert-winterreise/02_Annotations/")

# TODO Possibility of specifying a list of folders for each of these namespaces
# --- each of them will be considered as produced by a different annotator
format = "score"  # score or audio
namespace_dirs = {
    "chord": os.path.join(schubert_raw, f"ann_{format}_chord"),
    "segment_open": os.path.join(schubert_raw, f"ann_{format}_structure"),
    #"measure": os.path.join(schubert_raw, "ann_audio_measure")
}

# This is in case each annotation file provides multiple annotation formats
# -- which we will put into the corresponding separate namespaces.
# FIXME Should be generalised and used as a map for renaming columns in general.
namespace_mapping = {
    "shorthand": "chord_harte",
    "extended": "chord"
}

ignore_namespaces = ["majmin", "majmin_inv"]  # a list of namespaces that will be ignored

jams_dir = annotations_dir + "schubert-winterreise/" # TODO Create dir if it does not exist
# TODO Metadata that can be used to append information within each JAMS file (syntactic sugar)
metadata = os.path.join(rawdata_dir, "schubert-winterreise/", "03_ExtraMaterial", "ann_audio_meta.csv")

separator = ";"
default_confidence = 1.0



def parse_multiple_annotation_files():
    for outer_namespace, outer_namespace_dir  in namespace_dirs.items():
        raw_annotations = glob.glob(os.path.join(outer_namespace_dir, "*.csv"))

        for raw_annotation in raw_annotations:  # loopipng through all annotations

            fname = os.path.splitext(os.path.basename(raw_annotation))[0]
            jname = os.path.join(jams_dir, fname + ".jams")
            # Check whether a JAMS file already exists for appending this annotation
            if os.path.exists(jname):  # JAMS file already there to be loaded
                jam = jams.load(jname, strict=False)
            else:  # a fresh new JAMS file will be created
                jam = jams.JAMS()

            annotation_df = pd.read_csv(raw_annotation, sep=separator)
            # Renaming columns to match the namespace for the JAMS file
            annotation_df = annotation_df.rename(columns=namespace_mapping)
            # Check whether duration should be inferred from offsets or nullified
            if "end" in annotation_df.columns and "duration" not in annotation_df.columns:
                annotation_df["duration"] = annotation_df["end"] - annotation_df["start"]
            elif "end" not in annotation_df.columns:  # duration is assumed as null
                annotation_df["duration"] = 0.0
            # Check whether confidence is not provided and should be defaulted
            if "confidence" not in annotation_df.columns:
                annotation_df["confidence"] = default_confidence
            
            inner_namespaces = [cname for cname in annotation_df.columns
                if cname not in ["start", "end", "duration", "confidence"]]
            if len(inner_namespaces) == 1:  # make sure that it takes the namespace
                annotation_df = annotation_df.rename(
                    columns={inner_namespaces[0]: outer_namespace})
                inner_namespaces = [outer_namespace]
            inner_namespaces = [namespace for namespace in inner_namespaces \
                if namespace not in ignore_namespaces]
            
            for namespace in inner_namespaces:
                # Create the annotation space for the current level
                annotation = jams.Annotation(namespace=namespace)
                # Selecting the portion of the dataframe containing this annotation
                format_annotation_df = annotation_df[
                    ["start", "duration", "confidence", namespace]]
                # Append each observation in the dataframe to the annotation
                for _, row in format_annotation_df.iterrows():  # okay for short dataframes
                    annotation.append(
                        time=row["start"], duration=row["duration"],
                        value=row[namespace], confidence=row["confidence"])
                # Store the new annotation level in the jam
                jam.annotations.append(annotation)

            # Infer the track duration based on the last annotation
            # TODO (or retrieve it from a metadata specification)
            
            # Save the annotation to disk
            jam.save(jname, strict=False)  # either write or overwrite FIXME