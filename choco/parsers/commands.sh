
# ***********************************************************************************
# Isophonics
# ***********************************************************************************

isophonics() {
  python instances.py ../../partitions/isophonics/raw \
    ../../partitions/isophonics/choco/ jams audio \
    --dataset_name isophonics

  cd .. && python stats.py stats ../partitions/isophonics/choco/jams \
    ../partitions/isophonics/choco/
}

# ***********************************************************************************
# JAAH
# ***********************************************************************************

jaah() {
  python instances.py ../../partitions/jaah/raw \
    ../../partitions/jaah/choco/ json audio \
    --dataset_name jaah

  cd .. && python stats.py stats ../partitions/jaah/choco/jams \
    ../partitions/jaah/choco/
}

# ***********************************************************************************
# Schubert-Winterreise
# ***********************************************************************************

schubert-winterreise() {
  echo "... processing audio subset"
  python instances.py ../../partitions/schubert-winterreise \
    ../../partitions/schubert-winterreise/choco/audio/ multi_schubert audio \
    --dataset_name schubert-winterreise-audio \
    --score_meta ../../partitions/schubert-winterreise/raw/ann_score_overview.csv \
    --track_meta ../../partitions/schubert-winterreise/raw/ann_audio_meta.csv \
    --release_meta ../../partitions/schubert-winterreise/ann_release_metadata.csv \
    --chord_dir ../../partitions/schubert-winterreise/raw/ann_audio_chord \
    --lkey_dir ../../partitions/schubert-winterreise/raw/ann_audio_localkey-ann1 \
    --gkey_file ../../partitions/schubert-winterreise/raw/ann_audio_globalkey.csv \
    --segment_dir ../../partitions/schubert-winterreise/raw/ann_audio_structure
  
  cd .. && python stats.py stats ../partitions/schubert-winterreise/choco/audio/jams \
    ../partitions/schubert-winterreise/choco/audio && cd parsers
  
  echo "... processing score subset"
  python instances.py ../../partitions/schubert-winterreise \
    ../../partitions/schubert-winterreise/choco/score/ multi_schubert score \
    --dataset_name schubert-winterreise-score \
    --score_meta ../../partitions/schubert-winterreise/raw/ann_score_overview.csv \
    --chord_dir ../../partitions/schubert-winterreise/raw/ann_score_chord \
    --lkey_dir ../../partitions/schubert-winterreise/raw/ann_score_localkey-ann1 \
    --gkey_file ../../partitions/schubert-winterreise/raw/ann_score_globalkey.csv \
    --segment_dir ../../partitions/schubert-winterreise/raw/ann_score_structure

  cd .. && python stats.py stats ../partitions/schubert-winterreise/choco/score/jams \
    ../partitions/schubert-winterreise/choco/score
}

# ***********************************************************************************
# Billboard
# ***********************************************************************************

billboard() {
  python instances.py ../../partitions/billboard/raw \
    ../../partitions/billboard/choco/ billboard audio \
    --dataset_name billboard

  cd .. && python stats.py stats ../partitions/billboard/choco/jams \
    ../partitions/billboard/choco/
}

# ***********************************************************************************
# CASD
# ***********************************************************************************

chordify() {
  python instances.py ../../partitions/chordify/raw \
    ../../partitions/chordify/choco/ casd audio \
    --dataset_name casd \
    --track_meta ../../partitions/billboard/choco/meta.csv

  cd .. && python stats.py stats ../partitions/chordify/choco/jams \
    ../partitions/chordify/choco/
  }

# ***********************************************************************************
# Robbie Williams
# ***********************************************************************************

robbie-williams() {
  python instances.py ../../partitions/robbie-williams/raw \
    ../../partitions/robbie-williams/choco/ rwilliams audio \
    --dataset_name robbie-williams

  cd .. && python stats.py stats ../partitions/robbie-williams/choco/jams \
    ../partitions/robbie-williams/choco/
}

# ***********************************************************************************
# Uspop2002
# ***********************************************************************************

uspop2002() {
  python instances.py ../../partitions/uspop2002/raw \
    ../../partitions/uspop2002/choco/ lab-uspop audio \
    --dataset_name uspop2002

  cd .. && python stats.py stats ../partitions/uspop2002/choco/jams \
    ../partitions/uspop2002/choco/
}

# ***********************************************************************************
# RWC-Pop
# ***********************************************************************************

rwc-pop() {
  python instances.py ../../partitions/rwc-pop/raw \
    ../../partitions/rwc-pop/choco/ lab-rwc audio \
    --track_meta ../../partitions/rwc-pop/raw/meta/popular_music_database.txt \
    --dataset_name rwc-pop

  cd .. && python stats.py stats ../partitions/rwc-pop/choco/jams \
    ../partitions/rwc-pop/choco/
}

# ***********************************************************************************
# Real Book
# ***********************************************************************************

real-book() {
  python instances.py ../../partitions/real-book/raw \
    ../../partitions/real-book/choco/ xlab-rbook score \
    --dataset_name real-book

  cd .. && python stats.py stats ../partitions/real-book/choco/jams \
    ../partitions/real-book/choco/
}

# ***********************************************************************************
# Weimar Jazz Database
# ***********************************************************************************

weimar() {
  python instances.py ../../partitions/weimar/raw/wjazzd.db \
    ../../partitions/weimar/choco/ weimarjd audio \
    --dataset_name weimar

  cd .. && python stats.py stats ../partitions/weimar/choco/jams \
    ../partitions/weimar/choco/
}

# ***********************************************************************************
# iReal Pro: public playlists
# ***********************************************************************************

ireal-pro() {
  python instances.py ../../partitions/ireal-pro/raw/playlists \
    ../../partitions/ireal-pro/choco/playlists ireal score \
    --dataset_name ireal-pro

  cd .. && python stats.py stats ../partitions/ireal-pro/choco/playlists/jams \
    ../partitions/ireal-pro/choco/playlists
}


# ***********************************************************************************
# iReal Pro: public forum dump
# ***********************************************************************************

ireal-pro-forum() {
  python instances.py ../../partitions/ireal-pro/raw/forum \
    ../../partitions/ireal-pro/choco/forum ireal-forum score \
    --chocodb_path ../../xchoco_meta.db --n_workers 5 \
    --dataset_name ireal-pro-forum

  cd .. && python stats.py stats ../partitions/ireal-pro/choco/forum/jams \
    ../partitions/ireal-pro/choco/forum
}

# ***********************************************************************************
# When in Rome
# ***********************************************************************************

when-in-rome() {
  python instances.py ../../partitions/when-in-rome/raw/ \
    ../../partitions/when-in-rome/choco/ roman-wirome score \
    --dataset_name when-in-rome

  cd .. && python stats.py stats ../partitions/when-in-rome/choco/jams \
    ../partitions/when-in-rome/choco
}

# ***********************************************************************************
# Rock Corpus
# ***********************************************************************************

rock-corpus() {
  python instances.py ../../partitions/rock-corpus/raw/rs200_harmony_exp \
    ../../partitions/rock-corpus/choco/ roman-rockcorpus score \
    --track_meta ../../partitions/rock-corpus/raw/rs500.txt \
    --dataset_name rock-corpus

  cd .. && python stats.py stats ../partitions/rock-corpus/choco/jams \
    ../partitions/rock-corpus/choco
}


# ***********************************************************************************
# biab-internet-corpus
# ***********************************************************************************

biab-internet-corpus() {
  python instances.py /Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData \
    ../../partitions/biab-internet-corpus/choco/ biab score \
    --dataset_name biab-internet-corpus

  cd .. && python stats.py stats ../../partitions/biab-internet-corpus/choco/jams/ \
    ../../partitions/biab-internet-corpus/choco/
}


# ***********************************************************************************
# Jazz Corpus
# ***********************************************************************************
jazz-corpus() {
  python instances.py ../../partitions/jazz-corpus/raw/all_jazz_corpus_h.txt \
    ../../partitions/jazz-corpus/choco/ roman-jazzcorpus score \
    --dataset_name jazz-corpus

  cd .. && python stats.py stats ../partitions/jazz-corpus/choco/jams \
    ../partitions/jazz-corpus/choco
}

# ***********************************************************************************
# Mozart Piano Sonatas
# ***********************************************************************************
mozart-piano-sonatas() {
  python instances.py ../../partitions/mozart-piano-sonatas/raw/combined_harmonies.tsv \
    ../../partitions/mozart-piano-sonatas/choco/ roman-mozartps score \
    --track_meta ../../partitions/mozart-piano-sonatas/raw/metadata.tsv \
    --dataset_name mozart-piano-sonatas

  cd .. && python stats.py stats ../partitions/mozart-piano-sonatas/choco/jams \
    ../partitions/mozart-piano-sonatas/choco
}

# ***********************************************************************************
# Nottingham
# ***********************************************************************************

nottingham() {
  python instances.py ../../partitions/nottingham/raw \
    ../../partitions/nottingham/choco abc score \
    --dataset_name nottingham

  cd .. && python stats.py stats ../partitions/nottingham/choco/jams \
    ../partitions/nottingham/choco/
}


# define font-styles
bold=$(tput bold)
normal=$(tput sgr0)

# main function
for partition in "$@"
do
	if declare -f "$partition" > /dev/null
	then
		echo "Processing partition:" "$partition"
		$partition
	elif [[ "$partition" = "all" ]]
	then
		for partition_script in $(compgen -A function)
		do
			$partition_script
		done
	else
		echo "${bold}'$partition' is not a valid partition${normal}" >&2
		echo "The list of available partitions is the following:"
		for partition_script in $(compgen -A function)
		do
			echo "-" "$partition_script"
			continue
			exit 1
		done
	fi
done
