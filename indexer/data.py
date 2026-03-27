from .errors import ConstructorPreferred, InvalidDataClassState

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
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

    UPDATE_QUERY = ""
    DELETE_QUERY = ""

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
        """
        Insert this record into the database. Return the id or, for composite
        records, the number of inserted rows.

        > TODO: Make an actual distinction between the two return types?

        Side-effect: overwrite this object's id field with the generated id,
        when applicable.
        """
        pass
    
    @abstractmethod
    def create_update_tuple(self) -> tuple[Any, ...]:
        pass

    @abstractmethod
    def create_delete_tuple(self) -> tuple[Any, ...]:
        pass

    def save(self, cursor) -> bool:
        try:
            cursor.execute(type(self).UPDATE_QUERY, self.create_update_tuple())
            return True
        except:
            return False

    def delete(self, cursor) -> bool:
        try:
            cursor.execute(type(self).DELETE_QUERY, self.create_delete_tuple())
            return True
        except:
            return False


def starfields(cls) -> str:
    """
    Return a comma-separated string listing all the fields of this class.
    The order output is consistent with, for example, `from_sqlite_record`.

    NOTE: This assumes that the `dataclasses.fields` function returns the
    declaration order of the fields. The closest guarantee we have is the
    following claim in the docs:

    > The order of the fields in all of the generated methods is the order
    > in which they appear in the class definition.

    But the thing is, `fields` is not a generated method!
    """
    return ",".join([f.name for f in fields(cls)])


@dataclass
class MetadataRecord(SQLiteDataClass):
    key: str
    val: str
    UPDATE_QUERY = """
        UPDATE __metadata
        SET key=?,
        val=?
        WHERE key=?
        LIMIT 1
    """
    DELETE_QUERY = """
        DELETE FROM __metadata
        WHERE key=?
        LIMIT 1
    """

    @staticmethod
    def fetch(cursor, id: str) -> Optional["MetadataRecord"]:
        query = "SELECT key, val FROM __metadata WHERE key=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return MetadataRecord(*result) if result is not None else None

    @staticmethod
    def from_sqlite_record(record: tuple[Any, ...]) -> "MetadataRecord":
        raise ConstructorPreferred()
    
    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        """
        Since there is no integer id for this table, this only returns either 1
        or 0 for a successful and unsuccessful insertion respectively.
        """
        try:
            cursor.execute(
                "INSERT INTO __metadata (key, val) VALUES (?, ?)",
                (self.key, self.val)
            )
            return 1
        except:
            return 0

    def create_update_tuple(self) -> tuple[Any, ...]:
        return (self.key, self.val, self.key)

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return (self.key,)

@dataclass
class FileIndexRecord(SQLiteDataClass):
    id: Optional[int]
    filename: str
    fullpath: str
    review: Optional[str]
    rating: int = 0

    @staticmethod
    def fetch(cursor, id) -> Optional["FileIndexRecord"]:
        query = f"SELECT {starfields(FileIndexRecord)} FROM files WHERE id=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return FileIndexRecord(*result) if result is not None else None

    @staticmethod
    def from_sqlite_record(record: tuple[Any, ...]) -> "FileIndexRecord":
        raise ConstructorPreferred()

    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        cursor.execute(
            "INSERT INTO files (filename, fullpath, review, rating) VALUES (?, ?, ?, ?)",
            (self.filename, self.fullpath, self.review, self.rating)
        )
        self.id = cursor.lastrowid
        return self.id

    def __str__(self):
        return self.filename

    def create_update_tuple(self) -> tuple[Any, ...]:
        return tuple()

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return tuple()

@dataclass
class PersonIndexRecord(SQLiteDataClass):
    id: Optional[int]
    firstname: str
    lastname: Optional[str]
    extraction_rule: NameDecisionRule
    is_deactivated: int = 0

    @staticmethod
    def fetch(cursor, id) -> Optional["PersonIndexRecord"]:
        query = f"SELECT {starfields(PersonIndexRecord)} FROM persons WHERE id=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
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
        self.id = cursor.lastrowid
        return self.id

    @staticmethod
    def find_by_name(cursor, firstname: str, lastname: Optional[str]) -> Optional["PersonIndexRecord"]:
        test = None
        if lastname is not None:
            test = cursor.execute(
                f"SELECT {starfields(PersonIndexRecord)} FROM persons WHERE firstname=? AND lastname=? LIMIT 1;",
                (firstname, lastname)
            ).fetchone()
        else:
            test = cursor.execute(
                f"SELECT {starfields(PersonIndexRecord)} FROM persons WHERE firstname=? AND lastname IS NULL LIMIT 1;", (firstname,)).fetchone()

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

    def create_update_tuple(self) -> tuple[Any, ...]:
        return tuple()

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return tuple()

@dataclass
class PerformanceIndexRecord(SQLiteDataClass):
    """
    This relation has two fields: files and performers. Each field can either be
    a tuple of FileIndexRecords and PersonIndexRecords respectively or just a
    plain instance of those given types.

    An instance of this class is said to be _rooted_ if and only if one of the
    two fields is plain non-tuple instance while the other is a tuple.
    Furthermore, the record is said to be _rooted at_ the non-tuple field.
    """
    # FIXME This typing is hella confusing!
    files: Union[FileIndexRecord, tuple[FileIndexRecord, ...]]
    performers: Union[PersonIndexRecord, tuple[PersonIndexRecord, ...]]

    @dataclass
    class ExtraArgs:
        certainties: tuple[int, ...]

        def __post_init__(self):
            for c in self.certainties:
                assert c == 0 or c == 1

    def __is_person_rooted(self) -> bool:
        return (
            isinstance(self.performers, PersonIndexRecord) and
            isinstance(self.files, tuple)
        )

    def __is_performance_rooted(self) -> bool:
        return (
            isinstance(self.performers, tuple) and
            isinstance(self.files, FileIndexRecord)
        )

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

    def add_performers(self, performers: Iterable[PersonIndexRecord]): 
        if self.__is_performance_rooted():
            new_list = list(cast(tuple[PersonIndexRecord, ...], self.performers))
            new_list.extend(performers)
            self.performers = tuple(new_list)
        else:
            raise InvalidDataClassState("Object must be performance rooted to add performers.")

    def add_performances(self, performances: Iterable[FileIndexRecord]):
        if self.__is_person_rooted():
            new_list = list(cast(tuple[FileIndexRecord, ...], self.files))
            new_list.extend(performances)
            self.files = tuple(new_list)
        else:
            raise InvalidDataClassState("Object must be performer rooted to add performances.")

    @staticmethod
    def from_sqlite_record(record: tuple[Any, ...]) -> "PerformanceIndexRecord":
        raise ConstructorPreferred()

    def insert(self, cursor, extra_args: Optional["PerformanceIndexRecord.ExtraArgs"] = None) -> Optional[int]:
        """
        To insert a plain one-to-one relationship between performance and
        performer, just root the record in either field and then make a
        singleton tuple for the other field.
        """
        if extra_args is None:
            raise ValueError("extra_args can't be None")

        if isinstance(self.files, tuple) and isinstance(self.performers, tuple):
            raise InvalidDataClassState("record is not rooted, both files and performers are collections")
        query = """
            INSERT INTO participation (person_id, file_id, is_certain) VALUES (?, ?, ?);
        """
        val_tuples: tuple[tuple[int, int, int], ...]
        if self.__is_performance_rooted():
            # self.files is root
            root_val = cast(FileIndexRecord, self.files)
            self.performers = cast(tuple[PersonIndexRecord, ...], self.performers)
            if len(self.performers) != len(extra_args.certainties):
                raise ValueError("performers and certainties are not the same length")

            if root_val.id is None:
                root_val.insert(cursor)

            root_val.id = cast(int, root_val.id)
            temp_tuples = []

            for p, c in zip(self.performers, extra_args.certainties):
                if p.id is None:
                    p.insert(cursor)
            
                p.id = cast(int, p.id)
                temp_tuples.append((p.id, root_val.id, c))

            val_tuples = tuple(temp_tuples)
        elif self.__is_person_rooted():
            # self.performers is root
            root_performer = cast(PersonIndexRecord, self.performers)
            self.files = cast(tuple[FileIndexRecord, ...], self.files)
            if len(self.files) != len(extra_args.certainties):
                raise ValueError("files and certainties are not the same length")

            if root_performer.id is None:
                root_performer.insert(cursor)

            root_performer.id = cast(int, root_performer.id)
            temp_tuples = []

            for f, c in zip(self.files, extra_args.certainties):
                if f.id is None:
                    f.insert(cursor)

                f.id = cast(int, f.id)
                temp_tuples.append((root_performer.id, f.id, c))

            val_tuples = tuple(temp_tuples)
        else:
            raise InvalidDataClassState("Object is not rooted.")
        
        cursor.executemany(query, val_tuples)

        return cursor.lastrowid

    def create_update_tuple(self) -> tuple[Any, ...]:
        return tuple()

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return tuple()
