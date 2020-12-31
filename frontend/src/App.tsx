import React from "react";
import erdemHistory from "./erdemHistory";
import logo from "./img/erdem-logo.png";
import {Button, ThemeProvider, createTheme, Arwes, Row, Col} from "arwes";
import {BrowserRouter, Switch, Route, withRouter} from "react-router-dom";
import ListToggle from "./ListToggle";
import ParticipationList from "./ParticipationList";
import PerformanceList from "./PerformanceList";
import {SearchResults} from "./FileList";

class Erdem extends React.Component<any, any> {
    
    constructor(props: any) {
        super(props);
        this.state = {
            searchQuery: ""
        };
    }

    componentDidMount() {
        document.title = "Erdem";
    }

    handleQueryTyped(event: any) {
        this.setState({searchQuery: event.target.value});
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
                  <Row>
                    <Col s={0} m={3}></Col>
                    <Col s={6} m={5}>
                      <input className="fullwidth" type="text" placeholder="Query" value={this.state.searchQuery} onChange={this.handleQueryTyped}/>
                    </Col>
                    <Col s={0} m={1}>
                      <Button className="fullwidth" onClick={() => {erdemHistory.push("/search/" + this.state.searchQuery)}}>
                      Search
                      </Button>
                    </Col>
                  </Row>
                  <Switch>
                    <Route exact path="/" component={ListToggle}/>
                    <Route exact path="/participants/:fileid" component={withRouter(ParticipationList)}/>
                    <Route exact path="/performances/:personid" component={withRouter(PerformanceList)}/>
                    <Route exact path="/search/:query" component={withRouter(SearchResults)}/>
                  </Switch>
                </Arwes>
              </ThemeProvider>
            </BrowserRouter>
        )
    }
}

export default Erdem;
