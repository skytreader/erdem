import React from "react";
import {Row, Col} from "arwes";
import {Link} from "react-router-dom";
import {erdemCentered, makeName, PerformerItem} from "./utils";

interface ParticipationListState {
    participants: any[];
    isError: boolean;
}

class ParticipationList extends React.Component<any, ParticipationListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            participants: [],
            isError: false
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/fileparticipants/" + this.props.match.params.fileid)
            .then(res => res.json())
            .then((result) => {
                this.setState({
                    participants: result,
                    isError: false
                });
            },
            (error) => {
                this.setState({
                    participants: [],
                    isError: true
                });
                console.error("Error occurred", error);
            });
    }

    render() {
        if (this.state.isError) {
            // TODO Style better.
            return (
                <div>Error connecting to server.</div>
            )
        } else if (this.state.participants.length > 0) {
            return [
                (
                    <Row>
                        <Col s={0} m={3}></Col>
                        <Col s={12} m={6}>
                            Participants in <strong>{this.state.participants[0].filename}</strong>
                        </Col>
                    </Row>
                ),
                this.state.participants.map((record: PerformerItem) => (
                    <Row key={record.id}>
                        {erdemCentered((<Link to={`/performances/${record.id}`}>{makeName(record)}</Link>))}
                    </Row>
                ))
            ];
        }
        return null;
    }
}

export default ParticipationList;
