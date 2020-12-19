import React from "react";
import {Row} from "arwes";
import {Link} from "react-router-dom";
import {erdemCentered} from "./utils";

interface PerformanceListState {
    performances: any[];
    isError: boolean;
}

class PerformanceList extends React.Component<any, PerformanceListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            performances: [],
            isError: false
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/files/" + this.props.match.params.personid)
            .then(res => res.json())
            .then((result) => {
                console.log("CHAD", result);
                this.setState({
                    performances: result,
                    isError: false
                });
            },
            (error) => {
                console.error("request error", error);
                this.setState({
                    performances: [],
                    isError: true
                });
            });
    }

    render() {
        console.log("render", this.state);
        if (this.state.isError) {
            return (
                <div>Error connecting to server.</div>
            )
        } else if (this.state.performances.length > 0) {
            const sample = this.state.performances[0];
            const name = sample.firstname + " " + sample.lastname;
//{erdemCentered((<Link to={`/performances/${record.fileid}`}>record.filename</Link>))}
            return [
                (
                    <Row>
                        {erdemCentered("Performances of " + name)}
                    </Row>
                ),
                this.state.performances.map((record) => (
                    <Row key={record.fileid}>
                        {erdemCentered((<Link to={`/participants/${record.id}`}>{`${record.filename}`}</Link>))}
                    </Row>
                ))
            ];
        }
        return null;
    }
}

export default PerformanceList;
