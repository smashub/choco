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

import jams
import pandas as pd

from chord_converter import ChordConverter, ANNOTATION_SUPPORTED
from constants import CHORD_NAMESPACES
from converter_utils import create_dir, update_chord_list
from collections import defaultdict

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logger = logging.getLogger('choco.converters.converter_instances')

basedir = os.path.dirname(__file__)


def parse_jams(jams_path: str, output_path: str, dataset_name: str, filename: str, replace: bool = False):
    """

    """
    chord_metadata = []
    original_jams = jams.load(jams_path, strict=False)
    original_annotations = original_jams.annotations
    jam = jams.JAMS()
    jam.file_metadata = original_jams.file_metadata
    jam.sandbox = original_jams.sandbox

    all_annotations = []
    converter = ChordConverter(dataset_name=dataset_name)

    for annotation in original_annotations:
        if annotation.namespace in CHORD_NAMESPACES:
            converted_annotation = jams.Annotation(namespace='chord_harte')
            for observation in annotation:
                logger.info(f'Converting chord: {observation.value}')
                converted_value = converter.convert_chords(observation.value)
                converted_annotation.append(time=observation.time, duration=observation.duration,
                                            value=converted_value, confidence=observation.confidence)
                chord_metadata = update_chord_list(chord_metadata, [observation.value, converted_value, 'chord', 1])
            all_annotations.append(converted_annotation)
        elif annotation.namespace == 'key_mode':
            converted_annotation = jams.Annotation(namespace='key_mode')
            for key_observation in annotation:
                try:
                    converted_key = converter.convert_keys(key_observation.value)
                    converted_annotation.append(time=key_observation.time, duration=key_observation.duration,
                                                value=converted_key, confidence=key_observation.confidence)
                    chord_metadata = update_chord_list(chord_metadata, [key_observation.value, converted_key, 'key', 1])
                except ValueError:
                    logger.error('Impossible to convert key information.')
            all_annotations.append(converted_annotation)

    if replace is False:
        for oa in original_annotations:
            if oa.namespace != 'key_mode':
                jam.annotations.append(oa)
    # append converted annotations
    for a in all_annotations:
        jam.annotations.append(a)

    try:  # attempt saving the JAMS annotation file to disk
        jam.save(os.path.join(output_path, filename), strict=False)
    except jams.exceptions.SchemaError as jes:  # dumping error, logging for now
        logging.error(f"Could not save: {jams_path} because error occurred: {jes}")

    return chord_metadata


def parse_jams_dataset(jams_path: str, output_path: str, dataset_name: str, replace: bool = False):
    """

    """
    converted_jams_dir = create_dir(os.path.join(output_path, "jams_converted"))
    metadata = []
    jams_files = os.listdir(jams_path)
    for file in jams_files:
        if os.path.isfile(os.path.join(jams_path, file)):
            logger.info(f'\nConverting observation for file: {file}\n')
            file_metadata = parse_jams(os.path.join(jams_path, file), converted_jams_dir, dataset_name, file,
                                       replace)
            metadata = [update_chord_list(metadata, x) for x in file_metadata][0]

    metadata_df = pd.DataFrame(metadata,
                               columns=['original_chord', 'converted_chord', 'annotation_type', 'occurrences'])
    metadata_df.sort_values(by=['occurrences'], inplace=True)
    logger.info(f'\nSaving conversion metadata file: {os.path.join(output_path, "conversion_meta.csv")}\n')
    metadata_df.to_csv(os.path.join(output_path, "conversion_meta.csv"), index=False)


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
    parser.add_argument('dataset_name', type=str, choices=ANNOTATION_SUPPORTED.keys(),
                        help='Name of the dataset to convert.')
    parser.add_argument('replace', type=bool,
                        help='Whether to replace the annotations with the conversion or not.')

    args = parser.parse_args()

    parse_jams_dataset(args.input_dir,
                       args.out_dir,
                       args.dataset_name,
                       args.replace)


if __name__ == '__main__':
    main()
