import React from 'react';
// eslint-disable-next-line
import ReactDOM from 'react-dom';
import {ThemeProvider, createTheme} from 'arwes';

const App = () => (
    <ThemeProvider theme={createTheme()}>
      <div>Erdem</div>
    </ThemeProvider>
)

export default App;
