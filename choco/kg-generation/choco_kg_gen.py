import os
import sys

from jams2rdf import jams2rdf


def choco_kg_gen(path):
    abs_path = os.path.abspath(path)
    print("Walking {}".format(abs_path))

    for root, dirs, files in os.walk(abs_path):
        for file in files:
            if ".jams" in file:
                jams_path = os.path.join(root, file)
                # json_path = jams_path.replace('.jams', '.json')
                rdf_path = jams_path.replace('.jams', '.ttl')
                # print("Copying to JSON: {}".format(jams_path))
                # shutil.copy(jams_path, json_path)
                print("Converting to RDF: {}".format(jams_path))
                jams2rdf(jams_path, rdf_path)
                # print("Removing JSON: {}".format(json_path))
                # os.remove(json_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {0} <jams files path>".format(sys.argv[0]))
        exit(2)

    choco_kg_gen(sys.argv[1])

    exit(0)
