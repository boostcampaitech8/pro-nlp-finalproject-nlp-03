"use client";

import { useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import RecipeLayout from "@/layouts/RecipeLayout";
import "./CookCompletePage.css";

export default function CookCompletePage() {
  const navigate = useNavigate();
  const location = useLocation();

  // 전달받은 데이터 (나중에 연결)
  const recipe = location.state?.recipe || {
    name: "바지락양념칼국수",
    image: "/images/default-food.jpg",
  };
  const elapsedTime = location.state?.elapsedTime || 874; // 00:14:34 = 874초

  const [rating, setRating] = useState(2); // 기본 별점 2개

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const API_URL = import.meta.env.VITE_API_URL || "http://211.188.62.72:8080";

  // 로그인된 회원 정보
  const memberStr = typeof window !== 'undefined' ? localStorage.getItem("member") : null;
  const member = memberStr ? JSON.parse(memberStr) : null;
  const memberId = member?.id || 0;

  const handleSaveRecipe = async () => {
    try {
      const response = await fetch(`${API_URL}/api/recipe/save-my-recipe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          member_id: memberId,
          recipe: recipe,
          constraints: {},
          rating: rating,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert("담기 완료!");  // 알림 표시
        console.log("레시피 저장 성공:", data);
        navigate("/home");
      } else {
        alert("저장에 실패했습니다. 다시 시도해주세요.");
      }
    } catch (error) {
      console.error("레시피 저장 에러:", error);
      alert("저장 중 오류가 발생했습니다.");
    }
  };

  const handleSkip = () => {
    navigate("/home");
  };

  return (
    <RecipeLayout steps={[]} showBottomSheet={false}>
      {/* 타이틀 섹션 */}
      <div className="complete-title-section">
        <h1 className="complete-title">오늘의 요리가 끝났어요</h1>
        <p className="complete-subtitle">레시피를 전달드릴게요</p>
      </div>

      {/* 레시피 정보 카드 */}
      <div className="complete-recipe-card">
        <h2 className="complete-recipe-name">{recipe.name}</h2>
        <p className="complete-recipe-time">총 소요시간 {formatTime(elapsedTime)}</p>
      </div>

      {/* 음식 이미지 */}
      <div className="complete-food-image-wrapper">
        <img
          src={recipe.image || "/images/default-food.jpg"}
          alt={recipe.name}
          className="complete-food-image"
          onError={(e) => {
            e.target.src = "https://via.placeholder.com/238x289?text=Food";
          }}
        />
      </div>

      {/* 별점 */}
      <div className="complete-rating">
        {[1, 2, 3].map((star) => (
          <button
            key={star}
            className={`star-btn ${star <= rating ? "filled" : ""}`}
            onClick={() => setRating(star)}
          >
            {star <= rating ? "★" : "☆"}
          </button>
        ))}
      </div>

      {/* 버튼 영역 */}
      <div className="complete-buttons">
        <button className="btn-save" onClick={handleSaveRecipe}>
          마이레시피에<br />담을래요
        </button>
        <button className="btn-skip" onClick={handleSkip}>
          안담을래요
        </button>
      </div>
    </RecipeLayout>
  );
}
