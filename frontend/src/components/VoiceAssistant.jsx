import React, { useEffect, useRef, useState } from "react";
import "./VoiceAssistant.css";
import avatar from "../assets/avatar-olhos-verdes.png";

/**
 * VoiceAssistant.jsx (com tradução automática da UI)
 * - Suporta pt, en, es, fr, de, ar, ru
 * - Atualiza lang/dir do documento para acessibilidade/RTL
 * - Envia `lang` ao backend em JSON e FormData
 *
 * Ajuste as URLs do fetch se seu backend estiver em outro host/porta.
 */

const recognitionLangMap = {
  pt: "pt-BR",
  en: "en-US",
  es: "es-ES",
  fr: "fr-FR",
  de: "de-DE",
  ar: "ar-SA",
  ru: "ru-RU"
};

/* Traduções da interface */
const translations = {
  pt: {
    title: "Meu Assistente de Voz",
    placeholder: "Digite seu comando",
    sendText: "Enviar comando",
    speak: "Falar",
    viewHistory: "Ver conversa completa",
    feedbackTitle: "Enviar Feedback",
    feedbackPlaceholder: "Digite seu feedback...",
    ratingLabel: "Avaliação:",
    sendFeedback: "Enviar Feedback",
    recording: "🎙️ Gravando...",
    speakBtn: "🎙️ Falar",
    responseTitle: "Resposta do Assistente:",
    uploading: "⏳ Enviando áudio...",
    uploaded: "✅ Áudio enviado",
    uploadError: "❌ Erro ao enviar áudio",
    micNotSupported: "Seu navegador não suporta gravação de áudio.",
    recordingNotSupported: "Gravação não suportada neste navegador.",
    micAccessError: "Não foi possível acessar o microfone. Verifique permissões e dispositivo.",
    recognitionNotSupported: "Reconhecimento de voz não suportado neste navegador.",
    feedbackEmpty: "⚠️ Escreva uma mensagem antes de enviar.",
    feedbackSent: "Feedback enviado com sucesso!",
    feedbackError: "⚠️ Não foi possível enviar o feedback.",
    assistantNotAvailable: "Sem resposta."
  },
  en: {
    title: "My Voice Assistant",
    placeholder: "Type your command",
    sendText: "Send command",
    speak: "Speak",
    viewHistory: "View full conversation",
    feedbackTitle: "Send Feedback",
    feedbackPlaceholder: "Type your feedback...",
    ratingLabel: "Rating:",
    sendFeedback: "Send Feedback",
    recording: "🎙️ Recording...",
    speakBtn: "🎙️ Speak",
    responseTitle: "Assistant Response:",
    uploading: "⏳ Uploading audio...",
    uploaded: "✅ Audio uploaded",
    uploadError: "❌ Error uploading audio",
    micNotSupported: "Your browser does not support audio recording.",
    recordingNotSupported: "Recording not supported in this browser.",
    micAccessError: "Could not access the microphone. Check permissions and device.",
    recognitionNotSupported: "Voice recognition not supported in this browser.",
    feedbackEmpty: "⚠️ Write a message before sending.",
    feedbackSent: "Feedback sent successfully!",
    feedbackError: "⚠️ Could not send feedback.",
    assistantNotAvailable: "No response."
  },
  es: {
    title: "Mi Asistente de Voz",
    placeholder: "Escribe tu comando",
    sendText: "Enviar comando",
    speak: "Hablar",
    viewHistory: "Ver conversación completa",
    feedbackTitle: "Enviar Comentarios",
    feedbackPlaceholder: "Escribe tus comentarios...",
    ratingLabel: "Calificación:",
    sendFeedback: "Enviar Comentarios",
    recording: "🎙️ Grabando...",
    speakBtn: "🎙️ Hablar",
    responseTitle: "Respuesta del Asistente:",
    uploading: "⏳ Enviando audio...",
    uploaded: "✅ Audio enviado",
    uploadError: "❌ Error al enviar audio",
    micNotSupported: "Tu navegador no admite grabación de audio.",
    recordingNotSupported: "Grabación no compatible en este navegador.",
    micAccessError: "No se pudo acceder al micrófono. Verifica permisos y dispositivo.",
    recognitionNotSupported: "Reconocimiento de voz no compatible en este navegador.",
    feedbackEmpty: "⚠️ Escribe un mensaje antes de enviar.",
    feedbackSent: "Comentarios enviados con éxito!",
    feedbackError: "⚠️ No se pudieron enviar los comentarios.",
    assistantNotAvailable: "Sin respuesta."
  },
  fr: {
    title: "Mon Assistant Vocal",
    placeholder: "Tapez votre commande",
    sendText: "Envoyer commande",
    speak: "Parler",
    viewHistory: "Voir la conversation complète",
    feedbackTitle: "Envoyer un retour",
    feedbackPlaceholder: "Tapez votre retour...",
    ratingLabel: "Évaluation:",
    sendFeedback: "Envoyer",
    recording: "🎙️ Enregistrement...",
    speakBtn: "🎙️ Parler",
    responseTitle: "Réponse de l'assistant:",
    uploading: "⏳ Envoi de l'audio...",
    uploaded: "✅ Audio envoyé",
    uploadError: "❌ Erreur lors de l'envoi de l'audio",
    micNotSupported: "Votre navigateur ne prend pas en charge l'enregistrement audio.",
    recordingNotSupported: "Enregistrement non pris en charge dans ce navigateur.",
    micAccessError: "Impossible d'accéder au microphone. Vérifiez les autorisations et l'appareil.",
    recognitionNotSupported: "Reconnaissance vocale non prise en charge dans ce navigateur.",
    feedbackEmpty: "⚠️ Écrivez un message avant d'envoyer.",
    feedbackSent: "Retour envoyé avec succès!",
    feedbackError: "⚠️ Impossible d'envoyer le retour.",
    assistantNotAvailable: "Pas de réponse."
  },
  de: {
    title: "Mein Sprachassistent",
    placeholder: "Geben Sie Ihren Befehl ein",
    sendText: "Befehl senden",
    speak: "Sprechen",
    viewHistory: "Gespräch anzeigen",
    feedbackTitle: "Feedback senden",
    feedbackPlaceholder: "Geben Sie Ihr Feedback ein...",
    ratingLabel: "Bewertung:",
    sendFeedback: "Feedback senden",
    recording: "🎙️ Aufnahme...",
    speakBtn: "🎙️ Sprechen",
    responseTitle: "Antwort des Assistenten:",
    uploading: "⏳ Audio wird hochgeladen...",
    uploaded: "✅ Audio hochgeladen",
    uploadError: "❌ Fehler beim Hochladen des Audios",
    micNotSupported: "Ihr Browser unterstützt keine Audioaufnahme.",
    recordingNotSupported: "Aufnahme in diesem Browser nicht unterstützt.",
    micAccessError: "Mikrofon konnte nicht zugegriffen werden. Überprüfen Sie Berechtigungen und Gerät.",
    recognitionNotSupported: "Spracherkennung in diesem Browser nicht unterstützt.",
    feedbackEmpty: "⚠️ Schreiben Sie eine Nachricht, bevor Sie senden.",
    feedbackSent: "Feedback erfolgreich gesendet!",
    feedbackError: "⚠️ Feedback konnte nicht gesendet werden.",
    assistantNotAvailable: "Keine Antwort."
  },
  ar: {
    title: "مساعدي الصوتي",
    placeholder: "اكتب أمرك",
    sendText: "إرسال الأمر",
    speak: "تحدث",
    viewHistory: "عرض المحادثة كاملة",
    feedbackTitle: "إرسال ملاحظات",
    feedbackPlaceholder: "اكتب ملاحظاتك...",
    ratingLabel: "التقييم:",
    sendFeedback: "إرسال الملاحظات",
    recording: "🎙️ جاري التسجيل...",
    speakBtn: "🎙️ تحدث",
    responseTitle: "رد المساعد:",
    uploading: "⏳ جارٍ إرسال الصوت...",
    uploaded: "✅ تم إرسال الصوت",
    uploadError: "❌ خطأ في إرسال الصوت",
    micNotSupported: "المتصفح لا يدعم تسجيل الصوت.",
    recordingNotSupported: "التسجيل غير مدعوم في هذا المتصفح.",
    micAccessError: "تعذر الوصول إلى الميكروفون. تحقق من الأذونات والجهاز.",
    recognitionNotSupported: "التعرف على الصوت غير مدعوم في هذا المتصفح.",
    feedbackEmpty: "⚠️ اكتب رسالة قبل الإرسال.",
    feedbackSent: "تم إرسال الملاحظات بنجاح!",
    feedbackError: "⚠️ تعذر إرسال الملاحظات.",
    assistantNotAvailable: "لا توجد استجابة."
  },
  ru: {
    title: "Мой голосовой помощник",
    placeholder: "Введите команду",
    sendText: "Отправить команду",
    speak: "Говорить",
    viewHistory: "Просмотреть всю беседу",
    feedbackTitle: "Отправить отзыв",
    feedbackPlaceholder: "Введите ваш отзыв...",
    ratingLabel: "Оценка:",
    sendFeedback: "Отправить отзыв",
    recording: "🎙️ Запись...",
    speakBtn: "🎙️ Говорить",
    responseTitle: "Ответ помощника:",
    uploading: "⏳ Отправка аудио...",
    uploaded: "✅ Аудио отправлено",
    uploadError: "❌ Ошибка при отправке аудио",
    micNotSupported: "Ваш браузер не поддерживает запись аудио.",
    recordingNotSupported: "Запись не поддерживается в этом браузере.",
    micAccessError: "Не удалось получить доступ к микрофону. Проверьте разрешения и устройство.",
    recognitionNotSupported: "Распознавание голоса не поддерживается в этом браузере.",
    feedbackEmpty: "⚠️ Напишите сообщение перед отправкой.",
    feedbackSent: "Отзыв успешно отправлен!",
    feedbackError: "⚠️ Не удалось отправить отзыв.",
    assistantNotAvailable: "Нет ответа."
  }
};

/* Helper para obter tradução */
const t = (lang, key) => {
  return (translations[lang] && translations[lang][key]) || translations["en"][key] || key;
};

const VoiceAssistant = () => {
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [actions, setActions] = useState([]);
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem("voiceAssistantHistory");
    return saved ? JSON.parse(saved) : [];
  });

  const [listening, setListening] = useState(false);
  const [theme, setTheme] = useState("dark-theme");
  const [showWelcome, setShowWelcome] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackRating, setFeedbackRating] = useState(0);
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");

  const [language, setLanguage] = useState("pt");

  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Atualiza lang/dir do documento e reinicializa recognition quando muda idioma
  useEffect(() => {
    // define lang no html para acessibilidade
    document.documentElement.lang = language === "pt" ? "pt-BR" : language;
    // define direção para árabe (rtl)
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      recognitionRef.current = null;
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = recognitionLangMap[language] || language;
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (ev) => {
      console.error("SpeechRecognition error:", ev);
      setListening(false);
    };

    recognition.onresult = (event) => {
      const text = event?.results?.[0]?.[0]?.transcript || "";
      if (text) {
        setCommand(text);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.onstart = null;
        recognition.onend = null;
        recognition.onerror = null;
        recognition.onresult = null;
      } catch (cleanupError) {
        console.error("Erro no cleanup do recognition:", cleanupError);
      }
    };
  }, [language]);

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("voiceAssistantHistory", JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    const timer = setTimeout(() => setShowWelcome(false), 6000);
    return () => clearTimeout(timer);
  }, []);

  const handleSendCommand = async () => {
    const text = command.trim();
    if (!text) return;
    setHistory((prev) => [...prev, { role: "user", text }]);
    setResponse("");
    setAudioUrl("");
    try {
      const res = await fetch("http://127.0.0.1:8000/assistant/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text_input: text, lang: language })
      });
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} - ${txt}`);
      }
      const data = await res.json();
      setResponse(data.response || t(language, "assistantNotAvailable"));
      setAudioUrl(data.audio || "");
      setActions(Array.isArray(data.actions) ? data.actions : Object.entries(data.actions || {}));
      setHistory((prev) => [...prev, { role: "assistant", text: data.response || t(language, "assistantNotAvailable") }]);
    } catch (error) {
      console.error("Erro ao processar comando:", error);
      setResponse(t(language, "assistantNotAvailable"));
      setHistory((prev) => [...prev, { role: "error", text: "Erro de conexão com o servidor." }]);
    } finally {
      setCommand("");
    }
  };

  const startLocalRecognition = () => {
    const recognition = recognitionRef.current;
    if (!recognition) {
      setResponse(t(language, "recognitionNotSupported"));
      return;
    }
    try {
      recognition.start();
    } catch (error) {
      console.error("Erro ao iniciar reconhecimento:", error);
      setResponse(t(language, "recognitionNotSupported"));
    }
  };

  const startRecording = async () => {
    audioChunksRef.current = [];
    setUploadStatus("idle");
    setResponse("");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setResponse(t(language, "micNotSupported"));
      return;
    }
    if (typeof MediaRecorder === "undefined") {
      setResponse(t(language, "recordingNotSupported"));
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = { mimeType: "audio/webm;codecs=opus" };

      let recorder;
      try {
        recorder = new MediaRecorder(stream, options);
      } catch (error) {
        console.error("MediaRecorder init com options falhou:", error);
        try {
          recorder = new MediaRecorder(stream);
        } catch (fallbackError) {
          console.error("Fallback MediaRecorder também falhou:", fallbackError);
          setResponse(t(language, "recordingNotSupported"));
          return;
        }
      }

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) audioChunksRef.current.push(ev.data);
      };

      recorder.onstart = () => {
        setListening(true);
        setUploadStatus("idle");
        console.log("Gravação iniciada");
      };

      recorder.onerror = (ev) => {
        console.error("MediaRecorder error:", ev);
        setResponse(t(language, "uploadError"));
        setListening(false);
      };

      recorder.onstop = async () => {
        setListening(false);
        const blob = new Blob(audioChunksRef.current, { type: audioChunksRef.current[0]?.type || "audio/webm" });
        const localUrl = URL.createObjectURL(blob);
        setAudioUrl(localUrl);

        const formData = new FormData();
        formData.append("file", blob, "recording.webm");
        formData.append("lang", language);

        setUploadStatus("uploading");
        try {
          const res = await fetch("http://127.0.0.1:8000/assistant/process/upload", {
            method: "POST",
            body: formData
          });
          if (!res.ok) {
            const txt = await res.text().catch(() => "");
            throw new Error(`HTTP ${res.status} - ${txt}`);
          }
          const data = await res.json();

          if (data.audio && typeof data.audio === "string") {
            setAudioUrl(data.audio);
          }

          if (data.response) {
            setResponse(data.response);
            setHistory((prev) => [...prev, { role: "assistant", text: data.response }]);
          }
          if (data.input) {
            setHistory((prev) => [...prev, { role: "user", text: data.input }]);
          }
          if (data.actions) {
            setActions(Array.isArray(data.actions) ? data.actions : Object.entries(data.actions || {}));
          }

          setUploadStatus("done");
        } catch (error) {
          console.error("Erro ao enviar/processar áudio:", error);
          setUploadStatus("error");
          setResponse(t(language, "uploadError"));
          setHistory((prev) => [...prev, { role: "error", text: "Erro de conexão com o servidor." }]);
        }
      };

      recorder.start();
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
          try {
            mediaRecorderRef.current.stop();
          } catch (stopError) {
            console.error("Erro ao parar MediaRecorder:", stopError);
          }
        }
      }, 5000);
    } catch (error) {
      console.error("Erro ao acessar microfone:", error);
      setResponse(t(language, "micAccessError"));
    }
  };

  const handleSendFeedback = async () => {
    if (!feedbackMessage.trim()) {
      setFeedbackStatus(t(language, "feedbackEmpty"));
      return;
    }
    try {
      const res = await fetch("http://127.0.0.1:8000/feedback/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user: "Rogerio",
          message: feedbackMessage,
          rating: feedbackRating,
          lang: language
        })
      });
      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status} - ${txt}`);
      }
      const data = await res.json();
      setFeedbackStatus(data.status || t(language, "feedbackSent"));
      setFeedbackMessage("");
      setFeedbackRating(0);
    } catch (error) {
      console.error("Erro ao enviar feedback:", error);
      setFeedbackStatus(t(language, "feedbackError"));
    }
  };

  return (
    <div className="container">
      <div className="top-bar">
        <div className="left-controls">
          <div className="theme-toggle">
            <button
              className="theme-button"
              aria-label="Alternar tema claro/escuro"
              onClick={() => setTheme(theme === "dark-theme" ? "light-theme" : "dark-theme")}
            >
              {theme === "dark-theme" ? "🌞" : "🌙"}
            </button>
          </div>
        </div>

        <div className="right-controls">
          <label htmlFor="language-select" className="language-label">Idioma:</label>
          <select
            id="language-select"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="language-select"
            aria-label="Selecionar idioma"
          >
            <option value="pt">Português BR 🇧🇷</option>
            <option value="en">English US 🇺🇸</option>
            <option value="es">Español ES 🇪🇸</option>
            <option value="fr">Français FR 🇫🇷</option>
            <option value="de">Deutsch DE 🇩🇪</option>
            <option value="ar">العربية AR 🇸🇦</option>
            <option value="ru">Русский RU 🇷🇺</option>
          </select>
        </div>
      </div>

       <h1 className="main-title">{t(language, "title")}</h1> 

      {showWelcome && <div className="welcome-bubble">👋 {t(language, "title")}</div>}

      <div className={`avatar enlarged ${listening ? "listening" : ""} ${response ? "speaking" : ""}`}>
        <img src={avatar} alt="Avatar do assistente" className="avatar-img blink smile" />
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder={t(language, "placeholder")}
          aria-label={t(language, "placeholder")}
          value={command}
          onChange={(e) => setCommand(e.target.value)}
        />
        <button className="search-button" aria-label={t(language, "sendText")} onClick={handleSendCommand}>
          🔍
        </button>
      </div>

      <div className="controls">
        <button className="send-button" aria-label={t(language, "sendText")} onClick={handleSendCommand}>
          {t(language, "sendText")}
        </button>
        <button
          className="mic-button"
          aria-label={t(language, "speak")}
          onClick={() => {
            if (recognitionRef.current) startLocalRecognition();
            else startRecording();
          }}
        >
          {listening ? t(language, "recording") : t(language, "speakBtn")}
        </button>
      </div>

      <div className="status-line">
        {uploadStatus === "uploading" && <span>{t(language, "uploading")}</span>}
        {uploadStatus === "done" && <span>{t(language, "uploaded")}</span>}
        {uploadStatus === "error" && <span>{t(language, "uploadError")}</span>}
      </div>

      {response && (
        <div className={`response-area ${response.includes("⚠️") ? "error" : ""}`}>
          <h3>{t(language, "responseTitle")}</h3>
          <p>{response}</p>
        </div>
      )}

      {audioUrl && (
        <div className="audio-area">
          <audio key={audioUrl} controls src={audioUrl} aria-label="Áudio da resposta do assistente" />
        </div>
      )}

      {actions && actions.length > 0 && (
        <div className="links-area">
          <h4>{t(language, "viewHistory")}</h4>
          <ul>
            {actions.map((item, i) => {
              if (Array.isArray(item) && item.length >= 2) {
                const [key, url] = item;
                return (
                  <li key={i}>
                    <a href={url} target="_blank" rel="noopener noreferrer">
                      {key}
                    </a>
                  </li>
                );
              }
              if (item && typeof item === "object") {
                const key = item.label || item.title || item.name || `Action ${i + 1}`;
                const url = item.url || item.href || "#";
                return (
                  <li key={i}>
                    <a href={url} target="_blank" rel="noopener noreferrer">
                      {key}
                    </a>
                  </li>
                );
              }
              return null;
            })}
          </ul>
        </div>
      )}

      <button className="history-button" onClick={() => setShowHistory(!showHistory)}>
        {showHistory ? "❌ " + t(language, "viewHistory") : "📜 " + t(language, "viewHistory")}
      </button>

      <div className={`history-panel ${showHistory ? "open" : ""}`}>
        <h3>{t(language, "viewHistory")}</h3>
        <div className="history-content">
          {history.map((msg, i) => (
            <div key={i} className={`bubble ${msg.role}`}>
              {msg.text}
            </div>
          ))}
        </div>
      </div>

      <div className="feedback-area">
        <h4>{t(language, "feedbackTitle")}</h4>
        <textarea
          placeholder={t(language, "feedbackPlaceholder")}
          value={feedbackMessage}
          onChange={(e) => setFeedbackMessage(e.target.value)}
        />
        <div className="feedback-controls">
          <label>{t(language, "ratingLabel")}</label>
          <select value={feedbackRating} onChange={(e) => setFeedbackRating(parseInt(e.target.value, 10))}>
            <option value={0}>Nenhuma</option>
            <option value={1}>1 ⭐</option>
            <option value={2}>2 ⭐⭐</option>
            <option value={3}>3 ⭐⭐⭐</option>
            <option value={4}>4 ⭐⭐⭐⭐</option>
            <option value={5}>5 ⭐⭐⭐⭐⭐</option>
          </select>
          <button onClick={handleSendFeedback}>{t(language, "sendFeedback")}</button>
        </div>
        {feedbackStatus && <p className="feedback-status">{feedbackStatus}</p>}
      </div>
    </div>
  );
};

export default VoiceAssistant;
