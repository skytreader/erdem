import cors from 'cors';
import express from 'express';
import sqlite3 from 'sqlite3';
import {promisify} from 'util';

const db = new sqlite3.Database("cache.db");

const aDbAll = promisify(db.all).bind(db);
const asAnyArr = (x: any) => (x as any[]);

const app: express.Application = express();
app.use(cors());
app.use(express.json());
app.options("*", cors());

app.get("/", (req, res) => {
    res.send("Hello World!");
    db.each("SELECT * FROM files;", (err, row) => {
        console.log(row.filename);
    });
});

app.get("/files", async (req, res, next) => {
    console.log("/files");
    try {
        const rows = await aDbAll(`SELECT * FROM files;`);
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.get("/persons/active", async (req, res, next) => {
    console.log("/persons/active");
    try {
        const rows = await aDbAll(`SELECT * FROM persons WHERE is_deactivated=0;`);
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.get("/fetch/search/:query", async (req, res, next) => {
    console.log("/fetch/search/", req.params.query);
    try {
        const rows = await aDbAll("SELECT id, filename FROM files WHERE filename LIKE '%" + req.params.query + "%';");
        return res.json(rows);
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.get("/file/:fileid", async (req, res, next) => {
    console.log("/file/", req.params.fileid);
    try {
        const participants: any[] = asAnyArr(await aDbAll(`SELECT persons.id, persons.firstname, persons.lastname, files.filename, files.fullpath, files.review
            FROM files
            LEFT JOIN participation
                ON participation.file_id=files.id
            LEFT JOIN persons
                ON persons.id=participation.person_id
                AND persons.is_deactivated=0
            WHERE files.id=${req.params.fileid};`));
        if (participants.length != 0) {
            const filename = participants[0].filename;
            const fullpath = participants[0].fullpath;
            const review = participants[0].review;
            return res.json({filename, fullpath, participants, review});
        } else {
            const details: any = await aDbAll(`SELECT filename, fullpath, review
            FROM files
            WHERE id=${req.params.fileid}`);
            details["participants"] = []
            return res.json(details);
        }
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.post("/file/:fileid", async (req, res, next) => {
    console.log("POST /file/", req.params.fileid, req.headers, req.body);
    try {
        await aDbAll(`UPDATE files
        SET review="${req.body.review}"
        WHERE id=${req.params.fileid}`);
        return res.send("OK");
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

app.patch("/person/:id/is_deactivated/:stat", async (req, res, next) => {
    console.log("PATCH /person/", req.params.id, "/deactivate/", req.params.stat);
    try{
        await aDbAll(`UPDATE persons
        SET is_deactivated=${req.params.stat}
        WHERE id=${req.params.id}`);
        return res.send("OK");
    } catch(error) {
        console.error("Caught an exception:", error);
        next(error);
    }
});

app.listen(16981, () => {
    console.log("Hello");
});
