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
    setSessionId(uuid4()); 
    localStorage.removeItem("chatLog"); 
  }, []);

  const onNavigateToCal = () => {
    localStorage.removeItem("chatLog"); 
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
