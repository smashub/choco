"""
Instances
"""
import os
import sys
import glob
import shutil
import logging
import argparse

import pandas as pd

sys.path.append(os.path.dirname(os.getcwd()))

from utils import create_dir
from m21_parser import process_score, create_jam_annotation

logger = logging.getLogger("choco.parsers.instances")


# **************************************************************************** #
# Wikifonia
# **************************************************************************** #

def parse_wikifonia(wikifonia_dir, out_dir):
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
    
    Returns
    -------
    metadata_df : pandas.DataFrame
        A pandas dataframe providing metadata information about each score,
        either retrieved from the file name, and according to Wikifonia's
        conventions, or extracted from the MusicXML files.
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

        # [Step 3] Process the MusicXML file
        annotation = process_score(mxl_path)
        if annotation is not None:
            meta, chords, time_signatures, keys = annotation
            composers = ",".join(meta["composers"])
            score_meta["score_authors"] = composers
            score_meta["score_title"] = meta["title"]
            score_meta["jams_path"] = os.path.join(
                json_dir, f"wikifonia_{i}.jams")
            # Write JAMS file in non-validation mode
            jam = create_jam_annotation(
                {"chord": chords, "key_mode": keys},
                metadata=meta, corpus_meta="wikifonia")
            jam.save(score_meta["jams_path"], strict=False)

        metadata_df.append(score_meta)

    # Remove temporary folder
    shutil.rmtree(tmp_folder)
    # Finalise the metadata dataframe
    wikifonia_meta_df = pd.DataFrame(metadata_df)
    wikifonia_meta_df = wikifonia_meta_df.set_index("id", drop=True)
    wikifonia_meta_df.to_csv(os.path.join(out_dir, "meta.csv"))

    return wikifonia_meta_df


def main():
    """
    Main function to read the arguments and call the conversions.
    """

    parser = argparse.ArgumentParser(
        description='JAMification scripts for ChoCo partitions.')

    parser.add_argument('input_dir', type=str,
                        help='Directory where raw data is read.')
    parser.add_argument('out_dir', type=str,
                        help='Directory where JAMS will be saved.')

    # Logging and checkpointing 
    parser.add_argument('--log_dir', action='store',
                        help='Directory where log files will be generated.')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='Whether to resume the transformation process.')

    args = parser.parse_args()
    parse_wikifonia(args.input_dir, args.out_dir)


if __name__ == "__main__":
    main()