import os
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from typing import Union

import pandas as pd
from joblib import Parallel, delayed

from jams2rdf import jams2rdf


def parallel_jams2rdf(path: Union[str, Path],
                      output_path: str,
                      query_path: Union[str, Path],
                      sparql_anything_path: Union[str, Path],
                      metadata: pd.DataFrame,
                      rdf_serialisation: str = 'TTL',
                      handle_error: bool = False) -> None:
    """

    Parameters
    ----------
    path : Union[str, Path]
        The path (either absolute or relative) of the JAMS files dataset
        to be converted into RDF
    output_path : Union[str, Path]
        The path (either absolute or relative) to which the output file will be
        saved
    query_path : Union[str, Path]
        The path (either absolute or relative) to the SPARQL Anything query
    sparql_anything_path : Union[str, Path]
        The path to the SPARQL Anything .jar file, which can be downloaded from
        the SPARQL Anything GitHub repository
    metadata : pd.DataFrame
        A pandas DataFrame for storing metadata about the Knowledge Graph
        generation
    rdf_serialisation  : str
        The RDF serialisation to be used for the output file. For the
        serialisations available, please refer to the rdflib documentation
    handle_error : bool
        Defines whether to stop if an error ir raised or not.

    Returns
    -------
    None
    """
    try:
        file_path = Path(
            output_path) / f'{path.stem}.{rdf_serialisation.lower()}'

        file_metadata = jams2rdf(input_file=path,
                                 output_path=file_path,
                                 query_path=query_path,
                                 sparql_anything_path=sparql_anything_path)

        file_metadata = [path.stem, path, file_path].extend(file_metadata)
        metadata.append(file_metadata)

    except ValueError as ve:
        if handle_error:
            metadata.append([path.stem, 'error'])
        else:
            raise NameError(
                f'The conversion of the file {path.name} raised an error:\n'
                f'{ve}')


def kg_generation(dataset_path: Union[str, Path],
                  output_path: Union[str, Path],
                  query_path: Union[str, Path],
                  sparql_anything_path: Union[str, Path],
                  rdf_serialisation: str = 'TTL',
                  only_converted: bool = True,
                  handle_error: bool = False) -> pd.DataFrame:
    """

    Parameters
    ----------
    dataset_path : Union[str, Path]
        The path (either absolute or relative) of the JAMS files dataset
        to be converted into RDF
    output_path : Union[str, Path]
        The path (either absolute or relative) to which the output file will be
        saved
    query_path : Union[str, Path]
        The path (either absolute or relative) to the SPARQL Anything query
    sparql_anything_path : Union[str, Path]
        The path to the SPARQL Anything .jar file, which can be downloaded from
        the SPARQL Anything GitHub repository
    rdf_serialisation  : str
        The RDF serialisation to be used for the output file. For the
        serialisations available, please refer to the rdflib documentation
    only_converted : bool
        Defines whether to take into account only files contained in the
        "converted" folders (True) or all the JAMS files encountered (False)
    handle_error : bool
        Defines whether to stop if an error ir raised or not.

    Returns
    -------
    pd.DataFrame
    """
    dataset_path = Path(dataset_path)
    metadata = pd.DataFrame()

    harte_paths = []
    for path, dirs, files in os.walk(dataset_path):
        if only_converted:
            if 'forum' not in path:
                if 'jams-converted' in dirs:
                    harte_paths.extend(
                        Path(path).joinpath('jams-converted').rglob('*.jams'))
                elif 'jams' in dirs:
                    harte_paths.extend(
                        Path(path).joinpath('jams').rglob('*.jams'))
        else:
            harte_paths = dataset_path.rglob('*.jams')

    Parallel(n_jobs=-1)(delayed(parallel_jams2rdf)(path,
                                                   output_path,
                                                   query_path,
                                                   sparql_anything_path,
                                                   metadata,
                                                   rdf_serialisation,
                                                   handle_error) for path in
                        harte_paths)

    return metadata


def main() -> None:
    """
    Main function that allows to accept parameters from CLI using the argparse
    library.
    Returns
    -------
    None
    """
    parser = ArgumentParser(
        description='Converter from JAMS files dataset into RDF using the '
                    'SPARQL Anything software.')

    parser.add_argument('input_path',
                        type=str,
                        help='The path (either absolute or relative) of the '
                             'JAMS files directory')
    parser.add_argument('output_path',
                        type=str,
                        help='The path (either absolute or relative) to which '
                             'the output files will be saved')
    parser.add_argument('--query_path',
                        type=str,
                        help='The path (either absolute or relative) to the '
                             'SPARQL Anything query',
                        default='./queries/jams_ontology.sparql',
                        required=False)
    parser.add_argument('--sparql_anything_path',
                        type=str,
                        help='The path to the SPARQL Anything .jar file, '
                             'which can be downloaded from the SPARQL '
                             'Anything GitHub repository',
                        default='./bin/sa8.jar',
                        required=False)
    parser.add_argument('--rdf_serialisation',
                        type=str,
                        help='The RDF serialisation to be used for the output '
                             'file. For the serialisations available, please '
                             'refer to the SPARQL anything documentation.',
                        default='TTL',
                        required=False)
    parser.add_argument('--only_converted',
                        type=bool,
                        help='Defines whether to take into account only files'
                             'contained in the "converted" folders (True) or '
                             'all the JAMS files encountered (False).',
                        default=True,
                        action=BooleanOptionalAction,
                        required=False)
    parser.add_argument('--handle_error',
                        type=bool,
                        help='Defines whether to stop if an error ir raised or '
                             'not.',
                        action=BooleanOptionalAction,
                        default=False,
                        required=False)
    parser.add_argument('--save_metadata',
                        type=bool,
                        help='Defines whether to stop if an error ir raised or '
                             'not.',
                        action=BooleanOptionalAction,
                        default=True,
                        required=False)

    args = parser.parse_args()

    metadata = kg_generation(dataset_path=args.input_path,
                             output_path=args.output_path,
                             query_path=args.query_path,
                             sparql_anything_path=args.sparql_anything_path,
                             rdf_serialisation=args.rdf_serialisation,
                             only_converted=args.only_converted,
                             handle_error=args.handle_error)

    if args.save_metadata:
        metadata.to_csv(Path(args.output_path) / 'kg_generation_metadata.csv',
                        index=False,
                        header=['filename',
                                'path',
                                ])


if __name__ == "__main__":
    kg_generation('../../partitions', './knowledge-graph',
                  'queries/jams_ontology.sparql',
                  'bin/sa8.jar',
                  handle_error=True)

    # main()
