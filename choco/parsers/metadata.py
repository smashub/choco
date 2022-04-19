
import os
import re

def infer_title_name(file_name, has_number, has_cd="auto", number_sep=" ", isdir=False):

    def split_on_prefix(fname):
        """
        Simple utility to divide a string based on the given conventions.
        """
        splitted_text = fname.split()
        prefix =  splitted_text[0]
        offset = 2 if splitted_text[1]==number_sep else 1
        fname = " ".join(splitted_text[offset:])

        return prefix, fname

    fname = os.path.splitext(file_name)[0] if not isdir else file_name
    has_cd = bool(re.match(r"^CD[0-9]", fname)) if has_cd=='auto' else has_cd
    number_prefix, cd_prefix = None, None  # for now

    if " " not in fname and "_" in fname:
        fname = fname.replace("_", " ")

    if has_cd:  # the CD number is assumed to lead
        cd_prefix, fname = split_on_prefix(fname)
    if has_number:  # the number follows the cd prefix
        number_prefix, fname = split_on_prefix(fname)

    return fname, number_prefix, cd_prefix


def generate_artist_dataset_metadata(dataset_dir:str, dataset_name:str,
    artist_name:str, annotation_fmt:str, sep="-"):
    """
    Metadata generator for an artist dataset organised according to the
    following structure `dataset_dir/release/track_annotation`.

    Parameters
    ----------
    dataset_dir : str
        Path to the dataset main content, or a representative partition at
        least (in case the dataset contains multiple annotations in other
        folders, although the structure is consistent throghout).
    dataset_name : str
        A name to associate the dataset with, which will be used for ids.
    artist_name : str
        The name of the dataset, which will be used for the metadata.
    annotation_fmt : str
        A string representing the expected format of the annotation files.
    sep : str
        A symbol or a sub-string to extract/divide information from names.
    
    Notes:
        - Use custom functions to infer information from tracks and releases.
    """

    id_cnt = 0
    metadata = []

    for root, dirs, files in os.walk(dataset_dir):

        if len(dirs) != 0:
            continue  # nothing to parse, yet
        # Parent directory as release name
        release_name = os.path.basename(root)
        release_year, release_name = release_name.split(sep)

        for ann_file in [f for f in files if f.endswith(f".{annotation_fmt}")]:
            fname = os.path.splitext(os.path.basename(ann_file))[0]
            file_track_no, file_title = fname.split(sep)

            track_meta = {
                "id": f"{dataset_name}_{id_cnt}",
                "file_artists": artist_name,
                "file_title": file_title,
                "file_track": file_track_no,
                "file_release": release_name,
                "file_release_year": release_year,
                "file_path": os.path.join(root, ann_file),
                "jams_path": None,
            }

            metadata.append(track_meta)
            id_cnt += 1
    
    return metadata
