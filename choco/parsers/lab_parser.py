"""
Utilities to parse an .xlab file to produce a JAMS annotation object.
Partially inspired by https://github.com/marl/jams/blob/master/jams/util.py
"""

import jams
import pandas as pd


def import_xlab(namespace:str, filename:str, data_column:int, format:str,
    squeeze=False, **parse_options):
    """
    Load an .xlab file as an Annotation object, assumed the following format:
        ``measure:beat start_time beat end_time chord chord key``
    By default, similarly to .lab files, .xlab files are assumed to have columns
    separated by one or more white-space characters, and have no header or index
    column information.
    
    Parameters
    ----------
    namespace : str
        The namespace for the new annotation that will encapsulate the file.
    filename : str
        Path to the .xlab file.
    data_column : int
        Index of the column providing the annotation values.
    format : str
        Whether the .xlab was obtained from a score or a track.
    squeeze : bool
        Whether the annotation should be squeezed, by compressing all repeated
        annotations with the same value (e.g. useful for repeated keys).
    parse_options : **kwargs
        Additional keyword arguments passed to ``pandas.DataFrame.read_csv``
    
    Returns
    -------
    annotation : jams.Annotation
        The newly constructed annotation object.

    """
    if data_column < 5:  # the first locations/columns are reserved for times
        raise ValueError("Annotation value should follow timing information")
    # Create a new annotation object that will wrap the file
    annotation = jams.Annotation(namespace)

    parse_options.setdefault('sep', r'\s+')
    parse_options.setdefault('engine', 'python')
    parse_options.setdefault('header', None)
    parse_options.setdefault('index_col', False)
    # A hack to handle potentially ragged .lab data
    parse_options.setdefault('names', range(20))

    data = pd.read_csv(filename, **parse_options)
    data = data.dropna(how='all', axis=1)

    for row in data.itertuples():
        time, duration = (row[1].replace(":", "."), row[3]) \
            if format=="score" else (row[2], row[4])

        annotation.append(time=time,
                          duration=duration,
                          confidence=1.0,
                          value=row[data_column])
    
    if squeeze:  # TODO to implement as separate jams utility
        annotation_sq = jams.Annotation(namespace)
        annotation_sq.data.add(annotation.data[0])
        for observation in annotation.data[1:]:
            if observation.value == annotation_sq.data[-1].value:
                last_observation = annotation_sq.data[-1]
                duration = last_observation.duration + observation.duration
                new_observation = jams.Observation(
                    time=last_observation.time,
                    duration=duration,
                    value=observation.value,
                    confidence=last_observation.confidence
                )
                annotation_sq.data.pop()
                annotation_sq.append_records([new_observation])
            else:  # the annotation value is different the previous: add
                annotation_sq.data.append_records([observation])
        annotation = annotation_sq

    return annotation
