import React, { useState } from "react";
import { AppstoreOutlined, SearchOutlined } from "@ant-design/icons";
import { CiCalculator1 } from "react-icons/ci";
import { FaBalanceScaleLeft } from "react-icons/fa";


const Header = ({ onQuestionSelect, isAiResponding, onNavigateToCal }) => {
  const [isSearchVisible, setIsSearchVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredResults, setFilteredResults] = useState([]);

  const questions = [
    "노동법 관련 질문 1",
    "노동법 관련 질문 2",
    "노동법 관련 질문 3",
    "노동법 관련 질문 4",
    "Home2 관련 질문 1",
    "Home2 관련 질문 2",
  ];

  const toggleSearch = (event) => {
    event.preventDefault();
    setIsSearchVisible((prev) => !prev);
  };

  const handleSearchInputChange = (event) => {
    const query = event.target.value.toLowerCase();
    setSearchTerm(query);

    setFilteredResults(
      query ? questions.filter((q) => q.toLowerCase().includes(query)) : []
    );
  };

  const handleResultClick = (question) => {
    if (!isAiResponding) {
      onQuestionSelect(question);
      setFilteredResults([]);
      setSearchTerm("");
    } else {
      alert("AI가 응답 중입니다. 잠시 후 다시 시도해주세요.");
    }
  };

  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__logo">
          <a href="/home">
            <h1>LawChat</h1>
          </a>
        </div>
        <nav className="header__nav">
          <ul>
            <li>
              <a href="/home">
                <FaBalanceScaleLeft className="nav-icon" />
                <span>chat</span>
              </a>
            </li>
            <li>
            <a onClick={onNavigateToCal} style={{ cursor: "pointer" }}>
            <CiCalculator1 className="nav-icon" />
              <span>Cal</span>
            </a>
            </li>
            <li>
              <a onClick={toggleSearch} style={{ cursor: "pointer" }}>
                <SearchOutlined className="nav-icon" />
                <span>검색</span>
              </a>
            </li>
          </ul>
        </nav>
      </div>

      {isSearchVisible && (
        <div className="search-container">
          <input
            type="text"
            placeholder="키워드 질문 예) 실업, 해고, 퇴직"
            value={searchTerm}
            onChange={handleSearchInputChange}
            disabled={isAiResponding}
          />
          {filteredResults.length > 0 && (
            <ul className="search-results">
              {filteredResults.map((result, index) => (
                <li key={index} onClick={() => handleResultClick(result)}>
                  {result}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </header>
  );
};

export default Header;
