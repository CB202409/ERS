import React, { useState, useEffect } from "react";
import Header from "../components/Header";
import Header2 from "../components/Header2";
import ChatBot3 from '../components/ChatBot3'; 
import axios from "axios";
import { v4 as uuid4 } from "uuid";

const Cal = () => {
    const [chatbotMessages, setChatbotMessages] = useState([]);
    const [sessionId, setSessionId] = useState("");
    const [selectedQuestions, setSelectedQuestions] = useState([]); 
    const [filteredQuestions, setFilteredQuestions] = useState([]); // 필터링된 질문 리스트
    const [aiResponding, setIsAiResponding] = useState(false);  // AI 응답 중인지 여부를 상태로 관리

    useEffect(() => {
        setSessionId(uuid4());
    }, []);

    const addMessage = async (msg) => {
        setChatbotMessages(prevMessages => [...prevMessages, { sender: "사용자", message: msg }]);
        setIsAiResponding(true);  // AI 응답 중으로 설정

        try {
            const response = await axios.post("http://localhost:8000/query", {
                query: msg,
                session_id: sessionId
            });
            setChatbotMessages(prevMessages => [...prevMessages, { sender: "AI", message: response.data.answer }]);
        } catch (error) {
            setChatbotMessages(prevMessages => [...prevMessages, { sender: "AI", message: "서버에 문제가 발생했습니다." }]);
        } finally {
            setIsAiResponding(false);  // 응답 후 상태를 변경
        }
    };

    return (
        <>
            <Header setChatbotQuestions={setSelectedQuestions} /> 
            <Header2 
                setFilteredQuestions={setFilteredQuestions} 
                addMessage={addMessage} 
                isAiResponding={aiResponding}  // AI 응답 중 여부를 전달
            />  
            <ChatBot3 
                chatLog={chatbotMessages} 
                addMessage={addMessage} 
                aiResponding={aiResponding} 
                setIsAiResponding={setIsAiResponding}  // 응답 상태 변경 함수 전달
            />
        </>
    );
};

export default Cal;
