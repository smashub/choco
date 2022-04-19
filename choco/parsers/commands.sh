
# ***********************************************************************************
# Schubert-Winterreise
# ***********************************************************************************

python instances.py ../../partitions/schubert-winterreise \
	../../partitions/schubert-winterreise/choco/audio/ multi_schubert audio \
	--dataset_name schubert-winterreise-audio \
	--score_meta ../../partitions/schubert-winterreise/raw/ann_score_overview.csv \
	--track_meta ../../partitions/schubert-winterreise/raw/ann_audio_meta.csv \
	--release_meta ../../partitions/schubert-winterreise/ann_release_metadata.csv \
	--chord_dir ../../partitions/schubert-winterreise/raw/ann_audio_chord \
	--lkey_dir ../../partitions/schubert-winterreise/raw/ann_audio_localkey-ann1 \
	--gkey_file ../../partitions/schubert-winterreise/raw/ann_audio_globalkey.csv

python instances.py ../../partitions/schubert-winterreise \
	../../partitions/schubert-winterreise/choco/score/ multi_schubert score \
	--dataset_name schubert-winterreise-score \
	--score_meta ../../partitions/schubert-winterreise/raw/ann_score_overview.csv \
	--chord_dir ../../partitions/schubert-winterreise/raw/ann_score_chord \
	--lkey_dir ../../partitions/schubert-winterreise/raw/ann_score_localkey-ann1 \
	--gkey_file ../../partitions/schubert-winterreise/raw/ann_score_globalkey.csv

python stats.py ../partitions/schubert-winterreise/choco/audio/jams \
	../partitions/schubert-winterreise/choco/audio

python stats.py ../partitions/schubert-winterreise/choco/score/jams \
	../partitions/schubert-winterreise/choco/score


# ***********************************************************************************
# Billboard
# ***********************************************************************************

python instances.py ../../partitions/billboard/raw \
	../../partitions/billboard/choco/ billboard audio \
	--dataset_name billboard

python stats.py ../partitions/billboard/choco/jams \
	../partitions/billboard/choco/

# ***********************************************************************************
# CASD
# ***********************************************************************************

python instances.py ../../partitions/chordify/raw \
	../../partitions/chordify/choco/ casd audio \
	--dataset_name casd \
	--track_meta ../../partitions/billboard/choco/meta.csv

python stats.py ../partitions/chordify/choco/jams \
	../partitions/chordify/choco/
