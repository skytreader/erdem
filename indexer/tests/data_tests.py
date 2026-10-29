from dataclasses import dataclass
from unittest import mock

from .base import SQLiteTest, TestException

from ..data import (
    FileIndexRecord, MetadataRecord, PerformanceIndexRecord, PersonIndexRecord,
    starfields
)
from ..indexerdem import NameDecisionRule
from ..errors import InvalidDataClassState

import pytest

@dataclass
class TestDataClass:
    id: int
    firstname: str
    lastname: str

def test_starfields():
    assert starfields(TestDataClass) == "id,firstname,lastname"
    assert starfields(TestDataClass, True) == "firstname,lastname"
    assert starfields(
        TestDataClass,
        True,
        {"firstname": "first_name", "lastname": "ln"}
    ) == "first_name,ln"

class FileIndexRecordTests(SQLiteTest):

    def test_insert(self):
        testfile = self.cursor.execute("SELECT * FROM files WHERE filename='test' LIMIT 1;").fetchone()
        assert testfile is None
        file_record = FileIndexRecord(None, self.default_mountpoint, "test", "/", "", 0)
        assert file_record.id is None
        insert_id = file_record.insert(self.cursor)
        assert file_record is not None
        assert insert_id is not None
        assert file_record.id == insert_id
        testfile = self.cursor.execute("SELECT id, filename, fullpath, review, rating FROM files WHERE filename='test' LIMIT 1;").fetchone()
        assert file_record == FileIndexRecord(testfile[0], self.default_mountpoint, testfile[1], testfile[2], testfile[3], testfile[4])

    def test_save(self):
        # First the usual insertions
        file_record = FileIndexRecord(None, self.default_mountpoint, "test", "/", "", 0)
        assert file_record.id is None
        insert_id = file_record.insert(self.cursor)
        assert file_record is not None
        assert insert_id is not None
        assert file_record.id == insert_id
        # some edit-specific assertions
        assert file_record.rating == 0
        assert file_record.review == ""

        # edit it and save
        file_record.rating = 5
        file_record.review = "<3!"
        assert file_record.save(self.cursor)

        #refetch
        record_refetch = FileIndexRecord.fetch(self.cursor, file_record.id)
        assert record_refetch.rating == 5
        assert record_refetch.review == "<3!"

    def test_save_error(self):
        # First the usual insertions
        file_record = FileIndexRecord(None, self.default_mountpoint, "test", "/", "", 0)
        assert file_record.id is None
        insert_id = file_record.insert(self.cursor)
        assert file_record is not None
        assert insert_id is not None
        assert file_record.id == insert_id
        # some edit-specific assertions
        assert file_record.rating == 0
        assert file_record.review == ""

        # edit it and save
        file_record.rating = 5
        file_record.review = "<3!"
        with pytest.raises(TestException):
            mock_cursor = mock.Mock(
                **{
                    "execute.side_effect": TestException
                }
            )
            file_record.save(mock_cursor)

        #refetch
        record_refetch = FileIndexRecord.fetch(self.cursor, file_record.id)
        assert record_refetch.rating == 0
        assert record_refetch.review == ""

    def test_fetch(self):
        fine = FileIndexRecord(
            None,
            self.default_mountpoint,
            "This Is Fine.mp4",
            "/var/srv/videos",
            "It's fine",
            5
        )
        fine.insert(self.cursor)
        fetch_is_fine = FileIndexRecord.fetch(self.cursor, fine.id)
        assert fine == fetch_is_fine

class PersonIndexRecordTests(SQLiteTest):

    def test_eq(self):
        tinafey1 = PersonIndexRecord(
            1,
            "Tina",
            "Fey",
            NameDecisionRule.ALMOST_CERTAIN
        )
        tinafey2 = PersonIndexRecord(
            None,
            "Tina",
            "Fey",
            NameDecisionRule.ALMOST_CERTAIN
        )
        assert tinafey1 == tinafey2

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

    def test_save(self):
        scarjo = PersonIndexRecord(
            None,
            "Scar",
            "Johansson",
            NameDecisionRule.ALMOST_CERTAIN,
        )
        scarjo.insert(self.cursor)
        assert scarjo.firstname == "Scar"
        scarjo.firstname = "Scarlett"
        scarjo.extraction_rule = NameDecisionRule.MANUAL_INPUT
        assert scarjo.save(self.cursor)
        fetch_scarjo = PersonIndexRecord.fetch(self.cursor, scarjo.id)
        assert fetch_scarjo.firstname == "Scarlett"
        assert fetch_scarjo.extraction_rule == NameDecisionRule.MANUAL_INPUT

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
    """
    Naming convention for test fields for PerformanceIndexRecords:

    {root}_perf_{default branches}

    - {root} is the foreign key record entity on which this record is rooted
    - {default branches} is a collective description of the branch records in
      this relationship.
    """

    def setUp(self):
        super().setUp()
        self.everything_everywhere = self.insert(
            FileIndexRecord,
            None,
            self.default_mountpoint,
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
            self.default_mountpoint,
            "Parks and Recreation - Bailout.mp4",
            "/",
            "",
            0
        )
        self.p_and_r_perf = self.insert(
            PerformanceIndexRecord,
            self.p_and_r,
            tuple([self.jslate]),
            tuple([1])
        )
        self.ee_perf = self.insert(
            PerformanceIndexRecord,
            self.everything_everywhere,
            tuple([self.jslate, self.myeoh]),
            tuple([1, 1])
        )

        self.zendaya = self.insert(
            PersonIndexRecord,
            None,
            "Zendaya",
            None,
            NameDecisionRule.ALMOST_CERTAIN,
            0
        )
        self.dune = self.insert(FileIndexRecord, None, self.default_mountpoint, "Dune.mp4", "/", "", 0)
        self.dune_perf = self.insert(
            PerformanceIndexRecord,
            self.dune,
            tuple([self.zendaya]),
            tuple([1])
        )

        self.spiderman = self.insert(
            FileIndexRecord,
            None,
            self.default_mountpoint,
            "Spiderman - Homecoming.mp4",
            "/",
            "",
            0
        )
        self.zendaya_perf_spiderman = self.insert(
            PerformanceIndexRecord,
            tuple([self.spiderman]),
            self.zendaya,
            tuple([1])
        )

    def test_create(self):
        assert self.p_and_r_perf.files == self.p_and_r
        assert len(self.p_and_r_perf.performers) == 1
        assert self.jslate in self.p_and_r_perf.performers

    def test_add_performers_ex(self):
        with pytest.raises(InvalidDataClassState):
            self.zendaya_perf_spiderman.add_performers((self.jslate,), (1,))

    def test_add_files_ex(self):
        with pytest.raises(InvalidDataClassState):
            self.dune_perf.add_files((self.spiderman,), (1,))
    
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
