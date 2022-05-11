"""
Utilities for comparing strings and filtering metadata dataframe accordingly.

"""
import re
import itertools
from functools import partial

import pandas as pd

import unidecode
import textdistance as td
from difflib import SequenceMatcher


def preprocess_compstring(string):
    """
    Pre-process a given string and prepare it for comparison/similarity.
    
    Notes:
        - Parentheses may have a different meaning, depending on the context.

    """
    new_string = string.lower()
    new_string = re.sub("\(.+?\)", "", new_string)
    new_string = unidecode.unidecode(new_string)
    new_string = re.sub("\.", "", new_string)
    new_string = re.sub("\s+", " ", new_string)
    new_string = new_string.strip()

    return new_string


def orderless_similarity(x, y, simi_fn):
    """
    Wrapper for edit-based similarity functions, returning the best
    similarity score following the permutation of tokens / 1-grams.

    simi_fn : fn
        A function f(x, y) where x is the searched content and y is the query.

    """
    current_max = 0

    for permutation in list(itertools.permutations(y.split())):
        simi_score = simi_fn(x, " ".join(permutation))
        current_max = simi_score if simi_score > current_max else current_max

    return current_max


def filter_metadata(metadata, attribute, query, simi_fn=None, 
    threshold=.8, orderless=False):
    """
    Simple filtration/selection of a dataframe via ? similarity.

    Parameters
    ----------
    metadata : str or pd.DataFrame
        The content metadata to consider
    attribute : str
        Name of the column to use for search in the content metadata
    query : str
        String query to consider
    simi_fn : textdistance.BaseSimilarity
        A textdistance distance/similarity function to use for comparison.
    threshold : float
        Minimum threshold in (0,1] to include a match

    Returns
    -------
    matches : pd.DataFrame
        A dataframe containing the matched entries in the given dataframe. If
        no matches were found, the dataframe will be empty.

    """
    if isinstance(metadata, str):  # load dataframe
        metadata = pd.read_csv(metadata)
    
    fn = (lambda x,y: SequenceMatcher(None, x, y).ratio()) \
        if simi_fn is None else lambda x,y: simi_fn.normalized_similarity(x, y)
    if orderless:  # wrap the similarity function for orderless behaviour 
        fn = partial(orderless_similarity, simi_fn=fn)

    # Pre-processing: lower capping, remove extra spaces, markers, etc.
    query = preprocess_compstring(query)
    compmeta_df = metadata.copy()  # fresh deep copy for string comparison
    compmeta_df[attribute] = compmeta_df[attribute].apply(preprocess_compstring)

    simi_values = compmeta_df.apply(lambda x: fn(x[attribute], query), axis=1)

    matches_df = metadata.copy()
    matches_df["similarity"] = simi_values  # append extra column
    matches_df = matches_df[matches_df["similarity"] > threshold]
    
    return matches_df
