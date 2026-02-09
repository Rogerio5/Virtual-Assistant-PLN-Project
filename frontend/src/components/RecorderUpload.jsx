// frontend/src/components/RecorderUpload.jsx
import React, { useState, useRef } from "react";
import api from "../services/api";

export default function RecorderUpload() {
  const [recording, setRecording] = useState(false);
  const [message, setMessage] = useState("");
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRef.current = mediaRecorder;
    chunksRef.current = [];
    mediaRecorder.ondataavailable = e => chunksRef.current.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      const file = new File([blob], "record.webm", { type: "audio/webm" });
      setMessage("Enviando...");
      try {
        const form = new FormData();
        form.append("file", file, file.name);
        const res = await api.post("/voice-assistant/transcribe-and-respond", form, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        const { transcript, reply_text, audio_url } = res.data;
        setMessage(`Transcrição: ${transcript}\nResposta: ${reply_text}`);
        if (audio_url) {
          const audioRes = await fetch(audio_url, { credentials: "include" });
          const blob = await audioRes.blob();
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audio.play();
        }
      } catch (err) {
        setMessage("Erro: " + (err?.response?.data?.detail || err.message));
      }
    };
    mediaRecorder.start();
    setRecording(true);
  }

  function stop() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  return (
    <div>
      <button onClick={recording ? stop : start}>{recording ? "Parar" : "Gravar"}</button>
      <pre>{message}</pre>
    </div>
  );
}
