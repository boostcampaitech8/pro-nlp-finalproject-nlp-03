// src/components/RecipeBottomSheet.jsx
import { useState } from "react";
import "./RecipeBottomSheet.css";

export default function RecipeBottomSheet({ steps, currentStep = 1 }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!steps || steps.length === 0) {
    return null;
  }

  return (
    <>
      {/* Bottom Sheet Overlay */}
      <div
        className={`bottom-sheet-overlay ${isOpen ? "active" : ""}`}
        onClick={() => setIsOpen(false)}
      />

      {/* Bottom Sheet - 하단 고정 */}
      <div className={`recipe-bottom-sheet ${isOpen ? "open" : ""}`}>
        {/* 항상 보이는 트리거 */}
        <div className="sheet-trigger" onClick={() => setIsOpen(!isOpen)}>
          <div className="trigger-indicator" />
          <span className="trigger-text">레시피 전체보기</span>
        </div>

        {/* 올라오는 콘텐츠 */}
        {isOpen && (
          <div className="sheet-content">
            <div className="recipe-steps-list">
              {steps.map((step, index) => {
                const stepNumber = step.no || step.id || index + 1;
                const stepText = step.desc || step.text || "";

                return (
                  <div
                    key={index}
                    className={`recipe-step-item ${stepNumber === currentStep ? "active" : ""}`}
                  >
                    <span className="step-num">{stepNumber}.</span>
                    <span className="step-desc">{stepText}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
