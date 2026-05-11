import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }
  return Promise.reject(err)
})

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }).then(r => r.data),
}

export const stockApi = {
  analyze: (ticker: string, period = '1y') =>
    api.post('/analyze', { ticker, period }).then(r => r.data),
  batch: (tickers: string[], period = '1y') =>
    api.post('/batch', { tickers, period }).then(r => r.data),
  screen: (tickers: string[], filters: Record<string, number>) =>
    api.post('/screen', { tickers, ...filters }).then(r => r.data),
}

export const opportunitiesApi = {
  get: () => api.get('/opportunities').then(r => r.data),
  refresh: () => api.post('/opportunities/refresh').then(r => r.data),
}

export const marketPulseApi = {
  get: () => api.get('/market-pulse').then(r => r.data),
}

export const portfolioApi = {
  analyze: (text: string) =>
    api.post('/portfolio/analyze', { text }).then(r => r.data),
  risk: (positions: { ticker: string; shares: number; entry_price: number }[]) =>
    api.post('/portfolio/risk', { positions }).then(r => r.data),
}

export const aiApi = {
  research: (ticker: string, question: string, context: object) =>
    api.post('/ai/research', { ticker, question, context }).then(r => r.data),
  analystReport: (ticker: string, company_name: string, sector: string, metrics: object, score: object) =>
    api.post('/ai/analyst-report', { ticker, company_name, sector, metrics, score }).then(r => r.data),
}

export const gradesApi = {
  factors: (ticker: string, sector: string) =>
    api.get('/grades/factors', { params: { ticker, sector } }).then(r => r.data),
  dividend: (ticker: string, sector: string) =>
    api.get('/grades/dividend', { params: { ticker, sector } }).then(r => r.data),
  earnings: (ticker: string) =>
    api.get('/grades/earnings', { params: { ticker } }).then(r => r.data),
}

export const watchlistApi = {
  signals: (tickers: string[]) =>
    api.post('/watchlist/signals', { tickers }).then(r => r.data),
}

export const pennyStocksApi = {
  get: () => api.get('/penny-stocks').then(r => r.data),
  refresh: () => api.post('/penny-stocks/refresh').then(r => r.data),
}

export const aiPredictorApi = {
  predict: (ticker: string) => api.get(`/ai-predictor/${ticker}`).then(r => r.data),
}

export default api
