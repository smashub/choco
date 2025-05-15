"""
ChoCo running scripts for export, custom dataset creation, and aggregation of
metadata.

Notes: ongoing development.

"""

import argparse
import glob
import logging
import os
import pathlib
import shutil

import pandas as pd
from jams_utils import extract_jams_metadata
from joblib import Parallel, delayed
from namespaces import *
from tqdm import tqdm
from utils import create_dir, is_file, set_logger

logger = logging.getLogger("choco.create")
partition_dir = pathlib.Path(__file__).parent.parent.joinpath("partitions").resolve()

# Mapping from supported JAMS types to their directory name
JAMS_VERSIONS = {"original": "jams", "converted": "jams-converted"}
# Retrieving all the partition names currenty supported in ChoCo
PARTITIONS = [d.name for d in partition_dir.iterdir() if d.is_dir()]


def generate_jams_metadata(jams_dir: str, n_workers=1):
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

    all_meta = Parallel(n_jobs=n_workers)(
        delayed(extract_jams_metadata)(jam) for jam in tqdm(jams_files)
    )

    meta_df = pd.DataFrame(all_meta)  # all possible fields are kept
    meta_df.pop("jams_version")  # no need of the JAMS version

    return meta_df


def create_dataset(
    out_dir,
    jams_version="original",
    include_partitions=[],
    exclude_partitions=[],
    n_workers=1,
):
    """
    Create a custom ChoCo dataset by including/excluding partitions.

    Parameters
    ----------
    out_dir : str
        Directory where the custom dataset will be exported/saved.
    jams_version : str
        Either 'original' to use the original jams, or 'converted' to include
        the annotations resulting from the conversion/translation step.
    include_partitions : list
        An optional list of partition names to include in the dataset.
    exclude_partitions : list
        An optional list of partition names to exclude from nthe dataset.
    n_workers : int
        Number of threads that can be used for metadata extraction.

    """
    if jams_version not in JAMS_VERSIONS:
        raise ValueError(f"JAMS type is not {' or '.join(JAMS_VERSIONS.keys())}")
    if len(include_partitions) > 0 and len(exclude_partitions) > 0:
        raise ValueError("Can either provide include or exclude partitions")
    for pname in include_partitions + exclude_partitions:  # names sanity check
        print(pname)
        if pname.split(":")[0] not in PARTITIONS:  # outer-name
            raise ValueError(f"Partition {pname} is not in ChoCo, yet.")

    listdir = lambda x: [d for d in os.listdir(x) if not d.startswith(".")]
    if len(include_partitions) == 0:  # no partition explicitly selected
        include_partitions = PARTITIONS  # select all partitions

    jams_dirs = []  #  holds the selected JAMS directories to potentially export
    for partition_name in include_partitions:  # iterate all selections
        # Retrieve the sub-partition selection, if any, as a suffix
        sufx = "" if ":" not in partition_name else partition_name.split(":")[1]
        partition_choco_dir = os.path.join(
            partition_dir, partition_name.split(":")[0], "choco", sufx
        )
        if "jams" not in listdir(partition_choco_dir):
            jams_dirs += [
                partition_choco_dir + subset for subset in listdir(partition_choco_dir)
            ]
        else:  # partition does not have any further subset
            jams_dirs.append(partition_choco_dir)

    if len(exclude_partitions) > 0:  # exclude partitions/subpartitions on demand
        exclusions = [
            os.path.join(partition_dir, name.replace(":", "/choco/"))
            for name in exclude_partitions
        ]  # from names to paths
        jams_dirs = [d for d in jams_dirs if not d.startswith(tuple(exclusions))]

    jams_paths, jams_version_dirname = [], JAMS_VERSIONS[jams_version]
    for selected_jams_dir in jams_dirs:
        # Use required JAMS version, if possible, otherwise stick to vanilla
        version = (
            jams_version_dirname
            if jams_version_dirname in os.listdir(selected_jams_dir)
            else "jams"
        )
        version_dir = os.path.join(selected_jams_dir, version)
        assert os.path.isdir(version_dir), f"Could not find {version_dir}"
        jams_selection = glob.glob(os.path.join(version_dir, "*.jams"))
        logger.info(f"Found {len(jams_selection)} JAMS from {version_dir}")
        jams_paths += jams_selection  #  update dataset paths

    logger.info(f"Found {len(jams_paths)} JAMS files for the new dataset")
    out_jams_dir = create_dir(os.path.join(out_dir, "jams"))

    for jams_file in tqdm(jams_paths):  # copying all JAMS files
        shutil.copy(jams_file, out_jams_dir)
    # Extract metadata from JAMS and generate a content CSV
    metadata_df = generate_jams_metadata(out_jams_dir, n_workers)
    metadata_df = metadata_df.sort_values("id")  # improve readability
    metadata_df.to_csv(os.path.join(out_dir, "meta.csv"), index=None)

    return metadata_df


def main():
    """
    Main function to read the arguments and call the dataset creation scripts.
    """

    parser = argparse.ArgumentParser(description="Dataset creation scripts for ChoCo.")

    parser.add_argument(
        "out_dir", type=str, help="Directory where data will be exported."
    )

    parser.add_argument(
        "--jams_version",
        type=str,
        choices=JAMS_VERSIONS.keys(),
        help="Type of JAMS files to consider from ChoCo.",
    )
    parser.add_argument(
        "--input_meta",
        type=lambda x: is_file(parser, x),
        help="Path to the CSV file with the desired metadata.",
    )
    parser.add_argument(
        "--include",
        action="store",
        nargs="*",
        default=[],
        help="Name of partitions to include in the dataset.",
    )
    parser.add_argument(
        "--exclude",
        action="store",
        nargs="*",
        default=[],
        help="Name of partitions to exclude from the dataset.",
    )

    # Logging and checkpointing
    parser.add_argument(
        "--n_workers",
        action="store",
        type=int,
        default=1,
        help="Number of workers for parallel computation.",
    )
    parser.add_argument(
        "--log_dir",
        action="store",
        type=str,
        help="Directory where log files will be generated.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Whether to print logging info messages.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Whether to resume the transformation process.",
    )

    args = parser.parse_args()
    if args.debug:  # debug mode
        set_logger("choco")
    if args.log_dir is not None:
        set_logger("choco", log_dir=args.log_dir)

    # Provide for undefined include/exclude parameters
    if args.include == [""] or args.include == [0]:
        args.include = []
    if args.exclude == [""] or args.exclude == [0]:
        args.exclude = []

    create_dataset(
        out_dir=args.out_dir,
        jams_version=args.jams_version,
        include_partitions=args.include,
        exclude_partitions=args.exclude,
        n_workers=args.n_workers,
    )

    print(f"Done! A new ChoCo dataset has been created in {args.out_dir}")


if __name__ == "__main__":
    main()
