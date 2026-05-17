import { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AuthContext = createContext(null)


export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token') || null)
  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem('user') || 'null')
  )
  const [loading, setLoading] = useState(false)

  const login = async (email, password) => {
  setLoading(true)

  try {
    const res = await axios.post(
      `${API}/auth/login`,
      {
        email: email,
        password: password
      },
      {
        headers: {
          "Content-Type": "application/json"
        }
      }
    )

    const t = res.data.access_token

    const me = await axios.get(`${API}/auth/me`, {
      headers: {
        Authorization: `Bearer ${t}`
      }
    })

    localStorage.setItem("token", t)
    localStorage.setItem("user", JSON.stringify(me.data))

    setToken(t)
    setUser(me.data)

    setLoading(false)
    return { success: true }

  } catch (e) {
    setLoading(false)
    return {
      success: false,
      error: e.response?.data?.detail || "Login failed"
    }
  }
}

  const logout = () => {
    localStorage.clear()
    setToken(null)
    setUser(null)
  }

  const authHeaders = () => ({ Authorization: `Bearer ${token}` })

  const apiGet = async (url, params = {}) => {
    try {
      const res = await axios.get(`${API}${url}`,
        { headers: authHeaders(), params })
      return res.data
    } catch (e) {
      if (e.response?.status === 401) logout()
      return null
    }
  }

  const apiPost = async (url, data = {}) => {
    try {
      const res = await axios.post(`${API}${url}`, data,
        { headers: authHeaders() })
      return { data: res.data, status: res.status }
    } catch (e) {
      if (e.response?.status === 401) logout()
      return { data: e.response?.data, status: e.response?.status }
    }
  }

  const apiPatch = async (url, data = {}) => {
    try {
      const res = await axios.patch(`${API}${url}`, data,
        { headers: authHeaders() })
      return { data: res.data, status: res.status }
    } catch (e) {
      return { data: e.response?.data, status: e.response?.status }
    }
  }

  const apiDelete = async (url) => {
    try {
      const res = await axios.delete(`${API}${url}`,
        { headers: authHeaders() })
      return { data: res.data, status: res.status }
    } catch (e) {
      return { data: e.response?.data, status: e.response?.status }
    }
  }

  return (
    <AuthContext.Provider value={{
      token, user, loading, login, logout,
      authHeaders, apiGet, apiPost, apiPatch, apiDelete
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

