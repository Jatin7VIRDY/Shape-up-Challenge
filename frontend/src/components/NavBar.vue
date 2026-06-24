<script setup>
import { onMounted, ref, computed, watch } from "vue"
import { useRoute } from "vue-router"
import { useTheme } from "../compostables/useTheme"
import Swal from "sweetalert2"
const isReviewer = ref(false)
const { dark, toggle } = useTheme()
const route = useRoute()
const mobileOpen = ref(false)

const employeeLinks = [
  { to: "/submit", label: "Submit Activity", icon: "🏃" },
  { to: "/leaderboard", label: "Leaderboard", icon: "🏆" },
]
const reviewerLinks = computed(() => {
  return isReviewer.value
    ? [{ to: "/reviewer", label: "Review", icon: "✅" }]
    : []
})

async function logoutReviewer() {
  const result = await Swal.fire({
    title: "Logout?",
    icon: "question",
    showCancelButton: true,
    confirmButtonText: "Logout"
  })

  if (!result.isConfirmed) return

  localStorage.removeItem("reviewerAuth")
  isReviewer.value = false
  window.location.href="/submit"
}

onMounted(()=>{
  isReviewer.value = localStorage.getItem("reviewerAuth")==="true"
})

watch(() => route.path, () => {
  isReviewer.value = localStorage.getItem("reviewerAuth")==="true"
})
</script>

<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link to="/" class="brand">
        <span class="brand-icon">💪</span>
        <span class="brand-text">Shape Up</span>
      </router-link>

      <!-- Desktop links -->
      <div class="nav-links">
        <router-link
          v-for="link in employeeLinks"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ active: route.path === link.to }"
        >{{ link.icon }} {{ link.label }}</router-link>

        <div class="divider" />

        <router-link
          v-for="link in reviewerLinks"
          :key="link.to"
          :to="link.to"
          class="nav-link admin-link"
          :class="{ active: route.path === link.to }"
        >{{ link.icon }} {{ link.label }}</router-link>
      </div>

      <button class="logout" v-if="isReviewer" @click="logoutReviewer">Logout</button>

      <button class="theme-toggle" @click="toggle" :title="dark ? 'Light mode' : 'Dark mode'">
        {{ dark ? '☀️' : '🌙' }}
      </button>

      <button class="mobile-toggle" @click="mobileOpen = !mobileOpen">☰</button>
    </div>

    <!-- Mobile menu -->
    <div v-if="mobileOpen" class="mobile-menu">
      <router-link v-for="link in [...employeeLinks, ...reviewerLinks]" :key="link.to" :to="link.to"
        class="mobile-link" @click="mobileOpen = false">
        {{ link.icon }} {{ link.label }}
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--nav-bg, #fff);
  border-bottom: 1px solid var(--border, #E5E7EB);
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  font-family: 'Inter', system-ui, sans-serif;
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.25rem;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  font-weight: 800;
  font-size: 1.1rem;
  color: #4F46E5;
  letter-spacing: -0.02em;
  white-space: nowrap;
}
.brand-icon { font-size: 1.3rem; }

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex: 1;
}

.nav-link {
  text-decoration: none;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted, #6B7280);
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.nav-link:hover { background: var(--hover-bg, #F3F4F6); color: var(--text, #111827); }
.nav-link.active { background: #EEF2FF; color: #4F46E5; font-weight: 600; }
.admin-link.active { background: #FFF7ED; color: #C2410C; }

.divider {
  width: 1px;
  height: 20px;
  background: var(--border, #E5E7EB);
  margin: 0 0.5rem;
}

.theme-toggle {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.15rem;
  cursor: pointer;
  padding: 0.35rem;
  border-radius: 8px;
  transition: background 0.15s;
  line-height: 1;
}
.theme-toggle:hover { background: var(--hover-bg, #F3F4F6); }

.mobile-toggle {
  display: none;
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text, #111827);
  padding: 0.35rem;
}

.mobile-menu {
  display: none;
  flex-direction: column;
  padding: 0.75rem 1.25rem 1rem;
  border-top: 1px solid var(--border, #E5E7EB);
  background: var(--nav-bg, #fff);
}
.mobile-link {
  text-decoration: none;
  padding: 0.7rem 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text, #111827);
  border-bottom: 1px solid var(--border, #E5E7EB);
}
.mobile-link:last-child { border-bottom: none; }

.logout {
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.38rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout:hover {
  background: #b91c1c;
  transform: translateY(-1px);
}

.logout:active {
  transform: translateY(0);
}
@media (max-width: 768px) {
  .nav-links { display: none; }
  .mobile-toggle { display: block; }
  .mobile-menu { display: flex; }
}
</style>