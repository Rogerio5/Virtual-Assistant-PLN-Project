import api from "../api/axios";

export async function login(username, password) {
  const res = await api.post("/auth/login", { username, password });
  const token = res.data.access_token;
  sessionStorage.setItem("access_token", token);
  return token;
}

export function logout() {
  sessionStorage.removeItem("access_token");
}

export function getToken() {
  return sessionStorage.getItem("access_token");
}
