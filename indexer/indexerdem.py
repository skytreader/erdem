from argparse import ArgumentParser

import sqlite3

class Indexerdem(object):

    def __init__(self, index_filename: str):
        self.conn = sqlite3.connect(index_filename)

    def init(self):
        cursor = self.conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")
        # FIXME what if tables already exist?
        cursor.execute("""CREATE TABLE files
                          (id INTEGER PRIMARY KEY ASC, filename TEXT UNIQUE NOT NULL);""")
        cursor.execute("""CREATE TABLE persons
                          (id INTEGER PRIMARY KEY ASC, firstname TEXT NOT NULL, lastname TEXT);""")
        cursor.execute("""CREATE TABLE participation
                          (person_id INTEGER, file_id INTEGER,
                           FOREIGN KEY(person_id) REFERENCES persons(id),
                           FOREIGN KEY(file_id) REFERENCES file(id))""")
        self.conn.commit()

    def __normalize_filename(self, filename: str) -> str:
        spam = filename.split(".")
        # TODO Check, there might be dots before the extension too!
        return spam[0]

    def index(self, filename: str) -> None:
        cleaned = self.__normalize_filename(filename)
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO files (filename) VALUES (?)", (filename,))

if __name__ == "__main__":
    parser = ArgumentParser(description="indexer for erdem.")
    indexer: Indexerdem = Indexerdem("cache.db")
    indexer.init()
    indexer.index("lin.mp4")
