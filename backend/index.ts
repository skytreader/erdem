import express from 'express';
import sqlite3 from 'sqlite3';
import {promisify} from 'util';

const db = new sqlite3.Database("cache.db");

const aDbAll = promisify(db.all).bind(db);

const app: express.Application = express();

app.get("/", (req, res) => {
    res.send("Hello World!");
    db.each("SELECT * FROM files;", (err, row) => {
        console.log(row.filename);
    });
});

app.get("/files", async (req, res) => {
    const rows = await aDbAll("SELECT * FROM files;");
    return res.json(rows);
});

app.listen(16981, () => {
    console.log("Hello");
});
