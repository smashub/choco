cd ../choco/

python jams_tests.py test ../partitions/isophonics/choco \
    audio --skip_silver --debug

python jams_tests.py test ../partitions/jaah/choco \
    audio --skip_silver --debug

# Schubert
python jams_tests.py test ../partitions/schubert-winterreise/choco/audio \
    audio --skip_silver --debug

python jams_tests.py test ../partitions/schubert-winterreise/choco/score \
    score --skip_silver --debug

# Billboard
python jams_tests.py test ../partitions/billboard/choco/ \
    audio --skip_silver --debug

# CASD
python jams_tests.py test ../partitions/chordify/choco/ \
    audio --skip_silver --debug

# Robbie Williams
python jams_tests.py test ../partitions/robbie-williams/choco/ \
    audio --skip_silver --debug

# Real Book
python jams_tests.py test ../partitions/real-book/choco/ \
    score --skip_silver --debug

# Uspop-2002
python jams_tests.py test ../partitions/uspop2002/choco/ \
    audio --skip_silver --debug

# RWC-Pop
python jams_tests.py test ../partitions/rwc-pop/choco/ \
    audio --skip_silver --debug

# Jazz Corpus
python jams_tests.py test ../partitions/jazz-corpus/choco/ \
    score --skip_silver --debug

# Nottingham
python jams_tests.py test ../partitions/nottingham/choco/ \
    score --skip_silver --debug

# Mozart Piano Sonata
python jams_tests.py test ../partitions/mozart-piano-sonatas/choco/ \
    score --skip_silver --debug

# When in Rome
python jams_tests.py test ../partitions/when-in-rome/choco/ \
    score --skip_silver --debug

# Rock Corpus
python jams_tests.py test ../partitions/rock-corpus/choco/ \
    score --remapping ../tests/remapped_ids.csv --skip_silver --debug

# BiaB Internet Corpus
python jams_tests.py test ../partitions/biab-internet-corpus/choco/ \
    score --remapping ../tests/remapped_ids.csv --skip_silver --debug

# Wikifonia
python jams_tests.py test ../partitions/wikifonia/choco/ \
    score --remapping ../tests/remapped_ids.csv --skip_silver --debug
