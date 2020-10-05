import React from 'react';
import {ThemeProvider, createTheme, Arwes} from 'arwes';
import sqlite3 from 'sqlite3';

const db = new sqlite3.Database(":memory:");

const App = () => (
    <ThemeProvider theme={createTheme()}>
      <Arwes>
        <div>Erdem</div>
      </Arwes>
    </ThemeProvider>
)

export default App;
