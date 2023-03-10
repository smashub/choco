from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output, CalledProcessError
from typing import Union

from rdflib import Graph, Namespace
from rdflib.namespace import RDF


def jams2rdf(input_file: Union[str, Path],
             output_path: Union[str, Path],
             query_path: Union[str, Path],
             sparql_anything_path: Union[str, Path],
             rdf_serialisation: str = 'TTL') -> list:
    """
    Main function for converting a JAMS file into RDF, according to jams
    ontology and by using the SPARQL Anything software.
    In particular, this code calls the SPARQL Anything code, written in Java
    and runs it against a SPARQL Anything query, specifically developed for
    converting JAMS files.

    Parameters
    ----------
    input_file : Union[str, Path]
        The path (either absolute or relative) of the JAMS file to be converted
        into RDF
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
        serialisations available, please refer to the rdflib documentation.

    Returns
    -------
    List
        A list containing the metadata of the serialised graph.

    Raises
    -------
    ValueError
        If the output graph is empty it raises a ValueError, which very likely
        corresponds to an error in the input SPARQL query.
    """

    graph = Graph()

    github_base_url = 'https://raw.githubusercontent.com/smashub/choco/main/partitions/'
    file_path = str(input_file).split('partitions/')[-1]
    github = github_base_url + file_path

    try:
        sparql_anything_graph = check_output(['java', '-jar',
                                              sparql_anything_path,
                                              '-q', query_path,
                                              '-v', f'filepath={input_file}',
                                              '-v', f'filename={Path(input_file).name}',
                                              '-v', f'github={str(github)}',
                                              '-f', rdf_serialisation])

        graph.parse(sparql_anything_graph)
        jams_namespace = Namespace('http://w3id.org/polifonia/ontology/jams/')
        jams_file_uri = [s for s, p, o in
                         graph.triples(
                             (None, RDF.type, jams_namespace.JAMSFile))]
        if len(graph) == 0:
            raise ValueError(
                f'The output graph is empty. Please check you query.')

        graph.serialize(destination=Path(output_path),
                        format=rdf_serialisation.lower())
        return [jams_file_uri, len(graph)]

    except CalledProcessError as cpe:
        raise ValueError(
            f'The output graph is empty. Please check you query.\n{cpe}')
    except Exception as ge:
        raise ValueError(
            f'The query run returned an error:\n{ge}\n'
            f'Please check the input parameters.')


def main() -> None:
    """
    Main function that allows to accept parameters from CLI using the argparse
    library.
    Returns
    -------
    None
    """
    parser = ArgumentParser(
        description='Converter from JAMS files into RDF using the SPARQL '
                    'Anything software.')

    parser.add_argument('input_file',
                        type=str,
                        help='The path (either absolute or relative) of the '
                             'JAMS file to be converted into RDF')
    parser.add_argument('output_path',
                        type=str,
                        help='The path (either absolute or relative) to which '
                             'the output file will be saved')
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
                        default='./bin/sa.jar',
                        required=False)
    parser.add_argument('--rdf_serialisation',
                        type=str,
                        help='The RDF serialisation to be used for the output '
                             'file. For the serialisations available, please '
                             'refer to the SPARQL anything documentation.',
                        default='TTL',
                        required=False)

    args = parser.parse_args()

    jams2rdf(input_file=args.input_file,
             output_path=args.output_path,
             query_path=args.query_path,
             sparql_anything_path=args.sparql_anything_path,
             rdf_serialisation=args.rdf_serialisation)


if __name__ == '__main__':
    # Test case
    jams2rdf('examples/wikifonia.jams', 'examples/wikifonia.ttl',
             'queries/jams_ontology.sparql',
             'bin/sa8.jar')

    jams2rdf('examples/isophonics.jams', 'examples/isophonics.ttl',
             'queries/jams_ontology.sparql',
             'bin/sa8.jar')
    # main()
