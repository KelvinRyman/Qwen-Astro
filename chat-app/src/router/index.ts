import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import KnowledgeBaseView from '@/views/KnowledgeBaseView.vue'
import AgentView from '@/views/AgentView.vue'
import MarkdownTest from '@/components/MarkdownTest.vue'
import ImageUploadTest from '@/views/ImageUploadTest.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/chat'
    },
    {
      path: '/chat',
      name: 'NewChat',
      component: ChatView,
    },
    {
      path: '/chat/:id',
      name: 'Chat',
      component: ChatView,
    },
    {
      path: '/knowledge',
      name: 'KnowledgeBase',
      component: KnowledgeBaseView,
    },
    {
      path: '/agents',
      name: 'Agents',
      component: AgentView,
    },
    {
      path: '/markdown-test',
      name: 'MarkdownTest',
      component: MarkdownTest,
    },
    {
      path: '/image-upload-test',
      name: 'ImageUploadTest',
      component: ImageUploadTest,
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

export default router
