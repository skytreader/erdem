import React from "react";
import {Row} from "arwes";
import {Link} from "react-router-dom";
import {erdemCentered} from "./utils";

interface MediaItem {
    filename: string;
    id: number;
}

interface FileListState {
    mediaItems: MediaItem[];
    isError: boolean;
}

class FileList extends React.Component<any, FileListState> {
    constructor(props: any) {
        super(props);
        this.state = {
            mediaItems: [],
            isError: false
        };
    }

    componentDidMount() {
        fetch("http://localhost:16981/fetch/files")
            .then(res => res.json())
            .then((result) => {
                this.setState({
                    mediaItems: result.sort((a: MediaItem, b: MediaItem) => {
                        var normA = a.filename.toUpperCase();
                        var normB = b.filename.toUpperCase();

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
                    mediaItems: [],
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
            return this.state.mediaItems.map((file) => (
                <Row key={file.id}>
                    {erdemCentered((<Link to={`/participants/${file.id}`}>{file.filename}</Link>))}
                </Row>
            ));
        }
    }
}

export default FileList;
