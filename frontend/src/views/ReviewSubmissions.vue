<!-- <script setup>
import { ref, onMounted } from "vue"
import API from "../services/api"
const submissions = ref([])
const selectedSubmission = ref(null)
const approved_steps = ref(0)
const fitness_video_bonus = ref(1000)
const fitness_attendance_bonus = ref(1000)
const food_bonus = ref(1000)
const stats = ref({
  total: 0,
  pending: 0,
  approved: 0,
  rejected: 0})
const backendUrl = "http://127.0.0.1:5000"
        
const getSubmissions = async () => {
  const response = await API.get("/api/submission")
  submissions.value = response.data
}
        
const selectSubmission = (submission) => {
  selectedSubmission.value = submission
  approved_steps.value = submission.approved_steps || submission.steps
  fitness_video_bonus.value = submission.fitness_video_bonus || 0
  fitness_attendance_bonus.value = submission.fitness_attendance_bonus || 0
  food_bonus.value =submission.food_bonus || 0
}
        
const approveSubmission = async ()=>{
  await API.put( `/api/submission/${selectedSubmission.value.id}/review`,
    {
    approved_steps: approved_steps.value,
    fitness_video_bonus:fitness_video_bonus.value,
    fitness_attendance_bonus:fitness_attendance_bonus.value,
    food_bonus:food_bonus.value,
    review_status: "Approved"
    })  
    selectedSubmission.value = null
  alert("Approved")
  await getSubmissions()
  await getStats()
}
       
const rejectSubmission = async () => {
    await API.put(`/api/submission/${selectedSubmission.value.id}/review`,
    {
      approved_steps:0,
      fitness_video_bonus: 0,
      fitness_attendance_bonus: 0,
      food_bonus: 0,
      review_status: "Rejected"
    }) 
    selectedSubmission.value = null
  alert("Rejected")        
  await getSubmissions()
  await getStats()
}

const getStats = async () => {
  const response = await API.get(
    "/api/dashboard-stats"
  )
  stats.value = response.data
}

onMounted(() => {      
  getSubmissions()
  getStats()
})       
</script>
<template>
  <div class="container mt-4">
    <h2>Review Submissions</h2>
    <div class="row mb-4">
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h3>{{ stats.total }}</h3>
        <p>Total Submissions</p>
      </div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h3>{{ stats.pending }}</h3>
        <p>Pending Review</p>
      </div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h3>{{ stats.approved }}</h3>
        <p>Approved</p>
      </div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h3>{{ stats.rejected }}</h3>
        <p>Rejected</p>
      </div>
    </div>
  </div>
</div>
    <table class="table table-bordered mt-4">
      <thead>
        <tr>
          <th>Employee ID</th>
          <th>Name</th>
          <th>Status</th>
          <th>Action</th>
          <th>Total Points</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="submission in submissions"
          :key="submission.id">
          <td>{{ submission.employee_id }}</td>
          <td>{{ submission.name }}</td>
          <td>{{ submission.review_status }}</td>
          <td>
            <button v-if="submission.review_status === 'Pending'" class="btn btn-primary btn-sm" @click="selectSubmission(submission)">Review</button>
            <span v-else-if="submission.review_status === 'Approved'" class="badge bg-success">Approved</span>
            <span v-else class="badge bg-danger">Rejected</span>
          </td>
          <td>{{ submission.total_points }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="selectedSubmission" class="card p-3 mt-4">
      <h4>Review Submission</h4>
      <p>
        <strong>Name:</strong>{{ selectedSubmission.name }}
      </p>
      <p>
        <strong>Steps:</strong>{{ selectedSubmission.steps }}
      </p>
      <div class="mb-3">
        <a v-if="selectedSubmission.steps_proof"
          :href="backendUrl + '/' + selectedSubmission.steps_proof"
          target="_blank">
          View Step Screenshot</a>
      </div>
      <div class="mb-3">
        <a v-if="selectedSubmission.fitness_video"
          :href="backendUrl + '/' + selectedSubmission.fitness_video"
          target="_blank"
        >View Fitness Video</a>
      </div>
      <div class="mb-3">
        <a v-if="selectedSubmission.fitness_attendance_proof"
          :href="backendUrl + '/' + selectedSubmission.fitness_attendance_proof"
          target="_blank">
          View Attendance Proof</a>
      </div>
      <div class="mb-3">
        <a v-if="selectedSubmission.food_photo"
          :href="backendUrl + '/' + selectedSubmission.food_photo"
          target="_blank">View Food Challenge Photo</a>
      </div>
      <div class="mb-3">
        <label>Approved Steps</label>
        <input type="number" class="form-control" v-model="approved_steps">
      </div>
      <div class="mb-3">
        <label>Attendance Bonus</label>
        <input type="number" class="form-control" v-model="fitness_attendance_bonus">
      </div>
      <div class="mb-3">
        <label>Fitness Video Bonus</label>
        <input type="number" class="form-control" v-model="fitness_video_bonus">
      </div>
      <div class="mb-3">
        <label> Food Bonus</label>
        <input type="number" class="form-control" v-model="food_bonus">
      </div>
      <button class="btn btn-success me-2" @click="approveSubmission">Approve</button>
      <button class="btn btn-danger" @click="rejectSubmission">Reject</button>
    </div>
  </div>
</template>  -->
<script setup>
import { ref, computed, onMounted } from "vue"
import API from "../services/api"
import Swal from "sweetalert2"

const submissions = ref([])
const challenges = ref([])
const selectedChallenge = ref("")
const statusFilter = ref("All")
const search = ref("")
const stats = ref({ total: 0, pending: 0, approved: 0, rejected: 0 })
const selectedSubmission = ref(null)
const proofModal = ref(null)  // { url, type }
const loading = ref(false)
const toast = ref(null)
const BACKEND = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"

// Review fields
const approved_steps = ref(0)
const fitness_video_bonus = ref(0)
const fitness_attendance_bonus = ref(0)
const food_bonus = ref(0)
const challengeName = ref("")
const challengeStart = ref("")
const challengeEnd = ref("")

const passwordInput = ref("")
const isAuthenticated = ref(localStorage.getItem("reviewerAuth") === "true")

const verifyPassword = async () => {
  if (passwordInput.value === "ctrlaltheal") {
    localStorage.setItem("reviewerAuth", "true")
    isAuthenticated.value = true
    await fetchAll()
  } else {
    await Swal.fire({
      icon: "error",
      title: "Access Denied",
      text: "Incorrect password, please try again."
    })
    passwordInput.value = ""
  }
}

const fetchAll = async () => {
  loading.value = true
  try {
    const [subRes, statsRes, chalRes] = await Promise.all([
      API.get("/api/submission", { params: {
        status: statusFilter.value === "All" ? undefined : statusFilter.value,
        challenge_id: selectedChallenge.value || undefined,
        search: search.value || undefined,
      }}),
      API.get("/api/admin/stats", { params: { challenge_id: selectedChallenge.value || undefined } }),
      API.get("/api/challenges"),
    ])
    submissions.value = subRes.data
    stats.value = statsRes.data
    challenges.value = chalRes.data
  } catch (e) {
    showToast("error", e.message)
  } finally {
    loading.value = false
  }
}

const selectSubmission = (s) => {
  selectedSubmission.value = s
  approved_steps.value = s.review_status === "Rejected" ? s.steps : (s.approved_steps ?? s.steps)
  fitness_video_bonus.value = s.fitness_video_bonus ?? 0
  fitness_attendance_bonus.value = s.fitness_attendance_bonus ?? 0
  food_bonus.value = s.food_bonus ?? 0
}

const submitReview = async (status) => {
  if (status === "Approved") {
    const stepsVal = Number(approved_steps.value)
    if (isNaN(stepsVal) || stepsVal < 0 || stepsVal > 15000) {
      await Swal.fire({
        icon: "error",
        title: "Validation Error",
        text: "Approved steps must be between 0 and 15,000."
      })
      return
    }
    const videoVal = Number(fitness_video_bonus.value)
    if (isNaN(videoVal) || videoVal < 0 || videoVal > 1000) {
      await Swal.fire({
        icon: "error",
        title: "Validation Error",
        text: "Fitness video bonus must be between 0 and 1,000."
      })
      return
    }
    const attendVal = Number(fitness_attendance_bonus.value)
    if (isNaN(attendVal) || attendVal < 0 || attendVal > 1000) {
      await Swal.fire({
        icon: "error",
        title: "Validation Error",
        text: "Attendance bonus must be between 0 and 1,000."
      })
      return
    }
    const foodVal = Number(food_bonus.value)
    if (isNaN(foodVal) || foodVal < 0 || foodVal > 1000) {
      await Swal.fire({
        icon: "error",
        title: "Validation Error",
        text: "Food bonus must be between 0 and 1,000."
      })
      return
    }
  }

  try {
    const result = await Swal.fire({
      title:
        status === "Approved"
          ? "Approve Submission?"
          : "Reject Submission?",
      icon:
        status === "Approved"
          ? "question"
          : "warning",
      showCancelButton: true,
      confirmButtonText: status
    })

    if (!result.isConfirmed) return
    await API.put(`/api/admin/submission/${selectedSubmission.value.id}/review`, {
      review_status: status,
      approved_steps: approved_steps.value,
      fitness_video_bonus: fitness_video_bonus.value,
      fitness_attendance_bonus: fitness_attendance_bonus.value,
      food_bonus: food_bonus.value,
      reviewer: "Reviewer",
    })
    await Swal.fire({
      icon: "success",
      title: status,
      text: `Submission ${status.toLowerCase()} successfully`
    })
    selectedSubmission.value = null
    await fetchAll()
  } catch (e) {
    await Swal.fire({
      icon: "error",
      title: "Review Failed",
      text: e.message
    })
  }
}

const openProof = (path, type) => {
  if (!path) return
  const url = path.startsWith("http://") || path.startsWith("https://")
    ? path
    : `${BACKEND}/uploads/${path}`
  proofModal.value = { url, type }
}

const showToast = (type, msg) => {
  toast.value = { type, msg }
  setTimeout(() => { toast.value = null }, 3500)
}

const previewTotal = computed(() =>
  Number(approved_steps.value || 0) +
  Number(fitness_video_bonus.value || 0) +
  Number(fitness_attendance_bonus.value || 0) +
  Number(food_bonus.value || 0)
)

function logoutReviewer() {
  localStorage.removeItem("reviewerAuth")
  window.location.href = "/submit"
}

const createChallenge = async () => {
  try {
    await API.post("/api/challenges", {
      name: challengeName.value,
      start_date: challengeStart.value,
      end_date: challengeEnd.value,
    })
    await Swal.fire({
      icon: "success",
      title: "Challenge Created"
    })
    challengeName.value = ""
    challengeStart.value = ""
    challengeEnd.value = ""
    await fetchAll()
  } catch (e) {
    await Swal.fire({
      icon: "error",
      title: "Creation Failed",
      text: e.response?.data?.message || e.message
    })
  }
}

const openCreateChallengeModal = async () => {
  const { value: formValues } = await Swal.fire({
    title: "Create Challenge",
    html: `
      <input id="swal-name" class="swal2-input" placeholder="Challenge Name">
      <label style="display:block;margin-top:10px;">Start Date</label>
      <input id="swal-start" type="date" class="swal2-input">
      <label style="display:block;margin-top:10px;">End Date</label>
      <input id="swal-end" type="date" class="swal2-input">
    `,
    focusConfirm: false,
    showCancelButton: true,
    preConfirm: () => ({
      name: document.getElementById("swal-name").value,
      start_date: document.getElementById("swal-start").value,
      end_date: document.getElementById("swal-end").value
    })
  })

  if (!formValues) return

  try {
    await API.post("/api/challenges", formValues)

    await Swal.fire({
      icon: "success",
      title: "Challenge Created"
    })

    fetchAll()

  } catch (e) {
    Swal.fire({
      icon: "error",
      title: "Failed",
      text: e.response?.data?.message || e.message
    })
  }
}

const openManageChallenges = async () => {

  const html = challenges.value.map(c => `
    <div style="
      border:1px solid #ddd;
      padding:15px;
      margin-bottom:12px;
      border-radius:10px;
      text-align:left;
    ">
      <strong>${c.name}</strong><br>
      ${c.start_date} → ${c.end_date}<br>
      Status: <b>${c.status}</b><br><br>

      ${
        c.status === "Active"
        ? `<button
             onclick="stopChallenge(${c.id})"
             style="
               background:#f59e0b;
               color:white;
               border:none;
               padding:8px 12px;
               border-radius:8px;
               cursor:pointer;
             ">
             Stop Challenge
           </button>`
        : ""
      }

      ${
        c.status === "Upcoming"
        ? `<button
             onclick="deleteChallenge(${c.id})"
             style="
               background:#dc2626;
               color:white;
               border:none;
               padding:8px 12px;
               border-radius:8px;
               cursor:pointer;
             ">
             Delete Challenge
           </button>`
        : ""
      }

    </div>
  `).join("")

  Swal.fire({
    title: "Manage Challenges",
    html,
    width: 800,
    showConfirmButton: false
  })
}
window.stopChallenge = async (id) => {
  const result = await Swal.fire({
    title: "Stop Challenge?",
    text: "This challenge will be marked as completed.",
    icon: "warning",
    showCancelButton: true
  })

  if (!result.isConfirmed) return

  await API.put(`/api/challenges/${id}`, {
    status: "Completed"
  })

  await fetchAll()

  Swal.fire({
    icon: "success",
    title: "Challenge Stopped"
  })
}

window.deleteChallenge = async (id) => {
  const result = await Swal.fire({
    title: "Delete Challenge?",
    text: "This cannot be undone.",
    icon: "warning",
    showCancelButton: true
  })

  if (!result.isConfirmed) return

  await API.delete(`/api/challenges/${id}`)

  await fetchAll()

  Swal.fire({
    icon: "success",
    title: "Challenge Deleted"
  })
}

const activeChallenge = computed(() =>
  challenges.value.find(c => c.status === "Active")
)

onMounted(() => {
  if (isAuthenticated.value) {
    fetchAll()
  }
})
</script>

<template>
  <div class="page">

    <!-- Toast -->
    <transition name="toast-fade">
      <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
    </transition>

    <!-- Inline Lock Screen -->
    <div v-if="!isAuthenticated" class="login-overlay">
      <div class="login-card">
        <span class="lock-icon">🔒</span>
        <h2>Reviewer Dashboard</h2>
        <p>Please enter your access password to continue.</p>
        <form @submit.prevent="verifyPassword" class="login-form">
          <input
            type="password"
            v-model="passwordInput"
            placeholder="Enter password..."
            class="password-input"
            required
          />
          <button type="submit" class="btn-login">Unlock Dashboard →</button>
        </form>
        <router-link to="/submit" class="btn-cancel">← Back to Submissions</router-link>
      </div>
    </div>

    <!-- Main Dashboard Content -->
    <div v-else class="dashboard-content-wrap" style="width: 100%; display: flex; flex-direction: column; gap: 1.5rem;">

    <!-- Page header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Review Dashboard</h1>
        <p class="page-sub">Shape Up Challenge · Admin Panel</p>
      </div>
      <div class="header-actions">
        <a v-if="selectedChallenge" :href="`${BACKEND}/api/admin/export/${selectedChallenge}`" class="btn-export" target="_blank">⬇ Export Excel</a>
      </div>
    </div>

    <!-- Challenge Management -->
<div class="challenge-card">
  <div class="challenge-header">
    <h3>🏆 Challenge Management</h3>
  </div>

  <div class="challenge-actions">
    <button
      class="btn-create"
      @click="openCreateChallengeModal"
    >
      + Create Challenge
    </button>

    <button
      class="btn-manage"
      @click="openManageChallenges"
    >
      Manage Challenges
    </button>
  </div>
</div>
<div
  v-if="activeChallenge"
  class="active-challenge-card"
>
  <div class="active-badge">
    🟢 Active Challenge
  </div>

  <h3>{{ activeChallenge.name }}</h3>

  <p>
    {{ activeChallenge.start_date }}
    →
    {{ activeChallenge.end_date }}
  </p>
</div>
    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card stat-total"><span class="stat-num">{{ stats.total }}</span><span class="stat-label">Total</span></div>
      <div class="stat-card stat-pending"><span class="stat-num">{{ stats.pending }}</span><span class="stat-label">Pending</span></div>
      <div class="stat-card stat-approved"><span class="stat-num">{{ stats.approved }}</span><span class="stat-label">Approved</span></div>
      <div class="stat-card stat-rejected"><span class="stat-num">{{ stats.rejected }}</span><span class="stat-label">Rejected</span></div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <input class="search-input" v-model="search" placeholder="🔍 Search by name or ID…" @input="fetchAll" />
      <select class="filter-select" v-model="selectedChallenge" @change="fetchAll">
        <option value="">All challenges</option>
        <option v-for="c in challenges" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <div class="status-tabs">
        <button v-for="tab in ['All','Pending','Approved','Rejected']" :key="tab"
          class="tab-btn" :class="{ active: statusFilter === tab }"
          @click="statusFilter = tab; fetchAll()">{{ tab }}</button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div v-if="loading" class="table-loading">Loading…</div>
      <div v-else-if="!submissions.length" class="empty-state">No submissions found.</div>
      <div v-else class="table-wrap">
        <table class="submissions-table">
          <thead><tr>
            <th>Employee ID</th><th>Name</th><th>Date</th>
            <th>Status</th><th>Points</th><th>Action</th>
          </tr></thead>
          <tbody>
            <tr v-for="s in submissions" :key="s.id"
              :class="{ 'row-active': selectedSubmission?.id === s.id }">
              <td class="cell-id">{{ s.employee_id }}</td>
              <td class="cell-name">{{ s.name }}</td>
              <td class="cell-date">{{ s.submission_date }}</td>
              <td><span class="badge" :class="`badge-${s.review_status.toLowerCase()}`">{{ s.review_status }}</span></td>
              <td class="cell-pts">{{ s.total_points ?? '—' }}</td>
              <td>
                <button class="review-btn" @click="selectSubmission(s)">
                  {{ s.review_status === 'Pending' ? 'Review' : 'Edit' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Review Panel -->
    <transition name="panel-slide">
      <div v-if="selectedSubmission" class="review-panel">
        <div class="panel-top">
          <div>
            <h3 class="panel-title">{{ selectedSubmission.name }}</h3>
            <p class="panel-sub">{{ selectedSubmission.employee_id }} · {{ selectedSubmission.steps }} steps reported · {{ selectedSubmission.submission_date }}</p>
          </div>
          <button class="close-btn" @click="selectedSubmission = null">✕</button>
        </div>

        <!-- Proofs -->
        <div class="proofs-section">
          <div class="proofs-label">Submitted Proofs</div>
          <div class="proofs-grid">
            <button v-if="selectedSubmission.steps_proof" class="proof-chip"
              @click="openProof(selectedSubmission.steps_proof, 'image')">📸 Steps Screenshot</button>
            <button v-if="selectedSubmission.fitness_video" class="proof-chip"
              @click="openProof(selectedSubmission.fitness_video, 'video')">🎥 Fitness Video</button>
            <button v-if="selectedSubmission.fitness_attendance_proof" class="proof-chip"
              @click="openProof(selectedSubmission.fitness_attendance_proof, 'image')">🏋️ Attendance Proof</button>
            <button v-if="selectedSubmission.food_photo" class="proof-chip"
              @click="openProof(selectedSubmission.food_photo, 'image')">🥗 Food Photo</button>
            <span v-if="!selectedSubmission.steps_proof && !selectedSubmission.fitness_video && !selectedSubmission.fitness_attendance_proof && !selectedSubmission.food_photo" class="no-proof">No proofs attached</span>
          </div>
        </div>

        <!-- Score Inputs -->
        <div class="score-section">
          <div class="proofs-label">Award Points</div>
          <div class="score-grid">
            <div class="score-field">
              <label>Approved Steps</label>
              <input class="score-input" type="number" v-model="approved_steps" min="0" max="15000" />
            </div>
            <div class="score-field">
              <label>Attendance Bonus</label>
              <input class="score-input" type="number" v-model="fitness_attendance_bonus" min="0" max="1000" />
            </div>
            <div class="score-field">
              <label>Fitness Video Bonus</label>
              <input class="score-input" type="number" v-model="fitness_video_bonus" min="0" max="1000" />
            </div>
            <div class="score-field">
              <label>Food Bonus</label>
              <input class="score-input" type="number" v-model="food_bonus" min="0" max="1000" />
            </div>
          </div>
          <div class="total-preview">Total Points Preview: <strong>{{ previewTotal }}</strong></div>
        </div>

        <div class="panel-actions">
          <button class="btn-approve" @click="submitReview('Approved')">✓ Approve</button>
          <button class="btn-reject" @click="submitReview('Rejected')">✕ Reject</button>
        </div>
      </div>
    </transition>

    <!-- Proof Modal -->
    <transition name="modal-fade">
      <div v-if="proofModal" class="modal-overlay" @click.self="proofModal = null">
        <div class="modal-box">
          <button class="modal-close" @click="proofModal = null">✕</button>
          <img v-if="proofModal.type === 'image'" :src="proofModal.url" class="proof-media" />
          <video v-else :src="proofModal.url" class="proof-media" controls autoplay />
        </div>
      </div>
    </transition>

    </div> <!-- Close dashboard-content-wrap v-else -->
  </div>
</template>

<style scoped>
.page { min-height: calc(100vh - 56px); background: var(--bg); padding: 2rem 1.5rem 4rem; display: flex; flex-direction: column; gap: 1.5rem; max-width: 1200px; margin: 0 auto; font-family: 'Inter', system-ui, sans-serif; }

.toast { position: fixed; top: 1.25rem; left: 50%; transform: translateX(-50%); padding: 0.65rem 1.25rem; border-radius: 10px; font-size: 0.88rem; font-weight: 600; z-index: 200; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
.toast.success { background: #D1FAE5; color: #065F46; }
.toast.error { background: #FEE2E2; color: #991B1B; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
.page-title { font-size: 1.75rem; font-weight: 800; color: var(--text); margin: 0 0 0.2rem; letter-spacing: -0.03em; }
.page-sub { font-size: 0.84rem; color: var(--text-muted); margin: 0; }
.header-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; }
.btn-ghost { text-decoration: none; padding: 0.45rem 0.9rem; border-radius: 9px; font-size: 0.82rem; font-weight: 600; color: var(--primary); background: var(--primary-light); border: none; cursor: pointer; }
.btn-export { text-decoration: none; padding: 0.45rem 0.9rem; border-radius: 9px; font-size: 0.82rem; font-weight: 600; color: #065F46; background: #D1FAE5; border: none; cursor: pointer; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.stat-card { background: var(--surface); border-radius: 14px; padding: 1.2rem 1.4rem; display: flex; flex-direction: column; gap: 0.2rem; border-left: 4px solid transparent; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.stat-total { border-left-color: var(--primary); }
.stat-pending { border-left-color: var(--amber); }
.stat-approved { border-left-color: var(--green); }
.stat-rejected { border-left-color: var(--red); }
.stat-num { font-size: 2rem; font-weight: 800; color: var(--text); line-height: 1; font-variant-numeric: tabular-nums; }
.stat-label { font-size: 0.78rem; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }

.filter-bar { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
.search-input { border: 1.5px solid var(--border); border-radius: 10px; padding: 0.55rem 0.9rem; font-size: 0.88rem; color: var(--text); background: var(--surface); outline: none; min-width: 220px; transition: border-color 0.18s; }
.search-input:focus { border-color: var(--primary); }
.filter-select { border: 1.5px solid var(--border); border-radius: 10px; padding: 0.55rem 0.75rem; font-size: 0.88rem; color: var(--text); background: var(--surface); outline: none; cursor: pointer; }
.status-tabs { display: flex; gap: 0.3rem; background: var(--surface); border: 1.5px solid var(--border); border-radius: 10px; padding: 0.2rem; }
.tab-btn { border: none; background: none; padding: 0.35rem 0.75rem; border-radius: 7px; font-size: 0.82rem; font-weight: 600; cursor: pointer; color: var(--text-muted); transition: background 0.15s, color 0.15s; }
.tab-btn.active { background: var(--primary); color: #fff; }

.table-card { background: var(--surface); border-radius: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden; }
.table-loading, .empty-state { padding: 2.5rem; text-align: center; color: var(--text-muted); font-size: 0.9rem; }
.table-wrap { overflow-x: auto; }
.submissions-table { width: 100%; border-collapse: collapse; }
.submissions-table thead tr { background: var(--surface2); }
.submissions-table th { text-align: left; padding: 0.75rem 1rem; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-muted); border-bottom: 1px solid var(--border); }
.submissions-table tbody tr { border-bottom: 1px solid var(--border); transition: background 0.15s; }
.submissions-table tbody tr:hover { background: var(--surface2); }
.submissions-table tbody tr.row-active { background: var(--primary-light); }
.submissions-table tbody tr:last-child { border-bottom: none; }
.submissions-table td { padding: 0.85rem 1rem; font-size: 0.88rem; color: var(--text); }
.cell-id { font-family: monospace; font-size: 0.82rem; color: var(--text-muted); }
.cell-name { font-weight: 600; }
.cell-date, .cell-muted { color: var(--text-muted); font-size: 0.82rem; }
.cell-pts { font-weight: 700; color: var(--primary); font-variant-numeric: tabular-nums; }

.badge { display: inline-block; padding: 0.25rem 0.65rem; border-radius: 99px; font-size: 0.74rem; font-weight: 600; }
.badge-pending  { background: #FEF3C7; color: #92400E; }
.badge-approved { background: #D1FAE5; color: #065F46; }
.badge-rejected { background: #FEE2E2; color: #991B1B; }

.review-btn { background: var(--primary); color: #fff; border: none; border-radius: 8px; padding: 0.38rem 0.85rem; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: opacity 0.15s; }
.review-btn:hover { opacity: 0.85; }

/* Review Panel */
.review-panel { background: var(--surface); border-radius: 16px; box-shadow: 0 4px 24px rgba(79,70,229,0.12); overflow: hidden; border-top: 4px solid var(--primary); }
.panel-top { display: flex; align-items: flex-start; justify-content: space-between; padding: 1.5rem 1.75rem 1.25rem; border-bottom: 1px solid var(--border); }
.panel-title { font-size: 1.1rem; font-weight: 700; color: var(--text); margin: 0 0 0.2rem; }
.panel-sub { font-size: 0.83rem; color: var(--text-muted); margin: 0; }
.close-btn { background: var(--surface2); border: none; border-radius: 8px; width: 32px; height: 32px; cursor: pointer; font-size: 0.85rem; color: var(--text-muted); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

.proofs-section, .score-section { padding: 1.25rem 1.75rem; border-bottom: 1px solid var(--border); }
.proofs-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--primary); margin-bottom: 0.75rem; }
.proofs-grid { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.proof-chip { background: var(--primary-light); color: var(--primary); border: none; border-radius: 8px; padding: 0.45rem 0.85rem; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: opacity 0.15s; }
.proof-chip:hover { opacity: 0.8; }
.no-proof { font-size: 0.83rem; color: var(--text-muted); }

.score-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
.score-field { display: flex; flex-direction: column; gap: 0.4rem; }
.score-field label { font-size: 0.82rem; font-weight: 600; color: var(--text); }
.score-input { border: 1.5px solid var(--border); border-radius: 9px; padding: 0.6rem 0.8rem; font-size: 0.95rem; color: var(--text); background: var(--input-bg); outline: none; width: 100%; transition: border-color 0.18s; }
.score-input:focus { border-color: var(--primary); }
.total-preview { margin-top: 0.75rem; font-size: 0.88rem; color: var(--text-muted); }
.total-preview strong { color: var(--primary); font-size: 1rem; }

.panel-actions { padding: 1.25rem 1.75rem; display: flex; gap: 0.75rem; }
.btn-approve { background: var(--green); color: #fff; border: none; border-radius: 10px; padding: 0.7rem 1.6rem; font-size: 0.92rem; font-weight: 700; cursor: pointer; transition: opacity 0.15s; }
.btn-approve:hover { opacity: 0.85; }
.btn-reject { background: #FEE2E2; color: #B91C1C; border: none; border-radius: 10px; padding: 0.7rem 1.6rem; font-size: 0.92rem; font-weight: 700; cursor: pointer; transition: opacity 0.15s; }
.btn-reject:hover { opacity: 0.85; }

.panel-slide-enter-active, .panel-slide-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.panel-slide-enter-from, .panel-slide-leave-to { opacity: 0; transform: translateY(12px); }

/* Proof Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 300; padding: 1.5rem; }
.modal-box { background: var(--surface); border-radius: 16px; overflow: hidden; max-width: 90vw; max-height: 90vh; position: relative; display: flex; flex-direction: column; }
.modal-close { position: absolute; top: 0.75rem; right: 0.75rem; background: rgba(0,0,0,0.5); border: none; border-radius: 50%; width: 32px; height: 32px; color: #fff; cursor: pointer; font-size: 0.9rem; z-index: 1; }
.proof-media { max-width: 80vw; max-height: 80vh; object-fit: contain; display: block; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

.challenge-card {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.challenge-header {
  margin-bottom: 1rem;
}

.challenge-form {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.challenge-input {
  padding: 0.65rem;
  border-radius: 8px;
  border: 1px solid #ddd;
}


.date-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.date-group label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #94a3b8;
}

.challenge-input {
  height: 52px;
  padding: 0 14px;
  border-radius: 12px;
}

.challenge-actions {
  display: flex;
  gap: 1.5rem;
  align-items: stretch;
}

.btn-create,
.btn-manage {
  width: 250px;
  height: 50px;
  border: none;
  border-radius: 18px;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-create {
  background: #16a34a;
  color: white;
}

.btn-manage {
  background: #2563eb;
  color: white;
}

.btn-create:hover,
.btn-manage:hover {
  transform: translateY(-2px);
}

.active-challenge-card {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 14px;
  background: rgba(34,197,94,0.12);
  border: 1px solid rgba(34,197,94,0.35);
}

.active-badge {
  font-size: 0.9rem;
  font-weight: 700;
  color: #22c55e;
  margin-bottom: 0.5rem;
}

@media (max-width: 700px) {
  .page { padding: 1.25rem 1rem 3rem; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .score-grid { grid-template-columns: 1fr 1fr; }
  .filter-bar { flex-direction: column; align-items: stretch; }
}

/* ── Lock Screen Styles ── */
.login-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
  width: 100%;
}

.login-card {
  background: var(--surface);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  padding: 2.5rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  border: 1px solid var(--border);
}

.lock-icon {
  font-size: 3rem;
  background: var(--primary-light);
  width: 70px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-bottom: 0.5rem;
}

.login-card h2 {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text);
  margin: 0;
}

.login-card p {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
}

.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.password-input {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  color: var(--text);
  background: var(--input-bg);
  outline: none;
  width: 100%;
  transition: border-color 0.18s;
  text-align: center;
}

.password-input:focus {
  border-color: var(--primary);
}

.btn-login {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  transition: opacity 0.15s;
}

.btn-login:hover {
  opacity: 0.9;
}

.btn-cancel {
  text-decoration: none;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: 0.5rem;
}

.btn-cancel:hover {
  color: var(--text);
  text-decoration: underline;
}
</style>