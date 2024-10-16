import { BrowserRouter, Routes, Route } from "react-router-dom";
import React, { useState, useEffect } from 'react';
import ChooseSection from "./views/ChooseSection";
import HomeView from "./views/HomeView";
//import HomeView2 from "./views/HomeView2";
import CalView from "./views/CalView";
import LogoScreen from "./components/LogoScreen";

const App = () => {
  const [showLogoScreen, setShowLogoScreen] = useState(true);
  const [selectedOption, setSelectedOption] = useState(null);

  useEffect(() => {
    const buildTimestamp = Date.now(); // 현재 시간을 사용하여 서버 시작 시점을 기록
    const lastVisitTime = localStorage.getItem('lastVisitTime'); // 마지막 방문 시간을 가져옴

    if (!lastVisitTime || parseInt(lastVisitTime) < buildTimestamp) {
      const timer = setTimeout(() => {
        setShowLogoScreen(false);
        localStorage.setItem('lastVisitTime', Date.now().toString());
      }, 1500); // 1.5초 동안 로고 화면 표시
      return () => clearTimeout(timer);
    } else {
      setShowLogoScreen(false);
    }
  }, []);

  return (
    <BrowserRouter>
      {showLogoScreen ? (
        <LogoScreen />
      ) : (
        <Routes>
          <Route
            path="/"
            element={<ChooseSection setSelectedOption={setSelectedOption} />}
          />
          <Route
            path="/home"
            element={<HomeView selectedOption={selectedOption} />}
          />
          {/* <Route
            path="/home2"
            element={<HomeView2 selectedOption={selectedOption} />}
          /> */}
          <Route
            path="/cal"
            element={<CalView selectedOption={selectedOption} />}
          />
        </Routes>
      )}
    </BrowserRouter>
  );
};

export default App;
