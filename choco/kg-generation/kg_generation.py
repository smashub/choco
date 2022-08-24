from pathlib import Path
from typing import Union

import pandas as pd

from jams2rdf import jams2rdf


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
    dataset_path
    output_path
    query_path
    sparql_anything_path
    rdf_serialisation
    only_converted
    handle_error

    Returns
    -------

    """
    dataset_path = Path(dataset_path)
    metadata = pd.DataFrame()
    pattern = 'jams-converted/*.jams' if only_converted else '*.jams'

    for path in dataset_path.rglob(pattern):
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

    return metadata


if __name__ == "__main__":
    kg_generation('../../partitions', './knowledge-graph',
                  'queries/jams_ontology.sparql',
                  'bin/sa.jar')
