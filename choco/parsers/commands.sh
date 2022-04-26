
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


# ***********************************************************************************
# Robbie Williams
# ***********************************************************************************

python instances.py ../../partitions/robbie-williams/raw \
	../../partitions/robbie-williams/choco/ rwilliams audio \
	--dataset_name robbie-williams

python stats.py ../partitions/robbie-williams/choco/jams \
	../partitions/robbie-williams/choco/


# ***********************************************************************************
# Uspop2002
# ***********************************************************************************

python instances.py ../../partitions/uspop2002/raw \
	../../partitions/uspop2002/choco/ lab audio \
	--dataset_name uspop2002

python stats.py ../partitions/uspop2002/choco/jams \
	../partitions/uspop2002/choco/


# ***********************************************************************************
# RWC-Pop
# ***********************************************************************************

python instances.py ../../partitions/rwc-pop/raw \
	../../partitions/rwc-pop/choco/ lab-rwc audio \
	--track_meta ../../partitions/rwc-pop/raw/meta/popular_music_database.txt \
	--dataset_name rwc-pop

python stats.py ../partitions/rwc-pop/choco/jams \
	../partitions/rwc-pop/choco/


# ***********************************************************************************
# Real Book
# ***********************************************************************************

python instances.py ../../partitions/real-book/raw \
	../../partitions/real-book/choco/ xlab-rbook score \
	--dataset_name real-book

python stats.py ../partitions/real-book/choco/jams \
	../partitions/real-book/choco/


# ***********************************************************************************
# Weimar Jazz Database
# ***********************************************************************************

python instances.py ../../partitions/weimar/raw/wjazzd.db \
	../../partitions/weimar/choco/ weimarjd audio \
	--dataset_name weimar

python stats.py ../partitions/weimar/choco/jams \
	../partitions/weimar/choco/


# ***********************************************************************************
# iReal Pro: public playlists
# ***********************************************************************************

python instances.py ../../partitions/ireal-pro/raw/playlists \
	../../partitions/ireal-pro/choco/playlists ireal score \
	--dataset_name ireal-pro

python stats.py ../partitions/ireal-pro/choco/playlists/jams \
	../partitions/ireal-pro/choco/playlists


# ***********************************************************************************
# When in Rome
# ***********************************************************************************

python instances.py ../../partitions/when-in-rome/raw/ \
	../../partitions/when-in-rome/choco/ roman-wirome score \
	--dataset_name when-in-rome

python stats.py ../partitions/when-in-rome/choco/jams \
	../partitions/when-in-rome/choco


# ***********************************************************************************
# Rock Corpus
# ***********************************************************************************

python instances.py ../../partitions/rock-corpus/raw/rs200_harmony_exp \
	../../partitions/rock-corpus/choco/ roman-rockcorpus score \
	--track_meta ../../partitions/rock-corpus/raw/rs500.txt \
	--dataset_name rock-corpus

python stats.py ../partitions/rock-corpus/choco/jams \
	../partitions/rock-corpus/choco

# ***********************************************************************************
# biab-internet-corpus
# ***********************************************************************************

python instances.py ../../partitions/biab-internet-corpus/choco/raw/ \
	../../partitions/biab-internet-corpus/choco/ biab score \
	--dataset_name biab-internet-corpus

python ../stats.py ../../partitions/biab-internet-corpus/choco/jams/ \
	../../partitions/biab-internet-corpus/choco/
