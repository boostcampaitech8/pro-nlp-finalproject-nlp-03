"use client";

import { useNavigate } from "react-router-dom";
import { useState } from "react";
import "./CookModePage.css";

export default function RecipeRecommendation() {
  const navigate = useNavigate();
  const [isBottomSheetOpen, setIsBottomSheetOpen] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const recipeSteps = [
    {
      id: 1,
      text: "먼저 종이컵 기준 물 2컵에 떡볶이떡을 넣고 센불에서 팔팔 끓여 줍니다.",
    },
    {
      id: 2,
      text: "물이 팔팔 끓으면 양념을 다 넣어준 뒤 잘 풀어주고 또 자글자글 끓여 줍니다.",
    },
    {
      id: 3,
      text: "국물이 줄어들면 대파를 가위로 쫑쫑 썰어 넣어주시고 통깨 약간 뿌려 주시면 끝!",
    },
    { id: 4, text: "너무 간단한데 맛있어서 놀라는 분식집 떡볶이 완성입니다!" },
    {
      id: 5,
      text: "한개 먹어보니 어머머!정말 분식집에서 파는 떡볶이 맛이 나면서 넘 맛있어요. 너무 간단한데 맛있어서 놀랬어요^^",
    },
    {
      id: 6,
      text: "한개 먹어보니 어머머!정말 분식집에서 파는 떡볶이 맛이 나면서 넘 맛있어요. 너무 간단한데 맛있어서 놀랬어요^^",
    },
  ];

  const handlePrev = () =>
    setCurrentStepIndex((prev) => (prev > 0 ? prev - 1 : prev));
  const handleNext = () =>
    setCurrentStepIndex((prev) =>
      prev < recipeSteps.length - 1 ? prev + 1 : prev,
    );

  // 녹음 버튼 클릭 시 CookModeAudioPage로 이동 (현재 단계 전달)
  const handleRecordClick = () => {
    navigate("/cook-audio", {
      state: {
        currentStepIndex,
        recipeSteps,
      },
    });
  };

  return (
    <div className="recipe-container">
      <div className="mascot-wrapper">
        <img
          src="/chef-mascot.png"
          alt="요리사 마스코트"
          className="mascot-image"
        />
      </div>

      <div className="main-card">
        <button className="close-button" onClick={() => navigate("/home")}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              d="M18 6L6 18M6 6l12 12"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        <div className="recipe-display-section">
          <div className="step-indicator">
            Step {recipeSteps[currentStepIndex].id}
          </div>
          <p className="step-description">
            {recipeSteps[currentStepIndex].text}
          </p>
        </div>

        <div className="image-nav-container">
          <button
            className="nav-btn"
            onClick={handlePrev}
            disabled={currentStepIndex === 0}
          >
            <span className="arrow-icon">〈</span>
          </button>

          <div className="food-image-wrapper">
            <img
              src="/images/tteokbokki.jpg"
              alt="레시피 이미지"
              className="food-image-content"
              onError={(e) => {
                e.target.src = "https://via.placeholder.com/150?text=No+Image";
              }}
            />
          </div>

          <button
            className="nav-btn"
            onClick={handleNext}
            disabled={currentStepIndex === recipeSteps.length - 1}
          >
            <span className="arrow-icon">〉</span>
          </button>
        </div>

        <div className="record-section-spacer">
          {/* onClick 핸들러 추가됨 */}
          <button className="btn-record-giant" onClick={handleRecordClick}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="white">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          </button>
        </div>

        <div
          className="bottom-sheet-trigger"
          onClick={() => setIsBottomSheetOpen(true)}
        >
          <div className="drag-indicator" />
          <span className="view-all-text">레시피 전체보기</span>
        </div>
      </div>

      <div
        className={`bottom-sheet-overlay ${isBottomSheetOpen ? "active" : ""}`}
        onClick={() => setIsBottomSheetOpen(false)}
      />
      <div className={`bottom-sheet ${isBottomSheetOpen ? "active" : ""}`}>
        <div className="bottom-sheet-header">
          <div className="bottom-sheet-handle" />
          <h2 className="bottom-sheet-title">레시피 전체보기</h2>
        </div>
        <div className="bottom-sheet-content">
          <ul className="recipe-list">
            {recipeSteps.map((step, index) => (
              <li
                key={step.id}
                className={`recipe-item ${index === currentStepIndex ? "current" : ""}`}
                onClick={() => {
                  setCurrentStepIndex(index);
                  setIsBottomSheetOpen(false);
                }}
              >
                <span className="step-number">{step.id}.</span>
                <span className="step-text">{step.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
