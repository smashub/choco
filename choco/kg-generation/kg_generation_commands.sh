
kg_single() {
  python jams2rdf.py examples/audio_wiki.jams examples/audio_wiki.ttl \
  --query_path queries/jams_ontology.sparql \
  --sparql_anything_path bin/sa.jar \
  --rdf_serialisation TTl
}

kg_all() {
  python kg_generation.py ../../partitions ./knowledge-graph \
  --query_path queries/jams_ontology.sparql \
  --sparql_anything_path bin/sa.jar \
  --rdf_serialisation N3 \
  --only_converted \
  --no-handle_error \
  --save_metadata
}
