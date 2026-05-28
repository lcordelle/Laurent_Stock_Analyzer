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
  earningsPreview: (ticker: string, company_name: string, sector: string, metrics: object, earnings_dates: object[]) =>
    api.post('/ai/earnings-preview', { ticker, company_name, sector, metrics, earnings_dates }).then(r => r.data),
  catalysts: (ticker: string, company_name: string, sector: string, metrics: object) =>
    api.post('/ai/catalysts', { ticker, company_name, sector, metrics }).then(r => r.data),
  dcf: (ticker: string, company_name: string, sector: string, metrics: object) =>
    api.post('/ai/dcf', { ticker, company_name, sector, metrics }).then(r => r.data),
  comps: (ticker: string, company_name: string, sector: string, industry: string, metrics: object) =>
    api.post('/ai/comps', { ticker, company_name, sector, industry, metrics }).then(r => r.data),
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

export const advancedApi = {
  options: (ticker: string) => api.get(`/advanced/options/${ticker}`).then(r => r.data),
  insider: (ticker: string) => api.get(`/advanced/insider/${ticker}`).then(r => r.data),
  shortInterest: (ticker: string) => api.get(`/advanced/short-interest/${ticker}`).then(r => r.data),
  institutional: (ticker: string) => api.get(`/advanced/institutional/${ticker}`).then(r => r.data),
  patterns: (ticker: string) => api.get(`/advanced/patterns/${ticker}`).then(r => r.data),
  marketBreadth: () => api.get('/market-breadth').then(r => r.data),
}

export const journalApi = {
  open: () => api.get('/journal/open').then(r => r.data),
  closed: () => api.get('/journal/closed').then(r => r.data),
  summary: () => api.get('/journal/summary').then(r => r.data),
  add: (body: {
    ticker: string; direction: string; entry_date: string;
    entry_price: number; shares: number; notes?: string; tags?: string
  }) => api.post('/journal/add', body).then(r => r.data),
  close: (id: number, exit_date: string, exit_price: number) =>
    api.post(`/journal/${id}/close`, { exit_date, exit_price }).then(r => r.data),
  delete: (id: number) => api.delete(`/journal/${id}`).then(r => r.data),
}

export const alertsApi = {
  list: () => api.get('/alerts').then(r => r.data),
  add: (ticker: string, condition: string, threshold: number) =>
    api.post('/alerts/add', { ticker, condition, threshold }).then(r => r.data),
  delete: (id: string) => api.delete(`/alerts/${id}`).then(r => r.data),
  reset: (id: string) => api.post(`/alerts/${id}/reset`).then(r => r.data),
}

export const backtestApi = {
  strategies: () => api.get('/backtest/strategies').then(r => r.data),
  run: (ticker: string, strategy: string, period: string, initial_capital: number) =>
    api.post('/backtest/run', { ticker, strategy, period, initial_capital }).then(r => r.data),
}

export default api
