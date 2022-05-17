"""
JAMS-Score adds functionalities to vanilla JAMS to handle score annotations.

"""
import logging
from multiprocessing.sharedctypes import Value

import jams
import numpy as np

logger = logging.getLogger("choco.jams_score")


class UnexpectedOffsetType(Exception):
    """Raised when the offset type cannot be inferred"""
    pass


def encode_metrical_onset(measure, offset, offset_type="auto"):
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
    offset_type : str
        Describes the type of offset: either 'beat' or 'measure' offset. If no
        offset type is provided, it defaults to 'auto', which attempts to infer
        the type from the scalar type (int as beats, floats as measures).

    Returns
    -------
    A float encoding of the metrical onset: measure.offset

    """
    if not offset_type in ["auto", "beat", "measure"]:
        raise ValueError(f"Offset type unknown: {offset_type}")
    beat_to_measure_offset = lambda x: float(x)/10

    if offset_type == "auto":  # infer the type of offset
        if isinstance(offset, (int, np.integer)):  # beat offset
            offset = beat_to_measure_offset(offset)
        elif isinstance(offset, (float, np.floating)):  
            if float(offset).is_integer():  # still a beat offset
                offset = beat_to_measure_offset(offset)
            else:  # can only be a measure offset, so check the domain
                if not 0 <= offset < 1:
                    raise UnexpectedOffsetType(
                        f"Cannot infer offset type for {offset}")
        else:  # no other valid format is expected outside int and float
            raise UnexpectedOffsetType(f"Offset {offset} is not int nor float")
    
    elif offset_type == "beat":  # from beat to measure offset
        offset = beat_to_measure_offset(offset)

    else: # offset can only be a measure offset, check if in [0, 1) interval
        if not 0 <= offset < 1:  # the value does not reflect the offset type
            raise ValueError(f"Measure offset should be in [0,1)]: {offset}")

    return float(measure) + offset


def append_listed_annotation(jams_object:jams.JAMS, namespace:str,
    annotation_listed:list, offset_type='auto', confidence=1.):
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
    offset_type : str
        Describes the type of offset: either 'beat' or 'measure' offset that is
        specified in the score annotation to append. If no offset type is given,
        the 'auto' option will attempts to infer this automatically.
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
            time=encode_metrical_onset(
                ann_measure, ann_offset, offset_type),
            duration=ann_duration,
            confidence=confidence,
            value=ann_value
        )

    # Add namespace annotation to jam file
    jams_object.annotations.append(namespace)
    return jams_object  # modified in-place


def infer_duration(jams_object: jams.JAMS, append_meta=False):
    raise NotImplementedError
