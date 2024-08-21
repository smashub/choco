"""
Instantiation of the chord converters for each of the dataset to convert.
"""

import argparse
import logging
import os
import sys
from json import decoder
from typing import List

import jams
import pandas as pd
from joblib import Parallel, delayed

sys.path.append(os.path.dirname(os.getcwd()))
parsers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "parsers"))
sys.path.append(parsers_path)

lark_converters_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "lark-converters")
)
sys.path.append(lark_converters_path)

namespaces = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "namespaces")
)
sys.path.append(namespaces)

import namespaces
from chord_converter import ANNOTATION_SUPPORTED, ChordConverter
from constants import CHORD_NAMESPACES
from converter_utils import create_dir, update_chord_list

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logger = logging.getLogger("choco.converters.converter_instances")

basedir = os.path.dirname(__file__)


def parse_jams(
    jams_path: str,
    output_path: str,
    dataset_name: str,
    filename: str,
    replace: bool = False,
    handle_error: bool = True,
    verbose: bool = False,
) -> List:
    """
    Parser for JAMS files that replace the chord annotations with the
    converted ones.
    Parameters
    ----------
    verbose
    jams_path : str
        The path of the JAMS file to be converted.
    output_path : str
        The path in which the converted JAMS will be saved.
    dataset_name : str
        The name of the dataset the JAMS belongs to. Used by the conversion
        encoders/decoders.
    filename : str
        The name of the JAMS file parsed, used for saving the file with the
        same name as the original.
    replace : bool (default=False)
        Indicated whether to replace the annotation or to preserve the original
        ones and hence duplicate the annotation section of the original file.
    handle_error : bool
        Boolean parameter to set whether to stop the program if a conversion
        error is met (False) or to continue and skip the error (True).

    Returns
    -------
    chord_metadata : List[List]
        A list of list containing metadata about the chords converted, organised
        as follows:
            [original_chord, converted_chord, type(key, chord), occurrences]
    """
    chord_metadata = []

    try:
        original_jams = jams.load(jams_path, strict=False, validate=False)
    except decoder.JSONDecodeError as de:
        logger.error(f"Unable to open file {filename}, due to error {de}")
        return []
    original_annotations = original_jams.annotations
    jam = jams.JAMS()
    jam.file_metadata = original_jams.file_metadata
    jam.sandbox = original_jams.sandbox

    all_annotations = []
    converter = ChordConverter(dataset_name=dataset_name, handle_error=handle_error)

    for annotation in original_annotations:
        # make an exception for the jazz-corpus, for which
        # we cannot convert the chord_roman, so far
        if annotation.namespace in (
            CHORD_NAMESPACES
            if dataset_name != "jazz-corpus"
            else ["chord_jparser_harte"]
        ):
            converted_annotation = jams.Annotation(
                namespace="chord_harte",
                annotation_metadata=annotation.annotation_metadata,
            )

            converted_annotation.annotation_metadata.annotation_rules = (
                "Chord annotations converted using the ChoCo library "
            )

            for observation in annotation:
                converted_value = converter.convert_chords(observation.value)
                if verbose:
                    logger.info(
                        f"Converting chord: {observation.value} --> "
                        f"{converted_value}"
                    )
                converted_annotation.append(
                    time=observation.time,
                    duration=observation.duration,
                    value=converted_value,
                    confidence=observation.confidence,
                )
                chord_metadata = update_chord_list(
                    chord_metadata,
                    [
                        observation.value,
                        converted_value,
                        "chord",
                        annotation.namespace,
                        "chord_harte",
                        1,
                    ],
                )
            all_annotations.append(converted_annotation)
        elif annotation.namespace == "key_mode":
            converted_annotation = jams.Annotation(
                namespace="key_mode", annotation_metadata=annotation.annotation_metadata
            )

            converted_annotation.annotation_metadata.annotation_rules = (
                "Chord annotations converted using the ChoCo library"
            )

            for key_observation in annotation:
                try:
                    converted_key = converter.convert_keys(key_observation.value)
                    converted_annotation.append(
                        time=key_observation.time,
                        duration=key_observation.duration,
                        value=converted_key,
                        confidence=key_observation.confidence,
                    )
                    chord_metadata = update_chord_list(
                        chord_metadata,
                        [
                            key_observation.value,
                            converted_key,
                            "key",
                            annotation.namespace,
                            "key_mode",
                            1,
                        ],
                    )
                except ValueError:
                    logger.error("Impossible to convert key information.")
            all_annotations.append(converted_annotation)
        elif annotation.namespace == "timesig":
            all_annotations.append(annotation)

    if replace is False:
        for oa in original_annotations:
            if oa.namespace != "key_mode":
                jam.annotations.append(oa)
    # append converted annotations
    for a in all_annotations:
        jam.annotations.append(a)

    try:  # attempt saving the JAMS annotation file to disk
        jam.save(os.path.join(output_path, filename), strict=False)
    except jams.exceptions.SchemaError as jes:  # dumping error, logging for now
        logging.error(f"Could not save: {jams_path} because error occurred: {jes}")

    return chord_metadata


def parallel_parse(
    file_path: str,
    output_path: str,
    dataset_name: str,
    filename: str,
    metadata: list,
    replace: bool = False,
    handle_error: bool = True,
    verbose: bool = False,
):
    file_metadata = parse_jams(
        jams_path=file_path,
        output_path=output_path,
        dataset_name=dataset_name,
        filename=filename,
        replace=replace,
        handle_error=handle_error,
        verbose=verbose,
    )
    metadata = (
        [update_chord_list(metadata, x) for x in file_metadata][0]
        if len([update_chord_list(metadata, x) for x in file_metadata]) > 0
        else metadata
    )
    return metadata


def parse_jams_dataset(
    jams_path: str,
    output_path: str,
    dataset_name: str,
    replace: bool = False,
    handle_error: bool = True,
    verbose: bool = False,
) -> None:
    """
    Parser for JAMS files datasets that replace the chord annotations with the
    converted ones.
    Parameters
    ----------
    jams_path : str
        The path of the JAMS dataset to be converted.
    output_path : str
        The path in which the converted JAMS will be saved.
    dataset_name : str
        The name of the dataset the JAMS belongs to. Used by the conversion
        encoders/decoders.
    replace : bool (default=False)
        Indicated whether to replace the annotation or to preserve the original
        ones and hence duplicate the annotation section of the original file.
    handle_error : bool
        Boolean parameter to set whether to stop the program if a conversion
        error is met (False) or to continue and skip the error (True).
    verbose : bool
        Defines whether to log to the console the information about the chords
        being converted.
    """
    converted_jams_dir = create_dir(os.path.join(output_path, "jams-converted"))
    metadata = []
    jams_files = os.listdir(jams_path)

    Parallel(n_jobs=1, backend="threading")(
        delayed(parallel_parse)(
            file_path=os.path.join(jams_path, file),
            output_path=converted_jams_dir,
            dataset_name=dataset_name,
            filename=file,
            replace=replace,
            handle_error=handle_error,
            verbose=verbose,
            metadata=metadata,
        )
        for file in jams_files
        if os.path.isfile(os.path.join(jams_path, file))
    )

    metadata_df = pd.DataFrame(
        metadata,
        columns=[
            "original_chord",
            "converted_chord",
            "annotation_type",
            "original_namespace",
            "converted_namespace",
            "occurrences",
        ],
    )
    metadata_df.sort_values(
        by=["occurrences", "annotation_type"], inplace=True, ascending=False
    )
    logger.info(
        f"\nSaving conversion metadata file: "
        f'{os.path.join(output_path, "conversion_meta.csv")}\n'
    )
    metadata_df.to_csv(os.path.join(output_path, "conversion_meta.csv"), index=False)


def main():
    """
    Main function to read the arguments and call the conversion scripts.
    """
    parser = argparse.ArgumentParser(
        description="Converter scripts for ChoCo partitions."
    )

    parser.add_argument(
        "input_dir", type=str, help="Directory where original JAMS data is read."
    )
    parser.add_argument(
        "out_dir", type=str, help="Directory where converted JAMS will be saved."
    )
    parser.add_argument(
        "dataset_name",
        type=str,
        choices=ANNOTATION_SUPPORTED.keys(),
        help="Name of the dataset to convert.",
    )
    parser.add_argument(
        "--replace",
        type=bool,
        help="Whether to replace the annotations with " "the conversion or not.",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--handle_error",
        type=bool,
        help="Whether to raise an error if a chord is "
        'not converted or replace the chord with "N".',
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--verbose",
        type=bool,
        help="Defines whether to log to the console the "
        "information about the chords being converted",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    args = parser.parse_args()

    parse_jams_dataset(
        jams_path=args.input_dir,
        output_path=args.out_dir,
        dataset_name=args.dataset_name,
        replace=args.replace,
        handle_error=args.handle_error,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    # TEST
    # test single file
    # parse_jams('../../partitions/when-in-rome/choco/jams/when-in-rome_0.jams',
    #            '.',
    #            'when-in-rome',
    #            'when-in-rome_0.jams',
    #            False,
    #            False,
    #            True)

    # test multiple files
    # parse_jams_dataset('../../partitions/wikifonia/choco/jams',
    #                    'ciao/jams-converted',
    #                    'wikifonia',
    #                    True,
    #                    False)

    main()
