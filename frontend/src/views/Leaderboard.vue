<!-- <script setup>      
import { ref,onMounted } from "vue"
import API from "../services/api"
const leaderboard = ref([])      
const getLeaderboard = async ()=>{
  const response = await API.get("/api/leaderboard")
  leaderboard.value = response.data
}
onMounted(()=>{     
  getLeaderboard()
})
</script>
<template>
<div class="container mt-4">
  <h2>🏆 Leaderboard</h2>
  <table class="table table-bordered mt-4">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Employee ID</th>
        <th>Name</th>
        <th>Total Points</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="user in leaderboard"
        :key="user.employee_id">
        <td>{{ user.rank }}</td>
        <td>{{ user.employee_id }}</td>
        <td>{{ user.name }}</td>
        <td>{{ user.total_points }}</td>
      </tr>
    </tbody>
  </table>
</div>
</template> -->
<script setup>
import { ref, onMounted, computed } from "vue"
import API from "../services/api"

const leaderboard = ref([])
const challenges = ref([])
const selectedChallenge = ref("")
const loading = ref(false)

const top3 = computed(() => leaderboard.value.slice(0, 3))
const rest = computed(() => leaderboard.value.slice(3))
const isReviewer = localStorage.getItem("reviewerAuth") === "true"
const currentChallengeName = computed(() => {
  if (!selectedChallenge.value) return "All Time"
  return challenges.value.find(c => String(c.id) === String(selectedChallenge.value))?.name || ""
})

const load = async () => {
  loading.value = true
  try {
    const [lbRes, chalRes] = await Promise.all([
      API.get("/api/leaderboard", { params: { challenge_id: selectedChallenge.value || undefined } }),
      API.get("/api/challenges"),
    ])
    leaderboard.value = lbRes.data.entries || []
    challenges.value = chalRes.data
    if (!selectedChallenge.value && lbRes.data.challenge_id) {
      selectedChallenge.value = String(lbRes.data.challenge_id)
    }
  } catch {}
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="top-actions">
      <router-link v-if="isReviewer" to="/reviewer"class="back-btn">← Back To Dashboard</router-link>
      <router-link v-else to="/submit" class="back-btn">← Submit Activity</router-link>
    </div>
    <div class="page-header">
      <span class="trophy">🏆</span>
      <h1>Leaderboard</h1>
      <p>Shape Up Challenge</p>
      <div class="challenge-select-wrap">
        <select class="challenge-select" v-model="selectedChallenge" @change="load">
          <option value="">All Time</option>
          <option v-for="c in challenges" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="period-badge">{{ currentChallengeName }}</div>
    </div>

    <div v-if="loading" class="loading-state">Loading…</div>

    <!-- Podium -->
    <div v-if="!loading && top3.length" class="podium-row">
      <div v-if="top3[1]" class="podium-card podium-2">
        <div class="podium-medal">🥈</div>
        <div class="podium-rank">#2</div>
        <div class="podium-name">{{ top3[1].name }}</div>
        <div class="podium-id">{{ top3[1].employee_id }}</div>
        <div class="podium-pts">{{ top3[1].total_points }} <span class="pts-label">pts</span></div>
        <div class="podium-subs">{{ top3[1].submission_count }} days</div>
      </div>
      <div v-if="top3[0]" class="podium-card podium-1">
        <div class="podium-crown">👑</div>
        <div class="podium-medal">🥇</div>
        <div class="podium-rank">#1</div>
        <div class="podium-name">{{ top3[0].name }}</div>
        <div class="podium-id">{{ top3[0].employee_id }}</div>
        <div class="podium-pts">{{ top3[0].total_points }} <span class="pts-label">pts</span></div>
        <div class="podium-subs">{{ top3[0].submission_count }} days</div>
      </div>
      <div v-if="top3[2]" class="podium-card podium-3">
        <div class="podium-medal">🥉</div>
        <div class="podium-rank">#3</div>
        <div class="podium-name">{{ top3[2].name }}</div>
        <div class="podium-id">{{ top3[2].employee_id }}</div>
        <div class="podium-pts">{{ top3[2].total_points }} <span class="pts-label">pts</span></div>
        <div class="podium-subs">{{ top3[2].submission_count }} days</div>
      </div>
    </div>

    <!-- Rest of rankings -->
    <div v-if="!loading && rest.length" class="table-card">
      <div class="table-card-header">Full Rankings</div>
      <table class="rank-table">
        <thead><tr><th>Rank</th><th>Employee ID</th><th>Name</th><th>Days Active</th><th>Total Points</th></tr></thead>
        <tbody>
          <tr v-for="user in rest" :key="user.employee_id">
            <td class="cell-rank">{{ user.rank }}</td>
            <td class="cell-id">{{ user.employee_id }}</td>
            <td class="cell-name">{{ user.name }}</td>
            <td class="cell-days">{{ user.submission_count }}</td>
            <td class="cell-pts">{{ user.total_points }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && !leaderboard.length" class="empty-state">
      <div class="empty-icon">🏁</div>
      <div class="empty-title">No results yet</div>
      <div class="empty-sub">Approved submissions will appear here</div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: calc(100vh - 56px);
  background: linear-gradient(160deg, #0F172A 0%, #1E1B4B 60%, #1E293B 100%);
  padding: 2.5rem 1.5rem 4rem;
  display: flex; flex-direction: column; align-items: center; gap: 2rem;
  font-family: 'Inter', system-ui, sans-serif;
}

.page-header { text-align: center; color: #fff; }
.trophy { font-size: 3rem; display: block; margin-bottom: 0.5rem; filter: drop-shadow(0 0 16px rgba(250,204,21,0.5)); }
.page-header h1 { font-size: 2.2rem; font-weight: 900; margin: 0 0 0.4rem; letter-spacing: -0.04em; background: linear-gradient(90deg, #FBBF24, #F97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.page-header p { color: #94A3B8; font-size: 0.9rem; margin: 0 0 1rem; }

.challenge-select-wrap { margin: 0.75rem 0 0.5rem; }
.challenge-select { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; border-radius: 10px; padding: 0.5rem 1rem; font-size: 0.88rem; outline: none; cursor: pointer; }
.period-badge { display: inline-block; background: rgba(99,102,241,0.3); border: 1px solid rgba(99,102,241,0.4); color: #A5B4FC; border-radius: 99px; padding: 0.3rem 1rem; font-size: 0.8rem; font-weight: 600; }

.loading-state { color: #94A3B8; }

.podium-row { display: flex; align-items: flex-end; justify-content: center; gap: 1rem; width: 100%; max-width: 680px; }
.podium-card { flex: 1; max-width: 200px; border-radius: 18px; padding: 1.5rem 1.25rem 1.75rem; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 0.3rem; position: relative; transition: transform 0.2s; }
.podium-card:hover { transform: translateY(-4px); }
.podium-1 { background: linear-gradient(160deg, #3B2F00, #78491A); border: 1.5px solid #FBBF24; box-shadow: 0 8px 40px rgba(251,191,36,0.25); padding-bottom: 2.25rem; }
.podium-2 { background: linear-gradient(160deg, #1E2A3A, #2C3E54); border: 1.5px solid #94A3B8; }
.podium-3 { background: linear-gradient(160deg, #2A1A10, #4A2D1A); border: 1.5px solid #D97706; }
.podium-crown { font-size: 1.4rem; position: absolute; top: -1rem; filter: drop-shadow(0 0 8px rgba(250,204,21,0.7)); }
.podium-medal { font-size: 1.8rem; }
.podium-rank { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #94A3B8; }
.podium-name { font-size: 1rem; font-weight: 700; color: #F1F5F9; margin-top: 0.1rem; }
.podium-id { font-size: 0.75rem; color: #64748B; font-family: monospace; }
.podium-pts { font-size: 1.5rem; font-weight: 900; color: #FBBF24; margin-top: 0.4rem; font-variant-numeric: tabular-nums; line-height: 1; }
.podium-2 .podium-pts, .podium-3 .podium-pts { color: #CBD5E1; }
.podium-subs { font-size: 0.72rem; color: #64748B; }
.pts-label { font-size: 0.72rem; font-weight: 500; color: #64748B; vertical-align: middle; }

.table-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; overflow: hidden; width: 100%; max-width: 680px; backdrop-filter: blur(8px); }
.table-card-header { padding: 1rem 1.5rem; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #64748B; border-bottom: 1px solid rgba(255,255,255,0.06); }
.rank-table { width: 100%; border-collapse: collapse; }
.rank-table th { text-align: left; padding: 0.65rem 1.25rem; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: #475569; background: rgba(255,255,255,0.03); border-bottom: 1px solid rgba(255,255,255,0.05); }
.rank-table tbody tr { border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.15s; }
.rank-table tbody tr:hover { background: rgba(255,255,255,0.04); }
.rank-table tbody tr:last-child { border-bottom: none; }
.rank-table td { padding: 0.85rem 1.25rem; font-size: 0.9rem; color: #CBD5E1; }
.cell-rank { font-weight: 700; color: #6366F1; font-size: 0.85rem; width: 60px; }
.cell-id { font-family: monospace; font-size: 0.82rem; color: #475569; }
.cell-name { font-weight: 600; color: #E2E8F0; }
.cell-days { color: #64748B; font-size: 0.82rem; }
.cell-pts { font-weight: 700; color: #A5B4FC; font-variant-numeric: tabular-nums; }

.empty-state { text-align: center; padding: 3rem; color: #475569; }
.empty-icon { font-size: 3rem; margin-bottom: 0.75rem; }
.empty-title { font-size: 1.1rem; font-weight: 700; color: #64748B; }
.empty-sub { font-size: 0.85rem; margin-top: 0.35rem; }

.top-actions{
  width:100%;
  max-width:900px;
  margin-bottom:1rem;
}

.back-btn{
  display:inline-flex;
  align-items:center;
  gap:8px;

  background:rgba(255,255,255,0.08);
  border:1px solid rgba(255,255,255,0.1);

  color:#E2E8F0;
  text-decoration:none;

  padding:0.75rem 1rem;
  border-radius:12px;

  font-size:0.9rem;
  font-weight:600;

  transition:all .2s ease;
}

.back-btn:hover{
  background:rgba(255,255,255,0.12);
  transform:translateY(-2px);
}

.podium-1 {
  animation: championFloat 3s ease-in-out infinite;
}

@keyframes championFloat {
  0%,100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-6px);
  }
}
</style>