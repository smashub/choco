"""
Converter
"""
import argparse
import logging
import os
import sys

sys.path.append(os.path.dirname(os.getcwd()))
parsers_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'parsers'))
sys.path.append(parsers_path)
choco_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'choco'))
sys.path.append(choco_path)

import jams
import pandas as pd

print(sys.path)
from chord_converter import ChordConverter, ANNOTATION_SUPPORTED
from constants import CHORD_NAMESPACES
from converter_utils import create_dir

logger = logging.getLogger("choco.converters.converter_instances")

basedir = os.path.dirname(__file__)


def parse_jams(jams_path: str, output_path: str, annotation_type: str, replace: bool = False):
    """

    """
    chord_metadata = []
    original_jams = jams.load(jams_path, strict=False)
    original_annotations = original_jams.annotations
    jam = jams.JAMS()
    jam.file_metadata = original_jams.file_metadata
    jam.sandbox = original_jams.sandbox

    all_annotations = []

    for annotation in original_annotations:
        if annotation.namespace in CHORD_NAMESPACES:
            converted_annotation = jams.Annotation(namespace='chord_harte')
            for observation in annotation:
                converter = ChordConverter(annotation_type=annotation_type)
                converted_value = converter.convert_chords(observation.value)
                converted_annotation.append(time=observation.time, duration=observation.duration,
                                            value=converted_value, confidence=observation.confidence)
                chord_metadata.append((observation.value, converted_value))
            all_annotations.append(converted_annotation)
        elif annotation.namespace == 'key_mode':
            converted_annotation = jams.Annotation(namespace='key_mode')
            for key_observation in annotation:
                try:
                    # TODO implement a key converter
                    converted_key = key_observation.value.replace('-', ':').replace('maj', 'major').replace('min',
                                                                                                            'minor')
                    converted_annotation.append(time=key_observation.time, duration=key_observation.duration,
                                                value=converted_key, confidence=key_observation.confidence)
                except ValueError:
                    logger.error('Impossible to convert key information.')
            all_annotations.append(converted_annotation)

    if replace is True:
        for oa in original_annotations:
            if oa.namespace != 'key_mode':
                jam.annotations.append(oa)
    # append converted annotations
    for a in all_annotations:
        jam.annotations.append(a)

    try:  # attempt saving the JAMS annotation file to disk
        jam.save(output_path, strict=(True if replace is False else True))
        return chord_metadata
    except jams.exceptions.SchemaError as jes:  # dumping error, logging for now
        logging.error(f"Could not save: {jams_path} because error occurred: {jes}")
        # TODO: return error in metadata


def parse_jams_dataset(jams_path: str, output_path: str, annotation_type: str, replace: bool = False):
    """

    """
    converted_jams_dir = create_dir(os.path.join(output_path, "jams_converted"))
    metadata = []
    jams_files = os.listdir(jams_path)
    for file in jams_files:
        file_metadata = parse_jams(jams_path + file, converted_jams_dir, annotation_type, replace)
        metadata.append(file_metadata)
    # Finalise the metadata dataframe
    metadata_df = pd.DataFrame(metadata)
    metadata_df = metadata_df.set_index("id", drop=True)
    metadata_df.to_csv(os.path.join(output_path, "meta.csv"))


def main():
    """
    Main function to read the arguments and call the conversion scripts.
    """
    parser = argparse.ArgumentParser(
        description='Converter scripts for ChoCo partitions.')

    parser.add_argument('input_dir', type=str,
                        help='Directory where original JAMS data is read.')
    parser.add_argument('out_dir', type=str,
                        help='Directory where converted JAMS will be saved.')
    parser.add_argument('annotation_type', type=str, choices=ANNOTATION_SUPPORTED.keys(),
                        help='Raw type of the annotations to process.')
    parser.add_argument('replace', type=bool,
                        help='Whether to replace the annotations with the conversion or not.')

    args = parser.parse_args()

    parse_jams_dataset(args.input_dir,
                       args.out_dir,
                       args.annotation_type,
                       args.replace)


if __name__ == '__main__':
    main()
