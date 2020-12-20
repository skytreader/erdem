import React from "react";
import {Col} from "arwes";

export function erdemCentered(text: any): any {
    return [
        <Col s={12} m={6} offset={["s0", "m3"]}>{text}</Col>
    ];
}

export interface PerformerItem {
    id: number;
    firstname: string;
    lastname: string;
}

export function makeName(record: PerformerItem): string {
    if (record.lastname != null) {
        return record.firstname + " " + record.lastname;
    } else {
        return record.firstname;
    }
}
