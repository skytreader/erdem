import express from 'express';

const app: express.Application = express();

app.get("/", (req, res) => {
    res.send("Hello World!");
});

app.listen(16981, () => {
    console.log("Hello");
});
