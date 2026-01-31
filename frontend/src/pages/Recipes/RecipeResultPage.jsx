// src/pages/RecipeResult/RecipeResultPage.jsx
import { useLocation, useNavigate } from "react-router-dom";
import "./RecipeResultPage.css";

export default function RecipeResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { recipe, memberInfo, chatHistory } = location.state || {};

  if (!recipe) {
    return (
      <div className="error-page">
        <h2>레시피 정보가 없습니다</h2>
        <button onClick={() => navigate("/chat")}>돌아가기</button>
      </div>
    );
  }

  return (
    <div className="recipe-result-page">
      <div className="recipe-header">
        <button className="back-button" onClick={() => navigate("/chat")}>
          ← 돌아가기
        </button>
        <h1>{recipe.title}</h1>
      </div>

      <div className="recipe-content">
        {/* 메타 정보 */}
        <div className="recipe-meta">
          <div className="meta-item">
            <span className="label">조리시간</span>
            <span className="value">{recipe.cook_time}</span>
          </div>
          <div className="meta-item">
            <span className="label">난이도</span>
            <span className="value">{recipe.level}</span>
          </div>
          <div className="meta-item">
            <span className="label">분량</span>
            <span className="value">{recipe.servings}</span>
          </div>
        </div>

        {/* 소개 */}
        {recipe.intro && (
          <div className="recipe-intro">
            <p>{recipe.intro}</p>
          </div>
        )}

        {/* 재료 */}
        <div className="recipe-section">
          <h2>🥘 재료</h2>
          <ul className="ingredients-list">
            {recipe.ingredients?.map((ing, idx) => (
              <li key={idx}>
                <span className="ing-name">{ing.name}</span>
                <span className="ing-amount">{ing.amount}</span>
                {ing.note && <span className="ing-note">({ing.note})</span>}
              </li>
            ))}
          </ul>
        </div>

        {/* 조리법 */}
        <div className="recipe-section">
          <h2>👨‍🍳 조리법</h2>
          <ol className="steps-list">
            {recipe.steps?.map((step, idx) => (
              <li key={idx}>
                <span className="step-number">{step.no}</span>
                <span className="step-desc">{step.desc}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* 팁 */}
        {recipe.tips && recipe.tips.length > 0 && (
          <div className="recipe-section">
            <h2>💡 팁</h2>
            <ul className="tips-list">
              {recipe.tips.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 가족 정보 (디버그용 - 나중에 제거 가능) */}
        <details className="debug-info">
          <summary>적용된 정보</summary>
          <div className="debug-content">
            <p>
              <strong>대상:</strong> {memberInfo?.names?.join(", ")}
            </p>
            <p>
              <strong>알레르기:</strong> {memberInfo?.allergies?.join(", ")}
            </p>
            <p>
              <strong>비선호:</strong> {memberInfo?.dislikes?.join(", ")}
            </p>
            <p>
              <strong>대화 수:</strong> {chatHistory?.length}개
            </p>
          </div>
        </details>
      </div>

      {/* 하단 버튼 */}
      <div className="recipe-actions">
        <button className="btn-secondary" onClick={() => navigate("/chat")}>
          새로운 레시피 찾기
        </button>
        <button
          className="btn-primary"
          onClick={() => {
            // TODO: 조리 모드로 이동
            alert("조리 모드는 준비 중입니다!");
          }}
        >
          조리 시작하기
        </button>
      </div>
    </div>
  );
}
