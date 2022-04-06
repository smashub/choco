"""
Instances
"""
import os
import sys
import shutil
import logging
from venv import create
import pandas as pd

from utils import create_dir
from m21_parser import process_score, create_jam_annotation

sys.path.append(os.getcwd())  # use parent modules
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

    wikifonia_files = os.listdir(wikifonia_dir)
    n_files = len(wikifonia_files)  # should be 6672
    tmp_folder = os.path.join(wikifonia_dir, "tmp")
    os.mkdir("tmp")  # creating temporary directory

    for i, wikifonia_file in enumerate(wikifonia_files):
        logger.info(f"Processing ({i}/{n_files}): {wikifonia_file}")
        # [Step 1] Resolving path name and detecting ext-encoded versions
        fname, ext = os.path.splitext(os.path.basename(wikifonia_file))
        mxl_path = wikifonia_file  # path to the actual .mxl file

        if ext[1:].isnumeric():  # dealing with alternative versions
            logger.warn(f"Alternative version detected ({ext})")
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
            "file_path": fname,
            "jams_path": None
        }
        
        # [Step 3] Process the MusicXML file
        annotation = process_score(mxl_path)
        if annotation is not None:
            meta, chords, time_signatures, keys = annotation
            score_meta["score_authors"] = meta["composers"]
            score_meta["score_title"] = meta["title"]
            score_meta["jams_path"] = os.path.join(json_dir, f"wikifonia_{i}")
            # TODO Write JAMS file in non-validation mode
            jam = create_jam_annotation(
                {"chord": chords, "key_mode": keys},
                metadata=meta, corpus_meta="wikifonia")

        metadata_df.append(score_meta)

    # TODO Remove temporary folder
    shutil.rmtree(tmp_folder)
    # Finalise the metadata dataframe
    wikifonia_meta_df = pd.DataFrame(wikifonia_meta_df)
    return wikifonia_meta_df.set_index("id", drop=True)