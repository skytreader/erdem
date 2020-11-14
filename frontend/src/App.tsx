import React from "react";
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from "arwes";
import {Switch, Route, Link} from "react-router-dom";

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
            <ThemeProvider theme={createTheme()}>
              <Arwes animate show>
                <Row>
                  <Col s={0} m={3}></Col>
                  <Col s={12} m={6}><h1><img src={logo} alt="Erdem Logo" />Erdem</h1></Col>
                </Row>
                <Switch>
                  <Route exact path="/" component={FileList}/>
                  <Route exact path="/participants/:fileid" component={ParticipationList}/>
                </Switch>
              </Arwes>
            </ThemeProvider>
        )
    }
}

interface FileListState {
    mediaItems: any[];
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
                    mediaItems: result,
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
            }
        );
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
                this.state.participants.map((record) => (
                    <Row key={record.id}>
                        {erdemCentered(record.firstname + " " + record.lastname)}
                    </Row>
                ))
            ];
        }
        return null;
    }
}


export default Erdem;
