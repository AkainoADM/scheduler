import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/", // в dev: Vite proxy
  headers: { "Content-Type": "application/json" },
  timeout: 20000,
});

export default api;
