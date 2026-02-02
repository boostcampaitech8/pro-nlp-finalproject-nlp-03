// src/pages/Recipe/RecipeResultPage.jsx
import { useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import RecipeLayout from "@/layouts/RecipeLayout";
import ButtonRed from "@/components/ButtonRed";
import ButtonWhite from "@/components/ButtonWhite";
import "./RecipeResultPage.css";

export default function RecipeResultPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { recipe, userId, title, constraints, memberInfo, chatHistory } =
    location.state || {};

  const [remainingCount, setRemainingCount] = useState(1);

  if (!recipe) {
    console.error("[RecipeResultPage] 레시피 데이터 없음");
    navigate("/home", { replace: true });
    return null;
  }

  console.log("[RecipeResultPage] 받은 레시피:", recipe);

  const handleRegenerate = () => {
    if (remainingCount > 0) {
      setRemainingCount(remainingCount - 1);

      navigate("/loading", {
        state: {
          memberInfo,
          chatHistory,
        },
      });
    }
  };

  const handleStartCooking = () => {
    navigate("/cook", {
      state: {
        recipe: {
          name: recipe.title,
          intro: recipe.intro,
          time: recipe.cook_time,
          level: recipe.level,
          servings: recipe.servings,
          ingredients: recipe.ingredients,
          steps: recipe.steps,
        },
      },
    });
  };

  return (
    <RecipeLayout steps={recipe.steps || []} currentStep={1}>
      {/* 타이틀 */}
      <div className="result-title-section">
        <p className="result-subtitle">오늘의 추천 레시피는</p>
        <h1 className="result-title">
          <span className="highlight">{recipe.title}</span> 입니다
        </h1>
      </div>

      {/* 레시피 이미지 */}
      <div className="result-image-wrapper">
        <img
          src={recipe.image_url || recipe.img_url || "/images/default-food.jpg"}
          alt={recipe.title}
          className="result-image"
          onError={(e) => {
            e.target.src = "/images/default-food.jpg";
          }}
        />

        {/* 이미지 위 정보 태그 */}
        <div className="result-image-info">
          <div className="info-badge">
            <img src="/time-icon.png" alt="시간" className="badge-icon" />
            <span>{recipe.cook_time || "15분"}</span>
          </div>
          <div className="info-badge">
            <img src="/level-icon.png" alt="난이도" className="badge-icon" />
            <span>{recipe.level || "중급"}</span>
          </div>
        </div>
      </div>

      {/* 액션 버튼들 */}
      <div className="result-actions">
        <div className="result-button-wrapper">
          <ButtonRed
            onClick={handleRegenerate}
            disabled={remainingCount === 0}
            subText={`${remainingCount}회 남음`}
          >
            다시 생성
          </ButtonRed>
        </div>
        <div className="result-button-wrapper">
          <ButtonWhite onClick={handleStartCooking}>요리 시작하기</ButtonWhite>
        </div>
      </div>
    </RecipeLayout>
  );
}
