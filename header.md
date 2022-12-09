---
id: ChoCo
Name: "ChoCo: the Chord Corpus"
brief-description: A large dataset for musical harmony knowledge graphs.
type: Dataset, Knowledge Graph
release-date: 13-10-2022
release-number: v0.1
release-link: https://github.com/smashub/choco/releases/tag/data-v0.1.0
work-package: WP2
pilot: INTERLINK
keywords:
  - chords
  - harmony
changelog: n/a.
licence:
  - CC-BY
  - CC-BY-NC
image: https://github.com/smashub/choco/raw/main/assets/choco_main.png
logo: https://github.com/smashub/choco/raw/main/assets/choco_logo_a.png
demo: https://projects.dharc.unibo.it/melody/choco/chord_corpus_statistics
links:
  - https://github.com/smashub/choco/blob/main/void.ttl
  - https://github.com/smashub/choco/blob/main/notebooks/dataset_stats.ipynb
running-instance: https://polifonia.disi.unibo.it/choco/sparql
credits: J. de Berardinis (KCL), A. Poltronieri (UniBo), A. Meroño Peñuela (KCL), V. Presutti (UniBo)
related-components:
  - ontologies
    - JAMS Ontology
    - Roman Chord Ontology
    - Chord Ontology
bibliography:
  - "de Berardinis, Jacopo; Meroño Peñuela, Albert; Poltronieri, Andrea; Presutti, Valentina. ChoCo: a Chord Corpus and a Data Transformation Workflow for Musical Harmony Knowledge Graphs (manuscript in progress)."
  - "de Berardinis, Jacopo; Meroño Peñuela, Albert; Poltronieri, Andrea; Presutti, Valentina. The Music Annotation Pattern. In The 13th Workshop on Ontology Design and Patterns (WOP2022) in conjunction with the International Semantic Web Conference (ISWC)."
---

# ChoCo: the Chord Corpus

<p align="center">
<img src="assets/choco_banner.png" width="1200">
</p>

ChoCo is a music dataset and a [Knowledge Graph](https://en.wikipedia.org/wiki/Knowledge_graph) providing 20K+ timed chord annotations of scores and tracks. To compile ChoCo, we integrated, standardised, and semantically enriched from a number of repositories and databases, covering a variety of genres and styles (more info [below](#overview)).

To achieve consistency across annotations, chords are casted to the following 2 notational families: (i) [Harte](https://ismir2005.ismir.net/proceedings/1080.pdf), generalising Leadsheet-based notations and extensively used in music information retrieval systems; (ii) [Roman numerals](https://en.wikipedia.org/wiki/Roman_numeral_analysis), a well-known notation standard where chords are named according to their degree. In addition, to achieve interopability, Roman numeral chords are syntactically converted to the Harte notation. This implies that a corresponding Harte annotation is always available for all tracks/pieces in ChoCo.

The resulting annotations are rich in provenance data, including metadata of the annotated work or track, authors of the annotations, identifiers, and links, etc. We emphasise that the current version of ChoCo only includes high-quality timed chord annotations that were produced by **human** annotators (e.g. music experts, students), or crowdsourced and verified before publication.

<p align="center">
<img src="assets/choco_main.png" width="600">
</p>

ChoCo also comes with a family of tools for chord parsing and manipulation (*tutorial coming soon!*), together with a data transformation pipeline (a [Smashub](https://smashub.github.io) instance) to include new chord datasets in ChoCo.

The harmonic annotations in ChoCo are released in 2 different formats: JAMS and RDF.

## ChoCo is a JAMS dataset

ChoCo is released as a [JAMS](https://jams.readthedocs.io) dataset, where audio and score annotations are distinguished by the `type` attribute in their `Sandbox`; and temporal/metrical information is expressed in seconds (for audio) and measure:beat (for scores);

## ChoCo is also a Knowledge Graph
ChoCo also comes as a Knowledge Graph, based on our [JAMS ontology](https://github.com/polifonia-project/jams-ontology) to model music annotations, and on the [Chord](https://motools.sourceforge.net/chord_draft_1/chord.html) and [Roman](https://github.com/polifonia-project/roman-chord-ontology) ontologies to semantically describe chords; a SPARQL endpoint is available at [this link](https://polifonia.disi.unibo.it/choco/sparql).


## <a name="overview"></a> Content

The current version of ChoCo contains 20,280 JAMS files: 2,283 from the audio partitions, and 17,997 collected from symbolic music.
In turn, these JAMS files provide 42,187 different annotations: 20,924 chord annotations in the Harte notation, and 20,423 annotations of tonality and modulations -- hence spanning both local and global keys, when available.
Besides the harmonic content, ChoCo also provides 554 structural annotations (structural segmentations related to music form) and 286 beat annotations (temporal onsets of beats) for the audio partitions.

| **Partition**        | **Type** | **Notation**  | **Original format** | **Annotations**  | **Genres** |  **References**  |
|----------------------|----------|---------------|---------------------|------------------|------------|:----------------:|
| Isophonics           | A        | Harte         | LAB                 | 300              | pop, rock  |        [1]       |
| JAAH                 | A        | Harte         | JSON                | 113              | jazz       |        [2]       |
| Schubert-Winterreise | A, S     | Harte         | csv                 | 25 (S), 25*9 (A) | classical  |        [3]       |
| Billboard            | A        | Harte         | LAB, txt            | 890 (740)        | pop        |        [4]       |
| Chordify             | A        | Harte         | JAMS                | 50*4             | pop        |        [5]       |
| Robbie Williams      | A        | Harte         | LAB, txt            | 61               | pop        |        [6]       |
| The Real Book        | S        | Harte         | LAB                 | 2486             | jazz       |        [7]       |
| Uspop 2002           | A        | Harte         | LAB                 | 195              | pop        |        [8]       |
| RWC-Pop              | A        | Harte         | LAB                 | 100              | pop        |        [9]       |
| Weimar Jazz Database | A        | Leadsheet     | SQL                 | 456              | jazz       |       [10]       |
| Wikifonia            | S        | Leadsheet     | mxl                 | 6500+            | various    |       [11]       |
| iReal Pro            | S        | Leadsheet     | iReal               | 2000+            | various    |       [12]       |
| Band-in-a-Box        | S        | Leadsheet     | mgu, sku            | 5000+            | various    |       [13]       |
| When in Rome         | S        | Roman         | RomanText           | 450              | classical  |       [14]       |
| Rock Corpus          | S        | Roman         | har                 | 200              | rock       |       [15]       |
| Mozart Piano Sonata  | S        | Roman         | DCMLab              | 54 (18)          | classical  |       [16]       |
| Jazz Corpus          | S        | Hybrid        | txt                 | 76               | jazz       |       [17]       |
| Nottingham           | S        | ABC           | ABC                 | 1000+            | folk       |       [18]       |

This provides a heterogeneous corpus with a large extent of variability in the duration of pieces, which also confirms the diversity of musical genres in ChoCo.
Additional statistics can be found from [this](https://github.com/smashub/choco/blob/main/notebooks/dataset_stats.ipynb) Jupyter notebook.

## ℹ️ More info at [this page](https://github.com/smashub/choco/)