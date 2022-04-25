from subprocess import check_output, CalledProcessError
from rdflib import Graph
import sys
import os

query_template = "queries/jams.rq"
query_current = "queries/current.rq"

def jams2rdf(input, output=None, outformat='nt'):
    with open(query_template, 'r') as r:
        query_for_file =  r.read().replace("%FILEPATH%", input)
        with  open(query_current, 'w') as w:
            w.write(query_for_file)

    g = Graph()

    try: 
        out = check_output(["java", "-jar", "bin/sparql-anything.jar", "-q", query_current])
        g.parse(out)
    except CalledProcessError as e:
        print(e)
        print("Output graph is empty for {}".format(input))
        pass
    
    if output:
        with open(output, 'w') as wo:
            wo.write(g.serialize(format=outformat))
    else:
        print(g.serialize(format=outformat))

    os.remove(query_current)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: {0} <input file> [<output file>]".format(sys.argv[0]))
        exit(2)
    elif len(sys.argv) == 2:
        # Conversion to stdout 
        infilename = sys.argv[1]
        jams2rdf(os.path.abspath(infilename))
    elif len(sys.argv) == 3:
        # Conversion to file
        infilename = sys.argv[1]
        outfilename = sys.argv[2]
        jams2rdf(os.path.abspath(infilename), outfilename)

    exit(0)
