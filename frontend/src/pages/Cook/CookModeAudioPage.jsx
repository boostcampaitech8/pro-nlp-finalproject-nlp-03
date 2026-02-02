"use client";

import { useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import "./CookModeAudioPage.css";

export default function CookModeAudioPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isBottomSheetOpen, setIsBottomSheetOpen] = useState(false);

  // CookModePage에서 전달받은 단계 정보 (없으면 기본값 사용)
  const passedStepIndex = location.state?.currentStepIndex ?? 0;
  const passedRecipeSteps = location.state?.recipeSteps;

  // 실제 데이터 소스 (전달받은 레시피 또는 기본값)
  const recipeSteps = passedRecipeSteps || [
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
      text: "국물이 졸아들면 대파를 가위로 쫑쫑 썰어 넣어주시고 통깨 약간 뿌려 주시면 끝!",
    },
    { id: 4, text: "너무 간단한데 맛있어서 놀라는 분식집 떡볶이 완성입니다!" },
    {
      id: 5,
      text: "한개 먹어보니 어머머! 정말 분식집에서 파는 떡볶이 맛이 나면서 넘 맛있어요.",
    },
    { id: 6, text: "너무 간단한데 맛있어서 놀랬어요^^" },
  ];

  // 현재 단계를 추적하는 상태 (전달받은 단계로 초기화)
  const [currentStepIndex, setCurrentStepIndex] = useState(passedStepIndex);

  // 채팅 데이터 (사용자: 우측, AI: 좌측 배치용)
  const [messages] = useState([
    { id: 1, type: "user", text: "통깨는 얼마나 넣으면 돼?" },
    { id: 2, type: "ai", text: "통깨는 약간만 뿌려주시면 충분해요!" },
  ]);

  return (
    <div className="recipe-container">
      <div className="mascot-wrapper">
        <img src="/chef-mascot.png" alt="마스코트" className="mascot-image" />
      </div>

      <div className="main-card audio-layout">
        <button className="close-button" onClick={() => navigate("/home")}>
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#333"
            strokeWidth="2.5"
          >
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>

        <div className="audio-header">
          <h2 className="audio-recipe-title">바지락양념칼국수</h2>
          <span className="audio-time">소요시간 00:10:34</span>
        </div>

        {/* STEP 박스: currentStepIndex에 따라 실시간 텍스트 반영 */}
        <div className="step-display-container">
          <div className="step-number-tag">
            STEP {recipeSteps[currentStepIndex].id}
          </div>
          <p className="step-main-text">{recipeSteps[currentStepIndex].text}</p>
        </div>

        {/* [복구] 이미지와 동일한 채팅 박스 영역 */}
        <div className="chat-outer-box">
          <div className="chat-inner-list">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-bubble-row ${msg.type}`}>
                <div className="bubble">{msg.text}</div>
              </div>
            ))}
          </div>
          {/* 우측 하단 로딩 스피너 */}
          <div className="chat-loading-anchor">
            <div className="circle-loader"></div>
          </div>
        </div>

        {/* 하단 제어 영역: 녹음 버튼을 위로 올림 */}
        <div className="mic-control-section">
          <button className="orange-mic-btn">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          </button>
        </div>

        {/* 바텀시트 트리거 */}
        <div
          className="bottom-sheet-anchor"
          onClick={() => setIsBottomSheetOpen(true)}
        >
          <div className="handle-bar" />
          <span className="handle-text">레시피 전체보기</span>
        </div>
      </div>

      {/* 바텀시트: 클릭 시 상단 STEP 박스 연동 */}
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
                  setCurrentStepIndex(index); // 상단 STEP 박스 업데이트
                  setIsBottomSheetOpen(false);
                }}
              >
                <span className="step-num">{step.id}.</span>
                <span className="step-txt">{step.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
