import * as React from "react";
import {Button, Row} from "arwes";
import {Link} from "react-router-dom";
import {erdemCentered, makeName, PerformerItem} from "./utils";

interface ParticipationListState {
    fileid: string;
    participants?: any[];
    filename: string;
    fullpath: string;
    isError: boolean;
    review: string;
}

class ParticipationList extends React.Component<any, ParticipationListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            participants: [],
            isError: false,
            filename: "",
            fullpath: "",
            review: "",
            fileid: "0",
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/file/" + this.props.match.params.fileid)
            .then(res => res.json())
            .then((result) => {
                console.log(result);
                this.setState({
                    participants: result.participants,
                    isError: false,
                    filename: result.filename,
                    fullpath: result.fullpath,
                    review: result.review,
                    fileid: this.props.match.params.fileid
                });
            },
            (error) => {
                this.setState({
                    isError: true,
                });
                console.error("Error occurred", error);
            });
    }

    saveReview() {
        fetch(`http://localhost:16981/file/${this.state.fileid}`,
            {
                method: "POST",
                body: JSON.stringify({review: this.state.review}),
                headers: {
                    "content-type": "application/json"
                },
            }
        ).then((event) => {
            console.log("comment saved");
        });
    }

    render() {
        if (this.state.isError) {
            // TODO Style better.
            return (
                <div>Error connecting to server.</div>
            )
        } else if (this.state.participants && this.state.participants.length > 0) {
            return [
                (
                    <Row>
                        {erdemCentered((<h2>{this.state.filename}</h2>))}
                    </Row>
                ),
                (
                    <Row>
                        {erdemCentered((
                            <div>
                                <h3>Review</h3>
                                <textarea rows={15} cols={75} value={this.state.review} onChange={(event) => this.setState({review: event.target.value})}></textarea>
                                <Button onClick={() => this.saveReview()}>Save Review</Button>
                            </div>
                        ))}
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
