import React from "react";
import {Row} from "arwes";
import {Link} from "react-router-dom";
import {erdemCentered, makeName, PerformerItem} from "./utils";

interface ParticipationListState {
    participants: any[];
    filename: string;
    fullpath: string;
    isError: boolean;
}

class ParticipationList extends React.Component<any, ParticipationListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            participants: [],
            isError: false,
            filename: "",
            fullpath: ""
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/fileparticipants/" + this.props.match.params.fileid)
            .then(res => res.json())
            .then((result) => {
                console.log(result);
                this.setState({
                    participants: result.participants,
                    isError: false,
                    filename: result.filename,
                    fullpath: result.fullpath
                });
            },
            (error) => {
                this.setState({
                    isError: true,
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
                        {erdemCentered((<h2>Participants in &quot;{this.state.participants[0].filename}&quot;</h2>))}
                    </Row>
                ),
                (
                    <Row>
                        {erdemCentered((<p>Found in {this.state.fullpath}</p>))}
                    </Row>
                ),
                this.state.participants.map((record: PerformerItem) => (
                    <Row key={record.id}>
                        {erdemCentered((<Link to={`/performances/${record.id}`}>{makeName(record)}</Link>))}
                    </Row>
                ))
            ];
        } else {
            return [
                    <Row>
                        {erdemCentered((<h2>No participants found in &quot;{this.state.filename}&quot;</h2>))}
                    </Row>,
                    <Row>
                        {erdemCentered((<p>Found in {this.state.fullpath}</p>))}
                    </Row>
            ];
        }
    }
}

export default ParticipationList;
