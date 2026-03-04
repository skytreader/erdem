from .base import SQLiteTest

from ..indexerdem import FileIndexRecord, NameDecisionRule, PersonIndexRecord

class IndexerdemTests(SQLiteTest):

    def test_search_files(self):
        messi_files = self.indexerdem.search_files("messi")
        assert len(messi_files) == 0
        messi_record = FileIndexRecord(None, "Best Goals Messi 2017.mp4", "/", 0, "")
        messi_record.insert(self.cursor)
        ronaldo_record = FileIndexRecord(None, "Best Goals CR7 2017.mp4", "/", 0, "If not for Messi, would've been the best.")
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
