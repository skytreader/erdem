import React from "react";
import ReactDOMServer from "react-dom/server";
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from "arwes";
import {BrowserRouter, Switch, Route, Link} from "react-router-dom";

import {erdemCentered} from "./utils";

class Erdem extends React.Component {
    
    constructor(props: any) {
        super(props);
        this.state = {
            mediaItems: []
        };
    }

    componentDidMount() {
        document.title = "Erdem";
    }

    render() {
        return (
            <BrowserRouter>
              <ThemeProvider theme={createTheme()}>
                <Arwes animate show>
                  <Row>
                    <Col s={0} m={3}></Col>
                    <Col s={12} m={6}><h1><a href="/" className="logo"><img src={logo} alt="Erdem Logo" />Erdem</a></h1></Col>
                  </Row>
                  <Switch>
                    <Route exact path="/" component={FileList}/>
                    <Route exact path="/participants/:fileid" component={ParticipationList}/>
                    <Route exact path="/performances/:personid" component={PerformanceList}/>
                  </Switch>
                </Arwes>
              </ThemeProvider>
            </BrowserRouter>
        )
    }
}

interface MediaItem {
    filename: string;
    id: number;
}

interface FileListState {
    mediaItems: MediaItem[];
    isError: boolean;
}

class FileList extends React.Component<any, FileListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            mediaItems: [],
            isError: false
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/files")
            .then(res => res.json())
            .then((result) => {
                this.setState({
                    mediaItems: result.sort((a: MediaItem, b: MediaItem) => {
                        var normA = a.filename.toUpperCase();
                        var normB = b.filename.toUpperCase();

                        if (normA < normB) {
                            return -1;
                        } else if (normA > normB) {
                            return 1;
                        } else {
                            return 0;
                        }
                    }),
                    isError: false
                });
            },
            (error) => {
                this.setState({
                    mediaItems: [],
                    isError: true
                });
                console.error("Error occurred", error);
        });
    }

    render() {
        if (this.state.isError) {
            // TODO Style better.
            return (
                <div>Error fetching files. Check server.</div>
            )
        } else {
            return this.state.mediaItems.map((file) => (
                <Row key={file.id}>
                    <Col s={0} m={3}></Col>
                    <Col s={12} m={6}><Link to={`/participants/${file.id}`}>{file.filename}</Link></Col>
                    <Col s={0} m={3}></Col>
                </Row>
            ));
        }
    }
}

interface PersonRecord {
    id: number;
    firstname: string;
    lastname: string;
}

interface ParticipationListState {
    participants: any[];
    isError: boolean;
}

class ParticipationList extends React.Component<any, ParticipationListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            participants: [],
            isError: false
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/fileparticipants/" + this.props.match.params.fileid)
            .then(res => res.json())
            .then((result) => {
                this.setState({
                    participants: result,
                    isError: false
                });
            },
            (error) => {
                this.setState({
                    participants: [],
                    isError: true
                });
                console.error("Error occurred", error);
            });
    }

    render() {
        if (this.state.isError) {
            // TODO Style better.
            return (
                <div>Error connecting to server.</div>
            )
        } else if (this.state.participants.length > 0) {
            return [
                (
                    <Row>
                        <Col s={0} m={3}></Col>
                        <Col s={12} m={6}>
                            Participants in <strong>{this.state.participants[0].filename}</strong>
                        </Col>
                    </Row>
                ),
                this.state.participants.map((record: PersonRecord) => (
                    <Row key={record.id}>
                        {erdemCentered((<BrowserRouter><Link to={`/performances/${record.id}`}>{`${record.firstname} ${record.lastname}`}</Link></BrowserRouter>))}
                    </Row>
                ))
            ];
        }
        return null;
    }
}

interface PerformanceListState {
    performances: any[];
    isError: boolean;
}

class PerformanceList extends React.Component<any, PerformanceListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            performances: [],
            isError: false
        }
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/files/" + this.props.match.parmas.personid)
            .then(res => res.json())
            .then((result) => {
                this.setState({
                    performances: result,
                    isError: false
                });
            },
            (error) => {
                this.setState({
                    performances: [],
                    isError: true
                });
            });
    }

    render() {
        if (this.state.isError) {
            return (
                <div>Error connecting to server.</div>
            )
        } else if (this.state.performances.length > 0) {
            const sample = this.state.performances[0];
            const name = sample.firstname + " " + sample.lastname;
//{erdemCentered((<Link to={`/performances/${record.fileid}`}>record.filename</Link>))}
            return [
                (
                    <Row>
                        {erdemCentered("Performances of " + name)}
                    </Row>
                ),
                (
                    <BrowserRouter>
                        {this.state.performances.map((record) => (
                            <Row key={record.fileid}>
                                {erdemCentered(record.filename)}
                            </Row>
                        ))}
                    </BrowserRouter>
                )
            ];
        }
    }
}


export default Erdem;
