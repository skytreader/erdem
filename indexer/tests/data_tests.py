from .base import SQLiteTest

from ..indexerdem import FileIndexRecord

class FileIndexRecordTests(SQLiteTest):

    def test_insert(self):
        testfile = self.cursor.execute("SELECT * FROM files WHERE filename='test' LIMIT 1;").fetchone()
        assert testfile is None
        file_record = FileIndexRecord(None, "test", "/", 0, "")
        assert file_record.id is None
        insert_id = file_record.insert(self.cursor)
        assert file_record is not None
        assert insert_id is not None
        assert file_record.id == insert_id
        testfile = self.cursor.execute("SELECT id, filename, fullpath, rating, review FROM files WHERE filename='test' LIMIT 1;").fetchone()
        assert file_record == FileIndexRecord(testfile[0], testfile[1], testfile[2], testfile[3], testfile[4])

