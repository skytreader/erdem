/*
IMPORTANT: Do not change this file's extension to ts(x) so long as Arwes does
not have type definitions available.

For some reason, `npm run build` processes this just fine with a .js extension
(and no Arwes typedefs) but not if you change it to ts(x).
*/
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
