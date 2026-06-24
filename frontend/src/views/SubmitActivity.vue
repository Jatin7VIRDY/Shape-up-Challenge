<!-- <script setup>
import { ref } from "vue"
import axios from "axios"
import API from "../services/api"
const employee_id = ref("")
const name = ref("")
const steps = ref("") 
const stepsProof = ref(null)
const fitnessVideo = ref(null)
const foodPhoto = ref(null)  
const fitnessAttendanceProof = ref(null)  
const handleStepsProof = (e) => {
  stepsProof.value = e.target.files[0]
}    
const handleFitnessVideo = (e) => {
  fitnessVideo.value = e.target.files[0]
}  
const handleFoodPhoto = (e) => {
  foodPhoto.value = e.target.files[0]
}
const handleFitnessAttendanceProof = (e) => {
  fitnessAttendanceProof.value = e.target.files[0]
}
const submitForm = async () => {
  try {
    if (Number(steps.value) > 15000) {
        alert("Maximum 15000 steps allowed")
      return
    }
    const confirmed = confirm("Are you sure you want to submit?")  
    if (!confirmed) {
      return
    }
    const formData = new FormData()

    formData.append("employee_id",employee_id.value)
    formData.append("name",name.value)
    formData.append("steps",steps.value)

    if(stepsProof.value){
      formData.append("steps_proof",stepsProof.value)
    }
    if(fitnessVideo.value){
      formData.append("fitness_video",fitnessVideo.value) 
    }
    if (foodPhoto.value) {
      formData.append("food_photo", foodPhoto.value)
    }
    if (fitnessAttendanceProof.value) {
      formData.append("fitness_attendance_proof",fitnessAttendanceProof.value)}
    const response = await API.post(
      "/api/submission",
      formData,{
        headers: {
          "Content-Type": "multipart/form-data"
        }
      })
    alert("Submission Successful!")
    employeeId.value = ""
    name.value = ""
    steps.value = ""
    stepsProof.value = null
    fitnessVideo.value = null
    fitnessAttendanceProof.value = null
    foodPhoto.value = null
    console.log(response.data)
  } catch (error) {
    console.error(error);
    alert("Submission Failed!");
  }
};
</script>

<template>
  <div class="container mt-5">
    <h2 class="mb-4">Shape Up Challenge</h2>
    <form @submit.prevent="submitForm">
      <div class="mb-3">
        <label>Employee ID</label>
        <input v-model="employee_id" class="form-control" required/>
      </div>
      <div class="mb-3">
        <label>Name</label>
        <input v-model="name" class="form-control" required/>
      </div>
      <div class="mb-3">
        <label>Steps</label>
        <input v-model="steps" type="number" class="form-control" required/>
      </div>
      <div class="mb-3">
        <label>Steps Screenshot</label>
        <input type="file" class="form-control" @change="handleStepsProof"/>
      </div>
      <div class="mb-3">
        <label>Fitness Video</label>
        <input type="file" class="form-control" @change="handleFitnessVideo"/>
      </div>
      <div class="mb-3">
        <label>Fitness Atendance Screenshot</label>
        <input type="file" class="form-control" @change="handleFitnessAttendanceProof"/>
      </div>
      <div class="mb-3">
        <label>Food Photo</label>
        <input type="file" class="form-control" @change="handleFoodPhoto" />
      </div>
      <button class="btn btn-primary">Submit</button>
    </form>
  </div>
</template> -->
<script setup>
import { ref, onMounted } from "vue"
import API from "../services/api"
import Swal from "sweetalert2"
const employee_id = ref("")
const name = ref("")
const steps = ref("")
const activeChallenge = ref(null)
const loading = ref(false)
const toast = ref(null)   // { type: "success"|"error", msg }

const stepsProof = ref(null)
const fitnessVideo = ref(null)
const foodPhoto = ref(null)
const fitnessAttendanceProof = ref(null)

const handleStepsProof = (e) => { stepsProof.value = e.target.files[0] }
const handleFitnessVideo = (e) => { fitnessVideo.value = e.target.files[0] }
const handleFoodPhoto = (e) => { foodPhoto.value = e.target.files[0] }
const handleFitnessAttendanceProof = (e) => { fitnessAttendanceProof.value = e.target.files[0] }

const showToast = (type, msg) => {
  toast.value = { type, msg }
  setTimeout(() => { toast.value = null }, 4000)
}

onMounted(async () => {
  try {
    const { data } = await API.get("/api/challenges/active")
    activeChallenge.value = data
  } catch {}
})

const submitForm = async () => {
  if (loading.value) return
  const s = Number(steps.value)
  if (s > 15000) { await Swal.fire({
  icon: "error",
  title: "Invalid Steps",
  text: "Maximum 15000 steps allowed"
}); return }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append("employee_id", employee_id.value)
    formData.append("name", name.value)
    formData.append("steps", steps.value)
    if (activeChallenge.value) formData.append("challenge_id", activeChallenge.value.id)
    if (stepsProof.value) formData.append("steps_proof", stepsProof.value)
    if (fitnessVideo.value) formData.append("fitness_video", fitnessVideo.value)
    if (foodPhoto.value) formData.append("food_photo", foodPhoto.value)
    if (fitnessAttendanceProof.value) formData.append("fitness_attendance_proof", fitnessAttendanceProof.value)

    await API.post("/api/submission", formData, { headers: { "Content-Type": "multipart/form-data" } })
    await Swal.fire({
  icon: "success",
  title: "Submission Successful",
  text: "Your activity has been submitted."
})
    employee_id.value = ""; name.value = ""; steps.value = ""
    stepsProof.value = null; fitnessVideo.value = null
    fitnessAttendanceProof.value = null; foodPhoto.value = null
  } catch (error) {
    await Swal.fire({
  icon: "error",
  title: "Submission Failed",
  text: error?.response?.data?.message || "Something went wrong"
})
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-bg">
    <div class="form-card">

      <!-- Toast -->
      <transition name="toast-fade">
        <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
      </transition>

      <!-- Header -->
      <div class="form-header">
        <span class="header-icon">🏃</span>
        <h1>Shape Up Challenge</h1>
        <p v-if="activeChallenge">Active: <strong>{{ activeChallenge.name }}</strong></p>
        <p v-else>Log your daily wellness activity</p>
      </div>

      <form @submit.prevent="submitForm" class="form-body">

        <!-- Identity -->
        <div class="form-section">
          <div class="section-label">👤 Your Details</div>
          <div class="field-row">
            <div class="field">
              <label for="emp-id">Employee ID</label>
              <input id="emp-id" class="text-input" v-model="employee_id" placeholder="e.g. EMP001" required />
            </div>
            <div class="field">
              <label for="emp-name">Full Name</label>
              <input id="emp-name" class="text-input" v-model="name" placeholder="Your name" required />
            </div>
          </div>
        </div>

        <!-- Steps -->
        <div class="form-section">
          <div class="section-label">👟 Step Count</div>
          <div class="field">
            <label for="steps-input">
              Steps Today
              <span class="label-hint">max 15,000</span>
            </label>
            <input id="steps-input" class="text-input" v-model="steps" type="number" min="0" max="15000" placeholder="0" required />
            <div class="step-bar-track">
              <div class="step-bar-fill" :style="{ width: Math.min(((Number(steps) || 0) / 15000) * 100, 100) + '%' }"></div>
            </div>
            <div class="step-tally">{{ Number(steps) || 0 }} / 15,000 steps</div>
          </div>
        </div>

        <!-- Proof Uploads -->
        <div class="form-section">
          <div class="section-label">📎 Proof Uploads <span class="label-hint">all optional</span></div>
          <div class="upload-grid">
            <label class="upload-zone" :class="{ uploaded: stepsProof }">
              <input type="file" accept="image/*" @change="handleStepsProof" hidden />
              <span class="uz-icon">📸</span>
              <span class="uz-title">Steps Screenshot</span>
              <span class="uz-sub">{{ stepsProof?.name || 'Click to attach' }}</span>
            </label>
            <label class="upload-zone" :class="{ uploaded: fitnessVideo }">
              <input type="file" accept="video/*" @change="handleFitnessVideo" hidden />
              <span class="uz-icon">🎥</span>
              <span class="uz-title">Fitness Video</span>
              <span class="uz-sub">{{ fitnessVideo?.name || 'Click to attach' }}</span>
            </label>
            <label class="upload-zone" :class="{ uploaded: fitnessAttendanceProof }">
              <input type="file" accept="image/*" @change="handleFitnessAttendanceProof" hidden />
              <span class="uz-icon">🏋️</span>
              <span class="uz-title">Fitness Session Attendance</span>
              <span class="uz-sub">{{ fitnessAttendanceProof?.name || 'Click to attach' }}</span>
            </label>
            <label class="upload-zone" :class="{ uploaded: foodPhoto }">
              <input type="file" accept="image/*" @change="handleFoodPhoto" hidden />
              <span class="uz-icon">🥗</span>
              <span class="uz-title">Food Photo</span>
              <span class="uz-sub">{{ foodPhoto?.name || 'Click to attach' }}</span>
            </label>
          </div>
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spinner">⏳</span>
          <span v-else>Submit Activity →</span>
        </button>

        <div class="my-link" v-if="employee_id">
          <router-link :to="`/my/${employee_id}`">📋 View my submission history</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page-bg {
  min-height: calc(100vh - 56px);
  background: var(--bg);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 2.5rem 1rem 4rem;
}
.form-card {
  background: var(--surface);
  border-radius: 22px;
  box-shadow: 0 8px 48px rgba(79,70,229,0.1);
  width: 100%; max-width: 600px;
  overflow: hidden;
  position: relative;
}

/* Toast */
.toast {
  position: absolute;
  top: 1rem; left: 50%;
  transform: translateX(-50%);
  padding: 0.65rem 1.25rem;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  z-index: 10;
  white-space: nowrap;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}
.toast.success { background: #D1FAE5; color: #065F46; }
.toast.error   { background: #FEE2E2; color: #991B1B; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-8px); }

.form-header {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  color: #fff;
  padding: 2.5rem 2.5rem 2.2rem;
  text-align: center;
}
.header-icon { font-size: 2.5rem; display: block; margin-bottom: 0.6rem; }
.form-header h1 { font-size: 1.8rem; font-weight: 800; margin: 0 0 0.45rem; letter-spacing: -0.03em; }
.form-header p { margin: 0; opacity: 0.82; font-size: 0.93rem; }
.form-header strong { color: #FCD34D; }

.form-body { padding: 2.25rem 2.5rem 2.5rem; display: flex; flex-direction: column; gap: 2rem; }
.form-section { display: flex; flex-direction: column; gap: 1rem; }
.section-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--primary); padding-bottom: 0.6rem; border-bottom: 1.5px solid var(--primary-light); }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.45rem; }
.field label { font-size: 0.84rem; font-weight: 600; color: var(--text); display: flex; align-items: baseline; gap: 0.5rem; }
.label-hint { font-size: 0.72rem; font-weight: 400; color: var(--text-muted); }

.text-input {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 0.65rem 0.9rem;
  font-size: 0.95rem;
  color: var(--text);
  outline: none;
  background: var(--input-bg);
  width: 100%;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.text-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99,102,241,0.14); }

.step-bar-track { height: 7px; background: var(--border); border-radius: 99px; margin-top: 0.4rem; overflow: hidden; }
.step-bar-fill { height: 100%; background: linear-gradient(90deg, #6366F1, #F97316); border-radius: 99px; transition: width 0.35s ease; }
.step-tally { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.25rem; text-align: right; font-variant-numeric: tabular-nums; }

.upload-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem; }
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: 14px;
  padding: 1.3rem 1rem;
  text-align: center;
  cursor: pointer;
  background: var(--primary-light);
  display: flex; flex-direction: column; align-items: center; gap: 0.35rem;
  transition: border-color 0.2s, background 0.2s;
}
.upload-zone:hover { border-color: var(--primary); }
.upload-zone.uploaded { border-color: var(--green); border-style: solid; background: rgba(16,185,129,0.08); }
.uz-icon { font-size: 1.6rem; }
.uz-title { font-size: 0.82rem; font-weight: 600; color: var(--text); }
.uz-sub { font-size: 0.72rem; color: var(--text-muted); word-break: break-all; }
.uploaded .uz-sub { color: var(--green); }

.submit-btn {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: #fff; border: none; border-radius: 12px;
  padding: 0.9rem 2rem; font-size: 1rem; font-weight: 700;
  cursor: pointer; align-self: stretch;
  transition: opacity 0.18s, transform 0.12s;
}
.submit-btn:hover:not(:disabled) { opacity: 0.91; transform: translateY(-1px); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.my-link { text-align: center; font-size: 0.85rem; }
.my-link a { color: var(--primary); text-decoration: none; }
.my-link a:hover { text-decoration: underline; }

@media (max-width: 520px) {
  .form-body { padding: 1.5rem 1.25rem 2rem; }
  .form-header { padding: 2rem 1.25rem 1.75rem; }
  .field-row, .upload-grid { grid-template-columns: 1fr; }
}
</style>