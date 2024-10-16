import React from 'react';
import { useNavigate } from 'react-router-dom';

const ChooseSection = ({ setSelectedOption }) => {
    const navigate = useNavigate();

    const handleEasyClick = () => {
        setSelectedOption("easy");
        navigate('/home');
    };

    // const handleHardClick = () => {
    //     setSelectedOption("hard");
    //     navigate('/home2');
    // };

    const handleCalClick = () => {
        setSelectedOption("cal");
        navigate('/cal');
    };

    return (
        <div className="selection-container">
            <div className="section easy" onClick={handleEasyClick}>
                <h1>easy</h1>
                <p>초보자용</p>
            </div>
            {/* <div className="section hard" onClick={handleHardClick}>
                <h1>hard</h1>
                <p>전문가용</p>
            </div> */}
            <div className="section cal" onClick={handleCalClick}>
                <h1>cal</h1>
                <p>계산용</p>
            </div>
        </div>
    );
};

export default ChooseSection;
