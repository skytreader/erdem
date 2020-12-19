import React from "react";
import {Row, Col} from "arwes";
import FileList from "./FileList";

interface ListToggleState {
    isPerformerList: boolean;
}

class ListToggle extends React.Component<any, ListToggleState> {

    constructor(props: any) {
        super(props);
        this.state = {
            isPerformerList: true
        };
    }

    render() {
        return (
            <Row>
                <Col s={0} m={3}></Col>
                <Col s={6} m={4}>Files</Col>
                <Col s={6} m={4}>Performers</Col>
                <FileList/>
            </Row>
        )
    }
}

export default ListToggle;
