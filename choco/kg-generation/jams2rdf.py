from argparse import ArgumentParser
from subprocess import check_output, CalledProcessError

from rdflib import Graph


def jams2rdf(input_file: str,
             output_path: str,
             query_path: str,
             sparql_anything_path: str,
             rdf_serialisation: str = 'TTL') -> None:
    """
    Main function for converting a JAMS file into RDF, according to jams
    ontology and by using the SPARQL Anything software.
    In particular, this code calls the SPARQL Anything code, written in Java
    and runs it against a SPARQL Anything query, specifically developed for
    converting JAMS files.

    Parameters
    ----------
    input_file : str
        The path (either absolute or relative) of the JAMS file to be converted
        into RDF
    output_path : str
        The path (either absolute or relative) to which the output file will be
        saved
    query_path : str
        The path (either absolute or relative) to the SPARQL Anything query
    sparql_anything_path : str
        The path to the SPARQL Anything .jar file, which can be downloaded from
        the SPARQL Anything GitHub repository
    rdf_serialisation  : str
        The RDF serialisation to be used for the output file. For the
        serialisations available, please refer to the SPARQL anything
        documentation.

    Returns
    -------
    None

    Raises
    -------
    ValueError
        If the output graph is empty it raises a ValueError, which very likely
        corresponds to an error in the input SPARQL query.
    """

    graph = Graph()

    try:
        sparql_anything_graph = check_output(['java', '-jar',
                                              sparql_anything_path,
                                              '-q', query_path,
                                              '-v', f'filepath={input_file}',
                                              '-o', output_path,
                                              '-f', rdf_serialisation])
        graph.parse(sparql_anything_graph)
    except CalledProcessError as cpe:
        raise ValueError(
            f'The output graph is empty. Please check you query.\n{cpe}')
    except Exception as ge:
        raise ValueError(
            f'The query run returned an error:\n{ge}\n'
            f'Please check the input parameters.')


def main() -> None:
    """

    Returns
    -------

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
    # # Test case
    # jams2rdf('examples/wikifonia.jams', 'examples/ciao.ttl',
    #          'queries/jams_ontology.sparql',
    #          'bin/sa.jar')

    main()
