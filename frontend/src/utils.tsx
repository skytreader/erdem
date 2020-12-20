import React from "react";
import {Col} from "arwes";

export function erdemCentered(text: any): any {
    return [
        <Col s={12} m={6} offset={["s0", "m3"]}>{text}</Col>
    ];
}

