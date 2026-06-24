<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import API from "../services/api"

const route = useRoute()
const employeeId = route.params.employee_id

const participant = ref(null)
const rank = ref(null)
const submissions = ref([])
const totalPoints = ref(0)
const challenges = ref([])
const selectedChallenge = ref("")
const loading = ref(false)
const proofModal = ref(null) // { url, type }

const BACKEND = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"

const fetchHistory = async () => {
  loading.value = true
  try {
    const params = {}
    if (selectedChallenge.value) {
      params.challenge_id = selectedChallenge.value
    }
    const [historyRes, challengesRes] = await Promise.all([
      API.get(`/api/my-submissions/${employeeId}`, { params }),
      API.get("/api/challenges")
    ])
    
    if (historyRes.data && historyRes.data.participant) {
      participant.value = historyRes.data.participant
      rank.value = historyRes.data.rank
      submissions.value = historyRes.data.submissions || []
      totalPoints.value = historyRes.data.total_points || 0
    } else {
      participant.value = null
      submissions.value = []
      totalPoints.value = 0
    }
    challenges.value = challengesRes.data || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openProof = (path, type) => {
  if (!path) return
  const url = path.startsWith("http://") || path.startsWith("https://")
    ? path
    : `${BACKEND}/uploads/${path}`
  proofModal.value = { url, type }
}

onMounted(fetchHistory)
</script>

<template>
  <div class="page-container">
    <div class="top-bar">
      <router-link to="/submit" class="back-link">← Submit Activity</router-link>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !participant" class="loading-state">
      <div class="spinner">⏳</div>
      <p>Loading your history...</p>
    </div>

    <!-- Not Found State -->
    <div v-else-if="!participant" class="empty-state">
      <span class="empty-icon">🔍</span>
      <h2>History Not Found</h2>
      <p>No participant found with Employee ID: <strong>{{ employeeId }}</strong></p>
      <router-link to="/submit" class="btn-primary">Go Back</router-link>
    </div>

    <!-- Main Content -->
    <div v-else class="content-wrap">
      <!-- Profile Header -->
      <div class="profile-header-card">
        <div class="profile-info">
          <div class="avatar">👤</div>
          <div>
            <h1>{{ participant.name }}</h1>
            <p class="emp-tag">ID: {{ participant.employee_id }}</p>
          </div>
        </div>
        <div class="stats-grid">
          <div class="stat-box">
            <span class="stat-val">{{ totalPoints }}</span>
            <span class="stat-lbl">Total Points</span>
          </div>
          <div class="stat-box">
            <span class="stat-val">{{ rank || '—' }}</span>
            <span class="stat-lbl">Rank</span>
          </div>
        </div>
      </div>

      <!-- Filters & Controls -->
      <div class="filter-row">
        <h2>Submission History</h2>
        <div class="filter-controls">
          <label for="challenge-filter">Challenge:</label>
          <select id="challenge-filter" class="challenge-select" v-model="selectedChallenge" @change="fetchHistory">
            <option value="">All Time</option>
            <option v-for="c in challenges" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>

      <!-- Submissions Table/List -->
      <div class="table-card">
        <div v-if="!submissions.length" class="no-subs">
          <p>No submissions found for the selected period.</p>
        </div>
        <div v-else class="table-responsive">
          <table class="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Steps (Submitted / Approved)</th>
                <th>Bonuses (Video / Attend / Food)</th>
                <th>Proofs</th>
                <th>Status</th>
                <th>Points</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in submissions" :key="s.id">
                <td class="date-cell">{{ s.submission_date }}</td>
                <td class="steps-cell">
                  <div class="val-group">
                    <span class="raw-steps">{{ s.steps }}</span>
                    <span class="divider">/</span>
                    <span class="app-steps" :class="{ approved: s.review_status === 'Approved' }">{{ s.approved_steps }}</span>
                  </div>
                </td>
                <td class="bonuses-cell">
                  <div class="bonus-group">
                    <span class="bonus-tag video" :class="{ active: s.fitness_video_bonus }" title="Video Bonus">
                      🎥 {{ s.fitness_video_bonus || 0 }}
                    </span>
                    <span class="bonus-tag attendance" :class="{ active: s.fitness_attendance_bonus }" title="Attendance Bonus">
                      🏋️ {{ s.fitness_attendance_bonus || 0 }}
                    </span>
                    <span class="bonus-tag food" :class="{ active: s.food_bonus }" title="Food Bonus">
                      🥗 {{ s.food_bonus || 0 }}
                    </span>
                  </div>
                </td>
                <td class="proofs-cell">
                  <div class="proof-links">
                    <button v-if="s.steps_proof" class="proof-btn" @click="openProof(s.steps_proof, 'image')" title="View Steps Screenshot">📸</button>
                    <button v-if="s.fitness_video" class="proof-btn" @click="openProof(s.fitness_video, 'video')" title="View Fitness Video">🎥</button>
                    <button v-if="s.fitness_attendance_proof" class="proof-btn" @click="openProof(s.fitness_attendance_proof, 'image')" title="View Attendance Proof">🏋️</button>
                    <button v-if="s.food_photo" class="proof-btn" @click="openProof(s.food_photo, 'image')" title="View Food Photo">🥗</button>
                    <span v-if="!s.steps_proof && !s.fitness_video && !s.fitness_attendance_proof && !s.food_photo" class="no-proof">None</span>
                  </div>
                </td>
                <td>
                  <span class="status-badge" :class="s.review_status.toLowerCase()">{{ s.review_status }}</span>
                </td>
                <td class="points-cell">{{ s.total_points }} pts</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Proof Preview Modal -->
    <transition name="modal-fade">
      <div v-if="proofModal" class="modal-overlay" @click.self="proofModal = null">
        <div class="modal-box">
          <button class="modal-close" @click="proofModal = null">✕</button>
          <img v-if="proofModal.type === 'image'" :src="proofModal.url" class="proof-media" />
          <video v-else :src="proofModal.url" class="proof-media" controls autoplay />
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.page-container {
  min-height: calc(100vh - 56px);
  background: var(--bg);
  padding: 2rem 1.5rem 4rem;
  max-width: 1000px;
  margin: 0 auto;
  font-family: 'Inter', system-ui, sans-serif;
}

.top-bar {
  margin-bottom: 1.5rem;
}

.back-link {
  text-decoration: none;
  font-weight: 600;
  color: var(--primary);
  font-size: 0.9rem;
}
.back-link:hover {
  text-decoration: underline;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: var(--surface);
  border-radius: 18px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.btn-primary {
  display: inline-block;
  background: var(--primary);
  color: white;
  text-decoration: none;
  padding: 0.6rem 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.profile-header-card {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  border-radius: 20px;
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(79, 70, 229, 0.15);
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.avatar {
  font-size: 2.5rem;
  background: rgba(255, 255, 255, 0.2);
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.profile-info h1 {
  font-size: 1.6rem;
  font-weight: 800;
  margin: 0;
  letter-spacing: -0.02em;
}

.emp-tag {
  font-size: 0.9rem;
  opacity: 0.85;
  margin-top: 0.25rem;
}

.stats-grid {
  display: flex;
  gap: 1.5rem;
}

.stat-box {
  background: rgba(255, 255, 255, 0.12);
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  text-align: center;
  min-width: 100px;
}

.stat-val {
  display: block;
  font-size: 1.5rem;
  font-weight: 800;
}

.stat-lbl {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.75;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.filter-row h2 {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text);
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-controls label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted);
}

.challenge-select {
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  outline: none;
  cursor: pointer;
}

.table-card {
  background: var(--surface);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  overflow: hidden;
}

.no-subs {
  padding: 3rem;
  text-align: center;
  color: var(--text-muted);
}

.table-responsive {
  overflow-x: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  text-align: left;
  padding: 0.85rem 1.2rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
}

.history-table td {
  padding: 1rem 1.2rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
  color: var(--text);
}

.history-table tr:last-child td {
  border-bottom: none;
}

.date-cell {
  font-weight: 600;
}

.steps-cell .val-group {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.raw-steps {
  color: var(--text-muted);
  font-size: 0.82rem;
}

.app-steps {
  font-weight: 700;
}
.app-steps.approved {
  color: var(--green);
}

.bonus-group {
  display: flex;
  gap: 0.4rem;
}

.bonus-tag {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.4rem;
  border-radius: 6px;
  opacity: 0.4;
  background: var(--surface2);
  color: var(--text-muted);
}

.bonus-tag.active {
  opacity: 1;
}

.bonus-tag.video.active { background: rgba(79, 70, 229, 0.1); color: var(--primary); }
.bonus-tag.attendance.active { background: rgba(245, 158, 11, 0.1); color: var(--amber); }
.bonus-tag.food.active { background: rgba(16, 185, 129, 0.1); color: var(--green); }

.proof-links {
  display: flex;
  gap: 0.4rem;
}

.proof-btn {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.15s;
}
.proof-btn:hover {
  background: var(--border);
}

.no-proof {
  color: var(--text-muted);
  font-size: 0.8rem;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: capitalize;
}

.status-badge.pending { background: #fef3c7; color: #92400e; }
.status-badge.approved { background: #d1fae5; color: #065f46; }
.status-badge.rejected { background: #fee2e2; color: #991b1b; }

.points-cell {
  font-weight: 800;
  color: var(--primary);
}

/* Modal Styling */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
  padding: 1.5rem;
}

.modal-box {
  background: var(--surface);
  border-radius: 16px;
  overflow: hidden;
  max-width: 90vw;
  max-height: 90vh;
  position: relative;
  display: flex;
  flex-direction: column;
}

.modal-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: rgba(0,0,0,0.5);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  color: #fff;
  cursor: pointer;
  font-size: 0.9rem;
  z-index: 1;
}

.proof-media {
  max-width: 80vw;
  max-height: 80vh;
  object-fit: contain;
  display: block;
}

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .profile-header-card {
    flex-direction: column;
    align-items: flex-start;
  }
  .stats-grid {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
