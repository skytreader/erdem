"""
Assumptions:

- The filenames contain names but the library, as a whole cluster around 
  specific individuals, with very little overlap (though they certainly exist).
  So, for example, if we encounter "Emily Browning" subsequent references to
  "Emily" is probably also "Emily Browning" but "Emily Blunt" is probably also
  in there.
- Names are weird, the filenames even weirder/less standard.
"""
from .data import FileIndexRecord, MetadataRecord, NameDecisionRule, NameTuple, PerformanceIndexRecord, PersonIndexRecord
from .errors import MountpointMisMatch, MountpointUnderivable

from argparse import ArgumentParser
from collections import OrderedDict
from enum import Enum
from importlib import import_module
from typing import Any, cast, Iterable, Optional, List, Set, Tuple, Union

import locale as pylocale
import logging
import os
import re
import sqlite3
import traceback

NONWORD: re.Pattern = re.compile(r"[\W\_]+")

def error_string(ex: Exception) -> str:
    return '\n'.join([
        ''.join(traceback.format_exception_only(None, ex)).strip(),
        ''.join(traceback.format_exception(None, ex, ex.__traceback__)).strip()
    ])

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

class MetadataCheckResult(Enum):
    COMPLETELY_COMPATIBLE = 1
    LIKELY_COMPATIBLE = 2
    INCOMPATIBLE = 3
    INDETERMINATE = 4

class Indexerdem(object):

    SQLITE_TRUE = 1
    SQLITE_FALSE = 0

    DEFAULT_EXTENSIONS = ("mp4", "avi", "flv", "mkv")
    DEFAULT_LOCALES = ("en", "en_GB", "en_US", "en_NZ")
    # I can't be arsed about edge cases at the moment haha
    MOUNTPOINT_RE = re.compile(r"(?P<mountpoint>/media/[A-Za-z0-9]+/[A-Za-z0-9]+)(?P<restpath>/.+)")

    # The version of the index produced. This will be saved in the DB as
    # metadata. The major version should guarantee compatibility with similar
    # major versions of the indexer. The minor version represents changes that
    # might produce inconsistencies when presenting the data; this usually means
    # the code handling the data has changed assumptions somewhat. Schema
    # changes are _always_ major version bumps.
    INDEX_VERSION = "2.0"
    # The current version of this indexer. Follows semver. Major versions of
    # indexer should be able to continously work with similar major versions of
    # the index.
    INDEXER_VERSION = "2.0.0"

    def __init__(
        self,
        index_filename: str,
        locales: Optional[Iterable[str]] = None,
        extensions: Optional[Iterable[str]] = None,
        mountpoint: Optional[str] = None
    ):
        self.conn = sqlite3.connect(index_filename)
        self.first_names_female: Set[str] = set()
        self.last_names: Set[str] = set()
        self.mountpoint = mountpoint
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
        cursor.execute("""CREATE TABLE IF NOT EXISTS __metadata
                          (key TEXT PRIMARY KEY NOT NULL,
                           val TEXT NOT NULL);""")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mountpoints (
                id INTEGER PRIMARY KEY ASC,
                path TEXT UNIQUE NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY ASC,
                mountpoint_id INTEGER,
                filename TEXT UNIQUE NOT NULL,
                fullpath TEXT NOT NULL,
                rating TINYINT DEFAULT 0 CHECK (0 <= rating AND rating <= 10),
                review TEXT,
                UNIQUE(mountpoint_id, fullpath, filename),
                FOREIGN KEY(mountpoint_id) REFERENCES mountpoints(id)
            );
            """
        )
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
        # TODO Handle errors
        # The idea here is that this should only ever succeed when the index was
        # first created.
        MetadataRecord("indexer_version", Indexerdem.INDEXER_VERSION).insert(cursor)
        MetadataRecord("index_version", Indexerdem.INDEX_VERSION).insert(cursor)
        self.conn.commit()

    def check_compatibility(self) -> MetadataCheckResult:
        try:
            index_version = self.fetch_index_version()
            if index_version is not None:
                index_version_parse = index_version.val.split(".")
                indexer_version_parse = Indexerdem.INDEX_VERSION.split(".")

                if index_version.val == Indexerdem.INDEX_VERSION:
                    return MetadataCheckResult.COMPLETELY_COMPATIBLE
                elif index_version_parse[0] == indexer_version_parse[0]:
                    return MetadataCheckResult.LIKELY_COMPATIBLE
                else:
                    return MetadataCheckResult.INCOMPATIBLE
            else:
                return MetadataCheckResult.INDETERMINATE
        except Exception as e:
            return MetadataCheckResult.INDETERMINATE

    def fetch_index_version(self) -> Optional[MetadataRecord]:
        """
        Fetch the index version of the loaded index.
        """
        return MetadataRecord.fetch(self.conn.cursor(), "index_version")

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
            if self.mountpoint and absolute_path.startswith(self.mountpoint):
                fullpath_parse = Indexerdem.MOUNTPOINT_RE.match(absolute_path)
                absolute_path = fullpath_parse.group("pathrest")

            if absolute_path[-1] != os.path.sep:
                return f"{absolute_path}{os.path.sep}"

            return absolute_path

        def decide_mountpoint(cursor, absolute_path: str) -> MountpointRecord:
            """
            Decide the mountpoint when self.mountpoint is None.
            """
            if (mount_match := Indexerdem.MOUNTPOINT_RE.match(absolute_path)):
                mountpath = mount_match.group("mount")
                if (mountcheck := cursor.execute("SELECT * FROM mountpoints WHERE path=?", (mountpath,))):
                    return MountpointRecord.from_sqlite_record(cursor, mountcheck)
                else:
                    new_mount = MountpointRecord(None, mountpath)
                    new_mount.insert()
                    return new_mount
            else:
                raise MountpointUnderivable(absolute_path)

        try:
            cleaned = self.__normalize_filename(filename)
            file_id: Optional[int] = -1
            cursor = self.conn.cursor()
            # Determine which mountpoint we should use
            mountpoint = self.mountpoint if self.mountpoint else decide_mountpoint(cursor, fullpath)
            canon_fullpath = make_canonical(fullpath)
            try:
                file_record = FileIndexRecord(None, mountpoint, filename, canon_fullpath, None, 0)
                file_id = file_record.insert(cursor)
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
                if (file_record := FileIndexRecord.fetch(cursor, file_id)) is not None:
                    perf_record = PerformanceIndexRecord(
                        files=file_record,
                        performers=tuple(spam for spam in (PersonIndexRecord.fetch(cursor, pid) for pid in persons) if spam is not None)
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

    def fetch_files(self, limit: Optional[int] = None) -> tuple[FileIndexRecord, ...]:
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
        return tuple(PersonIndexRecord.from_sqlite_record(cursor, row) for row in cursor.execute(query).fetchall())
    
    def search_files(self, searchterm: str) -> Union[tuple[FileIndexRecord, ...], tuple]:
        cursor = self.conn.cursor()
        query = f"SELECT id, mountpoint_id, filename, fullpath, review, rating FROM files WHERE filename LIKE '%{searchterm}%'"
        return tuple(FileIndexRecord.from_sqlite_record(cursor, row) for row in cursor.execute(query).fetchall())

    def search_performers(self, searchterm: str) -> Union[tuple[PersonIndexRecord, ...], tuple]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM persons WHERE firstname LIKE '%{searchterm}%' OR lastname LIKE '%{searchterm}%'"
        return tuple(PersonIndexRecord(*row) for row in cursor.execute(query).fetchall())

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
    parser.add_argument(
        "--mountpoint", "-m", type=str, required=False,
        help="mountpoint of the drive"
    )
    args = vars(parser.parse_args())
    indexer: Indexerdem = Indexerdem(
        args["output"],
        args["locales"].split(","),
        Indexerdem.DEFAULT_EXTENSIONS
    )
    indexer.init()
    indexer.readdir(args["filepath"])
