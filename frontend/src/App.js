import React from 'react';
import {ThemeProvider, createTheme, Arwes} from 'arwes';

// TODO Decide on that verbose call
var sqlite3 = require('sqlite3').verbose();

const App = () => (
    <ThemeProvider theme={createTheme()}>
      <Arwes>
        <div>Erdem</div>
      </Arwes>
    </ThemeProvider>
)

export default App;
