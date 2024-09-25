import React, { useState } from "react";

const headerNav = [
    {
        title: "Law",
        url: "#Law",
        toggle: true
    },
    {
        title: "Cal",
        url: "#Cal",
        toggle: true 
    },
    {
        title: "chatbot",
        url: "#chatbot",
        toggle:true
    }
];

const Header = ({ toggleCal, toggleLaw, toggleChatbot }) => {
    const [showCal, setShowCal] = useState(false);
    const [showLaw, setShowLaw] = useState(false);
    const [showChatbot, setShowChatbot] = useState(false);

    const handleToggleCal = (e) => {
        e.preventDefault();
        setShowCal(!showCal);
        toggleCal();
    };

    const handleToggleLaw = (e) => {
        e.preventDefault();
        setShowLaw(!showLaw);
        toggleLaw();
    };

    const handleToggleChatbot = (e) => {
        e.preventDefault();
        setShowChatbot(!showChatbot);
        toggleChatbot(); 
    };

    return (
        <header id="header" role="banner">
            <div className="header__inner">
                <div className="header__logo">
                    <a href="/">team2</a>
                </div>
                <nav className={`header__nav ${showCal || showLaw || showChatbot ? "show" : ""}`} role="navigation" aria-label="메인 메뉴">
                    <ul>
                        {headerNav.map((nav, key) => (
                            <li key={key}>
                                <a 
                                    href={nav.url}
                                    onClick={nav.title === "Cal" ? handleToggleCal : nav.title === "Law" ? handleToggleLaw : handleToggleChatbot}
                                >
                                    {nav.title}
                                </a>
                            </li>
                        ))}
                    </ul>
                </nav>
                <div
                    className="header__nav__mobile"
                    id="headerToggle"
                    aria-controls="primary-menu"
                    aria-expanded={showCal || showLaw || showChatbot ? "true" : "false"}
                    role="button" 
                    tabIndex="0"
                >
                    <span></span>
                </div>
            </div>
        </header>
    );
};

export default Header;
