// src/pages/MyRecipes/RecipeDetailModal.jsx
import "./RecipeDetailModal.css";

export default function RecipeDetailModal({ recipe, onClose }) {
  const recipeData =
    typeof recipe.recipe_json === "string"
      ? JSON.parse(recipe.recipe_json)
      : recipe.recipe_json || recipe;

  const title = recipeData.title || recipe.title || "";
  const cookTime = recipeData.cook_time || "";
  const level = recipeData.level || "";
  const ingredients = recipeData.ingredients || [];
  const steps = recipeData.steps || [];
  const imageUrl = recipe.image_url || recipeData.image_url || null;

  // 날짜 포맷 (YY.MM.DD)
  const createdAt = recipe.created_at
    ? (() => {
        const d = new Date(recipe.created_at);
        const yy = String(d.getFullYear()).slice(2);
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${yy}.${mm}.${dd}`;
      })()
    : "";

  // 이전 소요시간
  const prevTime = recipe.cooking_time || recipeData.cooking_time || "";

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-page-wrap" onClick={(e) => e.stopPropagation()}>
        {/* 오렌지 클립 - 메인 클립과 동일 위치 */}
        <div className="detail-clip">
          <img src="/my-recipe-clip-orange.png" alt="clip" />
        </div>

        {/* 모달 본체 - 클립보드 보드와 동일 위치/크기 */}
        <div className="detail-modal">
          {/* 닫기 버튼 */}
          <button className="detail-close" onClick={onClose}>
            <img src="/my-recipe-close.png" alt="close" />
          </button>

          <div className="detail-content">
            {/* 날짜 */}
            {createdAt && <p className="detail-date">{createdAt}</p>}

            {/* 제목 + 밑줄 */}
            <h2 className="detail-title">{title}</h2>
            <hr className="detail-title-line" />

            {/* 이전 소요시간 */}
            <p className="detail-prev-time">
              이전 소요시간 {prevTime || "00:00:00"}
            </p>

            {/* 이미지 */}
            <div className="detail-image-wrap">
              {imageUrl ? (
                <img src={imageUrl} alt={title} className="detail-image" />
              ) : (
                <div className="detail-image-placeholder">
                  <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                    <circle cx="30" cy="30" r="27" stroke="#C4956A" strokeWidth="2" fill="none"/>
                    <path d="M18 38C18 38 24 27 30 27C36 27 42 38 42 38" stroke="#C4956A" strokeWidth="2"/>
                    <circle cx="23" cy="24" r="3" fill="#C4956A"/>
                  </svg>
                </div>
              )}
            </div>

            {/* 시간 & 난이도 */}
            <div className="detail-meta">
              {cookTime && (
                <span className="meta-item">
                  <img src="/my-recipe-time.png" alt="time" className="meta-icon" />
                  {cookTime}
                </span>
              )}
              {level && (
                <span className="meta-item">
                  <img src="/my-recipe-level.png" alt="level" className="meta-icon" />
                  {level}
                </span>
              )}
            </div>

            {/* 재료 */}
            <div className="detail-section">
              <h3 className="detail-section-title">재료</h3>
              <hr className="detail-section-line" />
              <div className="detail-ingredients">
                {ingredients.length > 0 ? (
                  <div className="ingredients-columns">
                    {ingredients.map((ing, idx) => (
                      <div key={idx} className="ingredient-item">
                        <span>• </span>
                        <span>{ing.name} {ing.amount}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="detail-empty-text">재료 정보가 없습니다</p>
                )}
              </div>
            </div>

            {/* 조리법 */}
            <div className="detail-section">
              <h3 className="detail-section-title">조리법</h3>
              <hr className="detail-section-line" />
              <ol className="detail-steps">
                {steps.length > 0 ? (
                  steps.map((step, idx) => (
                    <li key={idx} className="step-item">
                      {step.desc || step}
                    </li>
                  ))
                ) : (
                  <p className="detail-empty-text">조리법 정보가 없습니다</p>
                )}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
