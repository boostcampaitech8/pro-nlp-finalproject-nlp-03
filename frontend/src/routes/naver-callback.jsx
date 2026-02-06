// src/routes/naver-callback.jsx
import { createFileRoute } from "@tanstack/react-router";
import NaverCallbackPage from "@/pages/Auth/NaverCallbackPage";

export const Route = createFileRoute("/naver-callback")({
  component: NaverCallbackPage,
});
