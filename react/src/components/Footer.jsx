import React from "react";
const footerText = [
    {
        title: "",
        desc: "",
        link: "",
    }
    
];

const Footer = () => {
    return (
        <footer id="footer" role="contentinfo">
           <div className="right">
    <h3></h3>
    <ul>
        {footerText.map((footer, key) => (
            <li key={key}>
                <a href={footer.link}>{footer.title}</a>
                <em>{footer.desc}</em>
            </li>
        ))}
    </ul>
</div>
</footer>
    );
};

export default Footer;
