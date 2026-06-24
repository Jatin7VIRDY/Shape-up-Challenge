import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/", redirect: "/submit" },

  {
    path: "/submit",
    component: () => import("../views/SubmitActivity.vue"),
    meta: { title: "Submit" }
  },

  {
    path: "/leaderboard",
    component: () => import("../views/Leaderboard.vue"),
    meta: { title: "Leaderboard" }
  },

  {
    path: "/reviewer",
    component: () => import("../views/ReviewSubmissions.vue"),
    meta: { title: "Review" }
  },

  {
    path: "/my/:employee_id",
    component: () => import("../views/MySubmissions.vue"),
    meta: { title: "My Submissions" }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = `${to.meta.title || "Shape Up"} · Shape Up Challenge`
})

export default router