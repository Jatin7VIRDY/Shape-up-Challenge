<script setup>
import { ref, onMounted, computed } from "vue"
import API from "../services/api"
import Swal from "sweetalert2"

const BACKEND = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000"

// Authentication
const passwordInput = ref("")
const isAuthenticated = ref(localStorage.getItem("reviewerAuth") === "true")

// Upload States
const sessionId = ref(localStorage.getItem("winnerSessionId") || "")
const uploads = ref({
  day0: { file: null, name: "", loading: false, errors: [], total_rows: 0, valid_count: 0, incomplete_count: 0, incomplete_participants: [] },
  day45: { file: null, name: "", loading: false, errors: [], total_rows: 0, valid_count: 0, incomplete_count: 0, incomplete_participants: [] },
  day90: { file: null, name: "", loading: false, errors: [], total_rows: 0, valid_count: 0, incomplete_count: 0, incomplete_participants: [] },
})

// Processing States
const isCalculating = ref(false)
const calculationErrors = ref([])
const calculationWarnings = ref([])

// Results
const summary = ref(null)
const rankings = ref([]) // original rankings from backend
const incompleteRecords = ref([])
const searchQuery = ref("")
const topN = ref("10") // "10", "25", "50", "all"

// Sorting
const sortBy = ref("final_score")
const sortDesc = ref(true)

const verifyPassword = async () => {
  if (passwordInput.value === "ctrlaltheal") {
    localStorage.setItem("reviewerAuth", "true")
    isAuthenticated.value = true
  } else {
    await Swal.fire({
      icon: "error",
      title: "Access Denied",
      text: "Incorrect password, please try again."
    })
    passwordInput.value = ""
  }
}

// File Upload Handler
const handleFileUpload = async (event, day) => {
  const file = event.target.files[0]
  if (!file) return

  // Validate extension locally first
  const ext = file.name.split(".").pop().toLowerCase()
  if (ext !== "xlsx" && ext !== "xls") {
    uploads.value[day].errors = ["Only Excel files (.xlsx, .xls) are allowed."]
    return
  }

  uploads.value[day].loading = true
  uploads.value[day].errors = []
  
  const formData = new FormData()
  formData.append("file", file)
  formData.append("day", day)
  if (sessionId.value) {
    formData.append("session_id", sessionId.value)
  }

  try {
    const res = await API.post("/api/winner/upload", formData)
    
    if (res.data.success) {
      if (res.data.session_id) {
        sessionId.value = res.data.session_id
        localStorage.setItem("winnerSessionId", res.data.session_id)
      }
      uploads.value[day].name = file.name
      uploads.value[day].file = file
      uploads.value[day].total_rows = res.data.total_rows || 0
      uploads.value[day].valid_count = res.data.valid_count || 0
      uploads.value[day].incomplete_count = res.data.incomplete_count || 0
      uploads.value[day].incomplete_participants = res.data.incomplete_participants || []
      
      // Clear warnings/errors
      uploads.value[day].errors = []
      Swal.fire({
        toast: true,
        position: "top-end",
        icon: "success",
        title: res.data.message,
        showConfirmButton: false,
        timer: 3000
      })
    }
  } catch (err) {
    const backendErrors = err.response?.data?.errors || [err.response?.data?.message || err.message]
    uploads.value[day].errors = backendErrors
    uploads.value[day].name = ""
    uploads.value[day].file = null
    // Reset file input
    event.target.value = ""
  } finally {
    uploads.value[day].loading = false
  }
}

// Check if all files are uploaded
const canCalculate = computed(() => {
  return uploads.value.day0.file && uploads.value.day45.file && uploads.value.day90.file
})

// Calculate winner
const calculateWinner = async () => {
  if (!canCalculate.value) return

  isCalculating.value = true
  calculationErrors.value = []
  calculationWarnings.value = []
  summary.value = null
  rankings.value = []
  incompleteRecords.value = []

  try {
    let res
    const hasAllRealFiles = 
      uploads.value.day0.file instanceof File &&
      uploads.value.day45.file instanceof File &&
      uploads.value.day90.file instanceof File

    if (hasAllRealFiles) {
      const formData = new FormData()
      if (sessionId.value) formData.append("session_id", sessionId.value)
      formData.append("day0", uploads.value.day0.file)
      formData.append("day45", uploads.value.day45.file)
      formData.append("day90", uploads.value.day90.file)
      res = await API.post("/api/winner/calculate", formData)
    } else {
      res = await API.post("/api/winner/calculate", {
        session_id: sessionId.value
      })
    }

    if (res.data.success) {
      if (res.data.session_id) {
        sessionId.value = res.data.session_id
        localStorage.setItem("winnerSessionId", res.data.session_id)
      }
      summary.value = res.data.summary
      rankings.value = res.data.rankings
      incompleteRecords.value = res.data.incomplete_records || []
      calculationWarnings.value = res.data.warnings || []
      
      Swal.fire({
        icon: "success",
        title: "Winner Declared!",
        text: `The winner is ${summary.value.winner_name} with a final score of ${summary.value.winner_final_score}!`,
        confirmButtonText: "View Leaderboard"
      })
    }
  } catch (err) {
    const msg = err.response?.data?.message || err.message || "Calculation failed"
    const backendErrors = err.response?.data?.errors || [msg]
    calculationErrors.value = backendErrors

    // If session expired or missing files on backend, clear local session state so user can re-upload easily
    if (err.response?.status === 404 || msg.includes("session") || msg.includes("Missing files")) {
      sessionId.value = ""
      localStorage.removeItem("winnerSessionId")
      uploads.value = {
        day0: { file: null, name: "", loading: false, errors: [], total_rows: 0, valid_count: 0, incomplete_count: 0, incomplete_participants: [] },
        day45: { file: null, name: "", loading: false, errors: [], total_rows: 0, valid_count: 0, incomplete_count: 0, incomplete_participants: [] },
        day90: { file: null, name: "", loading: false, errors: [], total_rows: 0, valid_count: 0, incomplete_count: 0, incomplete_participants: [] },
      }
    }

    Swal.fire({
      icon: "error",
      title: "Calculation Failed",
      text: msg
    })
  } finally {
    isCalculating.value = false
  }
}

// Export Excel handler with check
const exportExcel = (type) => {
  if (!sessionId.value) {
    Swal.fire({
      icon: "warning",
      title: "No Session Found",
      text: "Please upload participant Excel files and calculate rankings before exporting."
    })
    return
  }
  const exportUrl = `${BACKEND}/api/winner/export?session_id=${sessionId.value}&type=${type}`
  window.open(exportUrl, "_blank")
}

// Reset Session
const resetSession = () => {
  Swal.fire({
    title: "Reset Uploaded Files?",
    text: "This will clear all current uploads and calculations.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Yes, reset"
  }).then((result) => {
    if (result.isConfirmed) {
      sessionId.value = ""
      localStorage.removeItem("winnerSessionId")
      uploads.value = {
        day0: { file: null, name: "", loading: false, errors: [] },
        day45: { file: null, name: "", loading: false, errors: [] },
        day90: { file: null, name: "", loading: false, errors: [] },
      }
      summary.value = null
      rankings.value = []
      calculationErrors.value = []
      calculationWarnings.value = []
    }
  })
}

// Sorting logic
const toggleSort = (field) => {
  if (sortBy.value === field) {
    sortDesc.value = !sortDesc.value
  } else {
    sortBy.value = field
    sortDesc.value = true
  }
}

// Filtered and Sorted Rankings
const processedRankings = computed(() => {
  let list = [...rankings.value]

  // Apply search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    list = list.filter(
      r => 
        r.name.toLowerCase().includes(query) || 
        r.employee_id.toLowerCase().includes(query)
    )
  }

  // Apply sorting
  list.sort((a, b) => {
    let valA = a[sortBy.value]
    let valB = b[sortBy.value]

    if (typeof valA === "string") {
      valA = valA.toLowerCase()
      valB = valB.toLowerCase()
    }

    if (valA < valB) return sortDesc.value ? 1 : -1
    if (valA > valB) return sortDesc.value ? -1 : 1
    return 0
  })

  // Apply top N limit
  if (topN.value !== "all") {
    const limit = parseInt(topN.value, 10)
    list = list.slice(0, limit)
  }

  return list
})

// Podium performers
const podium = computed(() => {
  if (rankings.value.length < 1) return []
  
  const top3 = rankings.value.slice(0, 3)
  const result = []
  
  // Return in order [2nd, 1st, 3rd] for visual podium positioning
  if (top3[1]) result.push({ ...top3[1], place: 2, icon: "🥈", medal: "silver" })
  if (top3[0]) result.push({ ...top3[0], place: 1, icon: "🥇", medal: "gold" })
  if (top3[2]) result.push({ ...top3[2], place: 3, icon: "🥉", medal: "bronze" })
  
  // If only 1 or 2 participants, sort them by place
  if (top3.length === 1) return [{ ...top3[0], place: 1, icon: "🥇", medal: "gold" }]
  
  return result
})

// Printing
const triggerPrint = () => {
  window.print()
}

onMounted(() => {
  // Clear any unverified local session state on mount so uploads are clean
  if (sessionId.value && !uploads.value.day0.file) {
    // If no active File objects in memory, let user upload fresh or calculate cleanly
  }
})
</script>

<template>
  <div class="page">
    <!-- lock overlay if not authenticated -->
    <div v-if="!isAuthenticated" class="login-overlay">
      <div class="login-card">
        <span class="lock-icon">🔒</span>
        <h2>Winner Declaration Panel</h2>
        <p>Please enter your access password to continue.</p>
        <form @submit.prevent="verifyPassword" class="login-form">
          <input
            type="password"
            v-model="passwordInput"
            placeholder="Enter password..."
            class="password-input"
            required
          />
          <button type="submit" class="btn-login">Unlock Page →</button>
        </form>
        <router-link to="/reviewer" class="btn-cancel">← Back to Dashboard</router-link>
      </div>
    </div>

    <!-- Main Content -->
    <div v-else class="winner-content">
      <div class="page-header no-print">
        <div>
          <h1 class="page-title">🏆 Winner Declaration Module</h1>
          <p class="page-sub">Shape Up Challenge · Evaluate rankings & declare the winner</p>
        </div>
        <div class="header-actions">
          <router-link to="/reviewer" class="btn-back">← Reviewer Dashboard</router-link>
          <button v-if="sessionId" @click="resetSession" class="btn-reset">Reset Uploads</button>
        </div>
      </div>

      <!-- Upload Cards Section -->
      <div class="section-card upload-section no-print">
        <div class="section-title">
          <h3>📂 Upload Participant Data Sheets</h3>
          <p>Please upload the three required Excel files containing participant weight and body measurements.</p>
        </div>

        <div class="upload-grid">
          <!-- Card Day 0 -->
          <div class="upload-card" :class="{ uploaded: uploads.day0.file, error: uploads.day0.errors.length }">
            <div class="card-icon">📊</div>
            <h4>Day 0 (Baseline)</h4>
            <p class="card-desc">Initial measurements at start of challenge</p>
            
            <div class="file-info" v-if="uploads.day0.name">
              <span class="file-check">✓</span>
              <span class="file-name" :title="uploads.day0.name">{{ uploads.day0.name }}</span>
            </div>

            <label class="btn-upload" :class="{ disabled: uploads.day0.loading }">
              <span>{{ uploads.day0.name ? 'Replace File' : 'Choose Excel File' }}</span>
              <input type="file" accept=".xlsx, .xls" @change="handleFileUpload($event, 'day0')" :disabled="uploads.day0.loading" />
            </label>

            <div class="card-stats" v-if="uploads.day0.total_rows">
              <div class="stat-text">✓ {{ uploads.day0.total_rows }} rows processed</div>
              <div class="stat-text text-green font-semibold">{{ uploads.day0.valid_count }} eligible records</div>
              <div class="stat-text text-amber font-semibold" v-if="uploads.day0.incomplete_count">
                ⚠ {{ uploads.day0.incomplete_count }} incomplete records
              </div>
            </div>

            <div class="card-spinner" v-if="uploads.day0.loading">Validating...</div>

            <!-- Errors -->
            <div class="card-errors" v-if="uploads.day0.errors.length">
              <div v-for="(err, idx) in uploads.day0.errors" :key="idx" class="error-item">⚠️ {{ err }}</div>
            </div>
          </div>

          <!-- Card Day 45 -->
          <div class="upload-card" :class="{ uploaded: uploads.day45.file, error: uploads.day45.errors.length }">
            <div class="card-icon">📈</div>
            <h4>Day 45 (Mid Challenge)</h4>
            <p class="card-desc">Midway measurements for history/graphs</p>
            
            <div class="file-info" v-if="uploads.day45.name">
              <span class="file-check">✓</span>
              <span class="file-name" :title="uploads.day45.name">{{ uploads.day45.name }}</span>
            </div>

            <label class="btn-upload" :class="{ disabled: uploads.day45.loading }">
              <span>{{ uploads.day45.name ? 'Replace File' : 'Choose Excel File' }}</span>
              <input type="file" accept=".xlsx, .xls" @change="handleFileUpload($event, 'day45')" :disabled="uploads.day45.loading" />
            </label>

            <div class="card-stats" v-if="uploads.day45.total_rows">
              <div class="stat-text">✓ {{ uploads.day45.total_rows }} rows processed</div>
              <div class="stat-text text-green font-semibold">{{ uploads.day45.valid_count }} eligible records</div>
              <div class="stat-text text-amber font-semibold" v-if="uploads.day45.incomplete_count">
                ⚠ {{ uploads.day45.incomplete_count }} incomplete records
              </div>
            </div>

            <div class="card-spinner" v-if="uploads.day45.loading">Validating...</div>

            <!-- Errors -->
            <div class="card-errors" v-if="uploads.day45.errors.length">
              <div v-for="(err, idx) in uploads.day45.errors" :key="idx" class="error-item">⚠️ {{ err }}</div>
            </div>
          </div>

          <!-- Card Day 90 -->
          <div class="upload-card" :class="{ uploaded: uploads.day90.file, error: uploads.day90.errors.length }">
            <div class="card-icon">🏁</div>
            <h4>Day 90 (Final)</h4>
            <p class="card-desc">Final measurements at end of challenge</p>
            
            <div class="file-info" v-if="uploads.day90.name">
              <span class="file-check">✓</span>
              <span class="file-name" :title="uploads.day90.name">{{ uploads.day90.name }}</span>
            </div>

            <label class="btn-upload" :class="{ disabled: uploads.day90.loading }">
              <span>{{ uploads.day90.name ? 'Replace File' : 'Choose Excel File' }}</span>
              <input type="file" accept=".xlsx, .xls" @change="handleFileUpload($event, 'day90')" :disabled="uploads.day90.loading" />
            </label>

            <div class="card-stats" v-if="uploads.day90.total_rows">
              <div class="stat-text">✓ {{ uploads.day90.total_rows }} rows processed</div>
              <div class="stat-text text-green font-semibold">{{ uploads.day90.valid_count }} eligible records</div>
              <div class="stat-text text-amber font-semibold" v-if="uploads.day90.incomplete_count">
                ⚠ {{ uploads.day90.incomplete_count }} incomplete records
              </div>
            </div>

            <div class="card-spinner" v-if="uploads.day90.loading">Validating...</div>

            <!-- Errors -->
            <div class="card-errors" v-if="uploads.day90.errors.length">
              <div v-for="(err, idx) in uploads.day90.errors" :key="idx" class="error-item">⚠️ {{ err }}</div>
            </div>
          </div>
        </div>

        <div class="action-bar">
          <button class="btn-calculate" :disabled="!canCalculate || isCalculating" @click="calculateWinner">
            <span v-if="isCalculating" class="spinner-icon">⏳</span>
            <span>{{ isCalculating ? 'Processing and Merging Data...' : '🏆 Declare Winner & Generate Rankings' }}</span>
          </button>
        </div>
      </div>

      <!-- Calculation Errors -->
      <div class="alert alert-danger no-print" v-if="calculationErrors.length">
        <h4>⚠️ Calculation Blocked due to data errors</h4>
        <ul>
          <li v-for="(err, idx) in calculationErrors" :key="idx">{{ err }}</li>
        </ul>
      </div>

      <!-- Spinner for Calculation -->
      <div class="loading-overlay-block no-print" v-if="isCalculating">
        <div class="spinner"></div>
        <h4>Analyzing measurements spreadsheets...</h4>
        <p>Merging records, calculating Weight Loss % and Waist-Hip Ratio improvements, and normalizing scores.</p>
      </div>

      <!-- Results view -->
      <div v-if="summary" class="results-container">
        
        <!-- Warnings Alert (Non-blocking) -->
        <div class="alert alert-warning no-print" v-if="calculationWarnings.length">
          <h4>⚠️ Data Warnings (Processed successfully, but check notes)</h4>
          <div class="warning-list-scroll">
            <ul>
              <li v-for="(warn, idx) in calculationWarnings" :key="idx">{{ warn }}</li>
            </ul>
          </div>
        </div>

        <!-- Winner Summary Cards -->
        <div class="results-header-summary">
          <div class="summary-card gold-border">
            <div class="summary-icon">👑</div>
            <div class="summary-info">
              <span class="summary-label">Winner Name</span>
              <span class="summary-value">{{ summary.winner_name }}</span>
              <span class="summary-sub">ID: {{ summary.winner_employee_id }}</span>
            </div>
          </div>

          <div class="summary-card">
            <div class="summary-icon">💯</div>
            <div class="summary-info">
              <span class="summary-label">Winner Final Score</span>
              <span class="summary-value">{{ summary.winner_final_score }}</span>
              <span class="summary-sub">Normalized Index</span>
            </div>
          </div>

          <div class="summary-card">
            <div class="summary-icon">👥</div>
            <div class="summary-info">
              <span class="summary-label">Participants Processed</span>
              <span class="summary-value">{{ summary.total_participants }}</span>
              <span class="summary-sub">Common in Day 0 & 90</span>
            </div>
          </div>

          <div class="summary-card">
            <div class="summary-icon">🔥</div>
            <div class="summary-info">
              <span class="summary-label">Highest Weight Loss</span>
              <span class="summary-value">{{ summary.highest_weight_loss }}%</span>
              <span class="summary-sub">Max Weight Loss %</span>
            </div>
          </div>

          <div class="summary-card">
            <div class="summary-icon">⚡</div>
            <div class="summary-info">
              <span class="summary-label">Highest WHR Improvement</span>
              <span class="summary-value">{{ summary.highest_whr_improvement }}%</span>
              <span class="summary-sub">Max WHR Ratio Imp</span>
            </div>
          </div>
        </div>

        <!-- Incomplete Participant Data Section -->
        <div class="section-card incomplete-section no-print" v-if="incompleteRecords.length">
          <div class="incomplete-hdr">
            <h3>⚠ Incomplete Participant Data</h3>
            <p class="incomplete-sub">
              <strong>{{ summary?.eligible_count }}</strong> participants eligible for ranking · 
              <strong>{{ incompleteRecords.length }}</strong> participants excluded due to incomplete measurement records
            </p>
          </div>

          <div class="table-wrap">
            <table class="rankings-table incomplete-table">
              <thead>
                <tr>
                  <th>Participant</th>
                  <th>Stage</th>
                  <th>Missing / Issues</th>
                  <th>Status</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(inc, idx) in incompleteRecords" :key="idx" class="row-incomplete">
                  <td class="font-bold">{{ inc.participant }}</td>
                  <td><span class="stage-tag">{{ inc.stage }}</span></td>
                  <td class="text-amber font-mono">{{ inc.missing_data }}</td>
                  <td><span class="badge-incomplete">{{ inc.status }}</span></td>
                  <td class="text-muted text-sm">{{ inc.reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top 3 Podium Section -->
        <div class="podium-section no-print">
          <h3 class="section-hdr">🏆 Podium Finishes</h3>
          <div class="podium-wrapper">
            <div v-for="p in podium" :key="p.employee_id" class="podium-card" :class="`podium-${p.medal}`">
              <div class="podium-place-badge">{{ p.icon }} {{ p.place }}</div>
              <h4 class="podium-name">{{ p.name }}</h4>
              <p class="podium-id">ID: {{ p.employee_id }}</p>
              <div class="podium-divider"></div>
              <div class="podium-stat">
                <span>Weight Loss:</span>
                <strong>{{ p.weight_loss_percent }}%</strong>
              </div>
              <div class="podium-stat">
                <span>WHR Imp:</span>
                <strong>{{ p.whr_improvement_percent }}%</strong>
              </div>
              <div class="podium-score-pill">
                <span>Final Score:</span>
                <strong>{{ p.final_score }}</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- Rankings Leaderboard -->
        <div class="section-card leaderboard-section">
          <div class="leaderboard-hdr no-print">
            <h3>📊 Challenge Leaderboard</h3>
            <div class="table-actions">
              <input type="text" v-model="searchQuery" placeholder="🔍 Search participant name or ID..." class="search-input" />
              
              <div class="select-wrapper">
                <label>Show: </label>
                <select v-model="topN" class="top-select">
                  <option value="10">Top 10</option>
                  <option value="25">Top 25</option>
                  <option value="50">Top 50</option>
                  <option value="all">All</option>
                </select>
              </div>

              <div class="btn-group">
                <button @click="exportExcel('all')" class="btn-export-full">💾 Full Excel</button>
                <button @click="exportExcel('top10')" class="btn-export-top10">💾 Top 10 Excel</button>
                <button @click="triggerPrint" class="btn-print">🖨️ Print Results</button>
              </div>
            </div>
          </div>

          <!-- Printable Header (Hidden in UI, visible in Print) -->
          <div class="print-only-header">
            <h2>Shape Up Challenge - Winner Declaration Results</h2>
            <p>Session ID: {{ sessionId }} | Total Participants: {{ summary.total_participants }}</p>
            <p>Winner: <strong>{{ summary.winner_name }} ({{ summary.winner_employee_id }})</strong> with Score: <strong>{{ summary.winner_final_score }}</strong></p>
            <p>Highest Weight Loss: {{ summary.highest_weight_loss }}% | Highest WHR Improvement: {{ summary.highest_whr_improvement }}%</p>
          </div>

          <!-- Leaderboard Table -->
          <div class="table-wrap">
            <table class="rankings-table">
              <thead>
                <tr>
                  <th @click="toggleSort('rank')" class="sortable">Rank <span v-if="sortBy === 'rank'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('employee_id')" class="sortable">Employee ID <span v-if="sortBy === 'employee_id'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('name')" class="sortable">Name <span v-if="sortBy === 'name'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('day0_weight')" class="sortable">Day 0 Weight <span v-if="sortBy === 'day0_weight'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('day90_weight')" class="sortable">Day 90 Weight <span v-if="sortBy === 'day90_weight'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('weight_loss_percent')" class="sortable">Weight Loss % <span v-if="sortBy === 'weight_loss_percent'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('day0_whr')" class="sortable">Day 0 WHR <span v-if="sortBy === 'day0_whr'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('day90_whr')" class="sortable">Day 90 WHR <span v-if="sortBy === 'day90_whr'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('whr_improvement_percent')" class="sortable">WHR Imp % <span v-if="sortBy === 'whr_improvement_percent'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                  <th @click="toggleSort('final_score')" class="sortable header-highlight">Final Score <span v-if="sortBy === 'final_score'">{{ sortDesc ? '▼' : '▲' }}</span></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in processedRankings" :key="r.employee_id" :class="{ 'row-winner': r.rank === 1 }">
                  <td class="cell-rank">
                    <span v-if="r.rank === 1">🥇</span>
                    <span v-else-if="r.rank === 2">🥈</span>
                    <span v-else-if="r.rank === 3">🥉</span>
                    <span v-else>{{ r.rank }}</span>
                  </td>
                  <td class="cell-id">{{ r.employee_id }}</td>
                  <td class="cell-name font-bold">{{ r.name }}</td>
                  <td>{{ r.day0_weight }} kg</td>
                  <td>{{ r.day90_weight }} kg</td>
                  <td :class="r.weight_loss_percent > 0 ? 'text-green font-semibold' : 'text-muted'">
                    {{ r.weight_loss_percent > 0 ? '+' : '' }}{{ r.weight_loss_percent }}%
                  </td>
                  <td class="font-mono">{{ r.day0_whr }}</td>
                  <td class="font-mono">{{ r.day90_whr }}</td>
                  <td :class="r.whr_improvement_percent > 0 ? 'text-green font-semibold' : 'text-muted'">
                    {{ r.whr_improvement_percent > 0 ? '+' : '' }}{{ r.whr_improvement_percent }}%
                  </td>
                  <td class="cell-score font-bold">{{ r.final_score }}</td>
                </tr>
                <tr v-if="processedRankings.length === 0">
                  <td colspan="10" class="empty-state">No matching participant records found.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: calc(100vh - 56px);
  background: var(--bg);
  padding: 2rem 1.5rem 4rem;
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text);
}

.winner-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
}

/* Authentication Overlay */
.login-overlay {
  min-height: calc(100vh - 120px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 3rem 2rem;
  border-radius: 20px;
  text-align: center;
  box-shadow: var(--shadow);
  max-width: 420px;
  width: 100%;
  transition: transform 0.2s ease;
}

.lock-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1.5rem;
}

.login-card h2 {
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: var(--text-h);
}

.login-card p {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin-bottom: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.password-input {
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  outline: none;
  background: var(--input-bg);
  color: var(--text);
  text-align: center;
  transition: border-color 0.2s;
}

.password-input:focus {
  border-color: var(--primary);
}

.btn-login {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.8rem;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-login:hover {
  opacity: 0.9;
}

.btn-cancel {
  display: block;
  margin-top: 1.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 600;
}

.btn-cancel:hover {
  color: var(--primary);
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-h);
  margin: 0;
}

.page-sub {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-back {
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  cursor: pointer;
}

.btn-back:hover {
  background: var(--hover-bg);
}

.btn-reset {
  padding: 0.5rem 1rem;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--red);
  background: var(--surface);
  border: 1px solid var(--border);
  cursor: pointer;
}

.btn-reset:hover {
  background: #fee2e2;
}

/* Upload Section */
.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.section-title {
  margin-bottom: 1.5rem;
}

.section-title h3 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-h);
  margin: 0;
}

.section-title p {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 900px) {
  .upload-grid {
    grid-template-columns: 1fr;
  }
}

.upload-card {
  border: 2px dashed var(--border);
  border-radius: 16px;
  padding: 2rem 1.5rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--surface2);
  transition: all 0.2s ease;
  position: relative;
}

.upload-card.uploaded {
  border-color: var(--green);
  background: var(--primary-light);
}

.upload-card.error {
  border-color: var(--red);
  background: #fff5f5;
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.upload-card h4 {
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
  color: var(--text-h);
}

.card-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 0.4rem 0.8rem;
  border-radius: 10px;
  margin-bottom: 1.25rem;
  max-width: 100%;
}

.file-check {
  color: var(--green);
  font-weight: bold;
}

.file-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-upload {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 0.45rem 1rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text);
  cursor: pointer;
  display: inline-block;
  transition: all 0.2s;
}

.btn-upload input[type="file"] {
  display: none;
}

.btn-upload:hover {
  background: var(--hover-bg);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-upload.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.card-spinner {
  font-size: 0.8rem;
  color: var(--primary);
  margin-top: 0.75rem;
}

.card-errors {
  margin-top: 1rem;
  background: #fee2e2;
  border-radius: 8px;
  padding: 0.5rem;
  text-align: left;
  width: 100%;
  max-height: 120px;
  overflow-y: auto;
}

.error-item {
  font-size: 0.72rem;
  color: var(--red);
  margin-bottom: 0.25rem;
  line-height: 1.3;
}

.error-item:last-child {
  margin-bottom: 0;
}

.action-bar {
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
}

.btn-calculate {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.9rem 2rem;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.btn-calculate:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
}

.btn-calculate:disabled {
  background: var(--border);
  color: var(--text-muted);
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* Alerts */
.alert {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.alert h4 {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
  font-weight: 700;
}

.alert ul {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.85rem;
}

.alert li {
  margin-bottom: 0.25rem;
}

.alert-danger {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.alert-warning {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.warning-list-scroll {
  max-height: 150px;
  overflow-y: auto;
}

/* Spinner Block */
.loading-overlay-block {
  text-align: center;
  padding: 3rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay-block h4 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.loading-overlay-block p {
  color: var(--text-muted);
  font-size: 0.85rem;
}

/* Results Header Summary */
.results-header-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}

@media (max-width: 1024px) {
  .results-header-summary {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 600px) {
  .results-header-summary {
    grid-template-columns: 1fr;
  }
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.summary-card.gold-border {
  border-color: #f59e0b;
  background: #fffbeb;
}

html.dark .summary-card.gold-border {
  background: #272217;
}

.summary-icon {
  font-size: 2.2rem;
}

.summary-info {
  display: flex;
  flex-direction: column;
}

.summary-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-h);
  line-height: 1.2;
  margin-top: 0.1rem;
}

.summary-sub {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.1rem;
}

/* Podium Section */
.podium-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2rem;
}

.section-hdr {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-h);
  margin-bottom: 2rem;
}

.podium-wrapper {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 1.5rem;
  width: 100%;
  max-width: 750px;
}

@media (max-width: 600px) {
  .podium-wrapper {
    flex-direction: column;
    align-items: stretch;
  }
}

.podium-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
  flex: 1;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: transform 0.2s;
}

.podium-card:hover {
  transform: translateY(-2px);
}

.podium-gold {
  border-color: #f59e0b;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.12);
  transform: scale(1.05);
  z-index: 2;
}

.podium-gold:hover {
  transform: scale(1.05) translateY(-2px);
}

.podium-silver {
  border-color: #94a3b8;
  box-shadow: 0 4px 15px rgba(148, 163, 184, 0.08);
}

.podium-bronze {
  border-color: #b45309;
  box-shadow: 0 4px 15px rgba(180, 83, 9, 0.08);
}

@media (max-width: 600px) {
  .podium-gold, .podium-gold:hover {
    transform: none;
  }
}

.podium-place-badge {
  font-size: 0.85rem;
  font-weight: 700;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 0.25rem 0.75rem;
  margin-bottom: 0.75rem;
}

.podium-gold .podium-place-badge {
  background: #fef3c7;
  color: #d97706;
  border-color: #fcd34d;
}

.podium-name {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-h);
  margin: 0;
}

.podium-id {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0.15rem 0 0;
}

.podium-divider {
  width: 80%;
  height: 1px;
  background: var(--border);
  margin: 1rem 0;
}

.podium-stat {
  font-size: 0.78rem;
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 0.25rem;
}

.podium-stat span {
  color: var(--text-muted);
}

.podium-stat strong {
  color: var(--text-h);
}

.podium-score-pill {
  margin-top: 1rem;
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  border-radius: 30px;
  padding: 0.35rem 0.85rem;
  font-size: 0.8rem;
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.podium-score-pill span {
  color: var(--accent);
  font-weight: 600;
}

.podium-score-pill strong {
  color: var(--accent);
  font-weight: bold;
}

/* Leaderboard Table Section */
.leaderboard-hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.leaderboard-hdr h3 {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-h);
  margin: 0;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.search-input {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 0.5rem 0.85rem;
  font-size: 0.85rem;
  color: var(--text);
  background: var(--surface);
  outline: none;
  min-width: 250px;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--primary);
}

.select-wrapper {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.top-select {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 0.48rem 0.6rem;
  font-size: 0.85rem;
  color: var(--text);
  background: var(--surface);
  outline: none;
  cursor: pointer;
}

.btn-group {
  display: flex;
  gap: 0.5rem;
}

.btn-export-full {
  text-decoration: none;
  padding: 0.5rem 0.85rem;
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #065f46;
  background: #d1fae5;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-export-full:hover {
  background: #a7f3d0;
}

.btn-export-top10 {
  text-decoration: none;
  padding: 0.5rem 0.85rem;
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e3a8a;
  background: #dbeafe;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-export-top10:hover {
  background: #bfdbfe;
}

.btn-print {
  padding: 0.5rem 0.85rem;
  border-radius: 10px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}

.btn-print:hover {
  background: var(--hover-bg);
}

/* Table Design */
.table-wrap {
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid var(--border);
}

.rankings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.rankings-table th {
  text-align: left;
  padding: 0.85rem 1rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
  user-select: none;
}

.rankings-table th.sortable {
  cursor: pointer;
}

.rankings-table th.sortable:hover {
  background: var(--border);
  color: var(--text-h);
}

.rankings-table th.header-highlight {
  background: var(--accent-bg);
  color: var(--accent);
}

.rankings-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}

.rankings-table tbody tr:last-child {
  border-bottom: none;
}

.rankings-table tbody tr:hover {
  background: var(--surface2);
}

.rankings-table tbody tr.row-winner {
  background: #fffbeb;
}

html.dark .rankings-table tbody tr.row-winner {
  background: #252118;
}

.rankings-table td {
  padding: 0.85rem 1rem;
  color: var(--text);
}

.cell-rank {
  font-weight: 700;
  width: 60px;
}

.cell-id {
  font-family: var(--mono);
  font-size: 0.8rem;
  color: var(--text-muted);
}

.cell-name {
  color: var(--text-h);
}

.cell-score {
  color: var(--accent);
  font-size: 0.95rem;
}

.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.font-mono { font-family: var(--mono); font-size: 0.82rem; }
.text-green { color: var(--green); }
.text-muted { color: var(--text-muted); }

.card-stats {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  align-items: center;
}

.stat-text {
  color: var(--text-muted);
}

.text-amber {
  color: #d97706;
}

.incomplete-section {
  background: #fffbeb;
  border-color: #fcd34d;
  margin-bottom: 1.5rem;
}

html.dark .incomplete-section {
  background: #231e13;
  border-color: #78350f;
}

.incomplete-hdr h3 {
  font-size: 1.15rem;
  font-weight: 700;
  color: #b45309;
  margin: 0 0 0.25rem;
}

.incomplete-sub {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0 0 1rem;
}

.stage-tag {
  background: var(--surface2);
  border: 1px solid var(--border);
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-incomplete {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
}

/* Print Styling */
.print-only-header {
  display: none;
}

@media print {
  body {
    background: white;
    color: black;
  }
  .no-print {
    display: none !important;
  }
  .page {
    padding: 0;
    min-height: auto;
    background: white;
  }
  .winner-content {
    gap: 0;
  }
  .section-card {
    border: none;
    box-shadow: none;
    padding: 0;
  }
  .table-wrap {
    border: none;
  }
  .rankings-table {
    font-size: 10pt;
  }
  .rankings-table th, .rankings-table td {
    padding: 6pt;
    border-bottom: 1px solid #ccc !important;
  }
  .print-only-header {
    display: block;
    margin-bottom: 20pt;
    border-bottom: 2px solid black;
    padding-bottom: 10pt;
  }
  .print-only-header h2 {
    margin: 0 0 5pt;
  }
  .print-only-header p {
    margin: 2pt 0;
    font-size: 9pt;
    color: #333;
  }
}
</style>
