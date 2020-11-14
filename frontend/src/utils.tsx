import React from "react";
import {Col} from "arwes";

export function erdemCentered(text: string): any {
    return [
        <Col s={0} m={3}></Col>,
        <Col s={12} m={6}>{text}</Col>
    ];
}

