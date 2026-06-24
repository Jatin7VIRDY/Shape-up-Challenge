import axios from "axios"

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000",
})

// Global error interceptor
API.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err?.response?.data?.message || err.message || "Unknown error"
    return Promise.reject(new Error(msg))
  }
)

export default API