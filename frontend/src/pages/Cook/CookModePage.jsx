"use client";

import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import RecipeLayout from "@/layouts/RecipeLayout";
import "./CookModePage.css";

export default function CookModePage() {
  const navigate = useNavigate();
  const location = useLocation();

  // CookModeAudioPage에서 돌아올 때 currentStepIndex, elapsedTime 유지
  const passedStepIndex = location.state?.currentStepIndex ?? 0;
  const passedElapsedTime = location.state?.elapsedTime ?? 0;
  const [currentStepIndex, setCurrentStepIndex] = useState(passedStepIndex);
  const [elapsedTime, setElapsedTime] = useState(passedElapsedTime);

  // RecipeResultPage 또는 CookModeAudioPage에서 전달받은 recipe 데이터
  const recipe = location.state?.recipe || {
    name: "레시피 없음",
    intro: "",
    time: "0분",
    level: "초급",
    servings: "1인분",
    ingredients: [],
    steps: [{ step: 1, description: "레시피 정보가 없습니다." }],
  };

  const recipeSteps = recipe.steps || [];

  // 타이머
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const handlePrev = () =>
    setCurrentStepIndex((prev) => (prev > 0 ? prev - 1 : prev));
  const handleNext = () =>
    setCurrentStepIndex((prev) =>
      prev < recipeSteps.length - 1 ? prev + 1 : prev
    );

  const handleRecordClick = () => {
    navigate("/cook-audio", {
      state: {
        currentStepIndex,
        recipeSteps,
        recipe,
        elapsedTime,
      },
    });
  };

  // RecipeBottomSheet용 steps - 이미 { no, desc } 형태로 옴
  const formattedSteps = recipeSteps.map((step, index) => ({
    no: step.no || index + 1,
    desc: step.desc || "",
  }));

  return (
    <RecipeLayout
      steps={formattedSteps}
      currentStep={currentStepIndex + 1}
      onStepClick={(index) => setCurrentStepIndex(index)}
    >
      {/* 레시피 제목 */}
      <h1 className="cook-recipe-title">{recipe.name}</h1>

      {/* 소요시간 & 스톱워치 아이콘 */}
      <div className="cook-time-row">
        <span className="cook-time-text">소요시간 {formatTime(elapsedTime)}</span>
        <img
          src="/stopwatch.png"
          alt="스톱워치"
          className="cook-stopwatch-icon"
          onError={(e) => (e.target.style.display = "none")}
        />
      </div>

      {/* 단계 설명 박스 */}
      <div className="cook-step-box">
        <span className="cook-step-label">
          STEP {recipeSteps[currentStepIndex]?.no || currentStepIndex + 1}
        </span>
        <p className="cook-step-description">
          {recipeSteps[currentStepIndex]?.desc || "단계 정보가 없습니다."}
        </p>
      </div>

      {/* 이미지 + 화살표 네비게이션 */}
      <div className="cook-image-nav">
        <button
          className="cook-nav-btn"
          onClick={handlePrev}
          disabled={currentStepIndex === 0}
        >
          <span className="cook-arrow">‹</span>
        </button>

        <div className="cook-food-image-wrapper">
          <img
            src={recipeSteps[currentStepIndex]?.image || "/images/default-food.jpg"}
            alt="조리 이미지"
            className="cook-food-image"
            onError={(e) => {
              e.target.src = "https://via.placeholder.com/200?text=No+Image";
            }}
          />
        </div>

        <button
          className="cook-nav-btn"
          onClick={handleNext}
          disabled={currentStepIndex === recipeSteps.length - 1}
        >
          <span className="cook-arrow">›</span>
        </button>
      </div>

      {/* 녹음 버튼 */}
      <div className="cook-record-wrapper">
        <button className="cook-record-btn" onClick={handleRecordClick}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        </button>
      </div>
    </RecipeLayout>
  );
}
