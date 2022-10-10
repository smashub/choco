<p align="left">
<img src="assets/choco_logo_a.png" width="320">
</p>

# ChoCo: the Chord Corpus

ChoCo provides 20K+ timed chord annotations from scores and tracks, that were collected, standardised, integrated, and semantically enriched from a number of repositories and databases (see [overview](#overview)).

The harmonic annotations in ChoCo are released in 2 formats:
- As a [JAMS](https://jams.readthedocs.io) dataset, where audio and score annotations are distinguished by the `type` attribute in their main `Sandbox`;
- As a Knowledge Graph, based on our [JAMS ontology](https://github.com/polifonia-project/jams-ontology) and the [Chord](https://motools.sourceforge.net/chord_draft_1/chord.html), [Roman](https://github.com/polifonia-project/roman-chord-ontology) ontologies; with a SPARQL endpoint at [this link](https://polifonia.disi.unibo.it/choco/sparql).

To achieve consistency and interoperability across annotations, chords are casted to the following 2 notational families, and syntactically converted to the Harte notation. 
- [Harte](https://ismir2005.ismir.net/proceedings/1080.pdf), generalising Leadsheet-based notations, and always available for all the annotations.
- [Roman numerals](https://en.wikipedia.org/wiki/Roman_numeral_analysis), a well-known notation standard where chords are named according to their degree.

The resulting annotations are rich in provenance data (e.g. metadata of the annotated work, authors of annotations, identifiers, etc.) and ...

ChoCo also comes with a family of tools for chord parsing and manipulation, together with a data transformation pipeline (a Smashub instance) to include new chord datasets in ChoCo.

## How to use ChoCo

**Option 1** (JAMS): If you are using the ChoCo as a JAMS dataset and you are using Python, you only need to make sure tha the `jams` library is installed in your system.
```python
pip install jams
```
After downloading a release of ChoCo (link), you can read, manipulate, and edit harmonic annotations via the `jams` library.
```python
import jams

audio_jams = jams.load("blabla/jams/blabla.jams")
```

**Option 2** (KG) If you are using ... you can use directly use the RDF files ... or query the SPARQL endpoint at ...
- Link to a query and example of query

## <a name="overview"></a> Overview

The current version of ChoCo contains ... JAMS files 

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


## Transformation workflow

<p align="center">
<img src="assets/lomir_workflow.png" width="800">
</p>

**Step 1: Jamification**
>Achieving interoperability among annotation standards.

Considering the diversity of annotation formats and conventions for data organisation (the way content is scattered across folders, files, database tables, etc.), each chord dataset in ChoCo undergoes a standardisation process finalised to the creation of a JAMS dataset.
This is needed to aggregate all relevant annotations of a piece (chord, keys, etc.) in a single JAMS file, and to extract content metadata from relevant sources.


**Step 2: Conversion**
>Achieving interoperability among chord notations.

The Chonverter module ...

**Step 3: Knowledge Graph creation**.
>Releasing musical knowledge that can be linked to other resources on the Web.

TODO

## Install

If you want to use ChoCo as a Python library in projects, first clone the repository and install the requirements through conda or pip.
```
git clone https://github.com/jonnybluesman/choco.git
```
In your environment, install the requirements throguh `pip`.
```
pip install -r requirements.txt
```





## Contributing

We are more than happy to extend ChoCo with your annotations/datasets. To contribute, make sure that your workflow is consistent with ChoCo's transformation pipeline and submit a pull request when you are ready. Please send us an email for questions if you have questions on our code of conduct, of if the process for submitting pull requests is unclear.

## Authors and attribution

* **Jacopo de Berardinis** - [King's College London](https://jonnybluesman.github.io)
* **Andrea Poltronieri** - [Università degli Studi di Bologna](https://andreapoltronieri.org)
* **Albert Meroño-Peñuela** - [King's College London](https://www.albertmeronyo.org)
* **Valentina Presutti** - [Università degli Studi di Bologna](https://www.unibo.it/sitoweb/valentina.presutti)

```
@inproceedings{deberardinis2021lharp,
  title={ChoCo: a Chord Corpus and a Data Transformation Workflow for Musical Harmony Knowledge Graphs},
  author={de Berardinis, Jacopo and Meroño-Peñuela, Albert and Poltronieri, Andrea and Presutti, Valentina},
  booktitle={Manuscript under review},
  year={2022}
}
```

## Acknowledgments

We thank all the annotators for contributing to the project.


## License

![](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)
This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).


## References

[1] Mauch, M., Cannam, C., Davies, M., Dixon, S., Harte, C., Kolozali, S., Tidhar, D., Sandler, M.: Omras2 metadata project 2009. In: 12th International Society for Music Information Retrieval Conference. ISMIR

[2] Eremenko, V., Demirel, E., Bozkurt, B., Serra, X.: Jaah: Audio-aligned jazz harmony dataset (Jun 2018), https://doi.org/10.5281/zenodo.1290

[3] Weiß, C., Zalkow, F., Arifi-Müller, V., Müller, M., Koops, H.V., Volk, A., Grohganz, H.G.: Schubert winterreise dataset: A multimodal scenario for music analysis. Journal on Computing and Cultural Heritage (JOCCH) 14(2), 1–18 (2021)

[4] Burgoyne, J.A., Wild, J., Fujinaga, I.: An expert ground truth set for audio chord recognition and music analysis. In: ISMIR. vol. 11, pp. 633–638 (2011)

[5] Koops, H.V., de Haas, W.B., Burgoyne, J.A., Bransen, J., Kent-Muller, A., Volk, A.: Annotator subjectivity in harmony annotations of popular music. Journal of New Music Research 48(3), 232–252 (2019), https://doi.org/10.1080/09298215.2019.1613436

[6] Di Giorgi, B., Zanoni, M., Sarti, A., Tubaro, S.: Automatic chord recognition based on the probabilistic modeling of diatonic modal harmony. In: nDS’13; Proceedings of the 8th International Workshop on Multidimensional Systems. pp. 1–6. VDE (2013)

[7] Mauch, M., Dixon, S., Harte, C., et al.: Discovering chord idioms through beatles and real book songs (2007)

[8] Berenzweig, A., Logan, B., Ellis, D.P., Whitman, B.: A large-scale evaluation of acoustic and subjective music-similarity measures. Computer Music Journal pp. 63–76 (2004)

[9] Goto, M., Hashiguchi, H., Nishimura, T., Oka, R.: Rwc music database: Popular, classical and jazz music databases. In: Ismir. vol. 2, pp. 287–288 (2002)

[10] Pfleiderer, M., Frieler, K., Abeßer, J., Zaddach, W.G., Burkhart, B. (eds.): Inside the Jazzomat - New Perspectives for Jazz Research. Schott Campus (2017)

[11] Wikifonia page on Wikipedia (discountined project) https://en.wikipedia.org/wiki/Wikifonia

[12] iReal Pro public playlists https://www.irealpro.com/main-playlists

[13] De Haas, W.B., Robine, M., Hanna, P., Veltkamp, R.C., Wiering, F.: Comparing approaches to the similarity of musical chord sequences. In: International Sympo- sium on Computer Music Modeling and Retrieval. pp. 242–258. Springer (2010)

[14] Micchi, G., Gotham, M., Giraud, M.: Not all roads lead to rome: Pitch represen- tation and model architecture for automatic harmonic analysis. Transactions of the International Society for Music Information Retrieval (TISMIR) 3(1), 42–54 (2020)

[15] De Clercq, T., Temperley, D.: A corpus analysis of rock harmony. Popular Music 30(1), 47–70 (2011)

[16] Hentschel, J., Neuwirth, M., Rohrmeier, M.: The annotated mozart sonatas: Score, harmony, and cadence. Transactions of the International Society for Music Infor- mation Retrieval 4(1) (2021)

[17] Granroth-Wilding, M., Steedman, M.: A robust parser-interpreter for jazz chord sequences. Journal of New Music Research 43(4), 355–374 (2014)

[18] Nottingham database. https://ifdo.ca/~seymour/nottingham/nottingham.html, accessed: 2022-05-05


