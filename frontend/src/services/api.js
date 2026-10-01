import axios from "axios"

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000",
})

// Global error interceptor
API.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err?.response?.data?.message || err.message || "Unknown error"
    const error = new Error(msg)
    error.response = err.response
    return Promise.reject(error)
  }
)

export default API