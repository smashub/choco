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
| Band-in-a-Box        | score        | Leadsheet    | mgu, sku   | 5000+                    | WIP        |
| When in Rome         | score        | Roman        | txt        | 450                      | JAMS       |
| Rock Corpus          | score        | Roman        | harm       | 200                      | JAMS       |
| Jazz Corpus          |              | Roman        |            | 111                      |            |
| Mozart Piano Sonata  | score        | Roman        |            | 18                       |            |
| Nottingham           | score        | ABC          | ABC        | 1000+                    | JAMS       |


## Transformation workflow

<p align="center">
<img src="assets/lomir_workflow.png" width="800">
</p>
