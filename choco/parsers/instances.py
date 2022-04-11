"""
Dataset parser instances for ChoCo's partitions.
[ ****** Very WORK IN PROGRESS. ******]

Notes:
    - Long-term goal > generalise datasets.
"""
import os
import sys
import glob
import shutil
import logging
import argparse

import music21
import pandas as pd

sys.path.append(os.path.dirname(os.getcwd()))

from utils import create_dir, set_logger
from m21_parser import process_score, create_jam_annotation

logger = logging.getLogger("choco.parsers.instances")


# **************************************************************************** #
# Wikifonia
# **************************************************************************** #

def parse_wikifonia(wikifonia_dir, out_dir, dataset_name):
    """
    Creates a more readable metadata file based on the main naming convention
    used in the Wikifonia project to identify scores: comma-separated list of
    artists, ' - ' separator, title of the score.

    Parameters
    ----------
    wikifonia_dir : str
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

    wikifonia_files = glob.glob(os.path.join(wikifonia_dir, "*"))
    n_files = len(wikifonia_files)  # should be 6672
    tmp_folder = os.path.join(wikifonia_dir, "tmp")
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
                json_dir, f"wikifonia_{i}.jams")
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

def parse_nottingham(nottingham_dir, out_dir, dataset_name):
    """
    Parse ABC data from a given dataset, produce a JAMS file from each tune and
    create a metadata file to keep track of identifiers and data content.

    Parameters
    ----------
    abc_dir : str
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

    abc_files = glob.glob(os.path.join(nottingham_dir, "*.abc"))
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


def main():
    """
    Main function to read the arguments and call the conversions.
    """

    parsers = {
        "mxl": parse_wikifonia,
        "abc": parse_nottingham,
    }

    parser = argparse.ArgumentParser(
        description='JAMification scripts for ChoCo partitions.')

    parser.add_argument('input_dir', type=str,
                        help='Directory where raw data is read.')
    parser.add_argument('out_dir', type=str,
                        help='Directory where JAMS will be saved.')
    parser.add_argument('format', type=str, choices=parsers.keys(),
                        help='File format ofto process.')

    # Logging and checkpointing
    parser.add_argument('--dataset_name', action='store', type=str,
                        help='Name of the dataset for metadata and JAMS.')
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

    dataset_parser = parsers.get(args.format)
    dataset_parser(
        args.input_dir,
        args.out_dir,
        dataset_name=args.dataset_name,
    )


if __name__ == "__main__":
    main()
