"""
Assumptions:

- The filenames contain names but the library, as a whole cluster around 
  specific individuals, with very little overlap (though they certainly exist).
  So, for example, if we encounter "Emily Browning" subsequent references to
  "Emily" is probably also "Emily Browning" but "Emily Blunt" is probably also
  in there.
- Names are weird, the filenames even weirder/less standard.
"""
from argparse import ArgumentParser
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from typing import Iterable, Optional, List, Set, Tuple, Union

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

class NameDecisionRule(Enum):
    ALMOST_CERTAIN = "almost-certain"
    TRUNCATED_FIRSTNAME = "truncated-firstname"
    LASTNAME_BACKWARD = "lastname-backward"
    MANUAL_INPUT = "manual-input"

NameTuple = Tuple[str, Optional[str], NameDecisionRule]

@dataclass
class FileIndexRecord:
    id: int
    filename: str
    fullpath: str
    rating: int
    review: str

@dataclass
class PersonIndexRecord:
    id: int
    firstname: str
    lastname: str
    extraction_rule: NameDecisionRule

@dataclass
class PerformanceIndexRecord:
    file: FileIndexRecord
    performer: PersonIndexRecord

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
                          (person_id INTEGER, file_id INTEGER, is_certain INTEGER NOT NULL DEFAULT {is_certain_default},
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
            file_id: Union[int, None] = -1
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

            for name in names:
                if len(name) == 3:
                    person_id: Optional[int] = self.__get_person_id(cursor, name[0], name[1])
                    if person_id is None:
                        person = (name[0], name[1], name[2].value)
                        cursor.execute("INSERT INTO persons (firstname, lastname, extraction_rule, is_deactivated) VALUES (?, ?, ?, 0)", person)
                        person_id = cursor.lastrowid

                    certainty = Indexerdem.SQLITE_TRUE if decide_certainty(name) else Indexerdem.SQLITE_FALSE
                    try:
                        cursor.execute(
                            "INSERT INTO participation (person_id, file_id, is_certain) VALUES (?, ?, ?);",
                            (person_id, file_id, certainty)
                        )
                    except sqlite3.IntegrityError:
                        logger.warn("Name previously indexed for file: " + str(name))
                else:
                    logger.error("Found an odd name: %s" % str(name))
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

    def fetch_files(self, limit=None):
        cursor = self.conn.cursor()
        query = (
            f"SELECT * FROM files LIMIT={limit}"
            if limit is not None else
            "SELECT * FROM files"
        )
        return tuple(FileIndexRecord(*row) for row in cursor.execute(query).fetchall())
    
    def fetch_persons(self, active_only=True):
        cursor = self.conn.cursor()

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
