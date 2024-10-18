import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import ChatBot from "../components/ChatBot";
import { v4 as uuid4 } from "uuid";
import { useNavigate } from "react-router-dom"; 

const HomeView = () => {
  const [sessionId, setSessionId] = useState("");
  const [aiResponding, setIsAiResponding] = useState(false);
  const [externalMessage, setExternalMessage] = useState(null);
  const navigate = useNavigate(); 

  useEffect(() => {
    const newSessionId = uuid4();
    setSessionId(newSessionId); 
    sessionStorage.setItem('session_id', newSessionId);  
    sessionStorage.removeItem("chatLog");  
  }, []);

  const onNavigateToCal = () => {
    sessionStorage.removeItem("chatLog"); 
    navigate("/cal"); 
  };

  return (
    <>
      <Header
        isAiResponding={aiResponding}
        onQuestionSelect={(msg) => setExternalMessage(msg)}
        onNavigateToCal={onNavigateToCal} 
      />
      <ChatBot
        sessionId={sessionId}
        aiResponding={aiResponding}
        setIsAiResponding={setIsAiResponding}
        externalMessage={externalMessage}
      />
    </>
  );
};

export default HomeView;
