"""
Utility functions to create, manipulate, and interrogate JAMS files. These are
expected to work for audio-based JAMS, although some of them generally work for
score-based JAMS (unless stated differently). For the latter, see `jams_score`.

"""
import os
import logging

import jams

from parsers.constants import CHORD_NAMESPACES

logger = logging.getLogger("choco.jams_utils")


def has_chords(jam_file):
    for namespace in CHORD_NAMESPACES:
        if jam_file.search(namespace=namespace):
            return True
    return False


def append_metadata(jams_object:jams.JAMS, metadata_dict:dict, meta_map={}):
    """
    Append metadata to a given JAMS object. Depending on their type, metadata
    information will be registered as `file_metadata` or in the `sandbox`.

    Parameters
    ----------
    jams_object : jams.JAMS
        A JAMS object to enrich with the given metadata.
    metadata_dict : dict
        A dictionary providing basic metadata (title, artists, duration),
        as well as additional (optional) ones such as identifiers, tuning, etc.
    meta_map : dict
        A mapping that will be used to rename the `metadata_dict` so that the
        expected fields will be found from it (e.g. {'file_title': 'title'}).

    Notes
    -----
        - Tmp. information in the sandbox to distinguish scores from audios.

    """
    metadata_dict = {meta_map.get(k, k): v for k, v in metadata_dict.items()}
    # Populating the metadata of the JAMS file
    jams_object.file_metadata.title = metadata_dict['title']

    if "duration" in metadata_dict:
        jams_object.file_metadata.duration = metadata_dict['duration']

    if "artists" in metadata_dict:
        jams_object.file_metadata.artist = metadata_dict['artists']
    elif "authors" in metadata_dict:
        jams_object.file_metadata.artist = metadata_dict['authors']

    if "release" in metadata_dict:
        jams_object.file_metadata.release = metadata_dict['release']
    if 'mbid' in metadata_dict:
        jams_object.file_metadata.identifiers = {"MB": metadata_dict['mbid']}

    if 'tuning' in metadata_dict:
        jams_object.sandbox.tuning = metadata_dict['tuning']
    if 'dataset' in metadata_dict:
        jams_object.sandbox.dataset = metadata_dict['dataset']
    if 'genre' in metadata_dict:
        jams_object.sandbox.genre = metadata_dict['genre']
    # jams_object.sandbox.metre = metre

    return jams_object


def append_listed_annotation(jams_object:jams.JAMS, namespace:str,
    annotation_listed:list, confidence=1.):
    """
    Append a time-annotation encoded as a list of observations.

    Parameters
    ----------
    jams_object : jams.JAMS
        A JAMS object that will be extended with the given annotation.
    namespace : str
        The name of the namespace to use for bundling the annotation.
    annotation_listed : list of lists
        A list representation of the annotation, which can also be partial, as
        long as onset and value of each observations are always provided.
    confidence : float
        A default confidence value to consider if such information is missing.

    """
    if len(annotation_listed[0]) < 2:
        raise ValueError("Onset and observation value are needeed")
    elif len(annotation_listed[0]) == 2:
        # TODO Compute duration from offsets and file metadata
        raise NotImplementedError
    elif len(annotation_listed[0]) == 3:
        # Adding confidence values using the default parameter
        annotation_listed = [ann_item+[confidence] \
            for ann_item in annotation_listed]
    elif len(annotation_listed[0]) == 4:
        logger.warning("Confidence value is provided!")
    elif len(annotation_listed[0]) > 4:
        raise ValueError("Cannot interpret more than 4 items")

    namespace = jams.Annotation(
                namespace=namespace, time=0,
                duration=jams_object.file_metadata.duration)

    for annotation_item in annotation_listed:
        namespace.append(
            time=annotation_item[0],
            duration=annotation_item[1],
            value=annotation_item[2],
            confidence=annotation_item[3])

    # Add namespace annotation to jam file
    jams_object.annotations.append(namespace)
    return jams_object  # XXX modified in-place


def infer_duration(jams_object: jams.JAMS, append_meta=False):
    """
    
    Notes
    -----
        - Consistent only for audio JAMS.
    """

    if len(jams_object.annotations)==0:
        raise ValueError("Cannot infer duration if JAMS has no annotations")
    
    durations = []
    for annotation in jams_object.annotations:
        last_annotation = annotation.data[-1]  # assumed to be temp. last
        durations.append(last_annotation.time + last_annotation.duration)

    duration = max(durations)
    if append_meta:  # update JAMS' metadata
        jams_object.file_metadata.duration = duration
    
    return duration


def get_global_key(jams_object: jams.JAMS):

    raise NotImplementedError
