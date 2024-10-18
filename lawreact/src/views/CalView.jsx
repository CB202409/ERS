import React, { useState, useEffect } from "react";
import Header2 from "../components/Header2";
import ChatBot3 from "../components/ChatBot3";
import { v4 as uuid4 } from "uuid";
import { useNavigate } from "react-router-dom"; 

const CalView = () => {
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

  const onNavigateToHome = () => {
    sessionStorage.removeItem("chatLog");  
    navigate("/home"); 
  };

  return (
    <>
      <Header2
        isAiResponding={aiResponding}
        onQuestionSelect={(msg) => setExternalMessage(msg)}
        onNavigateToHome={onNavigateToHome} 
      />
      <ChatBot3
        sessionId={sessionId}
        aiResponding={aiResponding}
        setIsAiResponding={setIsAiResponding}
        externalMessage={externalMessage}
      />
    </>
  );
};

export default CalView;
