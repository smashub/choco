"""
Basic testing primitives for JAMS sanity checks and 1-to-1 comparisons. These
can be used as utilities for validating JAMS individually as well as those
resulting from a manual or (semi-)automatic process.
"""
import os
import logging

import jams

logger = logging.getLogger("choco.test")


class JAMSanityCheck(object):
    """
    Provides functions for validating JAMS objects for internal consistency.

    Notes
    -----
    - Can be made as a test or should produce warnings / errors.
    """

    def __init__(self, jams_path: str, strict=False) -> None:
        """
        Creates a JAMS Sanity Check object from the given file.

        Parameters
        ==========
        jams_path : str
            Path to the JAMS file to be loaded and checked.
        strict : bool
            Whether the builtin JAMS validation should be triggered.

        """
        if not os.path.exists(jams_path):
            raise ValueError(f"No JAMS file at {jams_path}")
        self._jams = jams.load(jams_path, strict=strict)


    def check_annotation_times(self) -> bool:
        """
        Check whether annotation times are less than or equal to the total
        duration of the track / piece, if the latter information is available.

        Returns
        -------
        True if duration are consistent.
        """
        duration = self._jam.file_metadata.duration
        if duration is not None:  # piece duration is available
            annotation_times = [ann.duration <= duration for ann in \
                self.jams.annotations if ann is not None]
            # No annotation duration specified or all consistent
            # XXX Can be improved to include the end of the last obs if no
            # annotation-wise duration is made explicit.
            return annotation_times == [] or all(annotation_times)


    def check_annotation_order(self) -> bool:
        """
        Check wether observation times are temporally ordered in all annotations.
        Please, note that this check is trivial, as this already handled by
        `jams` but still necessary to validate the ordering operator.

        Returns
        -------
        True if annotations are temporally ordered according to the start times.
        """
        for annotation in self._jams.annotations:
            observation_times = [obs[0] for obs in annotation.data]
            if not observation_times[1:] >= observation_times[:-1]:
                return False  # ordering of observations is not indexed
        
        return True


    def check_annotation_uniqueness(self) -> bool:
        """
        Check whether the JAMS object contains duplicated annotations. Two
        annotations are considered the same if they share the same observations
        and they have either: the same annotator, or at least a null annotator.

        Returns
        -------
        True if annotations are unique in the JAMS object. Please, note that
        annotation metadata may still slightly differ.
        """
        duplicates = False
        annotation_hashes = {}  # hash: annotation idx
        for i, annotation in enumerate(self._jams.annotations):

            ann_hash = hash(frozenset(annotation.data))
            siblings = annotation_hashes.get(ann_hash, [])
            for sibling_idx in siblings:  # potential duplicates if not empty
                pdup_ann = self._jams.annotations[sibling_idx]
                # Retrieve and compare annotation metadata
                annotator_a = annotation.annotation_metadata.annotator
                annotator_b = pdup_ann.annotation_metadata.annotator
                if (annotator_a == annotator_b) or \
                    annotator_a is None or annotator_b is None:
                    duplicates = True  # JAMS contains duplicates
                    logger.warn(f"Annotations {i}, {sibling_idx} duplicated.")
                
            siblings.append(i)  # append in any case

        return not duplicates

