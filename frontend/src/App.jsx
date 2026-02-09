import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import VoiceAssistant from "./components/VoiceAssistant";
import ProtectedData from "./components/ProtectedData";
import Login from "./components/Login";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<VoiceAssistant />} />
        <Route path="/login" element={<Login />} />
        <Route path="/protected" element={<ProtectedData />} />
      </Routes>
    </BrowserRouter>
  );
}
