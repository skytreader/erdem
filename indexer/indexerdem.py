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
from importlib import import_module
from typing import Iterable, Optional, List, Set, Tuple, Union

import logging
import os
import re
import sqlite3

NONWORD: re.Pattern = re.compile("\W+")
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

NameTuple = Union[
    Tuple[str, Optional[str], bool],
    Tuple[str, Optional[str]]
]

class Indexerdem(object):

    SQLITE_TRUE = 1
    SQLITE_FALSE = 0

    def __init__(self, index_filename: str, locales: Iterable[str]):
        self.conn = sqlite3.connect(index_filename)
        self.first_names_female: Set[str] = set()
        self.last_names: Set[str] = set()
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
                          (id INTEGER PRIMARY KEY ASC, filename TEXT UNIQUE NOT NULL);""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS persons
                          (id INTEGER PRIMARY KEY ASC,
                           firstname TEXT NOT NULL,
                           lastname TEXT,
                           UNIQUE(firstname, lastname));""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS participation
                          (person_id INTEGER, file_id INTEGER, is_certain INTEGER NOT NULL DEFAULT {is_certain_default},
                           FOREIGN KEY(person_id) REFERENCES persons(id),
                           FOREIGN KEY(file_id) REFERENCES files(id))""".format(is_certain_default=Indexerdem.SQLITE_TRUE))
        self.conn.commit()

    def __normalize_filename(self, filename: str) -> str:
        spam = filename.rsplit(".", 1)
        return spam[0].replace("&", "and")

    def __find_names(self, haystack: str) -> Iterable[
        Union[
            Tuple[str, Optional[str], bool],
            Tuple[str, Optional[str]]
        ]
    ]:
        def sanitize(s: str) -> str:
            return "".join([c for c in s if str.isalpha(c)]).title()

        hayparse: List[str] = NONWORD.split(haystack)
        names: List[
            Union[
                Tuple[str, Optional[str]],
                Tuple[str, Optional[str], bool]
            ]
        ] = []
        i = 0
        limit = len(hayparse)

        while i < limit:
            word = hayparse[i]
            sanitized = sanitize(word)

            # FIXME This assumes names are only two-part. The "reasonable" thing
            # to do would be to consume until we encounter something that isn't
            # a name. However, watch out that sanitation means we lose boundary
            # cues in comma-listed names.
            if sanitized in self.first_names_female:
                forward = i + 1
                if forward < limit:
                    if hayparse[forward] in self.last_names:
                        names.append((sanitized, hayparse[forward]))
                        i = forward
                        continue
                    else:
                        names.append((sanitized, None))
                else:
                    names.append((sanitized, None))
            elif sanitized in self.last_names:
                backward = i - 1
                if backward >= 0:
                   names.append((hayparse[backward], sanitized))

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

    def index(self, filename: str) -> None:
        def decide_certainty(nametpl: NameTuple) -> bool:
            if len(nametpl) == 3:
                return nametpl[2] # type: ignore
            else:
                return nametpl[1] is not None

        try:
            cleaned = self.__normalize_filename(filename)
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO files (filename) VALUES (?)", (filename,))
            file_id = cursor.lastrowid
            names = self.__find_names(cleaned)

            for name in names:
                if len(name) == 2:
                    person_id: Optional[int] = self.__get_person_id(cursor, name[0], name[1])
                    if person_id is None:
                        logger.info("Inserting %s because person_id is %s" % (str(name), person_id))
                        cursor.execute("INSERT INTO persons (firstname, lastname) VALUES (?, ?)", name)
                        person_id = cursor.lastrowid

                    certainty = Indexerdem.SQLITE_TRUE if decide_certainty(name) else Indexerdem.SQLITE_FALSE
                    cursor.execute(
                        "INSERT INTO participation (person_id, file_id, is_certain) VALUES (?, ?, ?);",
                        (person_id, file_id, certainty)
                    )
                else:
                    logger.error("Found an odd name: %s" % str(name))

        except:
            logger.exception("Ran into some problems...")
        finally:
            logger.info("committing...")
            self.conn.commit()

    def readdir(self, dirpath: str) -> None:
        try:
            for root, dirs, files in os.walk(dirpath):
                for _file in files:
                    logger.info("processing %s" % _file)
                    self.index(_file)
        except:
            logger.exception("Ran into some problems...")
        finally:
            self.conn.close()

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
    args = vars(parser.parse_args())
    indexer: Indexerdem = Indexerdem("cache.db", args["locales"].split(","))
    indexer.init()
    indexer.readdir(args["filepath"])
