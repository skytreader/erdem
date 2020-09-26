from argparse import ArgumentParser
from importlib import import_module
from typing import Iterable, List, Set, Tuple

import logging
import os
import re
import sqlite3

NONWORD: re.Pattern = re.compile("\W+")
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class Indexerdem(object):

    def __init__(self, index_filename: str, locale: str="en"):
        self.conn = sqlite3.connect(index_filename)
        person_providers_module = import_module("faker.providers.person.%s" % locale)
        self.first_names_female: Set[str] = set(person_providers_module.Provider.first_names_female)
        self.last_names: Set[str] = set(person_providers_module.Provider.last_names)

    def init(self):
        cursor = self.conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("""CREATE TABLE IF NOT EXISTS files
                          (id INTEGER PRIMARY KEY ASC, filename TEXT UNIQUE NOT NULL);""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS persons
                          (id INTEGER PRIMARY KEY ASC, firstname TEXT NOT NULL, lastname TEXT);""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS participation
                          (person_id INTEGER, file_id INTEGER,
                           FOREIGN KEY(person_id) REFERENCES persons(id),
                           FOREIGN KEY(file_id) REFERENCES file(id))""")
        self.conn.commit()

    def __normalize_filename(self, filename: str) -> str:
        spam = filename.rsplit(".", 1)
        return spam[0]

    def __find_names(self, haystack: str) -> Iterable[Tuple[str]]:
        def sanitize(s: str) -> str:
            return "".join([c for c in s if str.isalpha(c)])

        hayparse: List[str] = NONWORD.split(haystack)
        names: List[Tuple[str]] = []
        i = 0
        limit = len(hayparse)

        while i < limit:
            word = hayparse[i]
            sanitized = sanitize(word)

            if sanitized in self.first_names_female:
                forward = i + 1
                if forward < limit:
                    if hayparse[forward] in self.last_names:
                        names.append((sanitized, hayparse[forward]))
                        i = forward
                        continue
                    else:
                        names.append((sanitized,))
                else:
                    names.append((sanitized,))

            i += 1
        
        return names

    def index(self, filename: str) -> None:
        try:
            cleaned = self.__normalize_filename(filename)
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO files (filename) VALUES (?)", (filename,))
            names = self.__find_names(cleaned)

            for name in names:
                if len(name) == 2:
                    cursor.execute("INSERT INTO persons (firstname, lastname) VALUES (?, ?)", name)
                elif len(name) == 1:
                    cursor.execute("INSERT INTO persons (firstname) VALUES (?)", name)
                else:
                    print("Found an odd name: %s" % name)

        except:
            logger.error("Ran into some problems...")
        finally:
            self.conn.commit()

    def readdir(self, dirpath: str) -> None:
        try:
            for root, dirs, files in os.walk(dirpath):
                for _file in files:
                    logger.info("processing %s" % _file)
                    self.index(_file)
        except:
            logger.error("Ran into some problems...")
            self.conn.close()

if __name__ == "__main__":
    parser = ArgumentParser(description="indexer for erdem.")
    indexer: Indexerdem = Indexerdem("cache.db")
    indexer.init()
    indexer.readdir("/home/chad/Videos/ytdlpl")
