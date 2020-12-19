import React from "react";
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from "arwes";
import {BrowserRouter, Switch, Route, Link, withRouter} from "react-router-dom";
import FileList from "./FileList";

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
                    <Route exact path="/participants/:fileid" component={withRouter(ParticipationList)}/>
                    <Route exact path="/performances/:personid" component={withRouter(PerformanceList)}/>
                  </Switch>
                </Arwes>
              </ThemeProvider>
            </BrowserRouter>
        )
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
                        {erdemCentered((<Link to={`/performances/${record.id}`}>{`${record.firstname} ${record.lastname}`}</Link>))}
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
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/files/" + this.props.match.params.personid)
            .then(res => res.json())
            .then((result) => {
                console.log("CHAD", result);
                this.setState({
                    performances: result,
                    isError: false
                });
            },
            (error) => {
                console.error("request error", error);
                this.setState({
                    performances: [],
                    isError: true
                });
            });
    }

    render() {
        console.log("render", this.state);
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
                this.state.performances.map((record) => (
                    <Row key={record.fileid}>
                        {erdemCentered((<Link to={`/participants/${record.id}`}>{`${record.filename}`}</Link>))}
                    </Row>
                ))
            ];
        }
        return null;
    }
}


export default Erdem;
