import React, { useState } from "react";

const Header2 = ({ setFilteredQuestions, addMessage, isAiResponding }) => {
    const [searchTerm, setSearchTerm] = useState("");
    const [filteredResults, setFilteredResults] = useState([]);

    const questions = [
        "노동법 관련 질문 1",
        "노동법 관련 질문 2",
        "노동법 관련 질문 3",
        "노동법 관련 질문 4",
        "Home2 관련 질문 1",
        "Home2 관련 질문 2"
    ];

    // 검색 입력 핸들러
    const handleSearchInputChange = (event) => {
        const query = event.target.value.toLowerCase();
        setSearchTerm(query);

        const filtered = questions.filter((question) =>
            question.toLowerCase().includes(query)
        );
        setFilteredResults(filtered);
    };

    // 질문 클릭 핸들러
    const handleResultClick = (question) => {
        if (!isAiResponding) {  // AI 응답 중이 아닐 때만 질문 전송 가능
            addMessage(question);  // 질문을 ChatBot에 전송
            setFilteredResults([]);  // 질문 전송 후 검색 결과 초기화
            setSearchTerm("");  // 입력 필드 초기화
        } else {
            alert("AI가 응답 중입니다. 응답이 끝난 후에 질문할 수 있습니다.");  // 응답 중일 때 경고
        }
    };

    return (
        <div className="header2">
            <header className="header2__inner">
                <div className="search-container">
                    <input
                        type="text"
                        placeholder="키워드 질문 예)실업 해고 퇴직"
                        value={searchTerm}
                        onChange={handleSearchInputChange}
                        disabled={isAiResponding}  // AI 응답 중일 때 검색 입력 금지
                    />
                </div>
            </header>

            {filteredResults.length > 0 && (
                <ul className="header2__search-results">
                    {filteredResults.map((result, index) => (
                        <li key={index} onClick={() => handleResultClick(result)}>
                            {result}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default Header2;
