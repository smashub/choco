"""
JAMS-Score adds functionalities to vanilla JAMS to handle score annotations.

"""
import logging

import jams

logger = logging.getLogger("choco.jams_score")


def encode_metrical_onset(measure, offset):
    return float(measure) + float(offset)/10


def append_listed_annotation(jams_object:jams.JAMS, namespace:str,
    annotation_listed:list, confidence=1.):
    """
    Append a score-annotation encoded as a list of observations.

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

    Notes
    -----
        - Add annotator name as an optional parameter.
        - Add default confidence only if needed: a check is necessary.

    """
    namespace = jams.Annotation(namespace=namespace)

    for annotation in annotation_listed:
        ann_measure = annotation[0]
        ann_offset = annotation[1]
        ann_duration = annotation[2]
        ann_value = annotation[3]
        # FIXME A time encoding is used temporarily
        namespace.append(
            time=encode_metrical_onset(ann_measure, ann_offset),
            duration=ann_duration, confidence=confidence, value=ann_value)

    # Add namespace annotation to jam file
    jams_object.annotations.append(namespace)
    return jams_object  # XXX modified in-place


def infer_duration(jams_object: jams.JAMS, append_meta=False):
    raise NotImplementedError
