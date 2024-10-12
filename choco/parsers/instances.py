"""
Dataset-specific parsing instances for ChoCo's partitions. Each method provides
utilities to read and process a partition e produce JAMS files and metadata.

"""

import argparse
import glob
import json
import logging
import math
import os
import re
import shutil
import sqlite3 as sql
import sys
from datetime import timedelta
from pathlib import Path

import jams
import music21
import numpy as np
import pandas as pd
from tqdm import tqdm

# from importlib_metadata import version


sys.path.append(os.path.dirname(os.getcwd()))

import jams_score
import jams_utils
import metadata as choco_meta
import namespaces

# from biab_parser import process_biab_cpp
from harm_parser import (
    process_harm_expanded,
    process_harm_json,
    process_multiline_annotation,
)
from ireal_parser import parse_ireal_dataset, parse_ireal_dump
from jamifier import jamify_dcmlab, jamify_m21, jamify_romantext
from jams_score import append_listed_annotation, to_jams_timesignature
from jams_utils import append_metadata
from json_parser import extract_annotations_from_json
from lab_parser import import_xlab
from m21_parser import process_score
from multifile_parser import process_text_annotation_multi
from utils import create_dir, get_files, is_dir, is_file, set_logger

logger = logging.getLogger("choco.parsers.instances")


# **************************************************************************** #
# Wikifonia
# **************************************************************************** #


def parse_wikifonia(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Creates a more readable metadata file based on the main naming convention
    used in the Wikifonia project to identify scores: comma-separated list of
    artists, ' - ' separator, title of the score.

    Parameters
    ----------
    dataset_dir : str
        Path to the Wikifonia folder containing .mxl (and related) raw files.
    out_dir : str
        Path to the output directory where all annotations will be saved.
    dataset : str
        Name of the dataset that will be processed, which will be used for
        the creation of metadata (ids) and within the JAMS files.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A pandas dataframe providing metadata information about each score,
        either retrieved from the file name, and according to Wikifonia's
        conventions, or extracted from the MusicXML files.

    Notes
    -----
        - Saving time signature annotations is still unimplemented; for this,
          we need an additional JAMS namespace, as it is not available now.
        - Handling of exception is not very elegant at this stage.
    """
    metadata_df = []
    json_dir = create_dir(os.path.join(out_dir, "jams"))

    wikifonia_files = glob.glob(os.path.join(dataset_dir, "*"))
    n_files = len(wikifonia_files)  # should be 6672
    tmp_folder = os.path.join(dataset_dir, "tmp")
    os.mkdir(tmp_folder)  # creating temporary directory

    for i, wikifonia_file in enumerate(wikifonia_files):
        logger.info(f"Processing ({i}/{n_files}): {wikifonia_file}")
        # [Step 1] Resolving path name and detecting ext-encoded versions
        mxl_path = wikifonia_file  # path to the actual .mxl file
        fname_base = os.path.basename(wikifonia_file)
        fname, ext = os.path.splitext(fname_base)

        if ext[1:].isnumeric():  # dealing with repeated version
            logger.warn(f"Repeated .X version detected ({ext})")
            mxl_path = os.path.join(tmp_folder, fname)
            shutil.copy(wikifonia_file, mxl_path)
            fname, ext = os.path.splitext(fname)

        assert ext == ".mxl", "Assuming .xml file at this stage"
        # [Step 2] Retrieving basic metadata information from file name
        fname_splitted = fname.split(" - ")  # as per Wikifonia conventions
        if len(fname_splitted) > 2:  # badly formatted file name
            logger.warn(f"Too many string separators ' - 's for {fname}")
            # XXX Temporary fix: assuming former entries to describe authors
            fname_splitted = ",".join(fname_splitted[:-1]), fname_splitted[-1]

        score_meta = {
            "id": f"wikifonia_{i}",
            "file_authors": fname_splitted[0],
            "score_composers": None,
            "file_title": fname_splitted[1],
            "score_title": None,
            "file_path": fname_base,
            "jams_path": None,
        }

        # [Step 3] Process the MusicXML file to extract annotations
        try:  # attempt to extract annotations from the score
            meta, jam = jamify_m21(mxl_path, chord_set="leadsheet")
        except Exception as exception:
            logger.error(
                "Extraction error \t" f" wikifonia_{i} \t {fname_base} \t {exception}"
            )
        else:  # registering annotation/corpus-metadata in the JAMS
            jams_utils.register_annotation_meta(
                jam,
                annotator_type="expert_human",
                annotation_version=1.0,
                dataset_name="Wikifonia",
                curator_name="Ghent University Association",
            )
            # Complementing JAMS metadata in case of empty fields
            if meta["composers"] == None or meta["composers"] == []:
                logger.warn(f"No composer found in {mxl_path}: using file name")
                jam.file_metadata.artist = score_meta["file_authors"]
            if meta["title"] == None or meta["title"].strip() == "":
                logger.warn(f"No title found in {mxl_path}: using file name")
                jam.file_metadata.title = score_meta["file_title"]
            # Keeping track of score-meta even if this is null or empty
            score_meta["score_composers"] = ",".join(meta["composers"])
            score_meta["score_title"] = meta["title"]
            score_meta["jams_path"] = os.path.join(json_dir, f"{dataset_name}_{i}.jams")
            try:  # Attempt to write JAMS in non-validation mode
                jam.save(score_meta["jams_path"], strict=False)
            except Exception as exception:  # JAMS cannot be saved
                logger.error(
                    f"JAMS error \t" f" wikifonia_{i} \t {fname_base} \t {exception}"
                )

        metadata_df.append(score_meta)
    # Remove temporary folder
    shutil.rmtree(tmp_folder)
    # Finalise the metadata dataframe
    wikifonia_meta_df = pd.DataFrame(metadata_df)
    wikifonia_meta_df = wikifonia_meta_df.set_index("id", drop=True)
    wikifonia_meta_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return wikifonia_meta_df


# **************************************************************************** #
# Nottingham
# **************************************************************************** #


def parse_nottingham(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Parse ABC data from a given dataset, produce a JAMS file from each tune and
    create a metadata file to keep track of identifiers and data content.

    Parameters
    ----------
    dataset_dir : str
        Path to the dataset folder containing raw .abc files.
    out_dir : str
        Path to the output directory where all annotations will be saved.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A pandas dataframe providing metadata information about each score.

    """
    metadata_df = []  # will also contain the subset
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    abc_files = glob.glob(os.path.join(dataset_dir, "*.abc"))
    n_files = len(abc_files)  # should be 14
    id_cnt = 0  # account for nested tunes

    for i, abc_file in enumerate(abc_files):
        abc_name = os.path.splitext(os.path.basename(abc_file))[0]
        logger.info(f"Opening library ({i}/{n_files}): {abc_name}")
        # Each ABC file in Nottingham is a library
        abc_opus = music21.converter.parse(abc_file)
        assert isinstance(abc_opus, music21.stream.Opus)
        # Iterating over tunes in the library
        for t, score in enumerate(abc_opus):
            logger.info(f"Processing tune {t} in opus: {abc_name}")
            score_id = f"{dataset_name}_{id_cnt}"  # mint a new id
            score_meta = {
                "id": score_id,
                "subset": abc_name,
                "composers": None,
                "title": None,
                "file_path": abc_file,
                "jams_path": None,
            }
            try:  # attempt to extract annotations from the score
                meta, jam = jamify_m21(score, chord_set="abc")
            except Exception as exception:
                logger.error(
                    "Extraction error \t" f" {score_id} \t {abc_file} \t {exception}"
                )
            else:  # registering annotation/corpus-metadata in the JAMS
                jams_utils.register_annotation_meta(
                    jam,
                    annotator_type="expert_human",
                    annotation_version=1.0,
                    dataset_name="Nottingham Music Database",
                    curator_name="Seymour Shlien",
                    curator_email="seymour.shlien@crc.ca",
                )
                # Saving metadata info for the ChoCo partition file
                score_meta["composers"] = ",".join(meta["composers"])
                score_meta["title"] = meta["title"]
                score_meta["jams_path"] = os.path.join(jams_dir, f"{score_id}.jams")
                try:  # Attempt to write JAMS in non-validation mode
                    jam.save(score_meta["jams_path"], strict=False)
                except Exception as exception:  # JAMS cannot be saved
                    logger.error(f"JAMS error {score_id}:{abc_file} \t {exception}")

            metadata_df.append(score_meta)
            id_cnt += 1

    # Finalise the metadata dataframe
    abc_meta_df = pd.DataFrame(metadata_df)
    abc_meta_df = abc_meta_df.set_index("id", drop=True)
    abc_meta_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return abc_meta_df


# **************************************************************************** #
# Isophonics
# **************************************************************************** #


def parse_isophonics(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Although it is currently isophonics-oriented, this script can generalise
    JAMS datasets that are redistributed without metadata, including different
    naming conventions, and not necessarility providing chord annotations for
    all JAMS. Still, some basic conventions are assumed, such as the rich file
    names as metadata-descriptors as well as the /artist/release organisation.

    Notes
    -----
        - Some artist-specific behaviours are hard-coded at the moment. A
            potential solution is to ask for a config file describing the
            conventions used for organising files; however, even in isophonics,
            these conventions are not entirely followed -- so this would have
            to specified for each artist-release partition, which is crazy!

    """
    id_cnt = 0
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    dataset_artists = [
        indir
        for indir in os.listdir(dataset_dir)
        if os.path.isdir(os.path.join(dataset_dir, indir))
    ]

    for artist in dataset_artists:
        track_sep = "-" if artist in ["The Beatles", "Zweieck"] else " "
        # Focus on the artist-specific folder and find releases
        artist_dir = os.path.join(dataset_dir, artist)
        for root, dirs, files in os.walk(artist_dir):
            jams_files = [f for f in files if f.endswith(".jams")]
            # First check if this is a release folder
            if len(dirs) > 0 and len(jams_files) == 0:
                continue  # nothing to parse
            # Parent directory as release name
            release_name = os.path.basename(root)
            if artist == "The Beatles":
                release_name, _, _ = choco_meta.infer_title_name(
                    release_name, True, number_sep="-", isdir=True
                )

            logger.info(f"Release: {release_name} ({len(jams_files)} files)")
            for jams_file in jams_files:  # JAMS candidates for chord anns

                file_title, track_no, _ = choco_meta.infer_title_name(
                    jams_file, True, number_sep=track_sep
                )

                track_meta = {
                    "id": f"{dataset_name}_{id_cnt}",
                    "file_performer": artist,
                    "file_title": file_title,
                    "file_track": track_no,
                    "file_release": release_name,
                    "file_path": os.path.join(root, jams_file),
                    "file_name": jams_file,
                    "jams_path": None,
                }

                jams_object = jams.load(os.path.join(root, jams_file))
                if jams_utils.has_chords(jams_object):  # check chord namespace
                    new_path = os.path.join(jams_dir, track_meta["id"] + ".jams")
                    new_jams = jams.JAMS(annotations=jams_object.annotations)
                    # Registering the metadata in the JAMS
                    jams_utils.register_jams_meta(
                        new_jams,
                        jam_type="audio",
                        title=file_title,
                        performers=artist,
                        duration=jams_object.file_metadata.duration,
                        release=release_name,
                        track_number=track_no,
                    )
                    jams_utils.register_annotation_meta(
                        new_jams,
                        annotator_type="expert_human",
                        annotation_version=1.0,
                        dataset_name="isophonics",
                        curator_name="Matthias Mauch",
                        curator_email="m.mauch@qmul.ac.uk",
                    )
                    new_jams.save(new_path, strict=False)
                    track_meta["jams_path"] = new_path

                metadata.append(track_meta)
                id_cnt += 1

    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# JAAH
# **************************************************************************** #


def parse_jaah(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Process a JSON dataset that follows the same conventions of JAAH, to create
    JAMS files and metadata from the given content.

    Notes:
        - For a dataset that follows a general "all files in a folder" schema,
            this script is quite clear and re-usable in other contexts.
    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    json_files = glob.glob(os.path.join(dataset_dir, "*.json"))
    logger.info(f"Found {len(json_files)} JSON files in {dataset_dir}")

    for i, json_file in enumerate(json_files):
        # Open JAMS for metadata-extraction only
        with open(json_file, "rb") as infile:
            json_raw = json.loads(infile.read())
        fname = os.path.splitext(os.path.basename(json_file))[0]

        track_meta = {
            "id": f"{dataset_name}_{i}",
            "file_title": fname,
            "track_title": json_raw["title"],
            "track_performer": json_raw["artist"],
            "track_mbid": json_raw["mbid"],
            "file_path": json_file,
            "jams_path": None,
        }

        try:
            jams_object = extract_annotations_from_json(json_file)
        except Exception as exception:
            logger.error(
                f"Extraction error for {fname}" f" ({dataset_name}_{i}) \t {exception}"
            )
            jams_object = None  # do not process this further
        if jams_object is not None:  # save meta and JAMS if not empty
            jams_path = os.path.join(jams_dir, track_meta["id"] + ".jams")
            jams_object.save(jams_path, strict=False)
            track_meta["jams_path"] = jams_path

        metadata.append(track_meta)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Schubert-Winterreise
# **************************************************************************** #

schubert_namespace_mapping = {
    "shorthand": "chord_harte",
    "extended": "chord",
    "structure": "segment_open",
    "key": "key_mode",
}

schubert_ignore_namespaces = ["majmin", "majmin_inv"]


def create_schubert_metadata(release_meta, audio_meta, score_meta, sep=";"):
    """
    Pre-process Schubert Winterreise's metadata and creates a single file
    encoding both data structures, that can be used to find and retrieve
    annotations according to the conventions of the creators.

    Parameters
    ----------
    release_meta : str
            Path to the CSV file containing the release metadata.
    audio_meta : str
            Path to the CSV file containing the audio metadata.
    score_meta : str
            Path to the CSV file containing the score metadata.
    sep : str
            String separator to use for splitting metadata fields.

    Returns
    -------
    combined_df : pandas.DataFrame
            A pandas dataframe with all the combined metadata.
    (release_meta_df, audio_meta_df, score_meta_df) : tuple
            A tuple with the pre-processed version of the given metadata.

    """
    zerify = lambda x, y=2: str(x).zfill(y)

    release_meta_df = pd.read_csv(release_meta, sep=sep)
    score_meta_df = pd.read_csv(score_meta, sep=sep)
    audio_meta_df = pd.read_csv(audio_meta, sep=sep)
    # Cleaning and adapting the score metadata df
    score_meta_df = score_meta_df[["SongID", "WorkID", "Title"]]
    score_meta_df = score_meta_df.rename(
        columns={
            "SongID": "score_id",
            "WorkID": "score_file",
            "Title": "title",
        }
    )
    # Cleaning and pre-procesing the release metadata df
    release_meta_df = release_meta_df.rename(
        columns={
            "ID": "release_id",
            "MusicBrainz ReleaseID": "release_mb_id",
            "Year": "release_year",
        }
    )
    release_meta_df = release_meta_df.replace({"not on MusicBrainz": None})
    release_meta_df["performer"] = (
        release_meta_df["Pianist"] + ", " + release_meta_df["Singer"]
    )
    release_meta_df = release_meta_df[
        ["release_id", "performer", "release_year", "release_mb_id"]
    ]
    # Last round of cleaning and pre-processing on the audio metadata df
    audio_meta_df.columns = [c.lower() for c in audio_meta_df.columns]
    audio_meta_df["songid"] = audio_meta_df["songid"].apply(zerify)
    audio_meta_df["track_file"] = (
        "Schubert_D911-" + audio_meta_df["songid"] + "_" + audio_meta_df["performid"]
    )
    audio_meta_df = audio_meta_df[["track_file", "duration"]]

    # First merge: score with release
    combined_meta = pd.merge(release_meta_df, score_meta_df, how="cross")
    combined_meta["track_file"] = (
        combined_meta["score_file"] + "_" + combined_meta["release_id"]
    )
    # Second merge: combined with audio
    combined_meta = pd.merge(
        combined_meta, audio_meta_df, how="left", on=["track_file"]
    )

    return combined_meta, (release_meta_df, audio_meta_df, score_meta_df)


def create_schubert_score_metadata(score_meta, sep=";"):

    score_meta = pd.read_csv(score_meta, sep=";")
    score_meta.columns = [c.lower() for c in score_meta.columns]

    score_meta = score_meta.rename(
        columns={"workid": "score_file", "nomeasures": "duration"}
    )
    score_meta["composer"] = "Franz Schubert"

    return score_meta


def parse_schubert_winterreise(
    annotation_paths,
    out_dir,
    format,
    dataset_name,
    score_meta,
    release_meta=None,
    track_meta=None,
    **kwargs,
):
    """
    Multi-file parser instance for the Schubert Winterreise collection, which
    follow a very specific organisation of annotation files in its folder.

    Parameters
    ----------
    annotation_paths : dict
        Path to the Schubert Winterreise folder containing metadata and anns.
    out_dir : str
        Path to the output directory where all annotations will be saved.
    format : str
        Either 'audio' or 'score' depending on the specific sub-partition.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.
    score_meta : str
        Path to the CSV file providing score metadata (mandatory).
    release_meta : str
        Path to the CSV file providing release metadata (mandatory for audio).
    track_meta : str
        Path to the CSV file providing track metadata (mandatory for audio).

    Returns
    -------
    metadata_df : pandas.DataFrame
        A pandas dataframe providing metadata information following the parsing,
        merging, and cleaning process operated on the given input metadata.

    """
    if format == "audio":  # 24*9 tracks expected
        metadata_df, _ = create_schubert_metadata(release_meta, track_meta, score_meta)
        use_meta = ["title", "performer", "duration", "track_file"]
    elif format == "score":  # 24 scores expected
        metadata_df = create_schubert_score_metadata(score_meta)
        use_meta = ["title", "composer", "duration", "score_file"]
    else:  # The format cannot be interpreted so we will stop here
        raise ValueError(f"{format} is not a valid supported format")

    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    for i, meta in metadata_df.iterrows():  # forgive me
        metadata_entry = {"id": f"{dataset_name}_{i}"}
        metadata_entry.update(
            {k: v for k, v in meta.to_dict().items() if k in use_meta}
        )

        namespace_sources = {}  # retrieving piece-specific paths
        for annotation_name, annotation_loc in annotation_paths.items():
            # Create a file path if a directory is given, otw leave unchanged
            if os.path.isdir(annotation_loc):
                namespace_sources[annotation_name] = [
                    os.path.join(annotation_loc, meta[use_meta[-1]] + ".csv")
                ]
            elif os.path.isfile(annotation_loc):
                namespace_sources[annotation_name] = annotation_loc
            else:  # not a valid directory nor file
                raise ValueError(f"{annotation_loc} is not a valid path")
        # Construction of the query used to find piece-specific entries from a
        # dataframe containing summative (global) annotations for all pieces.
        q = (
            {"WorkID": meta["score_file"], "PerformanceID": meta["release_id"]}
            if format == "audio"
            else {"WorkID": meta["score_file"]}
        )
        timesig = meta["timesign"] if format == "score" else None

        jam = process_text_annotation_multi(
            namespace_sources,
            schubert_namespace_mapping,
            ignore_annotations=schubert_ignore_namespaces,
            sum_query=q,
            duration=meta["duration"],
            timesig=timesig,
        )
        metadata_entry["jams_path"] = os.path.join(
            jams_dir, metadata_entry["id"] + ".jams"
        )
        # Injecting the metadata in the JAMS files
        jams_utils.register_annotation_meta(
            jam,
            annotator_type="expert_human",
            dataset_name="Schubert Winterreise Dataset",
            annotation_version=2.0,  # as per Zenodo
        )
        if format == "audio":
            jams_utils.register_jams_meta(
                jam,
                jam_type=format,
                genre="classical",
                title=meta["title"],
                duration=meta["duration"],
                composers="Franz Schubert",
                performers=[p.strip() for p in meta["performer"].split(",")],
                release_year=meta["release_year"],
                identifiers={"musicbrainz": meta["release_mb_id"]},
                resolve_iden=True,
                resolve_hook="release",
            )
        else:  # format can only be score here
            jams_utils.register_jams_meta(
                jam,
                jam_type=format,
                genre="classical",
                title=meta["title"],
                duration=meta["duration"],
                composers="Franz Schubert",
            )
        jam.save(metadata_entry["jams_path"], strict=False)
        metadata.append(metadata_entry)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata


# **************************************************************************** #
# McGill Billboard
# **************************************************************************** #


def extract_billboard_metadata(bboard_annotation):
    """
    Extract metadata information from a given BillBoard annotation file, in the
    original format. Metadata includes the ID of the track (which is consistent
    with the index file provided by the dataset curators), title, artist, meter,
    starting key, and the full duration of the track.

    Parameters
    ----------
    bboard_annotation : str
        Path to the original BillBoard annotation file (dir/salami_chords.txt).

    Returns
    -------
    meta_entry : dict
        A dictionary with the metadata, indexed by field.

    """
    # In BillBoard, the name of the directory is used as a track identifier
    bb_annotation_id = os.path.basename(os.path.dirname(bboard_annotation))
    meta_entry = {"id": os.path.basename(bb_annotation_id)}
    meta_entry.update(
        {"title": None, "artist": None, "metre": None, "global_key": None}
    )

    with open(bboard_annotation, "r") as bb_file:
        stream = bb_file.readlines()

    for meta_line in stream[:4]:  # isolate metadata
        if meta_line.startswith("# title: "):
            meta_entry["title"] = meta_line[9:].strip()
        # Name of the artist (performer)
        elif meta_line.startswith("# artist: "):
            meta_entry["artists"] = meta_line[10:].strip()
        # Starting (or global) metre
        elif meta_line.startswith("# metre: "):
            meta_entry["metre"] = meta_line[9:].strip()
        # Starting (or global) tonality
        elif meta_line.startswith("# tonic: "):
            meta_entry["key"] = meta_line[9:].strip()
        else:  # this should not happen in BillBoard
            raise ValueError(f"Unknown metadata: {meta_line}")

    meta_entry["duration"] = float(stream[-1].split()[0])
    return meta_entry


def extract_billboard_lkeys(bboard_annotation):
    """
    Extract local key changes from a Billboard annotation in the original format
    Onset of key changes are assumed to correspond to the start time of the
    subsequent annotation line found in the document.

    Parameters
    ----------
    bboard_annotation : str or list
        Path to the BillBoard annotation file (str) or stream object (list).

    Returns
    -------
    lkey_changes : list of lists
        A list containing local key annotations, where each element is a list
        specifying [onset of the key change, duration, key].

    """
    if isinstance(bboard_annotation, str):  # path given
        with open(bboard_annotation, "r") as bb_file:
            stream = bb_file.readlines()
    elif isinstance(bboard_annotation, list):  # stream given
        stream = bboard_annotation
    else:  # no lost, no string > not a valid input parameter
        raise ValueError("Not a valid Billboard annotation")

    lkey_changes = []
    for i, annotation_line in enumerate(stream):
        if "tonic" in annotation_line and i > 4:
            # Extracting key and onset
            lkey = annotation_line.split()[-1]
            onset = float(stream[i + 1].split()[0])
            lkey_changes.append([onset, lkey])

    if len(lkey_changes) > 0:  # re-structure annotation, if any
        track_duration = float(stream[-1].split()[0])
        lk_onsets = np.array([e[0] for e in lkey_changes])
        lk_durations = np.append(lk_onsets[1:], [track_duration]) - lk_onsets
        lkey_changes = [
            [onset, duration, lkey]
            for (onset, lkey), duration in zip(lkey_changes, lk_durations)
        ]  # constructing full annotation

    return lkey_changes


def parse_billboard(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Process the BillBoard dataset to extract chord and key annotations, as well
    as content metadata; this is done from both the original annotations and the
    MIREX .lab files that are provided by the dataset curators (see links).

    Parameters
    ----------
    dataset_dir : str
        Path to the main dataset directory, containing both `original` and
        `mirex` subdirectories for metadata and annotation extraction.
    out_dir : str
        Path to the output directory where all annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved content metadata for the
        integration in ChoCo (another more verbose dataframe is also saved).

    """
    metadata, metadata_extra = [], []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    bb_dir_original = os.path.join(dataset_dir, "original")
    bb_dir_mirex = os.path.join(dataset_dir, "mirex")

    bb_original_dirs = glob.glob(f"{bb_dir_original}/*")
    logger.info(f"Found {len(bb_original_dirs)} dirs in {bb_dir_original}")

    for i, dataset_subdir in enumerate(bb_original_dirs):
        # Find dataset-specific subfolders for each track
        fname_ori = f"{dataset_subdir}/salami_chords.txt"
        metadata_entry = extract_billboard_metadata(fname_ori)
        metadata_entry["dataset"] = dataset_name  # corpus meta

        track_meta = {
            "id": f"{dataset_name}_{i}",
            f"{dataset_name}_id": metadata_entry["id"],
            "track_title": metadata_entry["title"],
            "track_performer": metadata_entry["artists"],
            "file_path": fname_ori,
            "jams_path": None,
        }

        lkeys_ann = extract_billboard_lkeys(fname_ori)
        if len(lkeys_ann) > 0:  # fill the first span with metadata key
            lkeys_ann.insert(0, [0, lkeys_ann[0][0], metadata_entry["key"]])
        else:  # no local key changes: use the global for all duration
            lkeys_ann.append([0, metadata_entry["duration"], metadata_entry["key"]])

        fname_lab = f"{bb_dir_mirex}/{metadata_entry['id']}/full.lab"
        chord_ann = jams.util.import_lab("chord", fname_lab)
        # Create and save the JAMS file out of the annotations
        jam = jams.JAMS(annotations=[chord_ann])
        jams_utils.register_jams_meta(
            jam,
            jam_type="audio",
            title=metadata_entry["title"],
            performers=metadata_entry["artists"],
            duration=metadata_entry["duration"],
        )
        jam = jams_utils.append_listed_annotation(jam, "key_mode", lkeys_ann)
        jams_utils.register_annotation_meta(
            jam,
            annotation_version=1.0,
            annotator_type="expert_human",
            dataset_name="McGill Billboard",
            curator_name="Ashley Burgoyne",
            curator_email="john.ashley.burgoyne@mail.mcgill.ca",
        )
        jams_path = os.path.join(jams_dir, track_meta["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            track_meta["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
        # Keep track of both metadata
        metadata.append(track_meta)
        metadata_extra.append(metadata_entry)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))
    # Also save the verbose metadata extracted
    metadata_xt_df = pd.DataFrame(metadata_extra)
    metadata_xt_df = metadata_xt_df.set_index("id", drop=True)
    metadata_xt_df.to_csv(os.path.join(out_dir, "meta_extra.csv"))

    return metadata_df


# **************************************************************************** #
# Chordify Annotator Subjectivity Dataset (CASD)
# **************************************************************************** #


def parse_casd(dataset_dir, out_dir, dataset_name, track_meta, **kwargs):
    """
    Process the Chordify Annotator Subjectivity Dataset (CASD) to enrich the
    JAMS chord annotations with the loocal keys retrieved from BillBoard, and
    extract relevant metadata that is currently encoded only in the JAMS.

    Parameters
    ----------
    dataset_dir : str
        Path to the dataset folder containing JAMS annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.
    track_meta : str
        Path to the CSV file containing the metadata of BillBoard.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved content metadata for the
        integration in ChoCo (another more verbose dataframe is also saved),
    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    bboard_meta_df = pd.read_csv(track_meta)
    casd_jams = glob.glob(f"{dataset_dir}/*.jams")
    logger.info(f"Found {len(casd_jams)} JAMS in {dataset_dir}")

    for i, casd_jam_path in enumerate(casd_jams):
        # Loading CASD JAMS and retrieving BillBoard ID
        casd_jam = jams.load(casd_jam_path)
        bboard_id = int(casd_jam.file_metadata.identifiers["bbid"])
        bboard_entry = bboard_meta_df[bboard_meta_df["billboard_id"] == bboard_id]
        # Loading ChoCo's JAMS file and append its local keys
        bboard_jam = bboard_entry["jams_path"].values[0]
        bboard_jam = jams.load(bboard_jam, strict=False)
        lkey_annotation = bboard_jam.search(namespace="key_mode")[0]
        casd_jam.annotations.append(lkey_annotation)

        track_meta_entry = {
            "id": f"{dataset_name}_{i}",
            "billboard_id": bboard_id,
            "track_title": casd_jam.file_metadata.title,
            "track_performer": casd_jam.file_metadata.artist,
            "youtube_url": casd_jam.file_metadata.identifiers["youtube_url"],
            "file_path": casd_jam_path,
            "jams_path": None,
        }
        # Registering metadata in the JAMS
        jams_utils.register_jams_meta(
            casd_jam,
            jam_type="audio",
            title=casd_jam.file_metadata.title,
            performers=casd_jam.file_metadata.artist,
            duration=casd_jam.file_metadata.duration,
            identifiers={
                "youtube": casd_jam.file_metadata.identifiers["youtube_url"],
                "dataid_billboard": casd_jam.file_metadata.identifiers["bbid"],
            },
        )
        jams_utils.register_annotation_meta(
            casd_jam,
            annotator_type="expert_human",
            annotation_version=1.0,
            annotation_tools="https://chordify.net/",
            dataset_name="Chordify Annotator Subjectivity Dataset",
            curator_name="Chordify",
            curator_email="casd@chordify.net",
        )

        jams_path = os.path.join(jams_dir, track_meta_entry["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            casd_jam.save(jams_path, strict=False)
            track_meta_entry["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
        # Keep track of both metadata
        metadata.append(track_meta_entry)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Robbie Williams
# **************************************************************************** #


def parse_rwilliams(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Process the Robbie Williams dataset to generate metadata inforamtion from
    the artist-dataset pth structure, and combine LAB and TXT files in JAMS.

    Parameters
    ----------
    dataset_dir : str
        Path to the main dataset folder containing LAB and TXT annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    # Generate metadata from the artist-tree structure
    chord_dir = os.path.join(dataset_dir, "chordlabs")
    metadata = choco_meta.generate_artist_dataset_metadata(
        chord_dir, dataset_name, "Robbie Williams", "lab", sep="-"
    )

    for meta_record in metadata:

        chord_ann = jams.util.import_lab("chord", meta_record["file_path"])
        # Construct path for the local key annotation as per conventions
        lkey_path = meta_record["file_path"].replace("chordlabs", "keys")
        lkey_path = lkey_path.replace(".lab", "GTKeys.txt")
        lkey_ann = jams.util.import_lab("key_mode", lkey_path)
        # Create a JAMS object from the obtained annotations
        jam = jams.JAMS(annotations=[chord_ann, lkey_ann])

        jams_utils.register_jams_meta(
            jam,
            jam_type="audio",
            title=meta_record["file_title"],
            performers="Robbie Williams",
            duration=jams_utils.infer_duration(jam),
            track_number=meta_record["file_track"],
            release=meta_record["file_release"],
            release_year=meta_record["file_release_year"],
        )
        jams_utils.register_annotation_meta(
            jam,
            annotator_type="expert_human",
            annotation_version=1.1,  # with Bas' corrections
            dataset_name="Robbie Williams dataset",
            curator_name="Bruno Di Giorgi",  # as per readme
            curator_email="bruno@brunodigiorgi.it",
        )

        jams_path = os.path.join(jams_dir, meta_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            meta_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Uspop-2002
# **************************************************************************** #


def parse_lab_dataset(dataset_dir, out_dir, dataset_name, track_meta, **kwargs):
    """
    Process a dataset containing MIREX-style LAB annotations to automatically
    generate metadata information from content, and create a JAMS dataset.

    Parameters
    ----------
    dataset_dir : str
        Path to the main dataset folder containing LAB annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.
    track_meta : list of dicts
        An optional list of dictionaries containing piece-specific metadata. If
        not provided, metadata will be automatically generated.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    Notes
    -----
        - The logic should be separated: metadata extraction, jams creation.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    # Generate metadata from the artist-tree structure
    metadata = (
        choco_meta.generate_catalogue_dataset_metadata(
            dataset_dir, dataset_name, "lab", sep="-"
        )
        if track_meta is None
        else track_meta
    )

    for meta_record in metadata:

        chord_ann = jams.util.import_lab("chord", meta_record["file_path"])
        jam = jams.JAMS(annotations=[chord_ann])

        jams_utils.register_jams_meta(
            jam,
            jam_type="audio",
            title=meta_record["file_title"],
            performers=meta_record["file_performer"],
            duration=jams_utils.infer_duration(jam),
            track_number=meta_record["file_track"],
            release=meta_record["file_release"],
        )
        jams_utils.register_annotation_meta(
            jam,
            annotator_type="expert_human",
            annotation_version=1.0,
            dataset_name="Uspop 2002",
            curator_name="Taemin Cho",  # as per readme
            curator_email="tmc323@nyu.edu",
        )

        jams_path = os.path.join(jams_dir, meta_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            meta_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# RWC-Pop
# **************************************************************************** #


def create_rwcpop_meta(track_meta, dataset_name, dataset_dir):
    """
    Parse the RWC text-like metadata of the pop subset and disambiguate fields.
    Paths to the expected LAB files are also generated from the metadata, and
    new IDs are generated for ChoCo.
    """

    def transform_df(meta_item):
        # Work/track ID re-formatting as per conventions
        work_str = meta_item["Piece No."].split()[1]
        work_str = work_str.zfill(3)
        work_str = "N" + work_str
        track_no_str = meta_item["Tr. No."].split()[1]
        track_no_str = "T" + track_no_str
        # Duration is now mapped in seconds, from minutes
        mins, secs = map(float, meta_item["Length"].split(":"))
        duration = timedelta(minutes=mins, seconds=secs)
        meta_item["Length"] = duration.total_seconds()
        meta_item["Tr. No."] = meta_item["Tr. No."][4:]
        # Finally, construct the file path where a LAB is expected
        meta_item["file_path"] = os.path.join(
            dataset_dir, f"{work_str}-{meta_item['Cat. Suffix']}-{track_no_str}.lab"
        )
        return meta_item

    meta_df = pd.read_csv(track_meta, sep="\t")
    meta_df = meta_df.apply(transform_df, axis=1)
    meta_df.columns = [c.lower() for c in meta_df.columns]
    meta_df["id"] = [f"{dataset_name}_{i}" for i in meta_df.index.values]

    meta_df = meta_df.rename(
        columns={
            "artist (vocal)": "performer",
            "length": "duration",
            "tr. no.": "track",
        }
    )
    meta_df = meta_df[
        ["id", "title", "track", "performer", "duration", "tempo", "file_path"]
    ]
    meta_list = meta_df.to_dict("records")

    return meta_list


def parse_rwcpop(dataset_dir, out_dir, dataset_name, track_meta, **kwargs):
    """
    Process the RWC-Pop corpus from TMC as a LAB dataset, and exploits the
    metadata information from the original RWC collection to create JAMS and
    more informative content metadata.

    Parameters
    ----------
    dataset_dir : str
        Path to the main dataset folder containing LAB annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = create_rwcpop_meta(track_meta, dataset_name, dataset_dir)
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    for meta_record in metadata:
        # First create a JAMS object from the LAB annotation
        chord_ann = jams.util.import_lab("chord", meta_record["file_path"])
        jam = jams.JAMS(annotations=[chord_ann])
        # Inject the metadata from the current record into the JAMS
        jams_utils.register_jams_meta(
            jam,
            jam_type="audio",
            title=meta_record["title"],
            performers=meta_record["performer"],
            duration=meta_record["duration"],
            track_number=meta_record["track"],
        )
        jams_utils.register_annotation_meta(
            jam,
            annotator_type="expert_human",
            annotation_version=1.0,
            dataset_name="Real World Computing Music Database",
            curator_name="Taemin Cho",  # as per readme
            curator_email="tmc323@nyu.edu",
        )
        jams_path = os.path.join(jams_dir, meta_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            meta_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Real Book
# **************************************************************************** #


def parse_rbook(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Process the Real Book dataset, containing MIREX-style XLAB annotations to
    automatically generate metadata from content, and create a JAMS dataset.

    Parameters
    ----------
    dataset_dir : str
        Path to the main dataset folder containing XLAB annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.
    track_meta : list of dicts
        An optional list of dictionaries containing piece-specific metadata. If
        not provided, metadata will be automatically generated.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    # Generate metadata from the artist-tree structure
    metadata = choco_meta.generate_flat_dataset_metadata(
        dataset_dir, dataset_name, "xlab", " - "
    )

    # Get biab metadata file
    biab_file = [f for f in os.listdir(dataset_dir) if f.endswith(".csv")][0]
    biab_meta = pd.read_csv(os.path.join(dataset_dir, biab_file), sep=",")

    for meta_record in metadata:
        # Extract metadata from biab file
        file_name = meta_record["id"]
        num, den, key, mode = biab_meta.loc[biab_meta["id"] == file_name][
            ["numerator", "denominator", "key", "time"]
        ].values[0]
        # Extract annotations from xlab
        chord_ann = import_xlab(
            "chord",
            meta_record["file_path"],
            data_column=5,
            format="score",
        )
        lkey_ann = import_xlab(
            "key_mode",
            meta_record["file_path"],
            data_column=7,
            format="score",
            squeeze=True,
        )
        # Creating a JAMS object for both the annotations
        jam = jams.JAMS(annotations=[chord_ann, lkey_ann])
        jams_utils.register_jams_meta(
            jam,
            jam_type="score",
            title=meta_record["file_title"],
            artist=(
                [a.strip() for a in meta_record["file_artists"].split("&")]
                if meta_record["file_artists"] is not None
                else ""
            ),
            duration=int(jams_utils.infer_duration(jam)),
            genre="jazz",  # all jazz standard from RB
        )
        jams_utils.register_annotation_meta(
            jam,
            annotator_type="crowdsource",
            annotation_tools="Band-in-a-Box",
            annotation_version=1.0,
            dataset_name="Real Book",
        )

        # Add time signature annotation
        all_duration = sum([x.duration for x in lkey_ann.data])
        if num and den and not math.isnan(num) and not math.isnan(den):
            time_signatures = [[1, 1, all_duration, f"{int(num)}/{int(den)}"]]
            jam = append_listed_annotation(
                jam,
                "timesig",
                time_signatures,
                offset_type="beat",
                value_fn=to_jams_timesignature,
                reversed=False,
            )
        jams_path = os.path.join(jams_dir, meta_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            meta_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Weimar Jazz Database
# **************************************************************************** #


def annotate_weimar_sections(namespace: str, tuples: list, melo_events: list):

    annotation = jams.Annotation(namespace=namespace)

    for tuple_ann in tuples:
        start_onset, _ = melo_events[tuple_ann[2]]
        end_onset, _ = melo_events[tuple_ann[3]]

        annotation.append(
            time=start_onset,
            duration=end_onset - start_onset,
            value=tuple_ann[4],
            confidence=1,
        )

    return annotation


def process_weimar_melody(melo_id, run):
    """
    Interrogate the database to retrieve melody-specific information/annotations
    from different tables in Weimar, according to the schema presented at
    https://jazzomat.hfm-weimar.de/dbformat/dbformat.html (WJD).

    Parameters
    ----------
    melo_id : str
        String identifier of the melody for which data has to be retrieved.
    run : fn
        A function embedding a dataset cursor/connector for running queries.

    Returns
    -------
    metadata : dict
        The metadata that was found for the given melody.
    annotations : list
        A list of annotations, ideally including chord and key.

    """
    melo_events = run(f"SELECT onset, duration FROM melody WHERE melid=={melo_id}")
    melo_events = sorted(melo_events, key=lambda x: x[0])  # onset ordering
    duration = melo_events[-1][0] + melo_events[-1][1] - melo_events[0][0]
    # logger.info(f"Melody {melo_id} events: {len(melo_events)}")
    # Extracting section-like data: phrases, chords, ideas, form, keys
    sections = run(f"SELECT * FROM sections WHERE melid=={melo_id}")
    chords = list(filter(lambda x: x[1] == "CHORD", sections))
    keys = list(filter(lambda x: x[1] == "KEY", sections))

    annotations = [
        annotate_weimar_sections("chord_weimar", chords, melo_events),
    ]
    # Retrieving metadata from solo_info and track_info
    solo_metadata = run(
        f"SELECT trackid, title, performer, key, signature "
        f"FROM solo_info WHERE melid=={melo_id}"
    )
    assert len(solo_metadata) == 1, "Solo metadata missing or not consistent"
    track_id, title, performer, key, time_signature = solo_metadata[0]
    # Musicbrainz ID and pointers to release and composition
    track_info = run(
        f"SELECT mbzid, compid, recordid " f"FROM track_info WHERE trackid=={track_id}"
    )
    mb_id, comp_id, record_id = track_info[0] if len(track_info) == 1 else [""] * 3
    # From record ID to full release name and date (year)
    record_info = run(
        f"SELECT recordtitle, releasedate "
        f"FROM record_info WHERE recordid=={record_id}"
    )
    record_title, release_year = record_info[0] if len(record_info) == 1 else ("", "")
    # From composition ID to the composer name
    composers = run(
        f"SELECT composer " f"FROM composition_info WHERE compid=={comp_id}"
    )
    composers = list(composers[0]) if len(composers) == 1 else ""

    if len(keys) == 0:  # no key annotation was found in sections
        annotations.append(
            jams.Annotation(
                "key_mode",
                data=[
                    jams.Observation(
                        time=melo_events[0][0],
                        duration=duration,
                        value=key,
                        confidence=1,
                    )
                ],
            )
        )
    else:  # safe to go with the annotations found in sections
        annotations.append(annotate_weimar_sections("key_mode", keys, melo_events))

    metadata = {
        "id": melo_id,
        "title": title,
        "mbid": mb_id,
        "performers": performer,
        "composers": composers,
        "duration": duration,
        "release": record_title,
        "release_year": release_year,
        "jams_path": None,
    }

    return metadata, annotations


def parse_weimarjd(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Query and process the Weimar Jazz Databse to extract metadata and chord
    annotations related to the jazz solo in the collection.

    Parameters
    ----------
    dataset_dir : str
        Path to the Weimar Jazz Database, a file with .db extension.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    # Establish database connection and get cursor
    conn = sql.connect(dataset_dir)
    cursor = conn.cursor()
    run = lambda q: cursor.execute(q).fetchall()
    # Retrieve a list of all the melodies in the database
    melo_ids = run("SELECT DISTINCT melid FROM melody")
    melo_ids = [x[0] for x in melo_ids]  # flatten

    for melo_id in melo_ids:
        # Extracting metadata and annotations from the solo data
        melo_meta, melo_anns = process_weimar_melody(melo_id, run)
        melo_meta["id"] = f"{dataset_name}_{melo_meta['id']}"
        # Creating a JAMS object for both the annotations
        jam = jams.JAMS(annotations=melo_anns)
        jams_utils.register_jams_meta(
            jam,
            jam_type="audio",
            title=melo_meta["title"],
            composers=melo_meta["composers"],
            performers=melo_meta["performers"],
            duration=melo_meta["duration"],
            genre="jazz",  # general
            release=melo_meta["release"],
            release_year=melo_meta["release_year"],
            identifiers={"musicbrainz": melo_meta["mbid"]},
            resolve_iden=True,
            resolve_hook="recording",
        )
        jams_utils.register_annotation_meta(
            jam,
            annotator_type="expert_human",
            annotation_version=2.1,
            annotation_tools="Sonic Visualizer",
            dataset_name="Weimar Jazz Database",
            curator_name="Klaus Flierer",
            curator_email="klaus.frieler@hfm-weimar.de",
        )
        jams_path = os.path.join(jams_dir, melo_meta["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            melo_meta["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
            print(jam.file_metadata.identifiers)
            return
        metadata.append(melo_meta)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# When in Rome
# **************************************************************************** #

wheninrome_tools = {
    " via the 'Working in Harmony' app: https://fourscoreandmore.org/apps/working-in-harmony/": "https://fourscoreandmore.org/apps/working-in-harmony/"
}
wheninrome_ignore = [", manually", ", after", "Anonymous", " ABC", "  2015"]


def parse_wheninrome(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Create global metadata for the whole When-in-Rome collection and produce
    JAMS file from the analyses provided in RomanText format.

    Parameters
    ----------
    dataset_dir : str
        Path to the When in Rome corpus, with sub-datasets as sub-directories.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    analysis_reg = r"analysis(_.+)?\.txt"
    romant_analyses = []

    for root, dirs, files in os.walk(dataset_dir):
        # Check if analysis files are present
        mov_analyses = [
            os.path.join(root, f)
            for f in files
            if re.match(analysis_reg, os.path.basename(f))
        ]
        romant_analyses += mov_analyses

    for i, romant_analysis in enumerate(tqdm(romant_analyses)):
        # Infer metadata information from dataset structure
        dataset, composer, collection, mov = [
            choco_meta.clean_meta_info(meta_str, capitalise=False)
            for meta_str in romant_analysis.split("/")[-5:-1]
        ]
        # Composer as first last name, splitting movement and title
        composer = " ".join(composer.split(",")[::-1]).strip()
        mov, title = choco_meta.extract_meta_prefix(mov, prefix_sep=" ")
        inscore_meta, jam = jamify_romantext(
            romant_analysis,
            clean_str=True,
            annotation_tool_map=wheninrome_tools,
            annotation_ignore=wheninrome_ignore,
        )
        # Fixing inconsistent or uninformative metadata
        if (mov is None and title.isdigit()) or dataset == "Variations and Grounds":
            mov = title  # uninformative title may define movement
            title = inscore_meta["title"]  # more wordy but informative

        meta_record = {
            "id": f"{dataset_name}_{i}",
            "title": title,
            "composers": composer,
            "subset": dataset,
            "collection": collection,
            "movement": mov,
            "duration": inscore_meta["duration_beats"],
            "file_path": romant_analysis,
            "jams_path": None,
        }
        jams_utils.register_annotation_meta(
            jam,
            annotator_name=inscore_meta["annotator"],
            annotator_type="expert_human",
            annotation_version=1.0,
            annotation_tools=inscore_meta["annotation_tools"],
            dataset_name="When in Rome",
            curator_name="Mark Gotham",
        )
        # Additional metadata in the sandbox
        jam.sandbox["collection"] = collection
        jam.sandbox["movement"] = mov
        jam.file_metadata.title = title  # cleaner
        # Ready to close and dump the JAMS file
        jams_path = os.path.join(jams_dir, meta_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            meta_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
        metadata.append(meta_record)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Rock Corpus
# **************************************************************************** #

rockcorpus_annotators = {
    "tdc": "Trevor de Clercq",
    "dt": "David Temperley",
}

rockcorpus_annotators_list = list(rockcorpus_annotators.values())


def parse_rockcorpus(dataset_dir, out_dir, track_meta, dataset_name, **kwargs):
    """
    Create and synchronise content metadata for the Rock Corpus dataset and
    produce JAMS file from the harmonic analyses in corpus' custom format.

    Parameters
    ----------
    dataset_dir : str
        Path to the RockCorpus, with the expanded harmonic annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    track_meta : str
        Path to the TSV file containing non-aligned content metadata.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    meta_path = Path(dataset_dir, "songs.json")
    chords_path = Path(dataset_dir, "chords.json")
    meta = pd.read_csv(track_meta, sep="\t", header=None)

    all_files = json.load(open(os.path.join(dataset_dir, "files.json")))

    for i, file in enumerate(tqdm(all_files.keys())):
        artist_name = meta.loc[meta[1] == file, 2].values
        year = meta.loc[meta[1] == file, 3].values
        metadata_record = {
            "id": f"{dataset_name}_{i}",
            "title": file,
            "performers": artist_name[0] if len(artist_name) > 0 else [],
            "release_year": int(year[0]) if len(year) > 0 else None,
            "file_path": f"{dataset_dir}/files.json",
            "jams_path": None,
        }
        chords, time_sigs, keys = process_harm_json(file, chords_path, meta_path)
        jam = jams.JAMS()
        for idx, chord_data in enumerate(chords):
            jams_score.append_listed_annotation(
                jam, "chord_roman", chord_data, offset_type="beat"
            )
            jams_score.append_listed_annotation(
                jam, "key_mode", keys[idx], offset_type="beat"
            )
            jams_utils.register_annotation_meta(
                jam.annotations[idx],
                annotator_name=rockcorpus_annotators_list[idx],
                annotator_type="expert_human",
                annotation_version=2.1,
                dataset_name="A Corpus Study of Rock Music",
                curator_name="Trevor de Clercq",
                curator_email="trevor.declercq@gmail.com",
            )

        # Registering JAMS-level metadata
        jams_utils.register_jams_meta(
            jam,
            jam_type="score",
            genre="rock",
            title=metadata_record["title"],
            performers=metadata_record["performers"],
            release_year=metadata_record["release_year"],
        )

        jams_utils.register_jams_meta(
            jam,
            jam_type="score",
            genre="rock",
            title=metadata_record["title"],
            performers=metadata_record["performers"],
            release_year=metadata_record["release_year"],
        )

        jam = append_listed_annotation(
            jam,
            "timesig",
            time_sigs,
            offset_type="beat",
            value_fn=to_jams_timesignature,
            reversed=False,
        )

        jams_path = os.path.join(jams_dir, metadata_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            metadata_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
        metadata.append(metadata_record)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# biab-internet-corpus
# **************************************************************************** #


def parse_biab_internet_corpus(
    dataset_dir: str, out_dir: str, dataset_name: str = None, **kwargs
):
    """
    Process the biab-internet-corpus, containing files annotated using the
    Band-in-a-Box software to automatically generate metadata from content, and
    create a JAMS dataset.

    Parameters
    ----------
    dataset_dir : str
        Path to the main dataset folder containing biab annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.
    track_meta : list of dicts
        An optional list of dictionaries containing piece-specific metadata. If
        not provided, metadata will be automatically generated.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    json_dir = create_dir(os.path.join(out_dir, "jams"))

    biab_files = glob.glob(os.path.join(dataset_dir, "*"))
    n_files = len(biab_files)  # should be 5027
    annotation, metadata = [], []
    print(biab_files)
    errors = 0
    for i, biab_file in enumerate(biab_files):
        score_meta = {}
        logger.info(f"Processing ({i}/{n_files}): {biab_file}")
        fname_base = os.path.basename(biab_file)
        # fname, ext = os.path.splitext(fname_base)
        try:
            annotation = process_biab_cpp(biab_file)
        except (ValueError, IndexError, UnicodeDecodeError, TypeError):
            errors += 1
            continue

        if annotation:
            biab_meta, biab_chords, time_signatures, biab_keys = annotation
            score_meta["id"] = f"{dataset_name}_{i}.jams"
            score_meta["biab_id"] = fname_base
            score_meta["score_title"] = biab_meta["title"]
            score_meta["score_authors"] = ", ".join([x for x in biab_meta["composers"]])
            score_meta["file_path"] = biab_file
            score_meta["jams_path"] = os.path.join(json_dir, f"{dataset_name}_{i}.jams")
            # Create the JAMS object from given namespaces
            jam = jams.JAMS()
            jams_score.append_listed_annotation(
                jam, "chord_harte", biab_chords, offset_type="beat", reversed=True
            )
            jams_score.append_listed_annotation(
                jam, "key_mode", biab_keys, offset_type="beat", reversed=True
            )
            jam = append_listed_annotation(
                jam,
                "timesig",
                time_signatures,
                offset_type="beat",
                value_fn=to_jams_timesignature,
                reversed=True,
            )
            jams_utils.register_jams_meta(
                jam,
                jam_type="score",
                title=score_meta["score_title"],
                artist=score_meta["score_authors"],
                duration=biab_meta["duration_m"],
                expanded=biab_meta["expansion"],
            )
            jams_utils.register_annotation_meta(
                jam,
                annotator_type="crowdsource",
                annotation_version=0.95,
                annotation_tools="Band-in-a-Box",
                dataset_name="BiaB Internet Corpus",
                curator_name="Bas de Haas",
                curator_email="bas@chordify.net",
            )
            try:  # Attempt to write JAMS in validation mode
                jam.save(score_meta["jams_path"], strict=False)
            except Exception as exception:  # JAMS cannot be saved
                logger.error(
                    f"JAMS error \t" f" biab_{i} \t {fname_base} \t {exception}"
                )
        metadata.append(score_meta)

    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))
    return metadata_df


# **************************************************************************** #
# JazzCorpus
# **************************************************************************** #


def parse_jazzcorpus(dataset_dir, out_dir, dataset_name, **kwargs):
    """
    Create minimal metadata for the Jazz Corpus and produce multi-level JAMS
    file from the harmonic analyses in the corpus' custom format. One annotation
    level contains Harte-like chord annotations, whereas the other provides
    Roman-like annotations.

    Parameters
    ----------
    dataset_dir : str
        Path to the JazzCorpus txt file with all the human-readable annotations.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    with open(dataset_dir, "r") as sample_exp_file:
        annotation_str = sample_exp_file.readlines()
    # Pre-processing text lines before extraction
    annotation_str = [
        l
        for l in annotation_str
        if (not l.startswith("#")) and (l not in ["\n", "", "("])
    ]
    ann_boundaries = [
        i for i, l in enumerate(annotation_str) if l.startswith("Chords for")
    ]  # where each new annotation starts

    for multiline_ann in [annotation_str[b : b + 6] for b in ann_boundaries]:
        # As metadata of this dataset is still unknown, we keep the original ID
        id = re.search(r"Chords for 'sequence\-(\d+)'", multiline_ann[0])
        id = id.group(1)  # the original ID in the dataset

        metadata_record = {
            "id": f"{dataset_name}_{id}",
            "file_path": dataset_dir,
            "jams_path": None,
        }

        hartelike_ann, romanlike_ann, key_ann, ts_incomp = process_multiline_annotation(
            multiline_ann
        )
        jam = jams.JAMS()  # incremental JAMS constructions
        jams_score.append_listed_annotation(jam, "chord_jparser_harte", hartelike_ann)
        jams_score.append_listed_annotation(
            jam, "chord_jparser_functional", romanlike_ann
        )
        jams_score.append_listed_annotation(jam, "key_mode", key_ann)
        jam.annotations.append(
            jams.Annotation(
                "timesig",
                data=[
                    jams.Observation(
                        1, 1, {"numerator": ts_incomp[-1][0], "denominator": None}, 1
                    )
                ],
            )
        )

        jams_utils.register_jams_meta(
            jam, jam_type="score", genre="jazz", duration=ts_incomp[-2]
        )
        jams_utils.register_annotation_meta(
            jam,
            annotator_name="Mark Granroth-Wilding",
            annotator_type="expert_human",
            annotation_version=1.0,
            dataset_name="JazzCorpus",
            curator_name="Mark Granroth-Wilding",
            curator_email="work@m.g-w.fi",
        )

        jams_path = os.path.join(jams_dir, metadata_record["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            metadata_record["jams_path"] = jams_path
        except:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}")
        metadata.append(metadata_record)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# Mozart Piano Sonatas
# **************************************************************************** #


def parse_mozartsonatas(dataset_dir, out_dir, dataset_name, track_meta, **kwargs):
    """
    Re-organise the rich metadata of the Mozart Piano Sonata dataset and create
    JAMS files out of the DCMLab extended harmony annotations.

    Parameters
    ----------
    dataset_dir : str
        Path to the harmonies resulting from the expansion of the annotations.
        This corresponds to a TSV file for the whole collection, providing both
        local and global key information, as well as expanded measures.
    out_dir : str
        Path to the output directory where JAMS annotations will be saved.
    dataset_name : str
        Name of the dataset that which will be used for the creation of new ids
        in both the metadata returned the JAMS files produced.
    track_meta : str
        Path to the TSV file containing content metadata of the collection.

    Returns
    -------
    metadata_df : pandas.DataFrame
        A dataframe containing the retrieved and integrated content metadata.

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    metadata_df = pd.read_csv(track_meta, sep="\t")
    metadata_df = metadata_df.set_index("filename")
    all_annotations = pd.read_csv(dataset_dir, sep="\t")
    splitted_annotations = list(all_annotations.groupby("filename"))

    for i, annotation in enumerate(splitted_annotations):
        score_id, annotation_df = annotation
        corpus_meta = metadata_df.loc[score_id]

        choco_meta = {
            "id": f"{dataset_name}_{i}",
            "composers": corpus_meta["composer"],
            "title": corpus_meta["workTitle"],
            "movement_no": corpus_meta["movementNumber"],
            "movement_title": corpus_meta["movementTitle"],
            "annotator": corpus_meta["annotator"],
            "musicbrainz_id": corpus_meta["musicbrainz"],
            "wikidata_id": corpus_meta["wikidata"],
            "imslp_id": corpus_meta["imslp"],
            "file_path": corpus_meta["path"],
            "jams_path": None,
        }
        meta, jam = jamify_dcmlab(annotation_df, jams_meta=choco_meta)
        # Registering piece-level metadata in the JAMS file
        jams_utils.register_jams_meta(
            jam,
            jam_type="score",
            expanded=True,  # playthrough
            title=choco_meta["title"],
            composers=choco_meta["composers"],
            duration=meta["duration_beats"],
            identifiers={
                "musicbrainz": corpus_meta["musicbrainz"],
                "wikidata": corpus_meta["wikidata"],
                "imslp": corpus_meta["imslp"],
            },
        )
        jam.sandbox["movement_no"] = choco_meta["movement_no"].item()
        jam.sandbox["movement_title"] = choco_meta["movement_title"]
        # Temporary additions in the JAMS metadata for Wikidata and IMSLP
        # title_mov = f"{choco_meta['title']} ({choco_meta['movement_title']})"
        # jam.file_metadata.title = title_mov  # movement title is embedded
        jams_utils.register_annotation_meta(
            jam,
            annotator_name=choco_meta["annotator"],
            annotator_type="expert_human",
            annotation_version=1.0,
            dataset_name="The Annotated Mozart Sonatas",
            curator_name="Johannes Hentschel",
            curator_email="johannes.hentschel@epfl.ch",
        )

        jams_path = os.path.join(jams_dir, choco_meta["id"] + ".jams")
        try:  # attempt saving the JAMS annotation file to disk
            jam.save(jams_path, strict=False)
            choco_meta["jams_path"] = jams_path
        except Exception as e:  # dumping error, logging for now
            logging.error(f"Could not save: {jams_path}: {e}")
        metadata.append(choco_meta)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return metadata_df


# **************************************************************************** #
# **************************************************************************** #


def main():
    """
    Main function to read the arguments and call the conversion scripts.
    """

    parsers = {
        "mxl": parse_wikifonia,
        "abc": parse_nottingham,
        "jams": parse_isophonics,
        "json": parse_jaah,
        "multi_schubert": parse_schubert_winterreise,
        "billboard": parse_billboard,
        "casd": parse_casd,
        "rwilliams": parse_rwilliams,
        "lab-uspop": parse_lab_dataset,
        "lab-rwc": parse_rwcpop,
        "xlab-rbook": parse_rbook,
        "weimarjd": parse_weimarjd,
        "ireal": parse_ireal_dataset,
        "ireal-forum": parse_ireal_dump,
        "roman-wirome": parse_wheninrome,
        "roman-rockcorpus": parse_rockcorpus,
        "roman-jazzcorpus": parse_jazzcorpus,
        "roman-mozartps": parse_mozartsonatas,
        "biab": parse_biab_internet_corpus,
    }

    parser = argparse.ArgumentParser(
        description="JAMification scripts for ChoCo partitions."
    )

    parser.add_argument("input_dir", type=str, help="Directory where raw data is read.")
    parser.add_argument("out_dir", type=str, help="Directory where JAMS will be saved.")
    parser.add_argument(
        "format",
        type=str,
        choices=parsers.keys(),
        help="File format of the annotations to process.",
    )
    parser.add_argument(
        "type",
        type=str,
        choices=["audio", "score"],
        help="Type of music content in the collection.",
    )

    parser.add_argument(
        "--dataset_name",
        action="store",
        type=str,
        help="Name of the dataset for metadata and JAMS.",
    )
    parser.add_argument(
        "--dataset_version",
        action="store",
        type=str,
        help="A string description of this dataset version.",
    )
    parser.add_argument(
        "--chocodb_path",
        action="store",
        type=str,
        help="Path to the ChoCo database for ID allocation.",
    )
    # Type-specific metadata: for scores, tracks, and releases if separated
    parser.add_argument(
        "--score_meta",
        type=lambda x: is_file(parser, x),
        help="Path to the file providing score metadata.",
    )
    parser.add_argument(
        "--track_meta",
        type=lambda x: is_file(parser, x),
        help="Path to the file providing track metadata.",
    )
    parser.add_argument(
        "--release_meta",
        type=lambda x: is_file(parser, x),
        help="Path to the file providing release metadata.",
    )

    parser.add_argument(
        "--chord_dir",
        type=lambda x: is_dir(parser, x),
        help="Directory containing chord annotation files.",
    )
    parser.add_argument(
        "--lkey_dir",
        type=lambda x: is_dir(parser, x),
        help="Directory containing local key annotation files.",
    )
    parser.add_argument(
        "--gkey_file",
        type=lambda x: is_file(parser, x),
        help="A CSV file containing global key annotations.",
    )
    parser.add_argument(
        "--segment_dir",
        type=lambda x: is_dir(parser, x),
        help="Directory containing segment annotation files.",
    )

    # Logging and checkpointing
    parser.add_argument(
        "--log_dir",
        action="store",
        type=str,
        help="Directory where log files will be generated.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Whether to resume the transformation process.",
    )
    parser.add_argument(
        "--n_workers",
        action="store",
        type=int,
        default=1,
        help="Number of workers for stats computation.",
    )

    args = parser.parse_args()
    if args.log_dir is not None:
        set_logger("choco.parsers", log_dir=args.log_dir)
    if args.dataset_name is None:
        logger.warn("You did not provide a dataset name. Using: custom")
        args.dataset_name = "custom"

    # Bundle the (optional) annotation files and directories in a dictionary
    annotation_paths = {
        "chord": args.chord_dir,
        "lkey": args.lkey_dir,
        "gkey": args.gkey_file,
        "segment": args.segment_dir,
    }

    dataset_parser = parsers.get(args.format)
    dataset_parser(
        dataset_dir=args.input_dir,
        out_dir=args.out_dir,
        format=args.type,
        dataset_name=args.dataset_name,
        score_meta=args.score_meta,
        track_meta=args.track_meta,
        release_meta=args.release_meta,
        annotation_paths=annotation_paths,
        chocodb_path=args.chocodb_path,
        n_workers=args.n_workers,
    )


if __name__ == "__main__":
    main()
