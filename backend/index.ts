import cors from 'cors';
import express from 'express';
import sqlite3 from 'sqlite3';
import {promisify} from 'util';

const db = new sqlite3.Database("cache.db");

const aDbAll = promisify(db.all).bind(db);

const app: express.Application = express();
app.use(cors());
app.options("*", cors());

app.get("/", (req, res) => {
    res.send("Hello World!");
    db.each("SELECT * FROM files;", (err, row) => {
        console.log(row.filename);
    });
});

// WARNING: Kids, don't do this in prod!
app.get("/fetch/:table", async (req, res, next) => {
    console.log("/fetch");
    try {
        const rows = await aDbAll("SELECT * FROM " + req.params.table + ";");
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.get("/fetch/fileparticipants/:fileid", async (req, res, next) => {
    console.log("/fetch/fileparticipants/", req.params.fileid);
    try {
        const rows = await aDbAll("SELECT persons.id, persons.firstname, persons.lastname, files.filename FROM persons, participation, files WHERE participation.file_id=" + req.params.fileid + " AND participation.person_id=persons.id AND participation.file_id=files.id;");
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.get("/fetch/files/:personid", async (req, res, next) => {
    console.log("/fetch/files", req.params.personid);
    try{
        const rows = await aDbAll("SELECT files.id, files.filename, persons.id, persons.firstname, persons.lastname FROM files, participation, persons WHERE participation.file_id=files.id AND participation.person_id=" + req.params.personid + " AND persons.id=participation.person_id");
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.listen(16981, () => {
    console.log("Hello");
});
