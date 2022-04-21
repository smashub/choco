"""
Dataset parser instances for ChoCo's partitions.
[ ****** Very WORK IN PROGRESS. ******]

Notes:
    - Long-term goal > generalise datasets for the jamifier.
"""
import os
import sys
import json
import glob
import shutil
import logging
import argparse
from datetime import timedelta

import jams
import music21
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.getcwd()))

import metadata as choco_meta
from lab_parser import import_xlab
from m21_parser import process_score, create_jam_annotation
from json_parser import extract_annotations_from_json
from multifile_parser import process_text_annotation_multi
from jams_utils import has_chords, append_listed_annotation, append_metadata, infer_duration  # noqa
from choco.utils import create_dir, set_logger, is_file, is_dir

from jamifier import parse_lab_dataset

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
            "score_authors": None,
            "file_title": fname_splitted[1],
            "score_title": None,
            "file_path": fname_base,
            "jams_path": None
        }

        # [Step 3] Process the MusicXML file to extract annotations
        try:  # attempt to extract annotations from the score
            annotation = process_score(mxl_path)
        except Exception as exception:
            logger.error("Extraction error \t"
                         f" wikifonia_{i} \t {fname_base} \t {exception}")
            annotation = None  # do not process this further

        if annotation is not None:
            meta, chords, time_signatures, keys = annotation
            composers = ",".join(meta["composers"])
            score_meta["score_authors"] = composers
            score_meta["score_title"] = meta["title"]
            score_meta["jams_path"] = os.path.join(
                json_dir, f"{dataset_name}_{i}.jams")
            # Create the JAMS object from given namespaces
            jam = create_jam_annotation(
                {"chord": chords, "key_mode": keys},
                metadata=meta, corpus_meta="wikifonia")
            try:  # Attempt to write JAMS in non-validation mode
                jam.save(score_meta["jams_path"], strict=False)
            except Exception as exception:  # JAMS cannot be saved
                logger.error(f"JAMS error \t"
                             f" wikifonia_{i} \t {fname_base} \t {exception}")

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
            logger.info(f"Processing tune {t} in {abc_name}")
            score_id = f"{dataset_name}_{id_cnt}"  # mint a new id
            try:  # attempt to extract annotations from the score
                annotation = process_score(score)
            except Exception as exception:
                logger.error("Extraction error \t"
                             f" {score_id} \t {abc_file} \t {exception}")
                annotation = None  # do not process this further

            score_meta = {
                "id": score_id,
                "subset": abc_name,
                "score_authors": None,
                "score_title": None,
                "file_path": abc_file,
                "jams_path": None
            }

            if annotation is not None:
                meta, chords, time_signatures, keys = annotation
                composers = ",".join(meta["composers"])
                score_meta["score_authors"] = composers
                score_meta["score_title"] = meta["title"]
                score_meta["jams_path"] = os.path.join(
                    jams_dir, f"{score_id}.jams")
                # Create the JAMS object from given namespaces
                jam = create_jam_annotation(
                    {"chord": chords, "key_mode": keys},
                    metadata=meta, corpus_meta=dataset_name)
                try:  # Attempt to write JAMS in non-validation mode
                    jam.save(score_meta["jams_path"], strict=False)
                except Exception as exception:  # JAMS cannot be saved
                    logger.error(f"JAMS error \t"
                                 f" {score_id} \t {abc_file} \t {exception}")

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

    dataset_artists = [indir for indir in os.listdir(dataset_dir) \
                       if os.path.isdir(os.path.join(dataset_dir, indir))]

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
                    release_name, True, number_sep='-', isdir=True)

            logger.info(f"Release: {release_name} ({len(jams_files)} files)")
            for jams_file in jams_files:  # JAMS candidates for chord anns

                file_title, track_no, _ = choco_meta.infer_title_name(
                    jams_file, True, number_sep=track_sep)

                track_meta = {
                    "id": f"{dataset_name}_{id_cnt}",
                    "file_artist": artist,
                    "file_title": file_title,
                    "file_track": track_no,
                    "file_release": release_name,
                    "jams_path": None,
                }

                jams_object = jams.load(os.path.join(root, jams_file))
                if has_chords(jams_object):  # check chord namespace
                    new_path = os.path.join(jams_dir, track_meta["id"] + ".jams")
                    jams_object.save(new_path, strict=False)
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
            this script is quite clear and re-usable in other contexts (XXX).
    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    json_files = glob.glob(os.path.join(dataset_dir, "*.json"))
    logger.info(f"Found {len(json_files)} JSON files in {dataset_dir}")

    for i, json_file in enumerate(json_files):
        # Open JAMS for metadata-extraction only
        with open(json_file, 'rb') as infile:
            json_raw = json.loads(infile.read())
        fname = os.path.splitext(os.path.basename(json_file))[0]

        track_meta = {
            "id": f"{dataset_name}_{i}",
            "file_title": fname,
            "track_title": json_raw['title'],
            "track_artist": json_raw['artist'],
            "track_mbid": json_raw['mbid'],
            "file_path": json_file,
            "jams_path": None,
        }

        try:
            jams_object = extract_annotations_from_json(json_file)
        except Exception as exception:
            logger.error(f"Extraction error for {fname}"
                         f" ({dataset_name}_{i}) \t {exception}")
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
    score_meta_df = score_meta_df.rename(columns={
        "SongID": "score_id",
        "WorkID": "score_file",
        "Title": "title",
    })
    # Cleaning and pre-procesing the release metadata df
    release_meta_df = release_meta_df.rename(columns={
        "ID": "release_id",
        "MusicBrainz ReleaseID": "release_mb_id",
        "Year": "release_year"
    })
    release_meta_df = release_meta_df.replace({"not on MusicBrainz": None})
    release_meta_df["artists"] = \
        release_meta_df["Pianist"] + ", " + release_meta_df["Singer"]
    release_meta_df = release_meta_df[
        ["release_id", "artists", "release_year", "release_mb_id"]]
    # Last round of cleaning and pre-processing on the audio metadata df
    audio_meta_df.columns = [c.lower() for c in audio_meta_df.columns]
    audio_meta_df["songid"] = audio_meta_df["songid"].apply(zerify)
    audio_meta_df["track_file"] = "Schubert_D911-" \
                                  + audio_meta_df["songid"] + "_" + audio_meta_df["performid"]
    audio_meta_df = audio_meta_df[["track_file", "duration"]]

    # First merge: score with release
    combined_meta = pd.merge(release_meta_df, score_meta_df, how="cross")
    combined_meta["track_file"] = \
        combined_meta["score_file"] + "_" + combined_meta["release_id"]
    # Second merge: combined with audio
    combined_meta = pd.merge(
        combined_meta, audio_meta_df, how="left", on=["track_file"])

    return combined_meta, (release_meta_df, audio_meta_df, score_meta_df)


def create_schubert_score_metadata(score_meta, sep=";"):
    score_meta = pd.read_csv(score_meta, sep=";")
    score_meta.columns = [c.lower() for c in score_meta.columns]

    score_meta = score_meta.rename(columns={
        "workid": "score_file", "nomeasures": "duration"})
    score_meta["authors"] = "Franz Schubert"

    return score_meta


def parse_schubert_winterreise(annotation_paths, out_dir, format, dataset_name,
                               score_meta, release_meta=None, track_meta=None, **kwargs):
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
        metadata_df, _ = create_schubert_metadata(
            release_meta, track_meta, score_meta)
        use_meta = ["title", "artists", "duration", "track_file"]
    elif format == "score":  # 24 scores expected
        metadata_df = create_schubert_score_metadata(score_meta)
        use_meta = ["title", "authors", "duration", "score_file"]
    else:  # The format cannot be interpreted so we will stop here
        raise ValueError(f"{format} is not a valid supported format")

    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))

    for i, meta in metadata_df.iterrows():  # forgive me
        metadata_entry = {"id": f"{dataset_name}_{i}"}
        metadata_entry.update({k: v for k, v in \
                               meta.to_dict().items() if k in use_meta})

        namespace_sources = {}  # retrieving piece-specific paths
        for annotation_name, annotation_loc in annotation_paths.items():
            # Create a file path if a directory is given, otw leave unchanged
            if os.path.isdir(annotation_loc):
                namespace_sources[annotation_name] = [os.path.join(
                    annotation_loc, meta[use_meta[-1]] + ".csv")]
            elif os.path.isfile(annotation_loc):
                namespace_sources[annotation_name] = annotation_loc
            else:  # not a valid directory nor file
                raise ValueError(f"{annotation_loc} is not a valid path")
        # Construction of the query used to find piece-specific entries from a
        # dataframe containing summative (global) annotations for all pieces.
        q = {"WorkID": meta["score_file"], "PerformanceID": meta["release_id"]} \
            if format == "audio" else {"WorkID": meta["score_file"]}

        jam = process_text_annotation_multi(
            namespace_sources, schubert_namespace_mapping, metadata_entry,
            sum_query=q, ignore_annotations=schubert_ignore_namespaces)
        metadata_entry["jams_path"] = os.path.join(
            jams_dir, metadata_entry["id"] + ".jams")
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
    meta_entry.update({
        "title": None, "artist": None,
        "metre": None, "global_key": None})

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
        lkey_changes = [[onset, duration, lkey] for (onset, lkey), duration \
                        in zip(lkey_changes, lk_durations)]  # constructing full annotation

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
        integration in ChoCo (another more verbose dataframe is also saved),
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
            f"{dataset_name}_id": metadata_entry['id'],
            "track_title": metadata_entry['title'],
            "track_artist": metadata_entry['artists'],
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
        jam = append_metadata(jam, metadata_entry)
        jam = append_listed_annotation(jam, "key_mode", lkeys_ann)
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
        bboard_id = int(casd_jam.file_metadata.identifiers['bbid'])
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
            "track_artist": casd_jam.file_metadata.artist,
            "youtube_url": casd_jam.file_metadata.identifiers['youtube_url'],
            "file_path": casd_jam_path,
            "jams_path": None,
        }

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
        chord_dir, dataset_name, "Robbie Williams", "lab", sep="-")

    for meta_record in metadata:

        chord_ann = jams.util.import_lab("chord", meta_record['file_path'])
        # Construct path for the local key annotation as per conventions
        lkey_path = meta_record['file_path'].replace("chordlabs", "keys")
        lkey_path = lkey_path.replace(".lab", "GTKeys.txt")
        lkey_ann = jams.util.import_lab("key_mode", lkey_path)
        # Create a JAMS object from the obtained annotations
        jam = jams.JAMS(annotations=[chord_ann, lkey_ann])
        meta_map = {k: k.replace("file_", "") for k
                    in ["file_artists", "file_title", "file_release"]}
        jam = append_metadata(jam, meta_record, meta_map)
        infer_duration(jam, append_meta=True)

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

    def transform_df(meta_item):
        # Work/track ID re-formatting as per conventions
        work_str = meta_item["Piece No."].split()[1]
        work_str = work_str.zfill(3)
        work_str = "N" + work_str
        track_no_str = meta_item["Tr. No."].split()[1]
        track_no_str = "T" + track_no_str
        # Duration is now mapped in seconds, from minutes
        mins, secs = map(float, meta_item["Length"].split(':'))
        duration = timedelta(minutes=mins, seconds=secs)
        meta_item["Length"] = duration.total_seconds()
        # Finally, construct the file path where a LAB is expected
        meta_item["file_path"] = os.path.join(
            dataset_dir,
            f"{work_str}-{meta_item['Cat. Suffix']}-{track_no_str}.lab")
        return meta_item

    meta_df = pd.read_csv(track_meta, sep="\t")
    meta_df = meta_df.apply(transform_df, axis=1)
    meta_df.columns = [c.lower() for c in meta_df.columns]
    meta_df["id"] = [f"{dataset_name}_{i}" for i in meta_df.index.values]

    meta_df = meta_df.rename(columns={
        "artist (vocal)": "artists",
        "length": "duration",
    })
    meta_df = meta_df[
        ["id", "title", "artists",
         "duration", "tempo", "file_path"]
    ]
    meta_list = meta_df.to_dict('records')

    return parse_lab_dataset(
        dataset_dir, out_dir, dataset_name, track_meta=meta_list)


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
        dataset_dir, dataset_name, "xlab", " - ")

    for meta_record in metadata:
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

        meta_map = {k: k.replace("file_", "") for k
                    in ["file_artists", "file_title", "file_release"]}
        jam = append_metadata(jam, meta_record, meta_map)
        # infer_duration(jam, append_meta=True)

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
# biab-internet-corpus
# **************************************************************************** #

def parse_biab_interet_corpus(dataset_dir: str, out_dir: str, dataset_name: str = None, **kwargs):
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
    json_dir = create_dir(os.path.join(out_dir, "jams"))

    biab_files = glob.glob(os.path.join(dataset_dir, "*"))
    n_files = len(biab_files)  # should be 6672


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
        "lab": parse_lab_dataset,
        "lab-rwc": parse_rwcpop,
        "xlab-rbook": parse_rbook,
        "biab": parse_biab_interet_corpus,
    }

    parser = argparse.ArgumentParser(
        description='JAMification scripts for ChoCo partitions.')

    parser.add_argument('input_dir', type=str,
                        help='Directory where raw data is read.')
    parser.add_argument('out_dir', type=str,
                        help='Directory where JAMS will be saved.')
    parser.add_argument('format', type=str, choices=parsers.keys(),
                        help='File format of the annotations to process.')
    parser.add_argument('type', type=str, choices=["audio", "score"],
                        help='Type of music content in the collection.')

    parser.add_argument('--dataset_name', action='store', type=str,
                        help='Name of the dataset for metadata and JAMS.')
    # Type-specific metadata: for scores, tracks, and releases if separated
    parser.add_argument('--score_meta', type=lambda x: is_file(parser, x),
                        help='Path to the file providing score metadata.')
    parser.add_argument('--track_meta', type=lambda x: is_file(parser, x),
                        help='Path to the file providing track metadata.')
    parser.add_argument('--release_meta', type=lambda x: is_file(parser, x),
                        help='Path to the file providing release metadata.')

    parser.add_argument('--chord_dir', type=lambda x: is_dir(parser, x),
                        help='Directory containing chord annotation files.')
    parser.add_argument('--lkey_dir', type=lambda x: is_dir(parser, x),
                        help='Directory containing local key annotation files.')
    parser.add_argument('--gkey_file', type=lambda x: is_file(parser, x),
                        help='A CSV file containing global key annotations.')
    parser.add_argument('--segment_dir', type=lambda x: is_dir(parser, x),
                        help='Directory containing segment annotation files.')

    # Logging and checkpointing
    parser.add_argument('--log_dir', action='store', type=str,
                        help='Directory where log files will be generated.')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='Whether to resume the transformation process.')

    args = parser.parse_args()
    if args.log_dir is not None:
        set_logger("choco.parsers", log_dir=args.log_dir)
    if args.dataset_name is None:
        logger.warn("You did not provide a dataset name. Using: custom")
        args.dataset_name = "custom"

    # Bundle the (optional) annotation files and directories in a dictionary
    annotation_paths = {
        "chord": args.chord_dir,
        "lkey": args.chord_dir,
        "gkey": args.chord_dir,
        "segment": args.chord_dir,
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
    )


if __name__ == "__main__":
    # main()
    parse_biab_interet_corpus()
