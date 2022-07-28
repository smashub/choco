"""
Utility functions to create, manipulate, and interrogate JAMS files. These are
expected to work for audio-based JAMS, although some of them generally work for
score-based JAMS (unless stated differently). For the latter, see `jams_score`.

"""
import os
import logging
from typing import List, Union

import jams

from autolink import SOLVER_BUNDLE, InvalidIdentifierError
from parsers.constants import CHORD_NAMESPACES

logger = logging.getLogger("choco.jams_utils")


def has_chords(jam_file):
    """
    XXX To be deprecated, after checking use. Not useful: just use search.
    """
    for namespace in CHORD_NAMESPACES:
        if jam_file.search(namespace=namespace):
            return True
    return False


def append_metadata(jams_object:jams.JAMS, metadata_dict:dict, meta_map={}):
    """
    Append metadata to a given JAMS object. Depending on their type, metadata
    information will be registered as `file_metadata` or in the `sandbox`.
    XXX This function is DEPRECATED! Use `register_jams_meta()` instead.

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
    # Populating the metadata of the JAMS file, from the expected fields
    if "title" in metadata_dict:
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

    # Add namespace annotation to jams file
    jams_object.annotations.append(namespace)
    return jams_object  # XXX modified in-place


def infer_duration(jams_object: jams.JAMS, append_meta=False):
    """
    
    Notes
    -----
        - Consistent only for audio JAMS. Check the type first.
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


def register_jams_meta(jam: jams.JAMS, jam_type: str, title: str = "",
    artist: str = "", composers: List[str] = [], performers: List[str] = [],
    duration: float = None, release: str = "", release_year: int = None,
    track_number: int = None, genre: str = "", expanded: bool = None,
    identifiers: dict = {}, resolve_iden: bool = False):
    """
    Register all possible metadata in the proper JAMS sections, and perform type
    checking for all possible fields according to the new JAMS extensions. This
    function is supposed to work for both audio and score JAMS.

    Parameters
    ----------
    jam : jams.JAMS
        The JAMS file that will be enriched with the given metadata.
    jam_type : str
        Either 'audio' or 'score' to distinguish the two versions.
    title : str
        The full title of the track or the composition.
    artist : str
        A string defining the artist if this cannot be disambiaguated in either
        composer(s) and performer(s). Use the latter fields whenever possible.
    composers : list of str
        The composers of the score, or the authors of the work behind the track.
    performers : list of str
        The performers of the track, or of a transcribed performance.
    duration : float
        Defines the duration in seconds (audios) or beats (score).
    release : str
        If `type == 'audio'`, the name of the release of the track.
    release_year : int
        If `type == 'audio'`, the year when the release was published.
    track_number : str
        If `type == 'audio'`, a number identifying the track in the release.
    genre : str
        The specific genre and/or style of the composition or track.
    expanded : bool
        If `type == 'score'`, whether the score has been expanded / flattened.
    identifiers : dict
        A mapping from resource names (e.g. Musicbrainz) to identifiers, often
        in the form of full or partial URLs.
    resolve_iden : bool
        Whether attempting to resolve the URLs using the `autolink` features. 

    """
    tolist = lambda x: [x] if isinstance(x, str) else x
    if len(artist) != 0 and (len(composers) != 0 or len(performers) != 0):
        raise ValueError("Artist and composers / performers are exclusive!")

    jam.file_metadata.title = title
    jam.file_metadata.artist = artist
    jam.file_metadata.release = release
    jam.file_metadata.duration = duration

    jam.sandbox = {}
    jam.sandbox["type"] = jam_type
    jam.sandbox["genre"] = genre
    jam.sandbox["composers"] = tolist(composers)
    jam.sandbox["performers"] = tolist(performers)
    # Score-specific metadata: can be avoided in audio
    jam.sandbox["expanded"] = expanded
    # Audio-specific metadata: can be avoided in score
    jam.sandbox["release_year"] = release_year
    jam.sandbox["track_number"] = track_number

    jam.file_metadata.identifiers = {}

    for identifier_name, identifier in identifiers.items():
        if resolve_iden and identifier_name in SOLVER_BUNDLE:
            try:  # attempt resolution of the identifier 
                identifier = SOLVER_BUNDLE[identifier_name]\
                    .attempt_resolution(identifier)
            except InvalidIdentifierError as e:
                logger.warn(f"Resolving error: {e}")
        # Ready to write the identifier in the dicted sandbox
        jam.file_metadata.identifiers[identifier_name] = identifier


def register_annotation_meta(jo: Union[jams.JAMS, jams.Annotation],
    annotator_name="", annotator_type="", annotation_version="",
    annotation_tools="", annotation_rules="", validation="",
    dataset_name="", curator_name="", curator_email=""):
    """
    Register the provided metadata at the annotation level, directly in the
    Annotation object. This provides an alternative way of enriching metadata
    while masking the internal structure of the AnnotationMetadata.

    See also
    --------
    jams.AnnotationMetadata

    """
    annotations = jo.annotations if isinstance(jo, jams.JAMS) else [jo]

    for annotation in annotations:
        annotation.annotation_metadata.annotator.name = annotator_name
        annotation.annotation_metadata.data_source = annotator_type
        annotation.annotation_metadata.version = annotation_version
        annotation.annotation_metadata.annotation_tools = annotation_tools
        annotation.annotation_metadata.annotation_rules = annotation_rules
        annotation.annotation_metadata.validation = validation
        # Register dataset metadata in the annotation too
        register_corpus_meta(annotation, dataset_name,
            curator_name, curator_email)


def register_corpus_meta(jo: Union[jams.JAMS, jams.Annotation],
    dataset_name="", curator_name="", curator_email=""):
    """
    Register corpus metadata at the annotation level. These can be shared
    across a number of annotations even if annotators are different.

    See also
    --------
    jams.AnnotationMetadata

    """
    annotations = jo.annotations if isinstance(jo, jams.JAMS) else [jo]

    for annotation in annotations:
        annotation.annotation_metadata.corpus = dataset_name
        annotation.annotation_metadata.curator.name = curator_name
        annotation.annotation_metadata.curator.email = curator_email
