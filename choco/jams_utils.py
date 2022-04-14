"""
Utility functions to create, manipulate, and interrogate JAMS files.
"""
import jams

from parsers.constants import CHORD_NAMESPACES


def has_chords(jam_file):
    for namespace in CHORD_NAMESPACES:
        if jam_file.search(namespace=namespace):
            return True
    return False


def append_metadata(jams_object: jams.JAMS, metadata_dict: dict):
    """
    Append mandatory and supplementary metadata to a given JAMS object.

    Parameters
    ----------
    jams_object : jams.JAMS
        A JAMS object to enrich with the given metadata.
    metadata_dict : dict
        A dictionary providing mandatory metadata (title, artists, duration),
        as well as additional (optional) ones such as identifiers, tuning, etc.

    Notes
    -----
        - Tmp. information in the sandbox to distinguish scores from audios.
        - Append any other information in the sandbox.

    """
    # Populating the metadata of the JAMS file
    jams_object.file_metadata.title = metadata_dict['title']
    jams_object.file_metadata.duration = metadata_dict['duration']
    
    if "artists" in metadata_dict:
        jams_object.file_metadata.artist = metadata_dict['artists']
    elif "authors" in metadata_dict:
        jams_object.file_metadata.artist = metadata_dict['authors']
    
    if 'tuning' in metadata_dict:
        jams_object.sandbox.tuning = metadata_dict['tuning']
    if 'dataset' in metadata_dict:
        jams_object.sandbox.dataset = metadata_dict['dataset']
    if 'mbid' in metadata_dict:
        jams_object.file_metadata.identifiers = {"MB": metadata_dict['mbid']}
    # jams_object.sandbox.metre = metre

    # TODO Anything else is appended to sandbox (the first 2 conditional are
    # not useful, as they just register metadata to the sandbox).

    return jams_object


def infer_duration(jams_object: jams.JAMS):

    raise NotImplementedError

def get_global_key(jams_object: jams.JAMS):

    raise NotImplementedError