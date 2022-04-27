"""
Utilities to infer and generate metadata from datasets, according to the way
content is structured therein.
"""

import os
import re
from matplotlib import artist

from numpy import full

from utils import get_directories, get_files, strip_extension


def comparification(text, delete=[], replace={}, no_par=True):
    """
    Simplification of a string before comparison, with the given characters or
    sub-sequences removed or replaced. Text is then processed in lower case
    and stripped of extra bounding spaces. Parentheses, together with their
    content, can also be removed, if requested.

    Parameters
    ----------
    text : str
        The input string that will be simplified for comparison.
    delete : list
        List of strings (sub-sequences) that will be removed from `text`.
    replace : dict
        A mapping from sub-strings/characters to their replacements.
    no_par : bool
        Whether content in parentheses should be discarded.

    Returns
    -------
    text : str
        The new string following deletions and replacements, as required.

    """
    text = text.lower()
    for delete_str in delete:
        text = text.replace(delete_str, "")
    for to_replace, replace_str in replace.items():
        text = text.replace(to_replace, replace_str)
    if no_par:  # remove parentheses, if needed
        text = re.sub(f"\(.+\)", "", text)

    return text.strip()


def clean_meta_info(meta_str:str, sep="_", capitalise=True):

    clean_meta_str = [s for s in meta_str.split(sep) if s!=""]
    if capitalise:  # capitalising leading letters, if needed
        clean_meta_str = [w[0].upper()+w[1:] for w in clean_meta_str]
    clean_meta_str = " ".join(clean_meta_str)

    return clean_meta_str


def extract_meta_prefix(meta_str:str, prefix_re=r"^[0-9]+", prefix_sep="-"):

    split_pattern = prefix_re + prefix_sep  # full regexpr for splitting
    prefix_str = re.match(split_pattern, meta_str)
    deprefixed_str = meta_str
    if prefix_str is not None:  # found matching prefix
        prefix_str = prefix_str.group()[:-len(prefix_sep)]  # remove prefix_sep
        deprefixed_str = re.compile(split_pattern).split(meta_str)[1]

    return prefix_str, deprefixed_str




def infer_title_name(file_name, has_number, has_cd="auto", number_sep=" ", isdir=False):
    """

    Notes:
        - Still a bit too specific for the use case of Isophonics.
    """

    def split_on_prefix(fname):
        """
        Simple utility to divide a string based on the given conventions.
        """
        splitted_text = fname.split()
        prefix = splitted_text[0]
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


def generate_catalogue_dataset_metadata(dataset_dir:str, dataset_name:str,
    annotation_fmt:str, sep="-"):
    """
    Metadata generator for an catalogue dataset organised according to the
    following structure `dataset_dir/artist/release/track_annotation`. In sum,
    multiple artists, and multiple releases per artists can be present.

    Parameters
    ----------
    dataset_dir : str
        Path to the dataset root directory, where artist-subfolders are located.
    dataset_name : str
        A name to associate the dataset with, which will be used for ids.
    annotation_fmt : str
        A string representing the expected format of the annotation files.
    sep : str
        A symbol or a sub-string to extract/divide information from names.

    Notes:
        - Use custom functions to infer information from tracks and releases.
        - The method looks a bit repetitive/verbose, just to reflect on what
            can be better generalised to other dataset (e.g. dataset specific
            conventions for artists, releases, and track information in files).
    """

    id_cnt = 0
    metadata = []

    for artist_path in get_directories(dataset_dir, full_path=True):
        artist_name = clean_meta_info(os.path.basename(artist_path), "_", True)
        # Moving down to release directories, expected inside the artist dir
        for release_path in get_directories(artist_path, full_path=True):
            release_name = os.path.basename(release_path)
            release_name = clean_meta_info(release_name, "_", True)
            # And finally finding track-specific annotations/content to index
            for track_file in get_files(release_path, annotation_fmt, True):
                track_name = os.path.splitext(os.path.basename(track_file))[0]
                track_name = clean_meta_info(track_name, "_", True)
                track_no, track_name = extract_meta_prefix(track_name)

                track_meta = {
                    "id": f"{dataset_name}_{id_cnt}",
                    "file_artists": artist_name,
                    "file_title": track_name,
                    "file_track": track_no,
                    "file_release": release_name,
                    # "file_release_year": release_year,
                    "file_path": track_file,
                    "jams_path": None,
                }

                metadata.append(track_meta)
                id_cnt += 1

    return metadata


def generate_flat_dataset_metadata(dataset_dir:str, dataset_name:str,
    annotation_fmt:str, sep="-"):
    """
    Metadata generator for a flat dataset, where all the annotations are simply
    stored in the same folder -- hence with the folder structure not entailing
    any meaningful relationships for metadata-extraction.

    Parameters
    ----------
    dataset_dir : str
        Path to the dataset root directory, with all annotations stored therein.
    dataset_name : str
        A name to associate the dataset with, which will be used for ids.
    annotation_fmt : str
        A string representing the expected format of the annotation files.
    sep : str
        A symbol or a sub-string to extract/divide information from names.

    Notes
    -----
        - Parameterise the metadata-extraction behaviour from the file names.

    """
    metadata = []

    for i, fname in enumerate(get_files(dataset_dir, annotation_fmt, True)):

        title = strip_extension(os.path.basename(fname), all=True) # XXX DS
        artists, title = extract_meta_prefix(title,  r"^.+", sep)  # XXX DS
        if bool(artists and title):  # FIXME flipping roles
            artists, title = title, artists

        track_meta = {
            "id": f"{dataset_name}_{i}",
            "file_artists": artists,
            "file_title": title,
            # "file_track": track_no,
            # "file_release": release_name,
            # "file_release_year": release_year,
            "file_path": fname,
            "jams_path": None,
        }

        metadata.append(track_meta)

    return metadata
