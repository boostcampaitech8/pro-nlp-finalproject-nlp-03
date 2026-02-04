// src/pages/RankingRecipes/RankingRecipesPage.jsx
import { useState, useEffect } from "react";
import RecipeDetailModal from "@/pages/MyRecipes/RecipeDetailModal";
import BottomNav from "@/components/BottomNav";
import "./RankingRecipesPage.css";

const API_URL = import.meta.env.VITE_API_URL || "";

function StarRating({ rating = 0, size = 11 }) {
  const stars = [];
  for (let i = 1; i <= 5; i++) {
    stars.push(
      <span
        key={i}
        className={`star ${i <= rating ? "star-filled" : "star-empty"}`}
        style={{ fontSize: size }}
      >
        ★
      </span>,
    );
  }
  return <div className="card-star-overlay">{stars}</div>;
}

export default function RankingRecipesPage() {
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRankingRecipes();
  }, []);

  const fetchRankingRecipes = async () => {
    try {
      setLoading(true);
      setError(null);

      // 오늘의 랭킹 레시피 가져오기
      const res = await fetch(`${API_URL}/api/rankings/today?limit=100`);

      if (!res.ok) {
        throw new Error("랭킹 데이터를 불러올 수 없습니다");
      }

      const data = await res.json();
      // RecipePreview 형식: { recipe_id, title, author, image }
      setRecipes(data.recipes || []);
    } catch (err) {
      console.error("랭킹 레시피 불러오기 실패:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecipeClick = async (recipe) => {
    try {
      // 레시피 상세 정보 가져오기
      const res = await fetch(
        `${RANKING_API_URL}/api/rankings/recipes/${recipe.recipe_id}`,
      );

      if (res.ok) {
        const data = await res.json();
        // RecipeDetail 형식으로 반환됨
        setSelectedRecipe(data);
      } else {
        // 상세 정보를 못 가져오면 기본 정보만 표시
        setSelectedRecipe(recipe);
      }
    } catch (err) {
      console.error("레시피 상세 정보 불러오기 실패:", err);
      setSelectedRecipe(recipe);
    }
  };

  return (
    <div className="ranking-recipes-page">
      {/* 내부 스크롤 영역 */}
      <div className="ranking-recipes-scroll">
        {/* 클립 이미지 (베이지) */}
        <div className="clipboard-clip">
          <img src="/my-recipe-clip-beige.png" alt="clip" />
        </div>

        {/* 클립보드 본체 */}
        <div className="clipboard-board">
          <h1 className="clipboard-title">오늘의 인기 레시피</h1>

          {loading && (
            <div className="recipes-loading">
              <p>불러오는 중...</p>
            </div>
          )}

          {error && (
            <div className="recipes-error">
              <p className="error-message">{error}</p>
              <button className="retry-button" onClick={fetchRankingRecipes}>
                다시 시도
              </button>
            </div>
          )}

          {!loading && !error && recipes.length === 0 && (
            <div className="recipes-empty">
              <p className="empty-message">오늘의 랭킹 데이터가 없습니다</p>
            </div>
          )}

          {!loading && !error && recipes.length > 0 && (
            <div className="recipes-grid">
              {recipes.map((recipe, index) => (
                <div
                  key={recipe.recipe_id}
                  className="recipe-cards"
                  onClick={() => handleRecipeClick(recipe)}
                >
                  {/* 랭킹 번호 뱃지 */}
                  <div className="ranking-badge">{index + 1}</div>

                  <div className="recipe-cards-image">
                    {recipe.image ? (
                      <img src={recipe.image} alt={recipe.title} />
                    ) : (
                      <div className="recipe-cards-placeholder">
                        <svg
                          width="32"
                          height="32"
                          viewBox="0 0 32 32"
                          fill="none"
                        >
                          <circle
                            cx="16"
                            cy="16"
                            r="14"
                            stroke="#C4956A"
                            strokeWidth="1.5"
                            fill="none"
                          />
                          <path
                            d="M10 20C10 20 13 15 16 15C19 15 22 20 22 20"
                            stroke="#C4956A"
                            strokeWidth="1.5"
                          />
                          <circle cx="12" cy="13" r="1.5" fill="#C4956A" />
                        </svg>
                      </div>
                    )}
                    {/* 별점은 랭킹 데이터에 없으므로 제거하거나, 기본값 표시 */}
                  </div>

                  <div className="recipe-cards-info">
                    <span className="recipe-cards-title">{recipe.title}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 레시피 상세 모달 */}
      {selectedRecipe && (
        <RecipeDetailModal
          recipe={selectedRecipe}
          onClose={() => setSelectedRecipe(null)}
        />
      )}

      {/* 하단 고정 네비게이션 */}
      <BottomNav />
    </div>
  );
}
