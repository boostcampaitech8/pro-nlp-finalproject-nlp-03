// src/app/router.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";

import SplashPage from "@/pages/Splash/SplashPage";
import HomePage from "@/pages/Home/HomePage";
import ChatPage from "@/pages/Chat/ChatPage";
import LoadingPage from "@/pages/Loading/LoadingPage";
import RecipeResultPage from "@/pages/Recipes/RecipeResultPage";
// import RecipeDetailPage from "@/pages/Recipes/RecipeDetailPage";
import CookModePage from "@/pages/Cook/CookModePage";
import MyRecipesPage from "@/pages/MyRecipes/MyRecipesPage";
// import CookCompletePage from "@/pages/Cook/CookCompletePage";

import FixedLayout from "@/layouts/FixedLayout";
import ScrollLayout from "@/layouts/ScrollLayout";
import MobileLayout from "@/layouts/MobileLayout";

export default function Router() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Splash - 고정 화면 */}
        <Route
          path="/"
          element={
            <FixedLayout>
              <SplashPage />
            </FixedLayout>
          }
        />

        {/* Home - 스크롤 화면 */}
        <Route
          path="/home"
          element={
            <ScrollLayout>
              <HomePage />
            </ScrollLayout>
          }
        />

        {/* Chat - 고정 화면 (입력창 고정) */}
        <Route
          path="/chat"
          element={
            <FixedLayout>
              <ChatPage />
            </FixedLayout>
          }
        />

        {/* Loading - 고정 화면 (로딩 애니메이션) */}
        <Route
          path="/loading"
          element={
            <FixedLayout>
              <LoadingPage />
            </FixedLayout>
          }
        />

        {/* Recipe Result - 고정 화면 (모달형) */}
        <Route
          path="/recipe-result"
          element={
            <FixedLayout>
              <RecipeResultPage />
            </FixedLayout>
          }
        />

        {/* Cook Mode - 고정 화면 (음성 컨트롤) */}
        <Route
          path="/cook"
          element={
            <FixedLayout>
              <CookModePage />
            </FixedLayout>
          }
        />

        {/* 마이 레시피 - 고정 화면 (내부 스크롤) */}
        <Route
          path="/recipes/my"
          element={
            <FixedLayout>
              <MyRecipesPage />
            </FixedLayout>
          }
        />

        {/* 전체 레시피 - 스크롤 화면 */}
        <Route
          path="/recipes"
          element={
            <ScrollLayout>
              {/* TODO: AllRecipesPage 컴포넌트 생성 */}
              <div>전체 레시피 페이지</div>
            </ScrollLayout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
