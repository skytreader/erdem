from .errors import ConstructorPreferred, InvalidDataClassState

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import Any, cast, ClassVar, Iterable, Optional, List, Set, Tuple, Union
from typing_extensions import override

class NameDecisionRule(StrEnum):
    ALMOST_CERTAIN = "almost-certain"
    TRUNCATED_FIRSTNAME = "truncated-firstname"
    LASTNAME_BACKWARD = "lastname-backward"
    MANUAL_INPUT = "manual-input"

NameTuple = Tuple[str, Optional[str], NameDecisionRule]

@dataclass
class SQLiteDataClass(ABC):
    """
    This is the most common update query for updating a single record. Must work
    with `create_update_tuple`.
    """
    UPDATE_QUERY = ""
    """
    This is the most common delete query for deleting a single record. Must work
    with `create_delete_tuple`.
    """
    DELETE_QUERY = ""
    COL_MAPPING: ClassVar[dict[str, str]] = {}

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
    def from_sqlite_record(cursor, record: tuple[Any, ...]) -> "SQLiteDataClass":
        """
        Construct an instance of this class from the result of an SQLite query.
        The order of data in `record` would vary per class and should be noted
        down. The types in `record` must be primitives _from_ SQLite.

        If you prefer that instances be constructed with the auto-generated
        constructor, throw a `ConstructorPreferred` error.
        """
        pass
    
    @abstractmethod
    def insert(self, cursor) -> Optional[int]:
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
        """
        Assemble the tuple to pass to UPDATE_QUERY.
        """
        pass

    @abstractmethod
    def create_delete_tuple(self) -> tuple[Any, ...]:
        """
        Assemble the tuple to pass too DELETE_QUERY.
        """
        pass

    def save(self, cursor) -> bool:
        """
        For this method, you need to have an UPDATE_QUERY in your class as well
        as a corresponding proper override of create_update_tuple.
        """
        try:
            cursor.execute(type(self).UPDATE_QUERY, self.create_update_tuple())
            return True
        except Exception:
            raise

    def delete(self, cursor) -> bool:
        try:
            cursor.execute(type(self).DELETE_QUERY, self.create_delete_tuple())
            return True
        except:
            return False


def starfields(cls, noid: bool = False, col_mapping: Optional[dict[str, str]] = None) -> str:
    """
    Return a comma-separated string listing all the fields of this class.
    The order output is consistent with, for example, `from_sqlite_record`.

    NOTE: This assumes that the `dataclasses.fields` function returns the
    declaration order of the fields. The closest guarantee we have is the
    following claim in the docs:

    > The order of the fields in all of the generated methods is the order
    > in which they appear in the class definition.

    But the thing is, `fields` is not a generated method!

    Params:

    cls -- The dataclass we are listing the fields of
    noid -- If True we list the fields omitting a field named "id"
    col_mapping -- A dictionary mapping dataclass field names to SQL columns.
    You only need to specify those that actually differ.
    """
    def _map(name):
        if col_mapping is None:
            return name
        else:
            return col_mapping.get(name, name)

    if noid:
        return ",".join([_map(f.name) for f in fields(cls) if f.name != "id"])
    else:
        return ",".join([_map(f.name) for f in fields(cls)])


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
    @override
    def fetch(cursor, id: str) -> Optional["MetadataRecord"]:
        query = "SELECT key, val FROM __metadata WHERE key=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return MetadataRecord(*result) if result is not None else None

    @staticmethod
    @override
    def from_sqlite_record(cursor, record: tuple[Any, ...]) -> "MetadataRecord":
        raise ConstructorPreferred()
    
    @override
    def insert(self, cursor) -> Optional[int]:
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

    @override
    def create_update_tuple(self) -> tuple[Any, ...]:
        return (self.key, self.val, self.key)

    @override
    def create_delete_tuple(self) -> tuple[Any, ...]:
        return (self.key,)

@dataclass
class MountpointRecord(SQLiteDataClass):
    id: Optional[int]
    path: str
    UPDATE_QUERY = """
        UPDATE mountpoints
        SET path=?
        WHERE id=?
        LIMIT 1;
    """
    DELETE_QUERY = """
        DELETE FROM mountpoints
        WHERE id=?
        LIMIT 1;
    """

    @staticmethod
    def fetch(cursor, id: int) -> Optional["MountpointRecord"]:
        query = f"SELECT {starfields(MountpointRecord)} FROM mountpoints WHERE id=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return MountpointRecord(*result) if result is not None else None
    
    @staticmethod
    def from_sqlite_record(cursor, record: tuple[Any, ...]) -> "MountpointRecord":
        raise ConstructorPreferred()

    @staticmethod
    def to_mountpoint_record(cursor, mountpoint_path: str) -> "MountpointRecord":
        query = f"SELECT {starfields(MountpointRecord)} FROM mountpoints WHERE path=? LIMIT 1"
        if (record := cursor.execute(query, (mountpoint_path,)).fetchone()):
            return MountpointRecord(*record)
        else:
            record = MountpointRecord(None, mountpoint_path)
            record.insert(cursor)
            return record

    def insert(self, cursor) -> Optional[int]:
        cursor.execute(
            f"INSERT INTO mountpoints ({starfields(MountpointRecord, True)}) VALUES (?)",
            (self.path,)
        )
        self.id = cursor.lastrowid
        return self.id
    
    def create_update_tuple(self) -> tuple[Any, ...]:
        return (self.path, self.id)

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return (self.id,)

@dataclass
class FileIndexRecord(SQLiteDataClass):
    id: Optional[int]
    mountpoint: MountpointRecord
    filename: str
    fullpath: str
    review: Optional[str]
    rating: int = 0

    COL_MAPPING = {
        "mountpoint": "mountpoint_id"
    }

    UPDATE_QUERY = """
        UPDATE files
        SET mountpoint_id = ?,
        filename = ?,
        fullpath = ?,
        review = ?,
        rating = ?
        WHERE id = ?
        LIMIT 1;
    """

    def __post_init__(self):
        if self.rating is None:
            self.rating = 0

        if self.rating < 0 or self.rating > 10:
            raise InvalidDataClassState(f"Rating should be between 0 and 10. Given: {self.rating}")

    @staticmethod
    def fetch(cursor, id) -> Optional["FileIndexRecord"]:
        query = f"SELECT {starfields(FileIndexRecord, col_mapping=FileIndexRecord.COL_MAPPING)} FROM files WHERE id=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return FileIndexRecord.from_sqlite_record(cursor, result) if result is not None else None

    @staticmethod
    def from_sqlite_record(cursor, record: tuple[int, int, str, str, Optional[str], int]) -> "FileIndexRecord":
        mountpoint = MountpointRecord.fetch(cursor, record[1])
        if mountpoint:
            return FileIndexRecord(record[0], mountpoint, record[2], record[3], record[4], record[5])
        else:
            raise ValueError(f"Can't find provided mountpoint in record: {record}")

    def insert(self, cursor) -> Optional[int]:
        cursor.execute(
            f"INSERT INTO files ({starfields(FileIndexRecord, True, FileIndexRecord.COL_MAPPING)}) VALUES (?, ?, ?, ?, ?)",
            (self.mountpoint.id, self.filename, self.fullpath, self.review, self.rating)
        )
        self.id = cursor.lastrowid
        return self.id

    def __str__(self):
        return self.filename

    def create_update_tuple(self) -> tuple[Any, ...]:
        return (
            self.mountpoint.id,
            self.filename,
            self.fullpath,
            self.review,
            self.rating,
            self.id
        )

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return tuple()

@dataclass
class PersonIndexRecord(SQLiteDataClass):
    id: Optional[int]
    firstname: str
    lastname: Optional[str]
    extraction_rule: NameDecisionRule
    is_deactivated: int = 0

    UPDATE_QUERY = """
        UPDATE persons
        SET firstname = ?,
        lastname = ?,
        extraction_rule = ?,
        is_deactivated = ?
        WHERE id = ?
        LIMIT 1;
    """

    @staticmethod
    def fetch(cursor, id) -> Optional["PersonIndexRecord"]:
        query = f"SELECT {starfields(PersonIndexRecord)} FROM persons WHERE id=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return PersonIndexRecord.from_sqlite_record(cursor, result) if result is not None else None

    @staticmethod
    def from_sqlite_record(cursor, record: tuple[int, str, str, str, int]) -> "PersonIndexRecord":
        return PersonIndexRecord(record[0], record[1], record[2], NameDecisionRule(record[3]), record[4])

    def insert(self, cursor) -> Optional[int]:
        cursor.execute(
            """INSERT INTO persons (firstname, lastname, extraction_rule, is_deactivated)
            VALUES(?, ?, ?, ?)""",
            (self.firstname, self.lastname, str(self.extraction_rule), self.is_deactivated)
        )
        self.id = cursor.lastrowid
        return self.id

    def load_performances(self, cursor) -> Optional[tuple[FileIndexRecord, ...]]:
        _perfs = PerformanceIndexRecord.fetch(cursor, self)
        if _perfs:
            return cast(tuple[FileIndexRecord, ...], _perfs.files)
        else:
            return None

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
            return PersonIndexRecord.from_sqlite_record(cursor, test)
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
        return (
            self.firstname,
            self.lastname,
            str(self.extraction_rule),
            self.is_deactivated,
            self.id
        )

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return tuple()

@dataclass
class PerformanceIndexRecord(SQLiteDataClass):
    """
    This relation has two fields: files and performers. Each field can either be
    a tuple of FileIndexRecords and PersonIndexRecords respectively or just a
    plain instance of those given types.

    We use the root-and-branches terminology here to describe the exclusively 
    one-to-many relationship represented by this class.

    An instance of this class is said to be _rooted_ if and only if one of the
    two fields is plain non-tuple instance while the other is a tuple.
    Furthermore, the record is said to be _rooted at_ the non-tuple field.

    The root of an instance can never change.
    """
    # FIXME This typing is hella confusing!
    files: Union[FileIndexRecord, tuple[FileIndexRecord, ...]]
    """
    This represents the files in this relationship persisted in the DB. To get
    all the files currently saved in this object, use the property `all_files`.
    """

    performers: Union[PersonIndexRecord, tuple[PersonIndexRecord, ...]]
    """
    This represents all the performers in this relationship persisted in the DB.
    To get all the performers saved in this object, use the property
    `all_performers`.
    """

    certainties: tuple[int, ...]
    certainties_original: tuple[int, ...] = field(init=False)

    # Invariant: added_branches and added_certainties are parallel arrays.
    added_branches: Union[list[FileIndexRecord], list[PersonIndexRecord]] = field(init=False)
    added_certainties: list[int] = field(init=False)

    deleted_branches: Union[list[FileIndexRecord], list[PersonIndexRecord]] = field(init=False)

    # Intentionally blank because we have to set the query depending on how this
    # instance is rooted.
    UPDATE_QUERY = ""

    def __post_init__(self):
        for c in self.certainties:
            assert c == 0 or c == 1

        self.added_branches = []
        self.added_certainties = []
        self.deleted_branches = []

    @property
    def all_performers(self) -> Union[PersonIndexRecord, tuple[PersonIndexRecord, ...]]:
        if self.__is_person_rooted():
            return self.performers
        else:
            all_performers = [p for p in cast(list[PersonIndexRecord], self.added_branches)]
            all_performers.extend(cast(tuple[PersonIndexRecord], self.performers))
            return tuple(all_performers)

    @property
    def all_files(self) -> Union[FileIndexRecord, tuple[FileIndexRecord, ...]]:
        if self.__is_performance_rooted():
            return self.files
        else:
            all_files = [f for f in cast(list[FileIndexRecord], self.files)]
            all_files.extend(cast(tuple[FileIndexRecord], self.files))
            return tuple(all_files)

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
            f"SELECT file_id,is_certain FROM participation WHERE person_id={root_record.id}"
            if is_person_rooted else
            f"SELECT person_id,is_certain FROM participation WHERE file_id={root_record.id}"
        )
        result = cursor.execute(query).fetchall()
        non_root_type = FileIndexRecord if is_person_rooted else PersonIndexRecord
        non_root_attr = tuple() if result is None else tuple([non_root_type.fetch(cursor, _id[0]) for _id in result if _id is not None])
        certainties = tuple() if result is None else tuple([r[1] for r in result if r is not None])
        
        if non_root_attr is not None:
            if is_person_rooted:
                return PerformanceIndexRecord(
                    files=non_root_attr, # type: ignore
                    performers=cast(PersonIndexRecord, root_record),
                    certainties=certainties
                )
            else:
                return PerformanceIndexRecord(
                    files=cast(FileIndexRecord, root_record),
                    performers=non_root_attr, # type: ignore
                    certainties=certainties
                )

    def add_performers(self, performers: Iterable[PersonIndexRecord], certainties: Iterable[int]): 
        for certainty in certainties:
            if certainty != 0 and certainty != 1:
                raise ValueError(f"certainty must either be 0 or 1 given {certainty}")

        if self.__is_performance_rooted():
            self.added_branches = cast(list[PersonIndexRecord], self.added_branches)
            self.added_branches.extend(performers)
            self.added_certainties.extend(certainties)
        else:
            raise InvalidDataClassState("Object must be performance rooted to add performers.")

    def add_files(self, files: Iterable[FileIndexRecord], certainties: Iterable[int]):
        for certainty in certainties:
            if certainty != 0 and certainty != 1:
                raise ValueError(f"certainty must either be 0 or 1 given {certainty}")

        if self.__is_person_rooted():
            self.added_branches = cast(list[FileIndexRecord], self.added_branches)
            self.added_branches.extend(files)
            self.added_certainties.extend(certainties)
        else:
            raise InvalidDataClassState("Object must be performer rooted to add performances.")

    @staticmethod
    @override
    def from_sqlite_record(cursor, record: tuple[Any, ...]) -> "PerformanceIndexRecord":
        raise ConstructorPreferred()

    @override
    def insert(self, cursor) -> Optional[int]:
        """
        To insert a plain one-to-one relationship between performance and
        performer, just root the record in either field and then make a
        singleton tuple for the other field.
        """
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
            if len(self.performers) != len(self.certainties):
                raise ValueError("performers and certainties are not the same length")

            if root_val.id is None:
                root_val.insert(cursor)

            root_val.id = cast(int, root_val.id)
            temp_tuples = []

            for p, c in zip(self.performers, self.certainties):
                if p.id is None:
                    p.insert(cursor)
            
                p.id = cast(int, p.id)
                temp_tuples.append((p.id, root_val.id, c))

            val_tuples = tuple(temp_tuples)
        elif self.__is_person_rooted():
            # self.performers is root
            root_performer = cast(PersonIndexRecord, self.performers)
            self.files = cast(tuple[FileIndexRecord, ...], self.files)
            if len(self.files) != len(self.certainties):
                raise ValueError("files and certainties are not the same length")

            if root_performer.id is None:
                root_performer.insert(cursor)

            root_performer.id = cast(int, root_performer.id)
            temp_tuples = []

            for f, c in zip(self.files, self.certainties):
                if f.id is None:
                    f.insert(cursor)

                f.id = cast(int, f.id)
                temp_tuples.append((root_performer.id, f.id, c))

            val_tuples = tuple(temp_tuples)
        else:
            raise InvalidDataClassState("Object is not rooted.")
        
        cursor.executemany(query, val_tuples)

        return cursor.lastrowid

    @override
    def create_update_tuple(self) -> tuple[Any, ...]:
        return tuple()
    
    @override
    def save(self, cursor) -> bool:
        """
        Note that this might effectively issue deletes if branches were pruned
        as well as inserts if branches were added.
        """
        # TODO Maybe we should enclose this in a transaction
        if self.__is_person_rooted():
            performer = cast(PersonIndexRecord, self.performers)
            # Handle deletes first
            delete_stmt_tmp = """
                DELETE FROM participation
                WHERE person_id = ?
                AND file_id in (%s);
            """
            delete_stmt = delete_stmt_tmp % ",".join("?" * len(self.deleted_branches))
            delete_vals = [b.id for b in self.deleted_branches]
            delete_vals.insert(0, performer.id)
            cursor.execute(delete_stmt, delete_vals)

            # Handle insertions next
            insert_stmt_tmp = """
                INSERT INTO participation (person_id, file_id, certainty)
                VALUES %S;
            """
            insert_stmt = insert_stmt_tmp % ",".join("(?, ?, ?)" * len(self.added_branches))
            insert_vals = (
                (performer.id, file.id, cert)
                for file, cert in zip(cast(list[FileIndexRecord], self.added_branches), self.added_certainties)
            )
            cursor.execute(insert_stmt, insert_vals)

            # Bulk update last
            update_stmt_tmp = """
                UPDATE participation
                SET file_id=?
                WHERE person_id=?
                LIMIT 1;
            """
            cursor.execute(
                update_stmt_tmp,
                (
                    (performer.id, file.id, cert)
                    for file, cert in zip(cast(tuple[FileIndexRecord], self.files), self.certainties)
                )
            )
            return True
        else:
            file = cast(FileIndexRecord, self.files)
            # Handle deletes first
            delete_stmt_tmp = """
                DELETE FROM participation
                WHERE file_id = ?
                AND person_id in (%s);
            """
            delete_stmt = delete_stmt_tmp % ",".join("?" * len(self.deleted_branches))
            delete_vals = [b.id for b in self.deleted_branches]
            delete_vals.insert(0, file.id)
            cursor.execute(delete_stmt, delete_vals)

            # Handle insertions next
            insert_stmt_tmp = """
                INSERT INTO participation (person_id, file_id, certainty)
                VALUES %S;
            """
            insert_stmt = insert_stmt_tmp % ",".join("(?, ?, ?)" * len(self.added_branches))
            insert_vals = (
                (performer.id, file.id, cert)
                for performer, cert in zip(cast(list[PersonIndexRecord], self.added_branches), self.added_certainties)
            )
            cursor.execute(insert_stmt, insert_vals)

            # Bulk update last
            update_stmt_tmp = """
                UPDATE participation
                SET person_id=?
                WHERE file_id=?
                LIMIT 1;
            """
            cursor.execute(
                update_stmt_tmp,
                (
                    (performer.id, file.id, cert)
                    for performer, cert in zip(cast(tuple[PersonIndexRecord], self.performers), self.certainties)
                )
            )
            return True

        return False

    @override
    def create_delete_tuple(self) -> tuple[Any, ...]:
        return tuple()
