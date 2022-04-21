"""
The Jamifier creates JAMS files out of your dataset, as long as the way content
is organised in files/folders reflect one of our archetypes.

Notes:
    - Work in progress, after the lesson learned from the other collections.
    - The Jamifier should be in the `/choco/choco` as main entry point.
"""

import os
import logging

import jams
import pandas as pd

from metadata import generate_catalogue_dataset_metadata
from choco.jams_utils import append_metadata, infer_duration
from choco.utils import create_dir

logger = logging.getLogger("choco.parsers.jamifier")


class JAMSDataset(object):
    """
    TODO
    """

    def __init__(self, dataset_dir, out_dir) -> None:
        
        self._dataset_dir = dataset_dir
        self._out_dir = out_dir


def parse_lab_dataset(dataset_dir, out_dir, dataset_name, track_meta, **kwargs):
    """
    Process a dataset containing MIREX-style LAB annotations to automatically
    generate metadata information from content, and create a JAMS dataset.

    XXX Simplified implementation for the moment: to extend and generalise.

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

    """
    metadata = []
    jams_dir = create_dir(os.path.join(out_dir, "jams"))
    # Generate metadata from the artist-tree structure
    metadata = generate_catalogue_dataset_metadata(
        dataset_dir, dataset_name, "lab", sep="-") \
            if track_meta is None else track_meta

    for meta_record in metadata:

        chord_ann = jams.util.import_lab("chord", meta_record['file_path'])
        jam = jams.JAMS(annotations=[chord_ann])

        meta_map = {k: k.replace("file_", "") for k
            in ["file_artists", "file_title", "file_release"]}
        jam = append_metadata(jam, meta_record, meta_map)
        infer_duration(jam, append_meta=True)

        jams_path = os.path.join(jams_dir, meta_record["id"]+".jams")
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
