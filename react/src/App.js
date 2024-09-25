import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import HomeView from "./views/HomeView";

const App = () => {
    return (
        <BrowserRouter>
            <Routes> 
                <Route path="/" element={<HomeView />} />
            </Routes>
        </BrowserRouter>
    );
};

export default App;
