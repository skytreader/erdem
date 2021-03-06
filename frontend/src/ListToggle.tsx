import React from "react";
import {Button, Row, Col} from "arwes";
import FileList from "./FileList";
import PerformerList from "./PerformerList";

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
        const page = [
            (
                <Row>
                    <Col s={6} m={3} offset={["s0", "m3"]}>
                        <Button className="fullwidth" onClick={() => this.toggle("performers")}>
                            <span className={this.state.isPerformerList ? "selected" : ""}>Performers</span>
                        </Button>
                    </Col>
                    <Col s={6} m={3}>
                        <Button className="fullwidth" onClick={() => this.toggle("files")}>
                            <span className={this.state.isPerformerList ? "" : "selected"}>Files</span>
                        </Button>
                    </Col>
                </Row>
            ),
        ]
        if (this.state.isPerformerList) {
            page.push((<PerformerList/>));
        } else {
            page.push((<FileList/>));
        }
        return page;
    }
}

export default ListToggle;
