# ***********************************************************************************
# Weimar Jazz Database
# ***********************************************************************************

weimar() {
  python converter_instances.py ../../partitions/weimar/choco/jams ../../partitions/weimar/choco weimar True True
}

# ***********************************************************************************
# Wikifonia
# ***********************************************************************************

wikifonia() {
  python converter_instances.py ../../partitions/wikifonia/choco/jams ../../partitions/wikifonia/choco \
   wikifonia True True
}

# ***********************************************************************************
# iReal Pro
# ***********************************************************************************

ireal-pro() {
  python converter_instances.py ../../partitions/ireal-pro/choco/playlists/jams \
    ../../partitions/ireal-pro/choco/playlists ireal-pro True True
}

# ***********************************************************************************
# iReal Pro Forum
# ***********************************************************************************

ireal-pro-forum() {
  python converter_instances.py ../../partitions/ireal-pro/choco/forum/jams \
  ../../partitions/ireal-pro/choco/forum ireal-pro True True
}

# ***********************************************************************************
# Band-in-a-Box
# ***********************************************************************************

biab-internet-corpus() {
  python converter_instances.py ../../partitions/biab-internet-corpus/choco/jams \
  ../../partitions/biab-internet-corpus/choco band-in-a-box True True
}


# ***********************************************************************************
# When-in-rome
# ***********************************************************************************

when-in-rome() {
    python converter_instances.py ../../partitions/when-in-rome/choco/jams \
  ../../partitions/when-in-rome/choco when-in-rome False True
}

# ***********************************************************************************
# Rock-corpus
# ***********************************************************************************
rock-corpus() {
  python converter_instances.py ../../partitions/rock-corpus/choco/jams \
  ../../partitions/rock-corpus/choco rock-corpus False True
}

# ***********************************************************************************
# Jazz-corpus
# ***********************************************************************************

jazz-corpus() {
  python converter_instances.py ../../partitions/jazz-corpus/choco/jams \
  ../../partitions/jazz-corpus/choco jazz-corpus True True
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
