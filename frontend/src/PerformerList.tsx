import React from "react";
import {Button, Col, Row} from "arwes";
import {Link} from "react-router-dom";
import {makeName, PerformerItem} from "./utils";

interface PerformerListState {
    performers: PerformerItem[];
    isError: boolean;
}

class PerformerList extends React.Component<any, PerformerListState> {
    
    constructor(props: any) {
        super(props);
        this.state = {
            performers: [],
            isError: false
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/persons/active")
            .then(res => res.json())
            .then((result) => {
                this.setState({
                    performers: result.sort((a: PerformerItem, b: PerformerItem) => {
                        var normA = makeName(a).toUpperCase();
                        var normB = makeName(b).toUpperCase();

                        if (normA < normB) {
                            return -1;
                        } else if (normA > normB) {
                            return 1;
                        } else {
                            return 0;
                        }
                    }),
                    isError: false
                });
            },
            (error) => {
                this.setState({
                    performers: [],
                    isError: true
                });
                console.error("Error occurred", error);
            });
    }

    deactivatePerson(personId: number) {
        fetch(`http://localhost:16981/person/${personId}/is_deactivated/1`,
            {method: "PATCH"})
        .then((event) => {
            console.log("removed person", personId);
            this.setState({
                performers: this.state.performers.filter((p) => p.id !== personId)
            });
            // TODO Find out how to make render work.
            // ReactDOM.render(
            //     <Arwes><Appear animate>Removal successful</Appear></Arwes>,
            //     document.getElementById("root")
            // );
        });
    }

    render() {
        if (this.state.isError) {
            // TODO Style better.
            return (
                <div>Error fetching files. Check server.</div>
            )
        } else {
            return this.state.performers.map((performer) => (
                <Row key={performer.id}>
                    <Col s={5} offset={["s3"]}>
                        <Link to={`/performances/${performer.id}`}>{makeName(performer)}</Link>
                    </Col>
                    <Col s={1}>
                        <Button className="fullwidth" onClick={() => this.deactivatePerson(performer.id)}>Delete</Button>
                    </Col>
                </Row>
            ));
        }
    }
}

export default PerformerList;
