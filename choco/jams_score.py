"""
JAMS-Score adds functionalities to vanilla JAMS to handle score annotations.

"""
import logging

import jams
import numpy as np

logger = logging.getLogger("choco.jams_score")


def encode_metrical_onset(measure, offset):
    """
    Encode a composite metrical time as a float scalar measure.offset where the
    offset can be given either as a beat offset (an integer) or as a relative
    measure offset (a float in the [0, 1) interval).

    Parameters
    ----------
    measure : int
        A (positive) integer encoding the measure number.
    offset : int or float
        A measure (float) or beat (int) offset.

    Returns
    -------
    A float encoding of the metrical onset: measure.offset

    """
    if isinstance(offset, (int, np.integer)):  # beat offset
        offset = float(offset)/10
    elif isinstance(offset, (float, np.floating)):  
        if float(offset).is_integer():  # still a beat offset
            offset = float(offset)/10
        else:  # can only be a measure offset, so check the domain
            assert 0 <= offset < 1, f"Not a valid measure offset: {offset}" 
    else:  # no other valid format is expected outside int and float
        raise ValueError(f"Offset {offset} is not int nor float")

    return float(measure) + offset


def append_listed_annotation(jams_object:jams.JAMS, namespace:str,
    annotation_listed:list, confidence=1.):
    """
    Append a score annotation encoded as a list of score observations, each
    providing information of [measure, offset, metrical duration, value], where
    the offset can be provided in beats or in relative terms.

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
        - Temporary workaround to merge measure and offset in a single float
            that can be used in 'time' to keep the current JAMS structure.
        - Add annotator name as an optional parameter.
        - Add default confidence only if needed: a check is necessary.

    """
    namespace = jams.Annotation(namespace=namespace)

    for annotation in annotation_listed:
        ann_measure = annotation[0]
        ann_offset = annotation[1]
        ann_duration = annotation[2]
        ann_value = annotation[3]

        namespace.append(
            time=encode_metrical_onset(ann_measure, ann_offset),
            duration=ann_duration,
            confidence=confidence,
            value=ann_value
        )

    # Add namespace annotation to jam file
    jams_object.annotations.append(namespace)
    return jams_object  # modified in-place


def infer_duration(jams_object: jams.JAMS, append_meta=False):
    raise NotImplementedError
