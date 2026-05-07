import unittest
import uuid

from ..indexerdem import Indexerdem
from ..data import MountpointRecord

from typing import Any, Optional

class SQLiteTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(SQLiteTest, self).__init__(*args, **kwargs)
        self.indexerdem = Indexerdem(
            f"/tmp/indexerdem-tests-{uuid.uuid1()}.db",
            ("en", "en_GB", "en_US", "en_NZ")
        )

    @property
    def cursor(self):
        return self.indexerdem.conn.cursor()
    
    @property
    def connection(self):
        return self.indexerdem.conn

    def insert(self, constructor, *args, insert_extra_args: Optional[Any]=None):
        obj = constructor(*args)
        obj.insert(self.cursor, insert_extra_args)
        return obj

    def setUp(self):
        self.indexerdem.init()
        self.default_mountpoint = MountpointRecord(None, "/media/default")
        self.default_mountpoint.insert(self.cursor)

    def tearDown(self):
        self.cursor.executescript(
            """
            PRAGMA foreign_keys=OFF;
            DROP TABLE __metadata;
            DROP TABLE mountpoints;
            DROP TABLE files;
            DROP TABLE persons;
            DROP TABLE participation;
            """
        )
