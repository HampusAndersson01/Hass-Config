<template>
  <div id="app">
    <el-container class="app-container">
      <!-- Header -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>🔗 Nodalink</h1>
            <span class="subtitle">Visual Automation Editor</span>
          </div>

          <div class="header-stats">
            <el-statistic
              title="Scenarios"
              :value="stats.total_scenarios"
              suffix=""
            />
            <el-statistic
              title="Actions"
              :value="stats.total_actions"
              suffix=""
            />
            <el-statistic
              title="Rooms"
              :value="stats.rooms?.length || 0"
              suffix=""
            />
          </div>

          <div class="header-actions">
            <el-button @click="refreshData" type="primary" :icon="Refresh">
              Refresh
            </el-button>
            <el-button @click="validateAll" type="warning" :icon="Check">
              Validate
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- Navigation -->
      <el-container>
        <el-aside width="200px" class="sidebar">
          <el-menu :default-active="$route.name" router class="sidebar-menu">
            <el-menu-item index="VisualEditor">
              <el-icon><Edit /></el-icon>
              <span>Visual Editor</span>
            </el-menu-item>
            <el-menu-item index="ScenarioManager">
              <el-icon><List /></el-icon>
              <span>Scenarios</span>
            </el-menu-item>
            <el-menu-item index="Analytics">
              <el-icon><DataAnalysis /></el-icon>
              <span>Analytics</span>
            </el-menu-item>
            <el-menu-item index="Settings">
              <el-icon><Setting /></el-icon>
              <span>Settings</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- Main content -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- Global notifications -->
    <div id="notifications"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  Refresh,
  Check,
  Edit,
  List,
  DataAnalysis,
  Setting,
} from "@element-plus/icons-vue";
import { useScenarioStore } from "./stores/scenario";

const scenarioStore = useScenarioStore();
const stats = ref({
  total_scenarios: 0,
  total_actions: 0,
  rooms: [],
});

const refreshData = async () => {
  try {
    await scenarioStore.fetchScenarios();
    await fetchStats();
    ElMessage.success("Data refreshed successfully");
  } catch (error) {
    ElMessage.error("Failed to refresh data");
  }
};

const validateAll = async () => {
  try {
    const response = await fetch("/api/validate", { method: "POST" });
    const validation = await response.json();

    if (validation.valid) {
      ElMessage.success("All scenarios are valid!");
    } else {
      ElMessage.error(`${validation.errors.length} validation errors found`);
    }
  } catch (error) {
    ElMessage.error("Validation failed");
  }
};

const fetchStats = async () => {
  try {
    const response = await fetch("/api/stats");
    stats.value = await response.json();
  } catch (error) {
    console.error("Failed to fetch stats:", error);
  }
};

onMounted(async () => {
  await refreshData();
});
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.logo h1 {
  margin: 0;
  font-size: 1.8rem;
}

.subtitle {
  font-size: 0.9rem;
  opacity: 0.8;
}

.header-stats {
  display: flex;
  gap: 30px;
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border: none;
  background: transparent;
}

.main-content {
  background: #fff;
  padding: 20px;
}

:deep(.el-statistic__content) {
  color: white !important;
}

:deep(.el-statistic__title) {
  color: rgba(255, 255, 255, 0.8) !important;
}
</style>
