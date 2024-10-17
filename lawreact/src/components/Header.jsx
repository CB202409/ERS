import React from "react";
import { useLocation } from "react-router-dom";
import { AppstoreOutlined } from "@ant-design/icons";

const Header = () => {
    const location = useLocation();
    
    const headerNav = [
        {
            title: "chat",
            url: "home",
            icon: <AppstoreOutlined />
        },
        // {
        //     title: "자문",
        //     url: "home2",
        //     icon: <AppstoreOutlined />
        // },
        {
            title: "계산",
            url: "Cal",
            icon: <AppstoreOutlined />
        }
    ];

    return (
        <header className="header">
            <div className="header__inner">
                <div className="header__logo">
                    <a href="/">
                        <h1>HomeLex</h1>
                    </a>
                </div>

                <nav className="header__nav">
                    <ul>
                        {headerNav.map((item, index) => (
                            <li key={index}>
                                <a href={item.url}>
                                    {item.icon}
                                    <span>{item.title}</span>
                                </a>
                            </li>
                        ))}
                    </ul>
                </nav>
            </div>
        </header>
    );
};

export default Header;
