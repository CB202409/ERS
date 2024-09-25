import React from "react";

const lawLinks = [
    {
        title: "근로 기준법",
        url: "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B7%BC%EB%A1%9C%EA%B8%B0%EC%A4%80%EB%B2%95"
    },
    {
        title: "노동조합법",
        url: "https://www.law.go.kr/LSW//lsSc.do?section=&menuId=1&subMenuId=15&tabMenuId=81&eventGubun=060101&query=%EB%85%B8%EB%8F%99%EC%A1%B0%ED%95%A9%EB%B2%95#undefined"
    },
    {
        title: "고용보험법",
        url: "https://www.law.go.kr/LSW//lsSc.do?section=&menuId=1&subMenuId=15&tabMenuId=81&eventGubun=060101&query=%EB%85%B8%EB%8F%99%EC%A1%B0%ED%95%A9%EB%B2%95#liBgcolor0"
    },
    {
        title: "산업안전보건법",
        url: "https://www.law.go.kr/LSW//lsSc.do?section=&menuId=1&subMenuId=15&tabMenuId=81&eventGubun=060101&query=%EB%85%B8%EB%8F%99%EC%A1%B0%ED%95%A9%EB%B2%95#undefined"
    },
    {
        title: "최저임금법",
        url: "https://www.law.go.kr/LSW//lsSc.do?section=&menuId=1&subMenuId=15&tabMenuId=81&eventGubun=060101&query=%EB%85%B8%EB%8F%99%EC%A1%B0%ED%95%A9%EB%B2%95#undefined"
    },
    {
        title: "근로자퇴직급여 보장법",
        url: "https://www.law.go.kr/LSW//lsSc.do?section=&menuId=1&subMenuId=15&tabMenuId=81&eventGubun=060101&query=%EB%85%B8%EB%8F%99%EC%A1%B0%ED%95%A9%EB%B2%95#undefined"
    }
];

const Law = ({ className }) => {
    return (
        <section id="Law" className={className}>
            <h1 className="Law_title">노동법</h1>
            {lawLinks.map((law, index) => (
                <h3 key={index} className="Law_item">
                    <a 
                        href={law.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="law-link"
                    >
                        {law.title}
                    </a>
                </h3>
            ))}
        </section>
    );
};

export default Law;
