"""
JAMS-Score adds functionalities to vanilla JAMS to handle score annotations.

"""
import logging
from typing import Union

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
    ann_listed:list, offset_type='auto', ann_start:float=1.1,
    ann_duration: Union[float, str]=None, confidence=1., reversed=False):
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
    ann_listed : list of lists
        A list representation of the annotation, which can also be partial, as
        long as onset and value of each observations are always provided.
    ann_start: float
        A float expressing the starting time of the annotation, with
        respect to the music piece (e.g. 1.1 for 1st measure 1st beat).
    ann_duration: float or str
        Either a float expressing the duration of the annotation, with respect
        to the music piece, or a string indicating the method to use for
        inferring this value: ``meta`` if using the metadata of the JAMS, or
        `last_obs` for using the the end of the last observation.
    offset_type : str
        Describes the type of offset: either 'beat' or 'measure' offset that is
        specified in the score annotation to append. If no offset type is given,
        the 'auto' option will attempt to infer this automatically.
    confidence : float
        A default confidence value to consider if such information is missing.
    reversed : bool
        Whether the observation value is reversed in the annotation. If `True`,
        values are expected in leading position [0]; otherwise in position [3]. 

    Notes
    -----
        - Temporary workaround to merge measure and offset in a single float
            that can be used in 'time' to keep the current JAMS structure.
        - Add annotator name as an optional parameter.
        - Confidence may be given for each observation, instead of defaulting.
        - Consider extract keyword-args for annotation-corpus metadata.

    """
    namespace = jams.Annotation(namespace=namespace)
    if reversed:  # re-order the observation fields, as expected
        ann_listed = [obs[1:4]+obs[:1]+obs[4:] for obs in ann_listed]

    for observation in ann_listed:
        measure = observation[0]
        offset = observation[1]
        duration = observation[2]
        value = observation[3]

        namespace.append(
            time=encode_metrical_onset(measure, offset, offset_type),
            duration=duration,  # duration always expected in quarter beats
            confidence=confidence,
            value=value
        )

    # Add namespace annotation to jam file
    jams_object.annotations.append(namespace)
    return jams_object  # modified in-place


def infer_duration(jams_object: jams.JAMS, append_meta=False):
    """
    Infer the duration of a piece from the longest annotation.
    """
    raise NotImplementedError
