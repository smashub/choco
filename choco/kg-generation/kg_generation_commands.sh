
python kg_generation.py ../../partitions ./knowledge-graph-ttl \
  --query_path queries/jams_ontology.sparql \
  --sparql_anything_path bin/sa8.jar \
  --rdf_serialisation TTL \
  --only_converted \
  --no-handle_error \
  --save_metadata


python kg_generation.py ../../partitions ./knowledge-graph-nt \
  --query_path queries/jams_ontology.sparql \
  --sparql_anything_path bin/sa8.jar \
  --rdf_serialisation N3 \
  --only_converted \
  --no-handle_error \
  --save_metadata
