// src/pages/Loading/LoadingPage.jsx
import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./LoadingPage.css";

export default function LoadingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const { memberInfo, chatHistory, sessionId, isRegeneration } =
    location.state || {};

  const API_URL = import.meta.env.VITE_API_URL || "http://211.188.62.72:8080";

  useEffect(() => {
    const generateRecipe = async () => {
      if (!sessionId) {
        alert("세션 정보가 없습니다.");
        navigate("/chat");
        return;
      }

      try {
        console.log("[LoadingPage] 레시피 생성 요청:", sessionId);

        const response = await fetch(
          `${API_URL}/api/recipe/generate-from-chat?session_id=${sessionId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          },
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error("[LoadingPage] 에러 응답:", errorData);
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("[LoadingPage] 레시피 생성 완료:", data);

        const imageUrl = data.recipe?.image || data.recipe?.img_url || "";

        console.log("[LoadingPage] 이미지 URL:", imageUrl);

        // RecipeResultPage로 이동
        navigate("/recipe-result", {
          state: {
            recipe: data.recipe,
            userId: data.user_id,
            title: data.title,
            constraints: data.constraints,
            sessionId: sessionId,
            memberInfo: memberInfo,
            chatHistory: chatHistory,
            imageUrl: imageUrl,
            remainingCount: isRegeneration ? 0 : 1,
          },
          replace: true,
        });
      } catch (error) {
        console.error("[LoadingPage] 레시피 생성 실패:", error);
        alert("레시피 생성에 실패했습니다. 다시 시도해주세요.");
        navigate("/chat", { replace: true });
      }
    };

    generateRecipe();
  }, [API_URL, sessionId, memberInfo, chatHistory, isRegeneration, navigate]);

  return (
    <div className="loading-page">
      <div className="loading-content">
        <div className="loading-spinner"></div>
        <h2>맞춤 레시피를 생성하고 있어요</h2>
        <p>잠시만 기다려주세요...</p>
      </div>
    </div>
  );
}
