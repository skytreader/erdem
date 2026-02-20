import unittest
import uuid

from ..indexerdem import Indexerdem

class SQLiteTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(SQLiteTest, self).__init__(*args, **kwargs)
        self.indexerdem = Indexerdem(f"/tmp/indexerdem-tests-{uuid.uuid1()}.db")

    @property
    def cursor(self):
        return self.indexerdem.conn.cursor()

    def setUp(self):
        self.indexerdem.init()

    def tearDown(self):
        self.cursor.executescript(
            """
            DROP TABLE files;
            DROP TABLE persons;
            DROP TABLE participation;
            """
        )

