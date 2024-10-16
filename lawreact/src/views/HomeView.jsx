import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import Header2 from "../components/Header2";
import ChatBot from '../components/ChatBot'; 
import axios from "axios";
import { v4 as uuid4 } from "uuid";

const HomeView = () => {
    const [chatbotMessages, setChatbotMessages] = useState([]);
    const [sessionId, setSessionId] = useState("");
    const [selectedQuestions, setSelectedQuestions] = useState([]); 
    const [filteredQuestions, setFilteredQuestions] = useState([]);  
    const [aiResponding, setIsAiResponding] = useState(false); 
    const [externalMessage, setExternalMessage] = useState(null);

    useEffect(() => {
        setSessionId(uuid4());
    }, []);

    const addMessage = async (msg) => {
        setChatbotMessages(prevMessages => [...prevMessages, { sender: "사용자", message: msg }]);
        setIsAiResponding(true);  

        try {
            const response = await axios.post("http://localhost:8000/v1/chatbot/advice", {
                query: msg,
                session_id: sessionId
            });
            setChatbotMessages(prevMessages => [...prevMessages, { sender: "AI", message: response.data.answer }]);
        } catch (error) {
            setChatbotMessages(prevMessages => [...prevMessages, { sender: "AI", message: "서버에 문제가 발생했습니다." }]);
        } finally {
            setIsAiResponding(false);  
        }
    };

    return (
        <>
            <Header setChatbotQuestions={setSelectedQuestions} /> 
            <Header2 
                setFilteredQuestions={setFilteredQuestions}  
                addMessage={(msg) => setExternalMessage(msg)}  
                isAiResponding={aiResponding} 
            />  
            <ChatBot 
                chatLog={chatbotMessages} 
                addMessage={addMessage} 
                aiResponding={aiResponding} 
                setIsAiResponding={setIsAiResponding}  
                externalMessage={externalMessage}  
            />
        </>
    );
};

export default HomeView;
