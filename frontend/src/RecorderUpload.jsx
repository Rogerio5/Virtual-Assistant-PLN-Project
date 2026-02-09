import React, { useState, useRef } from "react";

export default function RecorderUpload() {
  const [recording, setRecording] = useState(false);
  const [response, setResponse] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream);
    mediaRecorderRef.current = mr;
    chunksRef.current = [];
    mr.ondataavailable = (e) => chunksRef.current.push(e.data);
    mr.start();
    setRecording(true);
  };

  const stopAndSend = async () => {
    const mr = mediaRecorderRef.current;
    if (!mr) return;
    mr.stop();
    setRecording(false);
    await new Promise((res) => (mr.onstop = res));
    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    const form = new FormData();
    form.append("file", blob, "recording.webm");
    form.append("user_id", "roger");
    const api = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const resp = await fetch(`${api}/assistant/process/upload`, { method: "POST", body: form });
    const data = await resp.json();
    setResponse(data);
  };

  return (
    <div>
      <button onClick={start} disabled={recording}>Start</button>
      <button onClick={stopAndSend} disabled={!recording}>Stop & Send</button>
      {response && (
        <div>
          <p><strong>Input:</strong> {response.input}</p>
          <p><strong>Response:</strong> {response.response}</p>
          {response.audio && <audio controls src={response.audio}></audio>}
        </div>
      )}
    </div>
  );
}
