"""
ChoCo running scripts for export, custom dataset creation, and aggregation of
metadata.

Notes: ongoing development.

"""
import os
import re
import jams
import glob

import shutil
import pathlib
import logging
import argparse
from tqdm import tqdm
from joblib import Parallel, delayed

import numpy as np
import pandas as pd

from utils import create_dir, is_file, set_logger

logger = logging.getLogger("choco.create")
partition_dir = pathlib.Path(__file__).parent\
    .parent.joinpath("partitions").resolve()

# Mapping from supported JAMS types to their directory name
JAMS_TYPES = {"original": "jams", "converted": "jams_converted"}
# Retrieving all the partition names currenty supported in ChoCo
PARTITIONS = [d.name for d in partition_dir.iterdir() if d.is_dir()]


def extract_jams_metadata(jams_path:str):
    """
    Simple function to extract content metadata from a JAMS file.

    Parameters
    ----------
    jams_path : str
        Path to the JAMS file that will be read for metadata extraction.

    Returns
    -------
    jam_metadict : dict
        A dictionary with all the content metadata found from the JAMS.

    """
    jam = jams.load(jams_path, strict=False)
    jam_metadict = {"id": os.path.splitext(os.path.basename(jams_path))[0]}
    jam_metadict = {**jam_metadict, **dict(jam.file_metadata)}

    jam_id_sandbox = dict(jam_metadict["identifiers"])
    jam_metadict["identifiers"] = "" if len(jam_id_sandbox) == 0 else \
        "; ".join([f"{name}: {id}" for name, id in jam_id_sandbox.items()])

    return jam_metadict


def generate_jams_metadata(jams_dir:str, n_workers=1):
    """
    Search a JAMS dataset for annotations matching a search query in the
    context of the given namespaces. Matches are saved as a CSV file.

    Parameters
    ----------
    jams_dir : str
        Path to the directory containing dataset's JAMS files.
    n_workers : int
        Number of threads that can be used for parallel extraction.

    Returns
    -------
    meta_df : pd.DataFrame
        A dataframe containing all metadata found from JAMS files.

    """
    jams_files = glob.glob(os.path.join(jams_dir, "*.jams"))
    if len(jams_files) == 0:  # no JAMS here: stop
        raise ValueError(f"No JAMS found in {jams_dir}")

    all_meta = Parallel(n_jobs=n_workers)\
        (delayed(extract_jams_metadata)(jam) for jam in tqdm(jams_files))
    
    meta_df = pd.DataFrame(all_meta)  # all possible fields are kept
    meta_df.pop("jams_version") # no need of the JAMS version

    return meta_df


def create_dataset(out_dir, jams_type="original",
    include_partitions=[], exclude_partitions=[], n_workers=1):
    """
    Create a custom ChoCo dataset by including/excluding partitions.

    Parameters
    ----------
    out_dir : str
        Directory where the custom dataset will be exported/saved.
    jams_type : str
        Either 'original' to use the original jams, or 'converted' to include
        the annotations resulting from the conversion/translation step.
    include_partitions : list
        An optional list of partition names to include in the dataset.
    exclude_partitions : list
        An optional list of partition names to exclude from nthe dataset.
    n_workers : int
        Number of threads that can be used for metadata extraction.

    """
    if jams_type not in JAMS_TYPES:
        raise ValueError(f"JAMS type is not {' or '.join(JAMS_TYPES.keys())}")
    if len(include_partitions) > 0 and len(exclude_partitions) > 0:
        raise ValueError("Can either provide include or exclude partitions")
    err_p = [p for p in include_partitions+exclude_partitions if p not in PARTITIONS]
    if len(err_p) > 0:  # some partitions do not exist or not yet supported
        raise ValueError(f"Cannot find partition(s): {', '.join(err_p)}")

    jams_roots = glob.glob(
        f"{partition_dir}/*/choco/**/{JAMS_TYPES[jams_type]}/", recursive=True)
    logger.info(f"Found {len(jams_roots)} JAMS ({jams_type}) root files.")
  
    if len(include_partitions) > 0:
        filter_str = f"partitions/({'|'.join(include_partitions)})"
        logger.info(f"Filtering based on: {filter_str}")
        jams_roots = [d for d in jams_roots if re.search(filter_str, d)]
    elif len(exclude_partitions) > 0:
        filter_str = f"partitions/({'|'.join(exclude_partitions)})"
        logger.info(f"Discarding based on: {filter_str}")
        jams_roots = [d for d in jams_roots if not re.search(filter_str, d)]

    out_jams_dir = create_dir(os.path.join(out_dir, "jams"))
    all_jams = [j for jdir in jams_roots for j \
        in glob.glob(os.path.join(jdir, "*.jams"))]
    logger.info(f"Found {len(all_jams)} JAMS files for the new dataset")

    for jams_file in all_jams: # copying all JAMS files
        shutil.copy(jams_file, out_jams_dir)
    # Extract metadata from JAMS and generate a content CSV
    metadata_df = generate_jams_metadata(out_jams_dir, n_workers)
    metadata_df = metadata_df.sort_values("id")  # improve readibility
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"), index=None)

    return metadata_df



def main():
    """
    Main function to read the arguments and call the dataset creation scripts.
    """

    parser = argparse.ArgumentParser(
        description='Dataset creation scripts for ChoCo.')

    parser.add_argument('out_dir', type=str,
                        help='Directory where data will be exported.')

    parser.add_argument('--jams_type', type=str, choices=JAMS_TYPES.keys(),
                        help='Type of JAMS files to consider from ChoCo.')
    parser.add_argument('--input_meta',  type=lambda x: is_file(parser, x),
                        help='Path to the CSV file with the desired metadata.')
    parser.add_argument('--include', action='store', nargs='+', default=[],
                        help='Name of partitions to include in the dataset.')
    parser.add_argument('--exclude', action='store', nargs='+', default=[],
                        help='Name of partitions to exclude from the dataset.')

    # Logging and checkpointing
    parser.add_argument('--n_workers', action='store', type=int, default=1,
                        help='Number of workers for parallel computation.')
    parser.add_argument('--log_dir', action='store', type=str,
                        help='Directory where log files will be generated.')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='Whether to resume the transformation process.')

    args = parser.parse_args()
    if args.log_dir is not None:
        set_logger("choco", log_dir=args.log_dir)

    create_dataset(
        out_dir=args.out_dir,
        jams_type= args.jams_type,
        include_partitions=args.include,
        exclude_partitions=args.exclude,
        n_workers=args.n_workers
    )



if __name__ == "__main__":
    main()
