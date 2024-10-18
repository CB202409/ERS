import React, { useState, useEffect, useRef } from "react";
import { GiWolfHowl } from "react-icons/gi";
import { FiCopy } from "react-icons/fi";
import { AiOutlineReload } from "react-icons/ai";
import { v4 as uuidv4 } from 'uuid';
import { marked } from 'marked';

const ChatBot = ({ addMessage, aiResponding, setIsAiResponding, externalMessage }) => {
    const chatLogRef = useRef(null);
    const [userInput, setUserInput] = useState("");
    const [isUserScrolling, setIsUserScrolling] = useState(false);
    const [chatLog, setChatLog] = useState(() => {
        const storedChatLog = JSON.parse(sessionStorage.getItem('chatLog'));
        return storedChatLog || [];
    });

    const [isExpert, setIsExpert] = useState(false);
    const [animationCompleted, setAnimationCompleted] = useState({}); // 애니메이션 완료 상태 관리

    const getSessionId = () => {
        let sessionId = sessionStorage.getItem('session_id');
        if (!sessionId) {
            sessionId = uuidv4();
            sessionStorage.setItem('session_id', sessionId);
        }
        return sessionId;
    };

    const [sessionId, setSessionId] = useState(getSessionId());

    useEffect(() => {
        if (chatLog.length === 0) {
            const welcomeMessage = { 
                sender: "AI", 
                message: "무엇을 도와드릴까요? 정해진 질문이 없으시다면 키워드 질문을 이용하세요."
            };
            setChatLog([welcomeMessage]);
        }
    }, []);

    useEffect(() => {
        sessionStorage.setItem('chatLog', JSON.stringify(chatLog));
    }, [chatLog]);

    useEffect(() => {
        if (externalMessage) {
            handleExternalMessage(externalMessage);
        }
    }, [externalMessage]);

    const handleExternalMessage = async (message) => {
        if (!aiResponding) {
            const messageData = { query: message, session_id: sessionId, is_expert: isExpert };
            setChatLog((prevChatLog) => [...prevChatLog, { sender: "사용자", message }]);
            setIsAiResponding(true);

            try {
                const response = await fetch('http://localhost:8000/v1/chatbot/advice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(messageData),
                });

                const data = await response.json();
                const newMessage = { sender: "AI", message: data.answer };
                setChatLog((prevChatLog) => [...prevChatLog, newMessage]);
            } catch (error) {
                console.error('Error calling the server:', error);
                setChatLog((prevChatLog) => [...prevChatLog, { sender: "AI", message: "서버에 문제가 발생했습니다." }]);
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

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && e.ctrlKey) {
            e.preventDefault();
            setUserInput(userInput + "\n");
        } else if (e.key === "Enter" && !e.ctrlKey) {
            e.preventDefault();
            handleFormSubmit(e);
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

    const handleCopyMessage = (message) => {
        navigator.clipboard.writeText(message)
            .then(() => alert("메시지가 복사되었습니다!"))
            .catch(() => alert("복사에 실패했습니다."));
    };

    const handleNewChat = () => {
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        const welcomeMessage = { 
            sender: "AI", 
            message: "무엇을 도와드릴까요? 정해진 질문이 없으시다면 키워드 질문을 이용하세요" 
        };
        setChatLog([welcomeMessage]); // 채팅 로그 초기화
        setAnimationCompleted({}); // 애니메이션 상태 초기화
        sessionStorage.setItem('session_id', newSessionId);
        sessionStorage.removeItem('chatLog');
    };

    const typeMessage = (element, message, index = 0) => {
        if (index < message.length) {
            const chunk = message.slice(0, index + 1);
            element.innerHTML = marked.parse(chunk);
            setTimeout(() => typeMessage(element, message, index + 1), 10);
        } else {
            setAnimationCompleted((prev) => ({ ...prev, [element.id]: true }));
        }
    };

    useEffect(() => {
        chatLog.forEach((msg, index) => {
            if (msg.sender === "AI" && !animationCompleted[`ai-message-${index}`]) {
                const element = document.getElementById(`ai-message-${index}`);
                if (element) typeMessage(element, msg.message);
            }
        });
    }, [chatLog]);

    const toggleExpertMode = () => {
        setIsExpert(!isExpert);
    };

    return (
        <div id="Chatbot">
            <div id="chat-log" ref={chatLogRef} onScroll={handleScroll}>
                {chatLog.map((msg, index) => (
                    <div key={index} className={msg.sender === "사용자" ? "user-message" : "ai-message"}>
                        {msg.sender === "AI" && (
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <GiWolfHowl size={24} style={{ marginRight: '8px' }} />
                                <div id={`ai-message-${index}`} />
                                <FiCopy
                                    size={16}
                                    style={{ marginLeft: '8px', cursor: 'pointer' }}
                                    onClick={() => handleCopyMessage(msg.message)}
                                    title="메시지 복사"
                                />
                            </div>
                        )}
                        {msg.sender === "사용자" && (
                            <span dangerouslySetInnerHTML={{ __html: marked(msg.query || msg.message) }} />
                        )}
                    </div>
                ))}
                {aiResponding && <div className="spinner"></div>}
            </div>
            <form onSubmit={handleFormSubmit}>
                <AiOutlineReload
                    size={20}
                    onClick={handleNewChat}
                    style={{ cursor: 'pointer', marginRight: '10px' }}
                    title="새 채팅 시작"
                />
                <textarea
                    value={userInput}
                    onKeyDown={handleKeyDown}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="메시지를 입력하세요"
                    disabled={aiResponding}
                />
                <button type="submit" disabled={aiResponding}>전송</button>
            </form>

            <div className="expert-toggle">
                <label>
                    <input
                        type="checkbox"
                        checked={isExpert}
                        onChange={toggleExpertMode}
                    />
                    <span>더 궁금해요 {isExpert ? 'On' : 'Off'}</span>
                </label>
            </div>

            <div className="word">
                <small>AI 기반의 서비스로 예상치 못한 피해가 발생할 수 있으니, 대답을 꼭 확인하세요.</small>
            </div>
        </div>
    );
};

export default ChatBot;
