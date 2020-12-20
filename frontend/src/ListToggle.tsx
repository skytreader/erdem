import React from "react";
import {Button, Row, Col} from "arwes";
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

    toggle(s: string) {
        this.setState({isPerformerList: s === "performers"});
    }

    render() {
        return (
            <Row>
                <Col s={6} m={3} className="tab" offset={["s0", "m3"]}><Button>Files</Button></Col>
                <Col s={6} m={3} className="tab"><Button>Performers</Button></Col>
                <FileList/>
            </Row>
        )
    }
}

export default ListToggle;
