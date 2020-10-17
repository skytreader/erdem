import express from 'express';
import sqlite3 from 'sqlite3';

const db = new sqlite3.Database("cache.db");
const app: express.Application = express();

app.get("/", (req, res) => {
    res.send("Hello World!");
    db.each("SELECT * FROM files;", (err, row) => {
        console.log(row.filename);
    });
});

app.listen(16981, () => {
    console.log("Hello");
});
