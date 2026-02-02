"use client";

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./ResultPage.css";

export default function ResultModePage() {
  const navigate = useNavigate();
  const [rating, setRating] = useState(0);

  const handleStarClick = (index) => {
    setRating(index + 1);
  };

  const handleSaveRecipe = () => {
    alert("마이레시피에 담겼습니다!");
  };

  return (
    <div className="result-mode-container">
      {/* 1. 상단 배경 및 마스코트 영역 */}
      <div className="result-mode-mascot-section">
        <img
          src="/chef-mascot.png"
          alt="결과 마스코트"
          className="result-mode-mascot-img"
        />
      </div>

      {/* 2. 메인 화이트 카드 */}
      <div className="result-mode-card">
        <button 
          className="result-mode-close-btn" 
          onClick={() => navigate("/home")}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#CCB6A1" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        {/* 텍스트 헤더 영역 */}
        <div className="result-mode-header">
          <h2 className="result-mode-main-title">오늘의 요리가 끝났어요</h2>
          <p className="result-mode-sub-desc">레시피를 전달해드릴게요.......?</p>
          
          {/* 요리명과 소요시간을 감싸는 흰색 박스 */}
          <div className="result-mode-info-card">
            <h1 className="result-mode-dish-name">바지락양념칼국수</h1>
            <span className="result-mode-duration">총 소요시간 00:14:34</span>
          </div>
        </div>

        {/* 요리 결과 이미지 */}
        <div className="result-mode-image-box">
          <img 
            src="/images/tteokbokki.jpg" 
            alt="요리 결과" 
            className="result-mode-dish-img"
            onError={(e) => { e.target.src = "https://via.placeholder.com/300?text=Result+Image"; }}
          />
        </div>

        {/* 별점 섹션 */}
        <div className="result-mode-rating-area">
          {[1, 2, 3].map((num) => (
            <button
              key={num}
              className={`result-mode-star ${rating >= num ? "is-active" : ""}`}
              onClick={() => handleStarClick(num - 1)}
            >
              ★
            </button>
          ))}
        </div>

        {/* 하단 액션 버튼 */}
        <div className="result-mode-footer-btns">
          <button className="result-mode-btn-confirm" onClick={handleSaveRecipe}>
            마이레시피에<br />담을래요
          </button>
          <button className="result-mode-btn-cancel" onClick={() => navigate("/home")}>
            안담을래요
          </button>
        </div>
      </div>
    </div>
  );
}