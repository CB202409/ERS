import React, { useState } from "react";
import Header from "../components/Header";
import Cal from "../components/Cal";
import Intro from "../components/Intro";
import Footer from "../components/Footer";
import Main from "../components/Main";
import Law from "../components/Law";
import Chatbot from "../components/ChatBot";

const HomeView = () => {
    const [showCal, setShowCal] = useState(false); // Cal 컴포넌트 표시 여부 상태 추가
    const [showLaw, setShowLaw] = useState(false); // Law 컴포넌트 표시 여부 상태 추가
    const [showChatbot, setShowChatbot] = useState(false); // Chatbot 표시 여부 상태 추가

    const toggleCal = () => {
        setShowCal((prev) => !prev); // Cal 컴포넌트의 표시 상태 토글
    };

    const toggleLaw = () => {
        setShowLaw((prev) => !prev); // Law 컴포넌트의 표시 상태 토글
    };

    const toggleChatbot = () => {
        setShowChatbot((prev) => !prev); // Chatbot 표시 상태 토글
    };

    return (
        <>
            <Header toggleCal={toggleCal} toggleLaw={toggleLaw} toggleChatbot={toggleChatbot} /> {/* Header에 toggleCal과 toggleLaw 함수 전달 */}
            <Main>
                <Intro />
                <Law className={showLaw ? "show" : ""} /> {/* showLaw가 true일 때만 Law 컴포넌트 표시 */}
                <Cal show={showCal} /> {/* showCal이 true일 때만 Cal 컴포넌트 표시 */}
                {showChatbot && <Chatbot />}
            </Main>
            <Footer />
        </>
    );
};

export default HomeView;
