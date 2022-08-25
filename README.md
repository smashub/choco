<p align="left">
<img src="assets/choco_logo_a.png" width="320">
</p>

# ChoCo: the Chord Corpus

ChoCo is the largest dataset providing chord annotations of scores and tracks that were collected, integrated, and semantically enriched from a number of repositories and databases — redistributed for personal or research use only. The project also provides a family of tools for chord parsing and manipulation, together with the data transformation pipeline needed to include new chord datasets in ChoCo.

| **Partition**        | **Type** | **Notation**  | **Original format** | **Annotations**  | **Genres** |  **References**  |
|----------------------|----------|---------------|---------------------|------------------|------------|:----------------:|
| Isophonics           | A        | Harte         | JAMS                | 300              | pop, rock  |        [1]       |
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

TODO: Briefly explain from the article.

## Contributing

ChoCo is not just a dataset and a Python library for dealing with chords, but a whole **data transformatin workflow** with the central goal of: standardising the format of MIR datasets according to the JAMS format, semantically describing the content of music annotations, and releasing music knowledge graph ready to be interlinked with other resources on the Web.

Therefore, we are more than happy to extend ChoCo with your annotations/datasets. To contribute, make sure that your workflow is consistent with ChoCo's transformation pipeline and submit a pull request when you are ready. Please send us an email for questions if you have questions on our code of conduct, of if the process for submitting pull requests is unclear.

## Authors

* **Jacopo de Berardinis** - [King's College London]()
* **Andrea Poltronieri** - [Università degli Studi di Bologna]()
* **Albert Meroño-Peñuela** - [King's College London]()
* **Valentina Presutti** - [Università degli Studi di Bologna]()


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


