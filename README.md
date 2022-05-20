# ChoCo
The Chord Corpus

ChoCo is the largest dataset providing chord annotations of scores and tracks that were collected, integrated, and semantically enriched from a number of repositories and databases — redistributed for personal or research use only. The project also provides a family of tools for chord parsing and manipulation, together with the data transformation pipeline needed to include new chord datasets in ChoCo.

| **Partition**        | **Type**     | **Notation** | **Format** | **Annotations**          | **Status** |
|----------------------|--------------|--------------|------------|--------------------------|------------|
| Isophonics           | audio        | Harte        | JAMS       | 300                      | JAMS       |
| JAAH                 | score        | Harte        | JSON       | 113                      | JAMS       |
| Schubert-Winterreise | audio, score | Harte        | CSV        | 25 (score), 25*9 (audio) | JAMS       |
| Billboard            | audio        | Harte        | LAB, TXT   | 890 (740)                | JAMS       |
| Chordify             | audio        | Harte        | JAMS       | 50                       | JAMS       |
| Robbie Williams      | audio        | Harte        | LAB, TXT   | 61                       | JAMS       |
| The Real Book        | score        | Harte        | LAB        | 2486                     | JAMS       |
| Uspop 2002           | audio        | Harte        | LAB        | 195                      | JAMS       |
| RWC-Pop              | audio        | Harte        | LAB        | 200/300                  | JAMS       |
| Weimar Jazz Database | score        | Leadsheet    | DB         | 456                      | JAMS       |
| Wikifonia            | score        | Leadsheet    | MXL        | 6500+                    | JAMS       |
| iReal Pro            | score        | Leadsheet    | iReal      | 2000+                    | JAMS       |
| Band-in-a-Box        | score        | Leadsheet    | mgu, sku   | 5000+                    | JAMS       |
| When in Rome         | score        | Roman        | txt        | 450                      | JAMS       |
| Rock Corpus          | score        | Roman        | harm       | 200                      | JAMS       |
| Jazz Corpus          | score        | Roman        | txt        | 76                       | JAMS       |
| Mozart Piano Sonata  | score        | Roman        | DCMLab     | 54 (18)                  | JAMS       |
| Nottingham           | score        | ABC          | ABC        | 1000+                    | JAMS       |


## Transformation workflow

<p align="center">
<img src="assets/lomir_workflow.png" width="800">
</p>

TODO: Briefly explain from the article.

## Exporting ChoCo as a JAMS dataset

```
python create.py ../../musilar/data/influence/choco-beatles \
    --jams_type original --n_workers 4
```

### Create your own ChoCo dataset

If you want a custom subset of ChoCo, based on specific partitions to include/exclude or on certain expected metadata, you just need to play around with the `choco/create.py` script (see below for documentation).

```
Dataset creation scripts for ChoCo.

positional arguments:
  out_dir               Directory where data will be exported.

optional arguments:
  -h, --help            show this help message and exit
  --jams_type {original,converted}
                        Type of JAMS files to consider from ChoCo.
  --input_meta INPUT_META
                        Path to the CSV file with the desired metadata.
  --include INCLUDE [INCLUDE ...]
                        Name of partitions to include in the dataset.
  --exclude EXCLUDE [EXCLUDE ...]
                        Name of partitions to exclude from the dataset.
  --n_workers N_WORKERS
                        Number of workers for parallel computation.
  --log_dir LOG_DIR     Directory where log files will be generated.
  --resume              Whether to resume the transformation process.
```

Example on a custom subset of ChoCo that we are using in `musilar` to trace musical influence.
```
python create.py ../../musilar/data/influence/choco-beatles --jams_type original \
    --exclude chordify robbie-williams uspop2002 rwc-pop biab-internet-corpus \
    jazz-corpus wikifonia --n_workers 4
```

Example of a custom subset including audio annotations only.

```
python create.py ../../musilar/data/genre/choco-audio --jams_type original \
    --include isophonics schubert-winterreise billboard chordify \
    robbie-williams uspop2002 rwc-pop --n_workers 4
```
