import subprocess
from rdflib import Graph
import argparse

parser = argparse.ArgumentParser(description='Converts JAMS (JSON) files into RDF.')
parser.add_argument('integers', metavar='N', type=int, nargs='+',
                    help='an integer for the accumulator')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=sum, default=max,
                    help='sum the integers (default: find the max)')

args = parser.parse_args()
print(args.accumulate(args.integers))

def jams2rdf(input, output):
    out = subprocess.check_output(["java", "-jar", "bin/sparql-anything-0.6.0.jar", "-q", "queries/jams.rq"])
    
    g = Graph()
    g.parse(out)
    
    print(g.serialize(format='turtle'))

jams2rdf()