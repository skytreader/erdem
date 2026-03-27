from .base import SQLiteTest

from ..data import FileIndexRecord, MetadataRecord, PersonIndexRecord
from ..indexerdem import MetadataCheckResult, NameDecisionRule

class IndexerdemTests(SQLiteTest):

    def test_search_files(self):
        messi_files = self.indexerdem.search_files("messi")
        assert len(messi_files) == 0
        messi_record = FileIndexRecord(None, "Best Goals Messi 2017.mp4", "/", "", 10)
        messi_record.insert(self.cursor)
        ronaldo_record = FileIndexRecord(None, "Best Goals CR7 2017.mp4", "/", "If not for Messi, would've been the best.")
        ronaldo_record.insert(self.cursor)
        messi_files = self.indexerdem.search_files("messi")
        assert len(messi_files) == 1
        assert messi_files[0] == messi_record

    def test_search_performers(self):
        lionels = self.indexerdem.search_performers("lionel")
        assert len(lionels) == 0
        goat = self.insert(PersonIndexRecord, None, "Lionel", "Messi", NameDecisionRule.ALMOST_CERTAIN, 0)
        self.insert(PersonIndexRecord, None, "Lionel", "Ritchie", NameDecisionRule.ALMOST_CERTAIN, 0)
        vice_goat = self.insert(PersonIndexRecord, None, "Cristiano", "Ronaldo", NameDecisionRule.ALMOST_CERTAIN, 0)
        lionels = self.indexerdem.search_performers("lionel")
        assert len(lionels) == 2
        assert goat in lionels
        assert vice_goat not in lionels

    def test_check_compatibility(self):
        assert self.indexerdem.check_compatibility() == MetadataCheckResult.COMPLETELY_COMPATIBLE
        index_version_record = MetadataRecord.fetch(self.cursor, "index_version")
        index_version_record.val = "1.1"
        assert index_version_record.save(self.cursor)
        self.connection.commit()
        assert self.indexerdem.check_compatibility() == MetadataCheckResult.LIKELY_COMPATIBLE
        index_version_record.val = "blerp"
        assert index_version_record.save(self.cursor)
        self.connection.commit()
        assert self.indexerdem.check_compatibility() == MetadataCheckResult.INCOMPATIBLE
        index_version_record.val = ""
        assert index_version_record.save(self.cursor)
        self.connection.commit()
        assert self.indexerdem.check_compatibility() == MetadataCheckResult.INCOMPATIBLE
        assert index_version_record.delete(self.cursor)
        self.connection.commit()
        assert self.indexerdem.check_compatibility() == MetadataCheckResult.INDETERMINATE
