import React from "react";

import about from "../assets/img/about.jpg";

const Intro = () => {
    return (
        <section id="intro">
            <div class="intro__inner">
                <div class="intro__lines" aria-hidden="true">
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                </div>
                    <div class="img">
                        <img src={about} alt="어바웃" />
                    </div>
                </div>
                <div class="intro__lines bottom" aria-hidden="true">
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                    <span class="line"></span>
                </div>
        </section>
    );
};

export default Intro;
