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
    // TS/JS is dumb. You can't put this in the constructor. Because apparently
    // some of these methods might be called before the object is constructed/initialized.
    private searchQuery: React.RefObject<HTMLInputElement> = React.createRef<HTMLInputElement>();
    
    constructor(props: any) {
        super(props);
        this.state = {
        };

        this.handleQueryTyped = this.handleQueryTyped.bind(this);
    }

    componentDidMount() {
        document.title = "Erdem";
    }

    handleQueryTyped(event: any) {
        this.setState({searchQuery: event.target.value});
    }

    decideSQVal(): string {
        // Okay TS is dumb, unlike MyPy. That's why you need all this bloody
        // bullshit type checks _and_ not null assertions! WTF!
        const tsDumber = this.searchQuery;
        if (tsDumber != null){
            return tsDumber!.current!.value;
        } else {
            return "";
        }
    }

    render() {
        return (
            <BrowserRouter forceRefresh={true}>
              <ThemeProvider theme={createTheme()}>
                <Arwes animate show>
                  <Row>
                    <Col s={0} m={3}></Col>
                    <Col s={12} m={6} className="App-header"><h1><a href="/" className="logo"><img src={logo} alt="Erdem Logo" />Erdem</a></h1></Col>
                  </Row>
                  <Row>
                    <Col s={0} m={3}></Col>
                    <Col s={6} m={5}>
                      <input className="fullwidth" type="text" placeholder="Query" value={this.state.searchQuery} ref={this.searchQuery}/>
                    </Col>
                    <Col s={0} m={1}>
                      <Button className="fullwidth" onClick={() => {erdemHistory.push("/search/" + this.decideSQVal()) }}>
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
