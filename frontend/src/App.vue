<script setup>
import NavBar from "./components/NavBar.vue"
</script>

<template>
  <div class="app-root">
    <NavBar />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
/* ── CSS Variables (light) ── */
:root {
  --bg: #F1F5F9;
  --surface: #FFFFFF;
  --surface2: #F8FAFC;
  --border: #E2E8F0;
  --text: #0F172A;
  --text-muted: #64748B;
  --primary: #4F46E5;
  --primary-light: #EEF2FF;
  --green: #10B981;
  --red: #EF4444;
  --amber: #F59E0B;
  --nav-bg: #FFFFFF;
  --hover-bg: #F1F5F9;
  --input-bg: #FAFAFA;
}

/* ── Dark mode ── */
html.dark {
  --bg: #0F172A;
  --surface: #1E293B;
  --surface2: #172033;
  --border: #334155;
  --text: #F1F5F9;
  --text-muted: #94A3B8;
  --primary: #818CF8;
  --primary-light: #1e1b4b;
  --green: #34D399;
  --red: #F87171;
  --amber: #FCD34D;
  --nav-bg: #1E293B;
  --hover-bg: #1E293B;
  --input-bg: #0F172A;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  transition: background 0.2s, color 0.2s;
  -webkit-font-smoothing: antialiased;
}

.app-root { min-height: 100vh; display: flex; flex-direction: column; }
.app-main { flex: 1; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
</style>