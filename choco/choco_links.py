import sys
import os
import hashlib
import json
from json import JSONDecodeError
from difflib import SequenceMatcher
from rdflib import Graph, URIRef

similarity_ratio = 0.75
midildc_prefix = "https://purl.org/midi-ld/piece/"
choco_prefix = "https://purl.org/choco/data/"
musicbrainz_prefix = "https://musicbrainz.org/recording/"
owl_prefix = "http://www.w3.org/2002/07/owl#"


def midi_choco_links(midi_path, jams_path):
    links = Graph()

    abs_midi_path = os.path.abspath(midi_path)
    abs_jams_path = os.path.abspath(jams_path)
    print("Walking {}".format(abs_midi_path))
    
    midis = []
    for root,dirs,files in os.walk(abs_midi_path):
        for file in files:
            if ".mid" in file or ".midi" in file:
                midi_file_path = os.path.join(root, file)
                midi_file_name = os.path.splitext(file)[0]
                md5_midi_id = hashlib.md5(open(midi_file_path, 'rb').read()).hexdigest()
                midis.append({'id': md5_midi_id, 'name': midi_file_name})
    
    print("Walking {}".format(abs_jams_path))

    jams = []
    for root,dirs,files in os.walk(abs_jams_path):
        for file in files:
            if ".jams" in file:
                with open(os.path.join(root,file), 'r') as jams_file:
                    try:
                        jams_data = json.load(jams_file)
                        jams_collection = str(os.path.join(root,file)).split('/')[6]
                        jams_item = str(os.path.join(root,file)).split('/')[-1].split('.')[0]
                        jams_id = jams_collection + '/' + jams_item
                        jams_name = str(jams_data['file_metadata']['artist']) + " " + str(jams_data['file_metadata']['title'])
                        jams.append({'id': jams_id, 'name': jams_name})

                        # If we have links to MusicBrainz, we add them
                        if 'MB' in jams_data['file_metadata']['identifiers']:
                            s = URIRef(choco_prefix + jams_id)
                            p = URIRef(owl_prefix + 'sameAs')
                            o = URIRef(musicbrainz_prefix + jams_data['file_metadata']['identifiers']['MB'])
                            links.add((s,p,o))

                    except JSONDecodeError as e:
                        print("Error reading JAMS file {}: {}".format(os.path.join(root,file), e))
                        pass

    print("Comparing JAMS with MIDI metadata...")
    
    for m in midis:
        for j in jams:
            if SequenceMatcher(None, m['name'], j['name']).ratio() > similarity_ratio:
                print("{} || {}".format(m['name'], j['name']))
                s = URIRef(midildc_prefix + m['id'])
                p = URIRef(owl_prefix + 'sameAs')
                o = URIRef(choco_prefix + j['id'])
                links.add((s,p,o))

    with open('links.nt', 'w') as linksfile:
        linksfile.write(links.serialize(format='nt'))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: {0} <midi file path> <jams file path>".format(sys.argv[0]))
        exit(2)

    midi_choco_links(sys.argv[1], sys.argv[2])

    exit(0)