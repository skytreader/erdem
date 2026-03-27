from .base import SQLiteTest

from ..data import FileIndexRecord, MetadataRecord, PerformanceIndexRecord, PersonIndexRecord
from ..indexerdem import NameDecisionRule

class FileIndexRecordTests(SQLiteTest):

    def test_insert(self):
        testfile = self.cursor.execute("SELECT * FROM files WHERE filename='test' LIMIT 1;").fetchone()
        assert testfile is None
        file_record = FileIndexRecord(None, "test", "/", "", 0)
        assert file_record.id is None
        insert_id = file_record.insert(self.cursor)
        assert file_record is not None
        assert insert_id is not None
        assert file_record.id == insert_id
        testfile = self.cursor.execute("SELECT id, filename, fullpath, review, rating FROM files WHERE filename='test' LIMIT 1;").fetchone()
        assert file_record == FileIndexRecord(testfile[0], testfile[1], testfile[2], testfile[3], testfile[4])

    def test_fetch(self):
        fine = FileIndexRecord(
            None,
            "This Is Fine.mp4",
            "/var/srv/videos",
            "It's fine",
            5
        )
        fine.insert(self.cursor)
        fetch_is_fine = FileIndexRecord.fetch(self.cursor, fine.id)
        assert fine == fetch_is_fine

class PersonIndexRecordTests(SQLiteTest):

    def test_fetch(self):
        scarjo = PersonIndexRecord(
            None,
            "Scarlett",
            "Johansson",
            NameDecisionRule.ALMOST_CERTAIN,
        )
        scarjo.insert(self.cursor)
        fetch_scarjo = PersonIndexRecord.fetch(self.cursor, scarjo.id)
        assert scarjo == fetch_scarjo

    def test_find_by_name(self):
        scarjo = PersonIndexRecord(
            None,
            "Scarlett",
            "Johansson",
            NameDecisionRule.ALMOST_CERTAIN,
        )
        scarjo.insert(self.cursor)
        zendaya = PersonIndexRecord(
            None,
            "Zendaya",
            None,
            NameDecisionRule.MANUAL_INPUT
        )
        zendaya.insert(self.cursor)
        assert PersonIndexRecord.find_by_name(
            self.cursor,
            "Scarlett",
            "Johansson"
        ) == scarjo
        assert PersonIndexRecord.find_by_name(
            self.cursor,
            "Zendaya",
            None
        ) == zendaya
        assert PersonIndexRecord.find_by_name(
            self.cursor,
            "Scarlett",
            None
        ) is None

class MetadataRecordTests(SQLiteTest):

    def test_fetch(self):
        assert MetadataRecord.fetch(self.cursor, "index_version") is not None

    def test_delete(self):
        index_version_record = MetadataRecord.fetch(self.cursor, "index_version")
        assert index_version_record is not None
        assert index_version_record.delete(self.cursor)
        self.connection.commit()
        assert MetadataRecord.fetch(self.cursor, "index_version") is None

class PerformanceIndexRecordTests(SQLiteTest):

    def setUp(self):
        super().setUp()
        self.everything_everywhere = self.insert(
            FileIndexRecord,
            None,
            "Everything, Everywhere, All at Once.mp4",
            "/",
            "",
            0
        )
        self.myeoh = self.insert(
            PersonIndexRecord,
            None,
            "Michelle",
            "Yeoh",
            NameDecisionRule.ALMOST_CERTAIN,
            0
        )
        self.jslate = self.insert(
            PersonIndexRecord,
            None,
            "Jenny",
            "Slate",
            NameDecisionRule.ALMOST_CERTAIN,
            0
        )
        self.p_and_r = self.insert(
            FileIndexRecord,
            None,
            "Parks and Recreation - Bailout.mp4",
            "/",
            "",
            0
        )
        self.p_and_r_perf = self.insert(
            PerformanceIndexRecord,
            self.p_and_r,
            tuple([self.jslate]),
            insert_extra_args=PerformanceIndexRecord.ExtraArgs(tuple([1]))
        )
        self.ee_perf = self.insert(
            PerformanceIndexRecord,
            self.everything_everywhere,
            tuple([self.jslate, self.myeoh]),
            insert_extra_args=PerformanceIndexRecord.ExtraArgs(tuple([1, 1]))
        )

        self.zendaya = self.insert(
            PersonIndexRecord,
            None,
            "Zendaya",
            None,
            NameDecisionRule.ALMOST_CERTAIN,
            0
        )
        self.dune = self.insert(FileIndexRecord, None, "Dune.mp4", "/", "", 0)
        self.dune_perf = self.insert(
            PerformanceIndexRecord,
            self.dune,
            tuple([self.zendaya]),
            insert_extra_args=PerformanceIndexRecord.ExtraArgs(tuple([1]))
        )

        self.spiderman = self.insert(
            FileIndexRecord,
            None,
            "Spiderman - Homecoming.mp4",
            "/",
            "",
            0
        )
        self.spiderman_perf = self.insert(
            PerformanceIndexRecord,
            tuple([self.spiderman]),
            self.zendaya,
            insert_extra_args=PerformanceIndexRecord.ExtraArgs(tuple([1]))
        )

    def test_create(self):
        assert self.p_and_r_perf.files == self.p_and_r
        assert len(self.p_and_r_perf.performers) == 1
        assert self.jslate in self.p_and_r_perf.performers
    
    def test_fetch(self):
        # Fetch with a performer
        jslate_perfs = PerformanceIndexRecord.fetch(self.cursor, self.jslate)
        assert jslate_perfs.performers == self.jslate
        assert len(jslate_perfs.files) == 2
        assert self.everything_everywhere in jslate_perfs.files
        assert self.p_and_r in jslate_perfs.files

        # Fetch performer with no last name
        zendaya_perfs = PerformanceIndexRecord.fetch(self.cursor, self.zendaya)
        assert zendaya_perfs.performers == self.zendaya
