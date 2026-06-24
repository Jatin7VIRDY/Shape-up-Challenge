import { ref, watch, onMounted } from "vue"

const dark = ref(false)

export function useTheme() {
  const apply = (isDark) => {
    document.documentElement.classList.toggle("dark", isDark)
    localStorage.setItem("theme", isDark ? "dark" : "light")
  }

  const toggle = () => {
    dark.value = !dark.value
  }

  onMounted(() => {
    const saved = localStorage.getItem("theme")
    dark.value = saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)
    apply(dark.value)
  })

  watch(dark, apply)

  return { dark, toggle }
}