import React, { useState, useEffect, useRef } from "react";
import { TypeAnimation } from 'react-type-animation';
import { GiWolfHowl } from "react-icons/gi"; 
import { FiCopy } from "react-icons/fi"; 
import { AiOutlineReload } from "react-icons/ai";  
import { v4 as uuidv4 } from 'uuid';  
import { marked } from 'marked';  

const ChatBot = ({ addMessage, aiResponding, setIsAiResponding, externalMessage }) => {
    const chatLogRef = useRef(null);
    const [userInput, setUserInput] = useState("");
    const [isUserScrolling, setIsUserScrolling] = useState(false);
    const [animationEnded, setAnimationEnded] = useState({});
    const [chatLog, setChatLog] = useState(() => {
        const storedChatLog = JSON.parse(localStorage.getItem('chatLog'));
        return storedChatLog || [];  
    });

    const [isExpert , setIsExpert] = useState(false); //false 기본값 

    const getSessionId = () => {
        let sessionId = localStorage.getItem('session_id');
        if (!sessionId) {
            sessionId = uuidv4(); 
            localStorage.setItem('session_id', sessionId);  // localStorage 저장
        }
        return sessionId;
    };

    const [sessionId, setSessionId] = useState(getSessionId());  // session_id 설정

    useEffect(() => {
        if (chatLog.length === 0) {
            const welcomeMessage = {
                sender: "AI",
                message: "무엇을 도와드릴까요? 정해진 질문이 없으시다면 키워드 질문을 이용하세요"
            };
            setChatLog([welcomeMessage]);
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('chatLog', JSON.stringify(chatLog));
    }, [chatLog]);

    useEffect(() => {
        if (externalMessage) {
            handleExternalMessage(externalMessage);
        }
    }, [externalMessage]);

    const handleExternalMessage = async (message) => {
        if (!aiResponding) {
            const messageData = {
                query: message,
                session_id: sessionId,
                is_expert: isExpert
            };

            setChatLog((prevChatLog) => [...prevChatLog, { sender: "사용자", message }]);

            setIsAiResponding(true);

            try {
                const response = await fetch('http://localhost:8000/v1/chatbot/advice' /* 실제 API로 변경 */, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(messageData)
                });

                const data = await response.json();

                setChatLog((prevChatLog) => [...prevChatLog, { sender: "AI", message: data.answer }]);

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

    const handleNewChat = () => {
        const newSessionId = uuidv4();
        setSessionId(newSessionId);  
        const welcomeMessage = {
            sender: "AI",
            message: "무엇을 도와드릴까요? 정해진 질문이 없으시다면 키워드 질문을 이용하세요"
        };
        setChatLog([welcomeMessage]); 
        localStorage.setItem('session_id', newSessionId);  
        localStorage.removeItem('chatLog');  
    };

    const getMarkdownContent = (message) => {
        return { __html: marked(message) };  // Markdown을 HTML로 변환
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && e.ctrlKey) {
            e.preventDefault();  // 기본 Enter 동작 방지
            handleFormSubmit(e);  // 메시지 전송
        } else if (e.key === "Enter" && !e.ctrlKey) {
            e.preventDefault();  // 기본 Enter 동작 방지
            setUserInput(userInput + "\n");  // 줄바꿈 추가
        }
    };

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
                                {!animationEnded[index] ? (
                                    <TypeAnimation
                                        sequence={[msg.message, 1000]}
                                        speed={70} // 타이핑 속도
                                        style={{ fontSize: '1em' }}
                                        repeat={1}
                                        cursor={false}
                                        onFinished={() => handleAnimationEnd(index)}
                                    />
                                ) : (
                                    <span dangerouslySetInnerHTML={getMarkdownContent(msg.message)} />
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
                            <span dangerouslySetInnerHTML={getMarkdownContent(msg.query || msg.message)} />
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

            <div className ="expert-toggle">
                <label>
                    <input
                        type="checkbox"
                        checked={isExpert}
                        onChange={toggleExpertMode}
                    />
                    <span>더 궁금해요{isExpert ? 'On' : 'OFF'}</span>
                </label>
            </div>

            <div className="word">
                <small>AI 기반의 서비스로 이용 시 예상하지 못한 피해가 발생할 수 있으니, 대답을 한 번 더 확인하세요.</small>
            </div>
        </div>
    );
};

export default ChatBot;
                <small>법적 책임 안 짐</small>
