// import React, { useState, useEffect, useRef } from "react";
// import { TypeAnimation } from 'react-type-animation';
// import { GiWolfHowl } from "react-icons/gi"; // 아이콘 import

// const ChatBot2 = ({ chatLog, addMessage, aiResponding, setIsAiResponding }) => {
//     const [userInput, setUserInput] = useState("");
//     const chatLogRef = useRef(null);
//     const [isUserScrolling, setIsUserScrolling] = useState(false);
//     const [animationEnded, setAnimationEnded] = useState({});

//     const handleFormSubmit = (e) => {
//         e.preventDefault();
//         if (userInput.trim() && !aiResponding) {
//             addMessage(userInput); // 사용자 메시지 전송
//             setUserInput(""); // 입력창 초기화
//             setIsAiResponding(true);  // AI 응답 중으로 설정

//             setTimeout(() => {
//                 setIsAiResponding(false);  // 2초 후 응답 완료 상태로 설정
//             }, 2000);
//         }
//     };

//     const handleScroll = () => {
//         if (chatLogRef.current) {
//             const { scrollTop, scrollHeight, clientHeight } = chatLogRef.current;
//             setIsUserScrolling(scrollTop + clientHeight < scrollHeight - 10);
//         }
//     };

//     useEffect(() => {
//         if (chatLogRef.current && !isUserScrolling) {
//             chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
//         }
//     }, [chatLog, isUserScrolling]);

//     // 애니메이션이 끝나면 상태 업데이트
//     const handleAnimationEnd = (index) => {
//         setAnimationEnded(prev => ({
//             ...prev,
//             [index]: true  // 해당 메시지의 애니메이션이 끝난 상태로 설정
//         }));
//     };

//     return (
//         <div id="Chatbot">
//             <div id="chat-log" ref={chatLogRef} onScroll={handleScroll}>
//                 {chatLog.map((msg, index) => (
//                     <div key={index} className={msg.sender === "사용자" ? "user-message" : "ai-message"}>
//                         {msg.sender === "AI" && (
//                             <div style={{ display: 'flex', alignItems: 'center' }}>
//                                 <GiWolfHowl size={24} style={{ marginRight: '8px' }} /> {/* AI 아이콘 */}
//                                 {!animationEnded[index] ? (
//                                     <TypeAnimation
//                                         sequence={[msg.message, 1000]}  // 애니메이션 적용
//                                         speed={50}
//                                         style={{ fontSize: '1em' }}
//                                         repeat={1}
//                                         cursor={false}  // 깜빡이는 커서를 비활성화
//                                         onFinished={() => handleAnimationEnd(index)}  // 애니메이션 완료 후 호출
//                                     />
//                                 ) : (
//                                     <span>{msg.message}</span>  // 애니메이션이 끝나면 정적인 텍스트로 표시
//                                 )}
//                             </div>
//                         )}
//                         {/* 사용자 메시지는 그대로 */}
//                         {msg.sender === "사용자" && (
//                             <span>{msg.message}</span>
//                         )}
//                     </div>
//                 ))}
//                 {aiResponding && (
//                     <div className="spinner"></div>
//                 )}
//             </div>
//             <form onSubmit={handleFormSubmit}>
//                 <textarea
//                     value={userInput}
//                     onChange={(e) => setUserInput(e.target.value)}
//                     placeholder="메시지를 입력하세요"
//                     disabled={aiResponding}  // AI 응답 중일 때 비활성화
//                 />
//                 <button type="submit" disabled={aiResponding}>전송</button>
//             </form>
//         </div>
//     );
// };

// export default ChatBot2;
