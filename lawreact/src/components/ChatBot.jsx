import React, { useState, useEffect, useRef } from "react";
import { TypeAnimation } from 'react-type-animation';
import { GiWolfHowl } from "react-icons/gi"; 
import { FiCopy } from "react-icons/fi"; 

const ChatBot = ({ chatLog, addMessage, aiResponding, setIsAiResponding }) => {
    const [userInput, setUserInput] = useState("");
    const chatLogRef = useRef(null);
    const [isUserScrolling, setIsUserScrolling] = useState(false);
    const [animationEnded, setAnimationEnded] = useState({});

    const handleFormSubmit = (e) => {
        e.preventDefault();
        if (userInput.trim() && !aiResponding) {
            addMessage(userInput); // 사용자 메시지 전송
            setUserInput(""); // 입력창 초기화
            setIsAiResponding(true);  // AI 응답 중으로 설정

            setTimeout(() => {
                setIsAiResponding(false);  // 2초 후 응답 완료 상태로 설정
            }, 2000);
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
            [index]: true  // 해당 메시지의 애니메이션이 끝난 상태로 설정
        }));
    };

    // 메시지 복사
    const handleCopyMessage = (message) => {
        navigator.clipboard.writeText(message).then(() => {
            alert("메시지가 복사되었습니다!"); 
        }).catch(() => {
            alert("복사실패.");
        });
    };

    return (
        <div id="Chatbot">
            <div id="chat-log" ref={chatLogRef} onScroll={handleScroll}>
                {chatLog.map((msg, index) => (
                    <div key={index} className={msg.sender === "사용자" ? "user-message" : "ai-message"}>
                        {msg.sender === "AI" && (
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <GiWolfHowl size={24} style={{ marginRight: '8px' }} /> {/* AI 아이콘 */}
                                {!animationEnded[index] ? (
                                    <TypeAnimation
                                        sequence={[msg.message, 1000]}  // 애니메이션 적용
                                        speed={50}
                                        style={{ fontSize: '1em' }}
                                        repeat={1}
                                        cursor={false}  // 깜빡이는 커서를 비활성화
                                        onFinished={() => handleAnimationEnd(index)}  // 애니메이션 완료 후 호출
                                    />
                                ) : (
                                    <span>{msg.message}</span>  // 애니메이션이 끝나면 정적인 텍스트로 표시
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
                            <span>{msg.message}</span>
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
                    disabled={aiResponding}  // AI 응답 중일 때 비활성화
                />
                <button type="submit" disabled={aiResponding}>전송</button>
            </form>
        </div>
    );
};

export default ChatBot;
