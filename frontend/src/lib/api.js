import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
    baseURL: `${API_BASE}/api/v1`,
    headers: { 'Content-Type': 'application/json' },
    timeout: 30000,
})

// Global Error Interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (!error.response) {
            console.error('Network/Server error or CORS mismatch', error)
        } else if (error.response.status >= 500) {
            console.error('Server encountered an error:', error.response.data)
        }
        return Promise.reject(error)
    }
)

// ── Dashboard ──────────────────────────────────────────────────────────────
export const fetchStats = () => api.get('/dashboard/stats')
export const fetchHealth = () => api.get('/dashboard/health')
export const fetchUploadChart = () => api.get('/dashboard/upload-chart')
export const fetchPublishedHistory = (limit = 20) => api.get('/dashboard/published-history', { params: { limit } })
export const testTelegram = (message = '') => api.post('/dashboard/test-telegram', { message })
export const fetchTelegramConfig = () => api.get('/dashboard/telegram-config')
export const saveTelegramConfig = (data) => api.post('/dashboard/telegram-config', data)
export const fetchTelegramBotInfo = () => api.post('/dashboard/telegram-bot-info')
export const fetchSystemReport = () => api.get('/dashboard/system-report')
export const cleanupPublished = (days = 7) => api.delete(`/dashboard/cleanup-published?days=${days}`)

// ── Accounts & Workspace ───────────────────────────────────────────────────
export const fetchAccounts = (platform) => api.get('/accounts/', { params: platform ? { platform } : {} })
export const createAccount = (data) => api.post('/accounts/', data)
export const deleteAccount = (id) => api.delete(`/accounts/${id}`)
export const updateAccount = (id, data) => api.patch(`/accounts/${id}`, data)
export const refreshAccountToken = (id) => api.post(`/accounts/${id}/refresh-token`)

// This is for the "Edit" button in Accounts/UploadZone to update automation settings
export const updateWorkspaceSettings = (accountId, settings) => api.patch(`/workspace/${accountId}/settings`, settings)
export const fetchWorkspaceSummary = (accountId) => api.get(`/workspace/${accountId}/summary`)

// ── Videos & Drive ─────────────────────────────────────────────────────────
export const fetchVideos = (status, unassigned) => api.get('/videos/', { params: { status_filter: status, unassigned_only: unassigned } })
export const syncAccountNow = (accountId, folderLink) => api.post('/videos/sync-drive', { account_id: accountId, folder_link: folderLink || undefined })
export const pollTaskStatus = (taskId) => api.get(`/videos/task-status/${taskId}`)
export const deleteVideo = (id) => api.delete(`/videos/${id}`)

// ── Schedules & Automation ───────────────────────────────────────────────
export const fetchSchedules = (published) => api.get('/schedules/', { params: published !== undefined ? { is_published: published } : {} })
export const createAutoDrip = (data) => api.post('/schedules/auto-drip', data)
export const deleteSchedule = (id) => api.delete(`/schedules/${id}`)
export const triggerPipeline = (id) => api.post(`/schedules/${id}/trigger`)
export const instantPost = (accountId) => api.post(`/schedules/instant-post-next`, { account_id: accountId }) // We might need to add this to backend if missing
export const clearQueueByAccounts = (accountIds) => api.post('/schedules/clear-queue', { account_ids: accountIds })


// ── Logs ───────────────────────────────────────────────────────────────────
export const fetchLogs = (limit = 100) => api.get('/logs/', { params: { limit } })
export const getLogsStreamUrl = () => `${API_BASE}/api/v1/logs/stream`

// ── API Vault & Rotation ──────────────────────────────────────────────────
export const listApiKeys = (service) => api.get('/api-vault/', { params: { service_name: service } })
export const uploadGoogleKeys = (files) => {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    return api.post('/api-vault/upload-json', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const addMetaKey = (data) => api.post('/api-vault/meta-key', data)
export const addCustomKey = (data) => api.post('/api-vault/custom-key', data)
export const deleteApiKey = (id) => api.delete(`/api-vault/${id}`)
export const unlockApiKey = (id) => api.post(`/api-vault/${id}/unlock`)
export const testApiKey = (id) => api.post(`/api-vault/${id}/test`)

// ── AI Engagement ──────────────────────────────────────────────────────────
export const aiChat = (message, persona) => api.post('/engagement/chat', { message, persona })
export const quickGen = (topic, platform, style) => api.post('/engagement/quick-gen', { topic, platform, style })

// ── Analytics ──────────────────────────────────────────────────────────────
export const fetchAnalyticsOverview = () => api.get('/analytics/overview')
export const fetchAnalyticsCharts = () => api.get('/analytics/charts')

export default api
