import React, { useState } from "react";
import axios from "axios";

const Chatbot = () => {
  const [userInput, setUserInput] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const [typingMessage, setTypingMessage] = useState(""); 
  const [isTyping, setIsTyping] = useState(false); 

  const sendMessage = async (e) => {
    e.preventDefault();

    if (!userInput.trim()) return;

    // 사용자 입력 추가
    addMessageToChatLog("사용자", userInput);

    try {
      const response = await axios.get("http://localhost:8000/", {
        params: {
          query: userInput,
          session_id: "default", // 세션별 id 분리해야 함
        }
      });

      startTyping(response.data.result);
      // addMessageToChatLog("AI", response.data.result); // 내 api 형태에 맞춰 수정함
    } catch (error) {
      addMessageToChatLog("에러", "서버에 문제가 발생했습니다.");
      console.error("Error:", error);
    }

    setUserInput("");
  };

  const addMessageToChatLog = (sender, message) => {
    setChatLog((prev) => [...prev, { sender, message }]);
  };

  const startTyping = (message) => {
    setIsTyping(true);
    setTypingMessage(""); 

    
    if (message.length > 0) {
      setTypingMessage(message.charAt(0));
    }

    let index = 0; 
    const typingSpeed = 50; 

    const typingInterval = setInterval(() => {
      if (index < message.length) {
        setTypingMessage((prev) => prev + message.charAt(index));
        index++;
      } else {
        clearInterval(typingInterval);
        addMessageToChatLog("AI", message);
        setIsTyping(false); 
      }
    }, typingSpeed);
  };

  return (
    <div id="Chatbot">
      <h1>ChatBot</h1>
      <div id="chat-log">
        {chatLog.map((msg, index) => (
          <div key={index} className={msg.sender === "사용자" ? "user-message" : "ai-message"}>
            <strong>{msg.sender}: </strong>
            {msg.message}
          </div>
        ))}
        {isTyping && (
          <div className="ai-message">
            <strong>AI: </strong>
            {typingMessage}
          </div>
        )}
      </div>
      <form onSubmit={sendMessage}>
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="메시지를 입력하세요"
        />
        <button type="submit">전송</button>
      </form>
    </div>
  );
};

export default Chatbot;
