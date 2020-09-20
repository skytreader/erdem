from argparse import ArgumentParser

import sqlite3

class Indexerdem(object):

    def __init__(self, index_filename: str):
        self.conn = sqlite3.connect(index_filename)

    def init(self):
        cursor = self.conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("""CREATE TABLE files
                          (id INTEGER PRIMARY KEY ASC, filename TEXT);""")
        cursor.execute("""CREATE TABLE persons
                          (id INTEGER PRIMARY KEY ASC, firstname TEXT NOT NULL, lastname TEXT);""")
        cursor.execute("""CREATE TABLE participation
                          (person_id INTEGER, file_id INTEGER,
                           FOREIGN KEY(person_id) REFERENCES persons(id),
                           FOREIGN KEY(file_id) REFERENCES file(id))""")
        self.conn.commit()

if __name__ == "__main__":
    parser = ArgumentParser(description="indexer for erdem.")
    indexer: Indexerdem = Indexerdem("cache.db")
    indexer.init()
