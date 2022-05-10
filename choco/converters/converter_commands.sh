# ***********************************************************************************
# Weimar Jazz Database
# ***********************************************************************************

python converter_instances.py ../../partitions/weimar/choco/jams ../../partitions/weimar/choco weimar True

# ***********************************************************************************
# Wikifonia
# ***********************************************************************************

python converter_instances.py ../../partitions/wikifonia/choco/jams ../../partitions/wikifonia/choco \
 wikifonia True

# ***********************************************************************************
# iReal Pro
# ***********************************************************************************

python converter_instances.py ../../partitions/ireal-pro/choco/playlists/jams \
  ../../partitions/ireal-pro/choco/playlists ireal-pro True

# ***********************************************************************************
# Band-in-a-Box
# ***********************************************************************************

python converter_instances.py ../../partitions/biab-internet-corpus/choco/jams \
  ../../partitions/biab-internet-corpus/choco band-in-a-box True

# ***********************************************************************************
# When-in-rome
# ***********************************************************************************

python converter_instances.py ../../partitions/when-in-rome/choco/jams \
  ../../partitions/when-in-rome/choco when-in-rome False

# ***********************************************************************************
# Rock-corpus
# ***********************************************************************************

python converter_instances.py ../../partitions/rock-corpus/choco/jams \
  ../../partitions/rock-corpus/choco rock-corpus False

# ***********************************************************************************
# Jazz-corpus
# ***********************************************************************************

python converter_instances.py ../../partitions/jazz-corpus/choco/jams \
  ../../partitions/jazz-corpus/choco jazz-corpus True

