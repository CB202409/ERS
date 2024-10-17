import React, { useState, useEffect } from 'react'; 
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'; 
import HomeView from './views/HomeView';
import CalView from './views/CalView';
import LogoScreen from './components/LogoScreen';

const App = () => {
  const [showLogoScreen, setShowLogoScreen] = useState(true);

  useEffect(() => {
    const buildTimestamp = Date.now();
    const lastVisitTime = localStorage.getItem('lastVisitTime');

    if (!lastVisitTime || parseInt(lastVisitTime) < buildTimestamp) {
      const timer = setTimeout(() => {
        setShowLogoScreen(false);
        localStorage.setItem('lastVisitTime', Date.now().toString());
      }, 1500);
      return () => clearTimeout(timer);
    } else {
      setShowLogoScreen(false);
    }
  }, []);

  return (
    <Router>
      {showLogoScreen ? (
        <LogoScreen />
      ) : (
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<HomeView />} />
          <Route path="/cal" element={<CalView />} />
          <Route path="*" element={<Navigate to="/home" replace />} />
        </Routes>
      )}
    </Router>
  );
};

export default App;
