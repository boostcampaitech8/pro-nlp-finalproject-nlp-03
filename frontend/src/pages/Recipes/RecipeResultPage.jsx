"use client";

import { useNavigate } from "react-router-dom";
import BottomNav from "@/components/BottomNav";
import { useState } from "react";
import "./RecipeResultPage.css";

export default function RecipeRecommendation() {
  const [isBottomSheetOpen, setIsBottomSheetOpen] = useState(false);
  const [remainingCount, setRemainingCount] = useState(1);
  const navigate = useNavigate();
  const currentStep = 3;

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

  const recipeList = [
    { id: 1, name: "바지락양념칼국수", time: "15분", level: "왕초급" },
    { id: 2, name: "계란후라이", time: "10분", level: "초급" },
    { id: 3, name: "김치찌개", time: "20분", level: "중급" },
    { id: 4, name: "된장찌개", time: "15분", level: "중급" },
    { id: 5, name: "된장국", time: "30분", level: "고급" },
    { id: 6, name: "계란국", time: "20분", level: "고급" },
  ];

  const handleRegenerate = () => {
    if (remainingCount > 0) {
      setRemainingCount(remainingCount - 1);
    }
  };

  const handleStartCooking = () => {
    const recipe = {
      name: "바지락양념칼국수",
      time: "15분",
      level: "왕초급",
      steps: recipeSteps.map((step) => ({
        no: step.id,
        desc: step.text,
        img: null,
      })),
    };
    navigate("/cook", { state: { recipe } });
  };

  const handleClose = () => {
    console.log("/home");
  };

  return (
    <div className="recipe-result-container">
      {/* Mascot - Outside the card */}
      <div className="recipe-result-mascot-wrapper">
        <img
          src="/public/chef-mascot.png"
          alt="요리사 마스코트"
          className="recipe-result-mascot-image"
        />
      </div>

      {/* Main Card */}
      <div className="recipe-result-main-card">
        {/* Close Button - On top of the card */}
        <button className="recipe-result-close-button" onClick={() => navigate("/home")}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M15 5L5 15M5 5L15 15"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>

        {/* Title */}
        <div className="recipe-result-title-section">
          <p className="recipe-result-title-prefix">오늘의 추천 레시피는</p>
          <div className="recipe-result-title-main">
            <span className="recipe-result-recipe-name">바지락양념칼국수</span>
            <span className="recipe-result-title-suffix"> 입니다</span>
          </div>
        </div>

        {/* Food Image */}
        <div className="recipe-result-food-image-container">
          <img
            src="/images/clam-noodle.jpg"
            alt="바지락양념칼국수"
            className="recipe-result-food-image"
          />
        </div>

        {/* Info Tags */}
        <div className="recipe-result-info-tags">
          <div className="recipe-result-info-tag">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle
                cx="8"
                cy="8"
                r="7"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M8 4V8L11 10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            <span>15분</span>
          </div>
          <div className="recipe-result-info-tag">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 2C9.5 2 11 3 11 5C11 7 8 8 8 8C8 8 5 7 5 5C5 3 6.5 2 8 2Z"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M4 14C4 11.7909 5.79086 10 8 10C10.2091 10 12 11.7909 12 14"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            <span>왕초급</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="recipe-result-action-buttons">
          <button className="recipe-result-btn-regenerate" onClick={() => navigate("/chat")}>
            <span className="recipe-result-btn-regenerate-text">다시 생성</span>
            <span className="recipe-result-btn-regenerate-sub">{remainingCount}회 남음</span>
          </button>
          <button className="recipe-result-btn-start" onClick={handleStartCooking}>
            요리 시작하기
          </button>
        </div>

        {/* Bottom Sheet Trigger */}
        <div
          className="recipe-result-bottom-sheet-trigger"
          onClick={() => setIsBottomSheetOpen(true)}
        >
          <div className="recipe-result-drag-indicator" />
          <span className="recipe-result-view-all-text">레시피 전체보기</span>
        </div>
      </div>

      {/* Bottom Sheet Overlay */}
      <div
        className={`recipe-result-bottom-sheet-overlay ${isBottomSheetOpen ? "active" : ""}`}
        onClick={() => setIsBottomSheetOpen(false)}
      />

      {/* Bottom Sheet */}
      <div className={`recipe-result-bottom-sheet ${isBottomSheetOpen ? "active" : ""}`}>
        <div className="recipe-result-bottom-sheet-header">
          <div
            className="recipe-result-bottom-sheet-handle"
            onClick={() => setIsBottomSheetOpen(false)}
          />
          <h2 className="recipe-result-bottom-sheet-title">레시피 전체보기</h2>
        </div>
        <div className="recipe-result-bottom-sheet-content">
          <ul className="recipe-result-recipe-list">
            {recipeSteps.map((step, index) => (
              <li
                key={step.id}
                className={`recipe-result-recipe-item ${index === currentStep - 1 ? "current" : ""}`}
                onClick={() => setIsBottomSheetOpen(false)}
              >
                <span className="recipe-result-step-number">{step.id}.</span>
                <span className="recipe-result-step-text">{step.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
