import unittest
import uuid

from ..indexerdem import Indexerdem

from typing import Any, Optional

class SQLiteTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(SQLiteTest, self).__init__(*args, **kwargs)
        self.indexerdem = Indexerdem(f"/tmp/indexerdem-tests-{uuid.uuid1()}.db")

    @property
    def cursor(self):
        return self.indexerdem.conn.cursor()

    def insert(self, constructor, *args, insert_extra_args: Optional[Any]=None):
        obj = constructor(*args)
        obj.insert(self.cursor, insert_extra_args)
        return obj

    def setUp(self):
        self.indexerdem.init()

    def tearDown(self):
        self.cursor.executescript(
            """
            PRAGMA foreign_keys=OFF;
            DROP TABLE files;
            DROP TABLE persons;
            DROP TABLE participation;
            """
        )
