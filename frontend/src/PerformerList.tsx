import React from "react";
import {Row} from "arwes";
import {Link} from "react-router-dom";
import {erdemCentered} from "./utils";

interface PerformerItem {
    id: number;
    firstname: string;
    lastname: string;
}

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
        fetch("http://localhost:16981/fetch/persons")
            .then(res => res.json())
            .then((result) => {
                // TODO SORT!
                this.setState({
                    performers: result,
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

    render() {
        if (this.state.isError) {
            // TODO Style better.
            return (
                <div>Error fetching files. Check server.</div>
            )
        } else {
            return this.state.performers.map((performer) => (
                <Row key={performer.id}>
                    {erdemCentered((<Link to={`/participants/${performer.id}`}>{this.makeName(performer)}</Link>))}
                </Row>
            ));
        }
    }

    private makeName(record: PerformerItem) {
        return record.firstname + " " + record.lastname;
    }
}

export default PerformerList;
