import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";

import App from "./App.vue";
import VisualEditor from "./views/VisualEditor.vue";
import ScenarioManager from "./views/ScenarioManager.vue";
import Analytics from "./views/Analytics.vue";
import Settings from "./views/Settings.vue";

// Router configuration
const routes = [
  { path: "/", name: "VisualEditor", component: VisualEditor },
  { path: "/scenarios", name: "ScenarioManager", component: ScenarioManager },
  { path: "/analytics", name: "Analytics", component: Analytics },
  { path: "/settings", name: "Settings", component: Settings },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Create app
const app = createApp(App);

// Add plugins
app.use(createPinia());
app.use(router);
app.use(ElementPlus);

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.mount("#app");
