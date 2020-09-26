from argparse import ArgumentParser
from importlib import import_module
from typing import List, Set, Tuple

import re
import sqlite3

NONWORD: re.Pattern = re.compile("\W+")

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

    def __find_names(self, haystack: str) -> Tuple[str]:
        def sanitize(s: str) -> str:
            return "".join([c for c in s if str.isalpha(c)])

        hayparse: List[str] = NONWORD.split(haystack)
        names: List[str] = []
        i = 0
        limit = len(hayparse)

        while i < limit:
            word = hayparse[i]
            sanitized = sanitize(word)

            if sanitized in self.first_names_female:
                forward = i + 1
                if forward < limit:
                    if hayparse[forward] in self.last_names:
                        person = (sanitized, hayparse[forward])
                        cursor.execute("INSERT INTO persons (firstname, lastname) VALUES (?, ?)", person)
                        i = forward
                        continue
                    else:
                        person = (sanitized,)
                        cursor.execute("INSERT INTO persons (firstname) VALUES (?)", person)
                else:
                    person = (sanitized,)
                    cursor.execute("INSERT INTO persons (firstname) VALUES (?)", person)

            i += 1

    def index(self, filename: str) -> None:
        cleaned = self.__normalize_filename(filename)
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO files (filename) VALUES (?)", (filename,))

if __name__ == "__main__":
    parser = ArgumentParser(description="indexer for erdem.")
    indexer: Indexerdem = Indexerdem("cache.db")
    indexer.init()
    indexer.index("lin.mp4")
