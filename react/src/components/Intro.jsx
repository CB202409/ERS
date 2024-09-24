import React from "react";

import about from "../assets/img/about.jpg";

const Intro = () => {
    return (
        <section id="intro">
            <div className="intro__inner">
                <div className="intro__lines" aria-hidden="true">
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                </div>
                    <div className="img">
                        <img src={about} alt="어바웃" />
                    </div>
                </div>
                <div className="intro__lines bottom" aria-hidden="true">
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                    <span className="line"></span>
                </div>
        </section>
    );
};

export default Intro;
