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

// WARNING: Kids, don't do this in prod!
app.get("/fetch/:table", async (req, res, next) => {
    try {
        const rows = await aDbAll("SELECT * FROM " + req.params.table + ";");
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.listen(16981, () => {
    console.log("Hello");
});
