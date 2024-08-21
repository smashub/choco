# ***********************************************************************************
# Weimar Jazz Database
# ***********************************************************************************

weimar() {
  python converter_instances.py ../../partitions/weimar/choco/jams ../../partitions/weimar/choco weimar \
   --replace --no-handle_error
}

# ***********************************************************************************
# Wikifonia
# ***********************************************************************************

wikifonia() {
  python converter_instances.py ../../partitions/wikifonia/choco/jams ../../partitions/wikifonia/choco \
   wikifonia --replace --no-handle_error
}

# ***********************************************************************************
# iReal Pro
# ***********************************************************************************

ireal-pro() {
  python converter_instances.py ../../partitions/ireal-pro/choco/playlists/jams \
    ../../partitions/ireal-pro/choco/playlists ireal-pro --replace --no-handle_error
}

# ***********************************************************************************
# iReal Pro Forum
# ***********************************************************************************

ireal-pro-forum() {
 python converter_instances.py ../../partitions/ireal-pro/choco/forum/jams \
 ../../partitions/ireal-pro/choco/forum ireal-pro --replace --no-handle_error
}

# ***********************************************************************************
# Band-in-a-Box
# ***********************************************************************************

biab-internet-corpus() {
  python converter_instances.py ../../partitions/biab-internet-corpus/choco/jams \
  ../../partitions/biab-internet-corpus/choco band-in-a-box --replace --no-handle_error
}


# ***********************************************************************************
# When-in-rome
# ***********************************************************************************

when-in-rome() {
    python converter_instances.py ../../partitions/when-in-rome/choco/jams \
  ../../partitions/when-in-rome/choco when-in-rome --no-replace --no-handle_error
}

# ***********************************************************************************
# Rock-corpus
# ***********************************************************************************
rock-corpus() {
  python converter_instances.py ../../partitions/rock-corpus/choco/jams \
  ../../partitions/rock-corpus/choco rock-corpus --no-replace --no-handle_error
}

# ***********************************************************************************
# Jazz-corpus
# ***********************************************************************************

jazz-corpus() {
  python converter_instances.py ../../partitions/jazz-corpus/choco/jams \
  ../../partitions/jazz-corpus/choco jazz-corpus --replace --no-handle_error
}

# ***********************************************************************************
# Mozart Piano Sonatas
# ***********************************************************************************

mozart-piano-sonatas() {
  python converter_instances.py ../../partitions/mozart-piano-sonatas/choco/jams \
  ../../partitions/mozart-piano-sonatas/choco mozart-piano-sonatas --no-replace --no-handle_error
}

# ***********************************************************************************
# Nottingham
# ***********************************************************************************

nottingham() {
  python converter_instances.py ../../partitions/nottingham/choco/jams \
  ../../partitions/nottingham/choco nottingham --replace --no-handle_error
}

# ***********************************************************************************
# Schubert Winterreise
# ***********************************************************************************

schubert-winterreise() {
  python converter_instances.py ../../partitions/schubert-winterreise/choco/audio/jams \
  ../../partitions/schubert-winterreise/choco/audio/ schubert-winterreise --replace --no-handle_error

  python converter_instances.py ../../partitions/schubert-winterreise/choco/score/jams \
  ../../partitions/schubert-winterreise/choco/score/ schubert-winterreise --replace --no-handle_error
}

# ***********************************************************************************
# Robbie Williams
# ***********************************************************************************

robbie-williams() {
  python converter_instances.py ../../partitions/robbie-williams/choco/jams \
  ../../partitions/robbie-williams/choco robbie-williams --replace --no-handle_error
}

# ***********************************************************************************
# Real Book
# ***********************************************************************************

real-book() {
  python converter_instances.py ../../partitions/real-book/choco/jams \
  ../../partitions/real-book/choco real-book --replace --no-handle_error
}

# define font-styles
bold=$(tput bold)
normal=$(tput sgr0)

# main function
for partition in "$@"
do
	if declare -f "$partition" > /dev/null
	then
		echo "Converting partition:" "$partition"
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
