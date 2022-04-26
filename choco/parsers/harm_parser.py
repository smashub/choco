"""
Parsing utilities to read and process harmonic annotations in the format
proposed by Trevor de Clercq [tdc] and David Temperley [dt].

See: http://rockcorpus.midside.com/harmonic_analyses.html

"""
import re
import os

KEY_REG = r"\[\w[b|\#]?\]"
TSG_REG = r"\[\d+\/\d+\]"  # FIXME


def process_harm_expanded(harm_annotation):
    """
    Parse an expande harmonic annotation, as defined by Trevor and David, to
    extract chord, time signature, and local key annotations together with their
    timing information: [measure, measure offset, duration, value]. This is done
    as the timed-chord annotations released by the authors are temporally not
    consistent due to potential bugs in the `expand6` function.

    Parameters
    ----------
    harm_annotation : str
        String representation of the harmonic annotation or file path.
    
    Returns
    -------
    chords : list of lists
        The chord annotations, where local keys and roman numerals are merged .
    time_signatures : list of lists
        The extracted time signatures, with timing information as for chords.
    keys : list of lists
        The extracted local keys, with timing information as for chords.

    Notes
    -----
        - Currently, time signatures are not returned (None is given).

    """
    if os.path.isfile(harm_annotation):
        with open(harm_annotation, "r") as sample_exp_file:
            annotation_str = sample_exp_file.readlines()
        annotation_str = [ann_line for ann_line in annotation_str \
            if not ann_line.startswith("Warning")]  # filtration
        assert len(annotation_str) == 1
        annotation_str = annotation_str[0]

    annotation_str = annotation_str.strip()
    measures = annotation_str.split("|")[:-1]  # annotation finishes with "|"

    keys, chords = [], []
    for measure_no, measure in enumerate(measures):
        measure = measure.strip()  # remove leading-tailing spaces
        if len(measure) == 0:  # measure has no new elements to process
            chords[-1][-2] += 1; continue  # extend duration of previous chord
        mspan = 1/len([c for c in measure.split() if c!="["])

        measure_offset = 0
        for annotation in measure.split():
            if "[" in annotation:  # key or time sig
                key = re.match(KEY_REG, annotation)
                if key is not None:
                    current_key = key.group(0)[1:-1]
                    max_dur = len(measures) - (measure_no + mspan)
                    keys.append([measure_no, measure_offset, max_dur, current_key])
            else:  # at this stage, either a roman numeral or a dot is expected
                chord = chords[-1][-1] if annotation=="." \
                    else f"{current_key}:{annotation}" 
                chords.append([measure_no, mspan, mspan, chord])
                measure_offset += mspan  # chords advance time

    if len(keys) > 1:  # duration of local keys can be adjusted
        for i, key in enumerate(keys[:-1]):
            start_i = key[0] + key[1]
            start_j = keys[i+1][0] + keys[i+1][1]
            key[-2] = start_j - start_i
    
    return chords, None, keys
