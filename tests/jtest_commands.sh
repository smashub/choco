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