<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-100 p-4 dark:bg-gray-900">
    <div class="mx-auto w-full max-w-md rounded-lg bg-white p-8 shadow-lg dark:bg-gray-800">
      <h1 class="mb-6 text-center text-2xl font-bold text-gray-900 dark:text-white">
        雅思词汇真经 - 登录
      </h1>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
            邮箱
          </label>
          <input
            v-model="form.email"
            type="email"
            required
            class="w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-gray-900 focus:ring-blue-500 focus:border-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
            placeholder="your@email.com"
          >
        </div>

        <div>
          <label class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
            密码
          </label>
          <input
            v-model="form.password"
            type="password"
            required
            class="w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-gray-900 focus:ring-blue-500 focus:border-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-500 dark:focus:border-blue-500"
            placeholder="••••••••"
          >
        </div>

        <button
          type="submit"
          :disabled="authStore.isLoading"
          class="w-full rounded-lg bg-blue-600 px-5 py-2.5 text-center text-sm font-medium text-white hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 dark:bg-blue-500 dark:hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span v-if="!authStore.isLoading">登录</span>
          <span v-else>登录中...</span>
        </button>

        <p class="text-sm text-center font-light text-gray-500 dark:text-gray-400">
          还没有账号？
          <router-link to="/register" class="ml-1 font-medium text-blue-600 hover:underline dark:text-blue-400">
            立即注册
          </router-link>
        </p>
      </form>

      <div v-if="error" class="mt-4 rounded-lg bg-red-50 p-4 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: '',
})
const error = ref('')

async function handleLogin() {
  error.value = ''
  const result = await authStore.login(form.value.email, form.value.password)

  if (result.success) {
    router.push('/')
  }
  else {
    error.value = result.error
  }
}
</script>
