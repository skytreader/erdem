from .errors import ConstructorPreferred, InvalidDataClassState

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast, Iterable, Optional, List, Set, Tuple, Union

class NameDecisionRule(StrEnum):
    ALMOST_CERTAIN = "almost-certain"
    TRUNCATED_FIRSTNAME = "truncated-firstname"
    LASTNAME_BACKWARD = "lastname-backward"
    MANUAL_INPUT = "manual-input"

NameTuple = Tuple[str, Optional[str], NameDecisionRule]

@dataclass
class SQLiteDataClass(ABC):

    @staticmethod
    @abstractmethod
    def fetch(cursor, id: Any) -> Optional["SQLiteDataClass"]:
        """
        Fetch one record from the represented table. `id` should be enough to
        fetch a unique record. Most of the time, this can be an integer but, for
        composite keys, it can also be a tuple or an object from which the
        defining attributes can be derived.
        """
        pass

    @staticmethod
    @abstractmethod
    def from_sqlite_record(record: tuple[Any, ...]) -> "SQLiteDataClass":
        """
        Construct an instance of this class from the result of an SQLite query.
        The order of data in `record` would vary per class and should be noted
        down.

        If you prefer that instances be constructed with the auto-generated
        constructor, throw a `ConstructorPreferred` error.
        """
        pass
    
    @abstractmethod
    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        pass

@dataclass
class FileIndexRecord(SQLiteDataClass):
    id: int
    filename: str
    fullpath: str
    rating: int
    review: str

    @staticmethod
    def fetch(cursor, id) -> Optional["FileIndexRecord"]:
        query = f"SELECT * FROM files WHERE id={id} LIMIT 1"
        result = cursor.execute(query).fetchone()
        return FileIndexRecord(*result) if result is not None else None

    @staticmethod
    def from_sqlite_record(record: tuple[Any, ...]) -> "FileIndexRecord":
        raise ConstructorPreferred()

    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        pass

    def __str__(self):
        return self.filename

@dataclass
class PersonIndexRecord(SQLiteDataClass):
    id: Optional[int]
    firstname: str
    lastname: Optional[str]
    extraction_rule: NameDecisionRule
    is_deactivated: int

    @staticmethod
    def fetch(cursor, id) -> Optional["PersonIndexRecord"]:
        query = f"SELECT * FROM persons WHERE id={id} LIMIT 1"
        result = cursor.execute(query).fetchone()
        return PersonIndexRecord.from_sqlite_record(result) if result is not None else None

    @staticmethod
    def from_sqlite_record(record: tuple[int, str, str, str, int]) -> "PersonIndexRecord":
        return PersonIndexRecord(record[0], record[1], record[2], NameDecisionRule(record[3]), record[4])

    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        cursor.execute(
            """INSERT INTO persons (firstname, lastname, extraction_rule, is_deactivated)
            VALUES(?, ?, ?, ?)""",
            (self.firstname, self.lastname, str(self.extraction_rule), self.is_deactivated)
        )
        return cursor.lastrowid

    @staticmethod
    def find_by_name(cursor, firstname: str, lastname: Optional[str]) -> Optional["PersonIndexRecord"]:
        test = None
        if lastname is not None:
            test = cursor.execute("SELECT * FROM persons WHERE firstname=? AND lastname=? LIMIT 1;", (firstname, lastname)).fetchone()
        else:
            test = cursor.execute("SELECT * FROM persons WHERE firstname=? AND lastname IS NULL LIMIT 1;", (firstname,)).fetchone()

        if test:
            return PersonIndexRecord.from_sqlite_record(test)
        else:
            return None

    @property
    def deactivated(self):
        return self.is_deactivated == 1

    def __str__(self):
        return (
            f"{self.lastname}, {self.firstname}"
            if self.lastname is not None else
            self.firstname
        )

@dataclass
class PerformanceIndexRecord(SQLiteDataClass):
    # FIXME This typing is hella confusing!
    files: Union[FileIndexRecord, tuple[FileIndexRecord, ...]]
    performers: Union[PersonIndexRecord, tuple[PersonIndexRecord, ...]]

    @dataclass
    class ExtraArgs:
        certainties: tuple[int, ...]

        def __post_init__(self):
            for c in self.certainties:
                assert c == 0 or c == 1

    @staticmethod
    def fetch(cursor, root_record: Union[PersonIndexRecord, FileIndexRecord]) -> Optional["PerformanceIndexRecord"]:
        is_person_rooted = isinstance(root_record, PersonIndexRecord)
        query = (
            f"SELECT file_id FROM participation WHERE person_id={root_record.id}"
            if is_person_rooted else
            f"SELECT person_id FROM participation WHERE file_id={root_record.id}"
        )
        result = cursor.execute(query).fetchall()
        non_root_type = FileIndexRecord if is_person_rooted else PersonIndexRecord
        non_root_attr = tuple() if result is None else tuple([non_root_type.fetch(cursor, _id[0]) for _id in result if _id is not None])
        
        if is_person_rooted:
            return PerformanceIndexRecord(files=non_root_attr, performers=cast(PersonIndexRecord, root_record)) # type: ignore
        else:
            return PerformanceIndexRecord(files=cast(FileIndexRecord, root_record), performers=non_root_attr) # type: ignore

    @staticmethod
    def from_sqlite_record(record: tuple[Any, ...]) -> "PerformanceIndexRecord":
        raise ConstructorPreferred()

    def insert(self, cursor, extra_args: Optional["PerformanceIndexRecord.ExtraArgs"] = None) -> Optional[int]:
        if extra_args is None:
            raise ValueError("extra_args can't be None")

        if isinstance(self.files, tuple) and isinstance(self.performers, tuple):
            raise InvalidDataClassState("record is not rooted, both files and performers are collections")
        query = """
            INSERT INTO participation (person_id, file_id, is_certain) VALUES (?, ?, ?);
        """
        if isinstance(self.performers, Iterable):
            # self.files is root
            root_val = cast(FileIndexRecord, self.files)
            if len(self.performers) != len(extra_args.certainties):
                raise ValueError("performers and certainties are not the same length")

            val_tuples = ((p.id, root_val.id, c) for p, c in zip(self.performers, extra_args.certainties))
            cursor.executemany(query, val_tuples)
        elif isinstance(self.files, Iterable):
            # self.performers is root
            root_file = cast(PersonIndexRecord, self.performers)
            if len(self.files) != len(extra_args.certainties):
                raise ValueError("files and certainties are not the same length")

            val_tuples_file = ((root_file.id, f, c) for f, c in zip(self.files, extra_args.certainties))
            cursor.executemany(query, val_tuples_file)

        return cursor.lastrowid

