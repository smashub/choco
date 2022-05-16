"""
Database utilities to keep track of ChoCo's partitions that are expected to be
regularly updated. Currently specialised on iReal data, but can be generalised.

"""
import sqlite3
import hashlib
import logging

logger = logging.getLogger("choco.db")

table_check = """
SELECT name FROM sqlite_master WHERE type='table';
"""

ireal_table = """
CREATE TABLE iRealHex (
    chartid INTEGER PRIMARY KEY,
    chartex TEXT NOT NULL UNIQUE
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


class iRealDatabaseHandler(object):

    def __init__(self, database_name):
        self._connection = sqlite3.connect(f"{database_name}.db")
        self._cursor = self._connection.cursor()

        tables = self._cursor.execute(table_check).fetchall()
        if len(tables) == 0:  # create ireal-table if it does not exist
            print("Creating iRealHex table")
            self._cursor.execute(ireal_table)


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
    
        """
        chartex = (hashlib.sha1(chart.encode("utf-8")).hexdigest(),)

        matches = self._cursor.execute(ireal_chart_search, chartex).fetchall()
        if len(matches) > 0: return None

        self._cursor.execute(ireal_chart_insert, chartex)  # insertion
        matches = self._cursor.execute(ireal_chart_search, chartex).fetchall()
        assert len(matches) == 1, "Non-unique iReal hashes"

        return matches[0][0]  # denotes a succesful insertion in the DB


    def list_all_charts(self):
        """
        Return a list with all the content of the iRealHex table.
    
        """
        return self._cursor.execute(ireal_chart_list).fetchall()


    def close(self):
        # Because we do things right
        self._connection.commit()
        self._connection.close()
