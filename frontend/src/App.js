import React from 'react';
import {ThemeProvider, createTheme, Arwes} from 'arwes';

const App = () => (
    <ThemeProvider theme={createTheme()}>
      <Arwes>
        <div>Erdem</div>
      </Arwes>
    </ThemeProvider>
)

export default App;
