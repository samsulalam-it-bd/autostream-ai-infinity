import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
export const cleanupPublished = (days = 7) => api.delete(`/dashboard/cleanup-published?days=${days}`)
export const fetchSystemReport = () => api.get('/dashboard/system-report')

// ── Accounts ───────────────────────────────────────────────────────────────
export const fetchAccounts = (platform) => api.get('/accounts/', { params: platform ? { platform } : {} })
export const createAccount = (data) => api.post('/accounts/', data)
export const deleteAccount = (id) => api.delete(`/accounts/${id}`)
export const updateAccount = (id, data) => api.patch(`/accounts/${id}`, data)
export const updateAccountFolder = (id, folderLink) => api.patch(`/accounts/${id}`, { drive_folder_link: folderLink })
export const fetchGroups = () => api.get('/accounts/groups')
export const createGroup = (data) => api.post('/accounts/groups', data)
export const deleteGroup = (id) => api.delete(`/accounts/groups/${id}`)
export const getGoogleOAuthUrl = () => api.get('/accounts/oauth/google/init')
export const getMetaOAuthUrl = () => api.get('/accounts/oauth/meta/init')
export const refreshAccountToken = (id) => api.post(`/accounts/${id}/refresh-token`)

// ── API Vault ──────────────────────────────────────────────────────────────
export const fetchApiKeys = (serviceName) => api.get('/api-vault/', { params: serviceName ? { service_name: serviceName } : {} })
export const fetchVaultStats = () => api.get('/api-vault/stats/summary')
export const deleteApiKey = (id) => api.delete(`/api-vault/${id}`)
export const unlockApiKey = (id) => api.post(`/api-vault/${id}/unlock`)
export const testApiKey = (id) => api.post(`/api-vault/${id}/test`)
export const addMetaApiKey = (data) => api.post('/api-vault/meta-key', data)
export const uploadJsonCredentials = (files, serviceName = 'google') => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    return axios.post(`${API_BASE}/api/v1/api-vault/upload-json?service_name=${serviceName}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
    })
}
export const addCustomApiKey = (data) => api.post('/api-vault/custom-key', data)
export const fetchAiRouting = () => api.get('/dashboard/ai-routing')
export const saveAiRouting = (data) => api.post('/dashboard/ai-routing', data)

// ── Videos ─────────────────────────────────────────────────────────────────
export const fetchVideos = (status, unassignedOnly = false) => api.get('/videos/', { params: { ...(status ? { status_filter: status } : {}), ...(unassignedOnly ? { unassigned_only: true } : {}) } })
export const syncDriveFolder = (accountId, folderLink) => api.post('/videos/sync-drive', { account_id: accountId, folder_link: folderLink })
export const fetchTaskStatus = (taskId) => api.get(`/videos/task-status/${taskId}`)
export const deleteVideo = (id) => api.delete(`/videos/${id}`)

// ── Schedules ─────────────────────────────────────────────────────────────
export const fetchSchedules = (published) => api.get('/schedules/', { params: published !== undefined ? { is_published: published } : {} })
export const createSchedule = (data) => api.post('/schedules/', data)
export const createAutoDrip = (data) => api.post('/schedules/auto-drip', data)
export const deleteSchedule = (id) => api.delete(`/schedules/${id}`)
export const bulkDeleteSchedules = (ids) => api.post('/schedules/bulk-delete', { ids })
export const triggerSchedule = (id) => api.post(`/schedules/${id}/trigger`)

// ── Logs ───────────────────────────────────────────────────────────────────
export const fetchLogs = (limit = 100) => api.get('/logs/', { params: { limit } })
export const getLogsStreamUrl = () => `${API_BASE}/api/v1/logs/stream`

export default api
