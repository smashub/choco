# ChoCo Validation

This file contains instructions for validating the data produced by the ChoCo library.\
More specifically, information is given on how to validate two main types of conversions operated by the ChoCo library,
namely conversions from the source dataset into JAMS and chord conversions into Harte notation.\
These two types of conversions are performed by the [Parser Module](#parsers-validation)
and [Converter module](#converters-validation), respectively.

## Parsers Validation

This section contains information on how to validate JAMS files produced by the Parser module of the ChoCo repository.

The validation consists of checking the correctness of annotations automatically converted into a standardised format (
JAMS).
The JAMS format is a serialisation of JSON and is documented in [1], [2] and [3].\
More specifically, validation consists of comparing the annotations contained in the JAMS file (automatically generated)
with the
original annotation files.\
Generally, each dataset originally contains annotations in a different formats.

Validation will take place on two levels:

- **preliminary_test**: a small number of tracks is assigned to each validator. The purpose of this validation phase is
  to assign a confidence score to the annotator, based on the accuracy of the test annotations produced;
- **validation**: the ChoCo datasets will be divided equally between the annotators and multiple tracks per dataset
  will be assigned to each annotator.

### Validation Guidelines

The annotations to be validated are assigned to validators in a csv file called [validator_map.csv](validator_map.csv).
This file has the following structure:

| **dataset_name** | **dataset_type** | **validator**  | **perliminary_test** |
|------------------|------------------|----------------|----------------------|
| Isophonics       | audio            | validator_name | True                 | 

The fields are described as follows:

- *dataset_name*: the dataset that needs to be validated;
- *dataset_type*: the type of the chord annotations contained in the dataset, which can be either `score` or `audio`;
- *validator*: the person who will take care of the validation of the dataset;
- *preliminary_test*: boolean that indicates whether the dataset is part of the preliminary validation or not.

### What to validate?

There are several fields that need to be checked in the validation process, which can be grouped into the following
categories:

- *file metadata*: the metadata of the file being analyzed, which include the title the composer, the artist, etc.
  This information is contained in the `file_metadata` and in the `sandbox` section of the JAMS files;
- *annotations*: general category that contains annotations related to the song. Specifically within this section it is
  important to validate:
    - *annotation metadata*: metadata related to the annotation and the annotator;
    - *chord observations*: chord annotations, including timing information. For each observation, it is therefore
      essential to
      validate both the accuracy of the chord itself, its duration and its starting time;
    - *key annotations*: annotations about the song's key, including temporal indications. For each key annotation,
      it is therefore essential to validate both the accuracy of the key label, its duration and its starting time.

There can be two main types of annotations contained in a JAMS file:

1. Audio annotations: contain time information expressed in real time (seconds);
2. Score annotations: contain time expressed symbolically. In particular, timing information is expressed through the
   convention `beasure.beat` while duration is expressed in `quarter_beat`.

You can get more information regarding these conventions and the structure of the JAMS files in the Wiki section of the
ChoCo repository, at [this link](https://github.com/jonnybluesman/choco/wiki/Examples-of-ChoCo-JAMS).

In order to make validation faster and simpler, the JAMS files have been further simplified,
as [documented here](https://github.com/jonnybluesman/choco/wiki/Evaluation-of-ChoCo), in order to reduce the number of
chords to be validated and consequently the complexity of the files.
Each file was in fact simplified using one of the following strategies:

- `last_n`: only the last n chords are taken into account;
- `first_n`: only the first n chords are considered.

Within the `partitions/partition_name/test` folder, files simplified according to the aforementioned strategies
(i.e. `first_n` or `last_n`) have already been generated.\
In the same folder, you can also find the file `test_meta.csv`, which contains information concerning the creation of
the validation files, such as the simplification strategy used, their name, and the path of both the original file
and the file to be validated.

### Instructions for Validators

The validation process should be organised as follows:

1. fork the ChoCo repository, by clicking on the `fork` button on the top right of the repository page

2. clone the forked repository:

```commandline
git clone <link_to_your_repository>
```

3. enter the repository:

```commandline
cd choco
```

4. switch to the 'validation' branch via:

```commandline
git switch validation
```

5. check in the [validator_map](validator_map.csv) file which dataset has been associated with you
6. look for the JAMS files to validate in the `partitions/dataset_name/test` folder
7. duplicate each file by adding your name to the file name, e.g., `isophonics_73_silver.jams` will
   become `isophonics_3_silver_yourname.jams`
8. for each file in the validation folder of the assigned dataset, look for the corresponding original file that is
   mapped to the `meta.csv` file, that can be found in the `partitions/dataset_name/choco` folder
9. validate the JAMS against the original files, taking into account the simplification strategy used for each file,
   which can be found in `partitions/dataset_name/test/test_meta.csv`
10. edit the renamed file (`isophonics_3_silver_yourname.jams` from the example at point 2.) by fixing any errors and/or
    inaccuracies
11. once a validation step is finished (i.e. both the preliminary_validation and final_validation levels, see above),
    [open a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)
    on the `validation` branch of the ChoCo repository.

## Converters Validation

TBD

## References:

1. https://www.researchgate.net/publication/265508524_JAMS_A_JSON_Annotated_Music_Specification_for_Reproducible_MIR_Research
2. https://github.com/marl/jams
3. https://jams.readthedocs.io/en/stable/ 