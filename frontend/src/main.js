import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入 Font Awesome
import '@fortawesome/fontawesome-free/css/all.min.css'

// 配置 axios 默认值
axios.defaults.baseURL = 'http://localhost:5000'
axios.defaults.headers.common['Content-Type'] = 'application/json'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

app.mount('#app') 