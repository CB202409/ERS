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

    const handleSearchInputChange = (event) => {
        const query = event.target.value.toLowerCase();
        setSearchTerm(query);

        const filtered = questions.filter((question) =>
            question.toLowerCase().includes(query)
        );
        setFilteredResults(filtered);
    };

    const handleResultClick = (question) => {
        if (!isAiResponding) {
            addMessage(question);  // 질문을 ChatBot으로 전달
            setFilteredResults([]);
            setSearchTerm("");
        } else {
            alert("AI가 응답 중입니다. 응답이 끝난 후에 질문할 수 있습니다.");
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
                        disabled={isAiResponding}
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
