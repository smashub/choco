"""
Database utilities to keep track of ChoCo's partitions that are expected to be
regularly updated. Currently specialised on iReal data, but can be generalised.

"""
import sqlite3
import hashlib
import logging

from contextlib import closing

logger = logging.getLogger("choco.db")

table_check = """
SELECT name FROM sqlite_master WHERE type='table';
"""

ireal_table = """
CREATE TABLE iRealHex (
    chartid INTEGER PRIMARY KEY,
    chartex TEXT NOT NULL UNIQUE,
    title TEXT,
    artists TEXT,
    genre VARCHAR(32),
    tempo TINYINT,
    time_signature VARCHAR(10),
    jams BOOL NOT NULL DEFAULT 0
);
"""

ireal_chart_search = """
SELECT chartid FROM iRealHex WHERE chartex == (?)
"""

ireal_chart_insert = """
INSERT INTO iRealHex(chartex) VALUES (?)
"""

ireal_chart_list = """
SELECT * FROM iRealHex
"""

ireal_chart_meta = """
UPDATE iRealHex SET
    title = ?,
    artists = ?,
    genre = ?,
    tempo = ?,
    time_signature = ?
WHERE chartid = ?
"""

ireal_chart_jam = """
UPDATE iRealHex SET jams = 1 WHERE chartid = ?
"""


class iRealDatabaseHandler(object):

    def __init__(self, database_path):
        self._connection = sqlite3.connect(
            database_path, check_same_thread=False)
        # Check whether the database is empty or not
        tables = self.execute_transaction(table_check)
        if len(tables) == 0:  # create ireal-table
            logger.warning("Creating iRealHex table")
            self.execute_transaction(ireal_table)


    def execute_transaction(self, query:str, parameters:tuple = ()):
        """
        Safely execute a transaction on the database given an SQL query with
        optional placeholders and a tuple of parameters to fill them.

        Parameters
        ----------
        query : str
            An SQL light query encoded as a string with '?' placeholders.
        parameters : tuple
            A tuple of parameters to use in the query (replace placeholders).

        Returns
        -------
        results : list
            A list of rows or transaction codes obtained from running the query.
        """
        with closing(self._connection.cursor()) as cursor:
            results = cursor.execute(query, parameters).fetchall()

        return results


    def register_chart(self, chart:str):
        """
        Check whether a chart is already present in the database and, if not,
        update the database with the new chart, returning True.

        Parameters
        ----------
        chart : str
            A string encoding an iReal chart, after decoding the URL.

        Returns
        -------
        An integer ID that has been registered to the new chart, if anew,
        otherwise None is returned.

        Notes
        -----
        TODO Executions should be bundled within the same transaction, although
        this seems to be tricky when using SQLite.

        """
        cursor = self._connection.cursor()  # get a fresh cursor
        chartex = (hashlib.sha1(chart.encode("utf-8")).hexdigest(),)
        # Check if the chart has already been registered in the database
        # The following 2 execution should be bundled in the same transaction.
        matches = cursor.execute(ireal_chart_search, chartex).fetchall()
        if len(matches) > 0: return None
        cursor.execute(ireal_chart_insert, chartex).fetchall()
        # matches = self.execute_transaction(ireal_chart_search, chartex)
        # assert len(matches) == 1, "Non-unique or unregistered iReal hash"

        return cursor.lastrowid  # succesful insertion in the DB
    

    def register_metadata(self, chart_id:int, chart_meta:dict):
        """
        Update chart information with the metadata extracted from the tune.

        Parameters
        ----------
        chart_id : int
            Unique integer identifier of the chart that is updated.
        chart_meta: dict
            A dictionary with the metadata of the chart.

        """
        # Stringify the time signature tuple before insertion
        time_signature = chart_meta["time_signature"]
        time_signature = f"{time_signature[0]}/{time_signature[1]}" \
            if len(time_signature) == 2 else ""
        # Create parameter tuple: important to preserve the order
        parameter_tuple = (
            chart_meta["title"], chart_meta["artists"],
            chart_meta["genre"], chart_meta["tempo"],
            time_signature, chart_id,)  # id is last
        self.execute_transaction(ireal_chart_meta, parameter_tuple)
    

    def register_jams(self, chart_id:int, jams_path:str):
        """
        Update chart information with the metadata extracted from the tune.

        Parameters
        ----------
        chart_id : int
            Unique integer identifier of the chart that is updated.
        jams_path: str
            Path to the JAMS file generated from the chart.
            XXX Currently not used, but a check is planned before transaction.

        """
        self.execute_transaction(ireal_chart_jam, (chart_id,))


    def list_all_charts(self):
        """
        Return a list with all the content of the iRealHex table.
    
        """
        return self.execute_transaction(ireal_chart_list)


    def close(self):
        # Because we do things right
        self._connection.commit()
        self._connection.close()
