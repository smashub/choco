# ***********************************************************************************
# Weimar Jazz Database
# ***********************************************************************************

python converter_instances.py ../../partitions/weimar/choco/jams ../../partitions/weimar/choco leadsheet_weimar True

# ***********************************************************************************
# Wikifonia
# ***********************************************************************************

python converter_instances.py ../../partitions/wikifonia/choco/jams ../../partitions/wikifonia/choco \
 leadsheet_music21 True

# ***********************************************************************************
# iReal Pro
# ***********************************************************************************

# python converter_instances.py ../../partitions/weimar/choco/jams ../../partitions/weimar/choco leadsheet_weimar True

# ***********************************************************************************
# Band-in-a-Box
# ***********************************************************************************

python converter_instances.py ../../partitions/biab-internet-corpus/choco/jams \
  ../../partitions/biab-internet-corpus/choco prettify_harte True

# ***********************************************************************************
# When-in-rome
# ***********************************************************************************

python converter_instances.py ../../partitions/when-in-rome/choco/jams \
  ../../partitions/when-in-rome/choco roman_numerals False

# ***********************************************************************************
# Rock-corpus
# ***********************************************************************************

python converter_instances.py ../../partitions/rock-corpus/choco/jams \
  ../../partitions/rock-corpus/choco roman_numerals False

# ***********************************************************************************
# Jazz-corpus
# ***********************************************************************************

# python converter_instances.py ../../partitions/jazz-corpus/choco/jams \
#   ../../partitions/jazz-corpus/choco roman_numerals False

