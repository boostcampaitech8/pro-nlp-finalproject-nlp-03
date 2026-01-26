// src/pages/Loading/LoadingPage.jsx
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './LoadingPage.css';

export default function LoadingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { recipeTitle, memberInfo, chatHistory } = location.state || {};

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // 데이터 검증
    if (!recipeTitle || !memberInfo || !chatHistory) {
      console.error('[LoadingPage] 필수 데이터 누락');
      alert('필요한 정보가 없습니다.');
      navigate('/chat', { replace: true });
      return;
    }

    console.log('[LoadingPage] 레시피 생성 시작...');
    console.log('- 제목:', recipeTitle);
    console.log('- 가족:', memberInfo.names);
    console.log('- 대화 수:', chatHistory.length);

    // API 호출
    const generateRecipe = async () => {
      try {
        const response = await fetch(`${API_URL}/api/recipes/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipe_title: recipeTitle,
            member_info: memberInfo,
            chat_history: chatHistory.map(m => ({
              role: m.role,
              content: m.content
            }))
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('[LoadingPage] 레시피 생성 완료:', data);

        // ✅ RecipeResultPage로 이동
        navigate('/recipe-result', {
          state: {
            recipe: data.recipe,
            memberInfo: memberInfo,
            chatHistory: chatHistory
          },
          replace: true  // 뒤로가기 시 LoadingPage 건너뜀
        });

      } catch (error) {
        console.error('[LoadingPage] 레시피 생성 실패:', error);
        alert('레시피 생성에 실패했습니다.');
        navigate('/chat', { replace: true });
      }
    };

    generateRecipe();
  }, [recipeTitle, memberInfo, chatHistory, navigate, API_URL]);

  return (
    <div className="loading-page">
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <h2>레시피를 생성하고 있어요...</h2>
        <p className="recipe-title">{recipeTitle}</p>
        {memberInfo?.names && (
          <p className="loading-info">
            {memberInfo.names.join(', ')}님을 위한 맞춤 레시피
          </p>
        )}
      </div>
    </div>
  );
}