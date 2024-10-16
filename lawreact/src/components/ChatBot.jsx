import React, { useState, useEffect, useRef } from "react";
import { TypeAnimation } from 'react-type-animation';
import { GiWolfHowl } from "react-icons/gi"; 
import { FiCopy } from "react-icons/fi"; 
import { v4 as uuidv4 } from 'uuid';  

const ChatBot = ({ addMessage, aiResponding, setIsAiResponding, externalMessage }) => {
    const chatLogRef = useRef(null);
    const [userInput, setUserInput] = useState("");
    const [isUserScrolling, setIsUserScrolling] = useState(false);
    const [animationEnded, setAnimationEnded] = useState({});
    const [chatLog, setChatLog] = useState(() => {

        // 컴포넌트가 처음 마운트될 때 localStorage에서 chatLog를 불러옴
        const storedChatLog = JSON.parse(localStorage.getItem('chatLog'));
        return storedChatLog || [];  
    });

    // session_id를 localStorage에서 불러오거나 새로 생성
    const getSessionId = () => {
        let sessionId = localStorage.getItem('session_id');
        if (!sessionId) {
            sessionId = uuidv4(); 
            localStorage.setItem('session_id', sessionId);  // localStorage 저장
        }
        return sessionId;
    };

    const sessionId = getSessionId();  // session_id 설정

    // chatLog localStorage 저장
    useEffect(() => {
        localStorage.setItem('chatLog', JSON.stringify(chatLog));
    }, [chatLog]);  // chatLog가 변경될 때마다 실행

    // 외부 메시지 받을 때마다 처리
    useEffect(() => {
        if (externalMessage) {
            handleExternalMessage(externalMessage);
        }
    }, [externalMessage]);

    const handleExternalMessage = async (message) => {
        if (!aiResponding) {
            const messageData = {
                query: message,  // 외부에서 받은 메시지
                session_id: sessionId  // session_id
            };

            setChatLog((prevChatLog) => [...prevChatLog, { sender: "사용자", message }]);

            setIsAiResponding(true);

            try {
                const response = await fetch('http://localhost:5000/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(messageData)
                });

                const data = await response.json();

                setChatLog((prevChatLog) => [...prevChatLog, { sender: "AI", message: data.response }]);

            } catch (error) {
                setChatLog((prevChatLog) => [...prevChatLog, { sender: "AI", message: "서버에 문제가 발생했습니다." }]);
                console.error('Error calling the server:', error);
            }

            setIsAiResponding(false);
        }
    };

    const handleFormSubmit = async (e) => {
        e.preventDefault();
        if (userInput.trim() && !aiResponding) {
            await handleExternalMessage(userInput);
            setUserInput("");  
        }
    };

    const handleScroll = () => {
        if (chatLogRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = chatLogRef.current;
            setIsUserScrolling(scrollTop + clientHeight < scrollHeight - 10);
        }
    };

    useEffect(() => {
        if (chatLogRef.current && !isUserScrolling) {
            chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
        }
    }, [chatLog, isUserScrolling]);

    const handleAnimationEnd = (index) => {
        setAnimationEnded(prev => ({
            ...prev,
            [index]: true 
        }));
    };

    const handleCopyMessage = (message) => {
        navigator.clipboard.writeText(message).then(() => {
            alert("메시지가 복사되었습니다!"); 
        }).catch(() => {
            alert("복사에 실패했습니다.");
        });
    };

    return (
        <div id="Chatbot">
            <div id="chat-log" ref={chatLogRef} onScroll={handleScroll}>
                {chatLog.map((msg, index) => (
                    <div key={index} className={msg.sender === "사용자" ? "user-message" : "ai-message"}>
                        {msg.sender === "AI" && (
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <GiWolfHowl size={24} style={{ marginRight: '8px' }} /> 
                                {!animationEnded[index] ? (
                                    <TypeAnimation
                                        sequence={[msg.message, 1000]}
                                        speed={50}
                                        style={{ fontSize: '1em' }}
                                        repeat={1}
                                        cursor={false}
                                        onFinished={() => handleAnimationEnd(index)}
                                    />
                                ) : (
                                    <span>{msg.message}</span>
                                )}
                                <FiCopy 
                                    size={16} 
                                    style={{ marginLeft: '8px', cursor: 'pointer' }} 
                                    onClick={() => handleCopyMessage(msg.message)} 
                                    title="메시지 복사" 
                                />
                            </div>
                        )}
                        {msg.sender === "사용자" && (
                            <span>{msg.query || msg.message}</span>
                        )}
                    </div>
                ))}
                {aiResponding && (
                    <div className="spinner"></div>
                )}
            </div>
            <form onSubmit={handleFormSubmit}>
                <textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="메시지를 입력하세요"
                    disabled={aiResponding}
                />
                <button type="submit" disabled={aiResponding}>전송</button>
            </form>
        </div>
    );
};

export default ChatBot;
