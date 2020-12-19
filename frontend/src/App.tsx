import React from "react";
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from "arwes";
import {BrowserRouter, Switch, Route, withRouter} from "react-router-dom";
import ListToggle from "./ListToggle";
import ParticipationList from "./ParticipationList";
import PerformanceList from "./PerformanceList";

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
                    <Col s={12} m={6} className="App-header"><h1><a href="/" className="logo"><img src={logo} alt="Erdem Logo" />Erdem</a></h1></Col>
                  </Row>
                  <Switch>
                    <Route exact path="/" component={ListToggle}/>
                    <Route exact path="/participants/:fileid" component={withRouter(ParticipationList)}/>
                    <Route exact path="/performances/:personid" component={withRouter(PerformanceList)}/>
                  </Switch>
                </Arwes>
              </ThemeProvider>
            </BrowserRouter>
        )
    }
}

export default Erdem;
