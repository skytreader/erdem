/*
IMPORTANT: Do not change this file's extension to ts(x) so long as Arwes does
not have type definitions available.

For some reason, `npm run build` processes this just fine with a .js extension
(and no Arwes typedefs) but not if you change it to ts(x).
*/
import React, {useState} from 'react';
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from 'arwes';

class Erdem extends React.Component {
    
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
              </Arwes>
            </ThemeProvider>
        )
    }
}


export default Erdem;
