import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)