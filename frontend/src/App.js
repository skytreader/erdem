/*
IMPORTANT: Do not change this file's extension to ts(x) so long as Arwes does
not have type definitions available.

For some reason, `npm run build` processes this just fine with a .js extension
(and no Arwes typedefs) but not if you change it to ts(x).
*/
import React from "react";
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from "arwes";
import {Switch, Route, Link} from "react-router-dom";

class Erdem extends React.Component {
    
    constructor(props) {
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
                  <Col s={0} m={3}></Col>
                </Row>
                <Switch>
                  <Route exact path="/" component={FileList}/>
                </Switch>
              </Arwes>
            </ThemeProvider>
        )
    }
}

class FileList extends React.Component {
    
    constructor(props) {
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
                    mediaIteams: [],
                    isError: true
                });
                console.error("Error occurred", error);
        });
    }

    render() {
        const mediaItems = this.state.mediaItems;
        return mediaItems.map((file) => (
            <Row key={file.id}>
                <Col s={0} m={3}></Col>
                <Col s={12} m={6}>{file.filename}</Col>
                <Col s={0} m={3}></Col>
            </Row>
        ));
    }
}


export default Erdem;
