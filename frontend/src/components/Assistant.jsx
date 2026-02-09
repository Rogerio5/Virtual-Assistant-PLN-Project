import React, { useState } from "react";
import "./Assistant.css"; // importa o CSS

function Assistant() {
  const [inputText, setInputText] = useState("");
  const [responseText, setResponseText] = useState("");
  const [actions, setActions] = useState({});

  const handleSendCommand = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/assistant/assistant/process", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text_input: inputText })
      });

      const data = await response.json();
      setResponseText(data.response || "Sem resposta.");
      setActions(data.actions || {});
    } catch (error) {
      console.error("Erro ao enviar comando:", error);
      setResponseText("Erro ao processar o comando.");
    }
  };

  const handleSpeak = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Seu navegador não suporta reconhecimento de voz.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "pt-BR";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Erro no reconhecimento de voz:", event.error);
    };
  };

  return (
    <div className="assistant-container">
      <h1 className="assistant-title">Meu Assistente de Voz</h1>

      <input
        type="text"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="Digite seu comando..."
        className="assistant-input"
      />
      <div className="assistant-buttons">
        <button onClick={handleSendCommand} className="btn neon-btn">Enviar comando</button>
        <button onClick={handleSpeak} className="btn mic-btn">Falar 🎤</button>
      </div>

      {responseText && (
        <div className="assistant-response">
          <h3>Resposta do Assistente:</h3>
          <p>{responseText}</p>
        </div>
      )}

      {Object.keys(actions).length > 0 && (
        <div className="assistant-actions">
          <h4>Ações sugeridas:</h4>
          <ul>
            {Object.entries(actions).map(([key, url]) => (
              <li key={key}>
                <a href={url} target="_blank" rel="noopener noreferrer">
                  {key}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default Assistant;
