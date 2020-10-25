/*
IMPORTANT: Do not change this file's extension to ts(x) so long as Arwes does
not have type definitions available.

For some reason, `npm run build` processes this just fine with a .js extension
(and no Arwes typedefs) but not if you change it to ts(x).
*/
import React from 'react';
import logo from "./img/erdem-logo.png";
import {ThemeProvider, createTheme, Arwes, Row, Col} from 'arwes';

class Erdem extends React.Component {
    
    constructor(props) {
        super(props);
        this.state = {
            mediaItems: []
        };
    }

    componentDidMount() {
        document.title = "Erdem";
        fetch("http://localhost:16981/fetch/files")
            .then(res => res.json())
            .then((result) => {
                console.log(result);
                this.setState({
                    mediaItems: result
                });
            },
            (error) => {
                console.error("Error occurred", error);
        });
    }

    render() {
        console.log("wat");
        const mediaItemsRender = this.state.mediaItems.map((file) => (
            <Row key={file.id}>
                <Col s={0} m={3}></Col>
                <Col s={12} m={6}>{file.name}</Col>
                <Col s={0} m={3}></Col>
            </Row>
        ))
        console.log(mediaItemsRender);
        return (
            <ThemeProvider theme={createTheme()}>
              <Arwes animate show>
                <Row>
                  <Col s={0} m={3}></Col>
                  <Col s={12} m={6}><h1><img src={logo} alt="Erdem Logo" />Erdem</h1></Col>
                  <Col s={0} m={3}></Col>
                </Row>
                {mediaItemsRender}
              </Arwes>
            </ThemeProvider>
        )
    }
}


export default Erdem;
