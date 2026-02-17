"""
Assumptions:

- The filenames contain names but the library, as a whole cluster around 
  specific individuals, with very little overlap (though they certainly exist).
  So, for example, if we encounter "Emily Browning" subsequent references to
  "Emily" is probably also "Emily Browning" but "Emily Blunt" is probably also
  in there.
- Names are weird, the filenames even weirder/less standard.
"""
from .errors import ConstructorPreferred, InvalidDataClassState

from abc import ABC, abstractmethod
from argparse import ArgumentParser
from collections import OrderedDict
from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module
from typing import Any, cast, Iterable, Optional, List, Set, Tuple, Union

import locale as pylocale
import logging
import os
import re
import sqlite3

NONWORD: re.Pattern = re.compile("[\W\_]+")

# From https://stackoverflow.com/a/56944256/777225
class ColoredLogFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_ = "%(asctime)s - (%(filename)s:%(lineno)d)- %(name)s.%(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_ + reset,
        logging.INFO: grey + format_ + reset,
        logging.WARNING: yellow + format_ + reset,
        logging.ERROR: red + format_ + reset,
        logging.CRITICAL: bold_red + format_ + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
_loghandler = logging.StreamHandler()
_loghandler.setFormatter(ColoredLogFormatter())
logger.addHandler(_loghandler)

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
    files: Union[FileIndexRecord, tuple[Optional[FileIndexRecord], ...]]
    performers: Union[PersonIndexRecord, tuple[Optional[PersonIndexRecord], ...]]

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

class Indexerdem(object):

    SQLITE_TRUE = 1
    SQLITE_FALSE = 0

    DEFAULT_EXTENSIONS = ("mp4", "avi", "flv", "mkv")
    DEFAULT_LOCALES = ("en", "en_GB", "en_US", "en_NZ")

    def __init__(self, index_filename: str, locales: Optional[Iterable[str]] = None, extensions: Optional[Iterable[str]] = None):
        self.conn = sqlite3.connect(index_filename)
        self.first_names_female: Set[str] = set()
        self.last_names: Set[str] = set()
        self.extensions: Set[str] = set(extensions) if extensions is not None else set(Indexerdem.DEFAULT_EXTENSIONS)
        if locales is None:
            runtime_locale = pylocale.getlocale()
            if len(runtime_locale) >= 1 and runtime_locale[0] is not None:
                locales = (runtime_locale[0],)
            else:
                locales = Indexerdem.DEFAULT_LOCALES
        for loc in locales:
            person_providers_module = import_module("faker.providers.person.%s" % loc)
            self.first_names_female |= self.__extract_names(person_providers_module.Provider.first_names_female) # type: ignore
            self.last_names |= self.__extract_names(person_providers_module.Provider.last_names) # type: ignore
            self.last_names |= self.__extract_names(person_providers_module.Provider.first_names_male) # type: ignore

    def __extract_names(self, faker_listings: Union[OrderedDict, Tuple]) -> Set[str]:
        if isinstance(faker_listings, tuple):
            return set(faker_listings)
        elif isinstance(faker_listings, OrderedDict):
            return set(faker_listings.keys())
        else:
            raise TypeError("We can only operate with OrderedDicts or tuples. Given: %s" % type(faker_listings))

    def init(self):
        cursor = self.conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("""CREATE TABLE IF NOT EXISTS files
                          (id INTEGER PRIMARY KEY ASC,
                           filename TEXT UNIQUE NOT NULL,
                           fullpath TEXT NOT NULL,
                           rating TINYINT DEFAULT 0 CHECK (0 <= rating AND rating <= 10),
                           review TEXT);""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS persons
                          (id INTEGER PRIMARY KEY ASC,
                           firstname TEXT NOT NULL,
                           lastname TEXT,
                           extraction_rule TEXT NOT NULL,
                           is_deactivated TINYINT DEFAULT 0 NOT NULL,
                           UNIQUE(firstname, lastname));""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS participation
                          (person_id INTEGER,
                           file_id INTEGER,
                           is_certain INTEGER NOT NULL DEFAULT {is_certain_default},
                           FOREIGN KEY(person_id) REFERENCES persons(id),
                           FOREIGN KEY(file_id) REFERENCES files(id),
                           UNIQUE(person_id, file_id))""".format(is_certain_default=Indexerdem.SQLITE_TRUE))
        self.conn.commit()

    def __normalize_filename(self, filename: str) -> str:
        spam = filename.rsplit(".", 1)
        return spam[0].replace("&", "and")

    def __find_names(self, haystack: str) -> Iterable[NameTuple]:
        hayparse: List[str] = NONWORD.split(haystack)
        names: List[NameTuple] = []
        i = 0
        limit = len(hayparse)

        while i < limit:
            word = hayparse[i].title()

            # FIXME This assumes names are only two-part. The "reasonable" thing
            # to do would be to consume until we encounter something that isn't
            # a name. However, watch out that sanitation means we lose boundary
            # cues in comma-listed names.
            if word in self.first_names_female:
                forward = i + 1
                if forward < limit:
                    if hayparse[forward] in self.last_names:
                        names.append(
                            (
                                word.capitalize(),
                                hayparse[forward].capitalize(),
                                NameDecisionRule.ALMOST_CERTAIN
                            )
                        )
                        i = forward + 1
                        continue
                    else:
                        names.append(
                            (
                                word.capitalize(),
                                None,
                                NameDecisionRule.TRUNCATED_FIRSTNAME
                            )
                        )
                else:
                    names.append(
                        (
                            word.capitalize(),
                            None,
                            NameDecisionRule.TRUNCATED_FIRSTNAME
                        )
                    )
            elif word in self.last_names:
                backward = i - 1
                if backward >= 0:
                   names.append(
                        (
                            hayparse[backward].capitalize(),
                            word.capitalize(),
                            NameDecisionRule.LASTNAME_BACKWARD
                        )
                    )

            i += 1
        
        return names

    def __get_person_id(self, cursor, firstname: str, lastname: Optional[str]) -> Optional[int]:
        if lastname is not None:
            test = cursor.execute("SELECT id FROM persons WHERE firstname=? AND lastname=? LIMIT 1;", (firstname, lastname)).fetchone()
        else:
            test = cursor.execute("SELECT id FROM persons WHERE firstname=? AND lastname IS NULL LIMIT 1;", (firstname,)).fetchone()

        if test:
            return test[0]
        else:
            return None

    def index(self, filename: str, fullpath: str) -> None:
        def decide_certainty(nametpl: NameTuple) -> bool:
            return nametpl[2] == NameDecisionRule.ALMOST_CERTAIN

        def make_canonical(absolute_path: str) -> str:
            if absolute_path[-1] != os.path.sep:
                return f"{absolute_path}{os.path.sep}"

            return absolute_path

        try:
            cleaned = self.__normalize_filename(filename)
            file_id: Optional[int] = -1
            cursor = self.conn.cursor()
            canon_fullpath = make_canonical(fullpath)
            try:
                cursor.execute("INSERT INTO files (filename, fullpath) VALUES (?, ?)", (filename, canon_fullpath))
                file_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                file_id = cursor.execute("SELECT id FROM files WHERE filename=? AND fullpath=? LIMIT 1;", (filename, canon_fullpath)).fetchone()[0]
                logger.warn("File %s%s previously indexed as id %s." % (fullpath, filename, file_id))
            names = self.__find_names(cleaned)
            logger.info("'%s' has the ff. names: %s" % (filename, names))
            persons = []
            certainties = []

            for name in names:
                if len(name) == 3:
                    person = PersonIndexRecord.find_by_name(cursor, name[0], name[1])
                    if person is None:
                        new_person = PersonIndexRecord(
                            firstname=name[0],
                            lastname=name[1],
                            extraction_rule=name[2],
                            is_deactivated=0,
                            id=None
                        )
                        person_id = new_person.insert(cursor)

                        if person_id is not None:
                            persons.append(person_id)
                            certainties.append(Indexerdem.SQLITE_TRUE if decide_certainty(name) else Indexerdem.SQLITE_FALSE)
                    elif person.id is not None:
                        persons.append(person.id)
                        certainties.append(Indexerdem.SQLITE_TRUE if person.extraction_rule is NameDecisionRule.ALMOST_CERTAIN else Indexerdem.SQLITE_FALSE)
                else:
                    logger.error("Found an odd name: %s" % str(name))

            if file_id is not None and file_id != -1:
                file_record = FileIndexRecord.fetch(cursor, file_id)
                if file_record is not None:
                    perf_record = PerformanceIndexRecord(
                        files=file_record,
                        performers=tuple(PersonIndexRecord.fetch(cursor, pid) for pid in persons)
                    )
                    try:
                        perf_record.insert(
                            cursor,
                            PerformanceIndexRecord.ExtraArgs(certainties=tuple(certainties))
                        )
                    except sqlite3.IntegrityError:
                        logger.warn(f"Some persons are already associated with {file_record}")
        except:
            logger.exception("Ran into some problems...")
        finally:
            self.conn.commit()

    def __get_ext(self, fname: str) -> str:
        return fname.rsplit(".", 1)[1]

    def readdir(self, dirpath: str) -> None:
        try:
            for root, dirs, files in os.walk(dirpath):
                for _file in files:
                    if self.__get_ext(_file) in self.extensions:
                        logger.info("processing %s" % _file)
                        self.index(_file, root)
        except:
            logger.exception("Ran into some problems...")
        finally:
            self.conn.close()

    def __sqliteify(self, b: bool) -> int:
        return Indexerdem.SQLITE_TRUE if b else Indexerdem.SQLITE_FALSE

    def fetch_files(self, limit=None) -> tuple[FileIndexRecord, ...]:
        cursor = self.conn.cursor()
        query = (
            f"SELECT * FROM files LIMIT={limit}"
            if limit is not None else
            "SELECT * FROM files"
        )
        return tuple(FileIndexRecord(*row) for row in cursor.execute(query).fetchall())
    
    def get_file_record_from_id(self, id: int) -> Optional[FileIndexRecord]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM files WHERE id={id} LIMIT 1"
        result = cursor.execute(query).fetchone()
        return FileIndexRecord(*result) if result is not None else None
    
    def fetch_persons(self, activity_status: Optional[bool] = None) -> tuple[PersonIndexRecord, ...]:
        cursor = self.conn.cursor()
        query = (
            f"SELECT * FROM persons WHERE is_deactivated={self.__sqliteify(activity_status)}"
            if activity_status is not None else
            "SELECT * FROM persons"
        )
        return tuple(PersonIndexRecord.from_sqlite_record(row) for row in cursor.execute(query).fetchall())

if __name__ == "__main__":
    parser = ArgumentParser(description="indexer for erdem.")
    parser.add_argument(
        "--filepath", "-f", required=True, type=str,
        help="The full filepath of the directory to index."
    )
    parser.add_argument(
        "--locales", "-l", type=str, default="en,en_GB,en_US,en_NZ",
        help="Comma-separated list of locales that we will use to detect names."
    )
    parser.add_argument(
        "--output", "-o", type=str, default="cache.db",
        # TODO Ensure overwrite guarantee is true!
        help="filepath to output file. An existing file will be appended to."
    )
    args = vars(parser.parse_args())
    indexer: Indexerdem = Indexerdem(args["output"], args["locales"].split(","), Indexerdem.DEFAULT_EXTENSIONS)
    indexer.init()
    indexer.readdir(args["filepath"])
