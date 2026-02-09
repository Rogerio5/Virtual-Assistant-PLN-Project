import React, { useEffect, useState } from "react";
import api from "../api/axios";

export default function ProtectedData() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get("/protected/data")
      .then(res => setData(res.data))
      .catch(err => setError(err.response?.data || err.message));
  }, []);

  if (error) return <div>Erro: {JSON.stringify(error)}</div>;
  if (!data) return <div>Carregando...</div>;
  return (
    <div style={{ padding: 16 }}>
      <h3>Rota protegida</h3>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
