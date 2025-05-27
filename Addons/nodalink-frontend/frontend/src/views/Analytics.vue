<template>
  <div class="analytics">
    <el-row :gutter="20">
      <!-- Overview Cards -->
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic
            title="Total Scenarios"
            :value="stats.total_scenarios"
          />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="Total Actions" :value="stats.total_actions" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic title="Rooms" :value="stats.rooms?.length || 0" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card">
          <el-statistic
            title="Time Buckets"
            :value="stats.time_buckets?.length || 0"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Room Distribution -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>📊 Scenarios by Room</span>
          </template>
          <div ref="roomChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>

      <!-- Time Distribution -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>⏰ Scenarios by Time Bucket</span>
          </template>
          <div ref="timeChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Interaction Types -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🎯 Interaction Types</span>
          </template>
          <div ref="interactionChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>

      <!-- Day Type Distribution -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>📅 Day Type Distribution</span>
          </template>
          <div ref="dayTypeChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Unmatched Scenarios -->
    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🔍 Unmatched Scenarios Analysis</span>
              <el-button
                @click="loadUnmatchedScenarios"
                :icon="Refresh"
                size="small"
              >
                Refresh
              </el-button>
            </div>
          </template>

          <div v-if="unmatchedScenarios.length > 0">
            <el-table
              :data="unmatchedScenarios.slice(0, 10)"
              style="width: 100%"
            >
              <el-table-column
                prop="scenario_id"
                label="Scenario ID"
                min-width="200"
              >
                <template #default="{ row }">
                  <el-tag type="warning" size="small">{{
                    row.scenario_id
                  }}</el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="count" label="Count" width="80">
                <template #default="{ row }">
                  <el-badge :value="row.count" type="danger" />
                </template>
              </el-table-column>

              <el-table-column prop="last_seen" label="Last Seen" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.last_seen) }}
                </template>
              </el-table-column>

              <el-table-column label="Actions" width="120">
                <template #default="{ row }">
                  <el-button
                    @click="createFromUnmatched(row)"
                    size="small"
                    type="primary"
                  >
                    Create
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="No unmatched scenarios found" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Real-time Log Viewer -->
    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📋 Real-time Log Viewer</span>
              <div class="header-actions">
                <el-switch
                  v-model="autoRefreshLogs"
                  active-text="Auto-refresh"
                  @change="toggleAutoRefresh"
                />
                <el-button
                  @click="clearLogs"
                  :icon="Delete"
                  size="small"
                  type="danger"
                  plain
                >
                  Clear
                </el-button>
                <el-button @click="loadLogs" :icon="Refresh" size="small">
                  Refresh
                </el-button>
              </div>
            </div>
          </template>

          <div class="log-controls" style="margin-bottom: 15px">
            <el-row :gutter="10">
              <el-col :span="6">
                <el-select
                  v-model="logFilter.level"
                  placeholder="Filter by level"
                  @change="filterLogs"
                >
                  <el-option label="All Levels" value="" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                  <el-option label="DEBUG" value="DEBUG" />
                </el-select>
              </el-col>
              <el-col :span="8">
                <el-input
                  v-model="logFilter.search"
                  placeholder="Search logs..."
                  :prefix-icon="Search"
                  @input="filterLogs"
                  clearable
                />
              </el-col>
              <el-col :span="4">
                <el-input-number
                  v-model="logFilter.maxLines"
                  :min="10"
                  :max="1000"
                  :step="10"
                  controls-position="right"
                  @change="filterLogs"
                />
              </el-col>
              <el-col :span="6">
                <el-text type="info"
                  >Showing {{ filteredLogs.length }} of
                  {{ allLogs.length }} entries</el-text
                >
              </el-col>
            </el-row>
          </div>

          <div class="log-viewer">
            <div
              v-for="(log, index) in filteredLogs"
              :key="index"
              :class="['log-entry', `log-${log.level?.toLowerCase()}`]"
            >
              <div class="log-header">
                <el-tag
                  :type="getLogTagType(log.level)"
                  size="small"
                  effect="dark"
                >
                  {{ log.level }}
                </el-tag>
                <span class="log-timestamp">{{
                  formatLogTime(log.timestamp)
                }}</span>
                <span class="log-source">{{ log.source || "Nodalink" }}</span>
              </div>
              <div class="log-message">{{ log.message }}</div>
              <div v-if="log.data" class="log-data">
                <el-collapse>
                  <el-collapse-item title="Additional Data" name="1">
                    <pre>{{ JSON.stringify(log.data, null, 2) }}</pre>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>

          <el-empty
            v-if="filteredLogs.length === 0"
            description="No log entries found"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { Refresh, Delete, Search } from "@element-plus/icons-vue";
import { useScenarioStore } from "../stores/scenario";

const scenarioStore = useScenarioStore();

// State
const stats = ref({
  total_scenarios: 0,
  total_actions: 0,
  rooms: [],
  time_buckets: [],
  interaction_types: [],
});

const unmatchedScenarios = ref([]);

// Log viewer state
const allLogs = ref([]);
const filteredLogs = ref([]);
const autoRefreshLogs = ref(false);
const logRefreshInterval = ref(null);
const logFilter = ref({
  level: "",
  search: "",
  maxLines: 100,
});

// Chart refs
const roomChartRef = ref();
const timeChartRef = ref();
const interactionChartRef = ref();
const dayTypeChartRef = ref();

// Methods
const loadStats = async () => {
  try {
    const response = await fetch("/api/stats");
    stats.value = await response.json();
  } catch (error) {
    console.error("Failed to load stats:", error);
  }
};

const loadUnmatchedScenarios = async () => {
  try {
    const response = await fetch("/api/suggestions");
    const data = await response.json();
    unmatchedScenarios.value = data.suggestions || [];
  } catch (error) {
    console.error("Failed to load unmatched scenarios:", error);
  }
};

const createRoomChart = () => {
  if (!roomChartRef.value) return;

  const roomCounts = {};
  scenarioStore.scenarios.forEach((scenario) => {
    roomCounts[scenario.room] = (roomCounts[scenario.room] || 0) + 1;
  });

  // Simple text-based chart for now (would use Chart.js in real implementation)
  const chartData = Object.entries(roomCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  roomChartRef.value.innerHTML = chartData
    .map(
      ([room, count]) =>
        `<div style="margin: 5px 0;">
      <span style="display: inline-block; width: 100px;">${room}:</span>
      <span style="display: inline-block; width: ${
        count * 20
      }px; height: 20px; background: #409eff; border-radius: 3px;"></span>
      <span style="margin-left: 10px;">${count}</span>
    </div>`
    )
    .join("");
};

const createTimeChart = () => {
  if (!timeChartRef.value) return;

  const timeCounts = {};
  scenarioStore.scenarios.forEach((scenario) => {
    const time = scenario.time_bucket || "any";
    timeCounts[time] = (timeCounts[time] || 0) + 1;
  });

  const chartData = Object.entries(timeCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  timeChartRef.value.innerHTML = chartData
    .map(
      ([time, count]) =>
        `<div style="margin: 5px 0;">
      <span style="display: inline-block; width: 100px;">${time}:</span>
      <span style="display: inline-block; width: ${
        count * 20
      }px; height: 20px; background: #67c23a; border-radius: 3px;"></span>
      <span style="margin-left: 10px;">${count}</span>
    </div>`
    )
    .join("");
};

const createInteractionChart = () => {
  if (!interactionChartRef.value) return;

  const interactionCounts = {};
  scenarioStore.scenarios.forEach((scenario) => {
    const interaction = scenario.interaction_type || "any";
    interactionCounts[interaction] = (interactionCounts[interaction] || 0) + 1;
  });

  const chartData = Object.entries(interactionCounts).sort(
    ([, a], [, b]) => b - a
  );

  interactionChartRef.value.innerHTML = chartData
    .map(
      ([interaction, count]) =>
        `<div style="margin: 5px 0;">
      <span style="display: inline-block; width: 120px;">${interaction}:</span>
      <span style="display: inline-block; width: ${
        count * 30
      }px; height: 20px; background: #e6a23c; border-radius: 3px;"></span>
      <span style="margin-left: 10px;">${count}</span>
    </div>`
    )
    .join("");
};

const createDayTypeChart = () => {
  if (!dayTypeChartRef.value) return;

  const dayTypeCounts = {};
  scenarioStore.scenarios.forEach((scenario) => {
    const dayType = scenario.day_type || "any";
    dayTypeCounts[dayType] = (dayTypeCounts[dayType] || 0) + 1;
  });

  const chartData = Object.entries(dayTypeCounts).sort(([, a], [, b]) => b - a);

  dayTypeChartRef.value.innerHTML = chartData
    .map(
      ([dayType, count]) =>
        `<div style="margin: 5px 0;">
      <span style="display: inline-block; width: 100px;">${dayType}:</span>
      <span style="display: inline-block; width: ${
        count * 40
      }px; height: 20px; background: #f56c6c; border-radius: 3px;"></span>
      <span style="margin-left: 10px;">${count}</span>
    </div>`
    )
    .join("");
};

const createFromUnmatched = (unmatchedScenario) => {
  // Parse scenario ID components
  const parts = unmatchedScenario.scenario_id.split("|");

  scenarioStore.currentScenario = {
    room: parts[0] || "",
    time_bucket: parts[1] || "",
    day_type: parts[2] || "",
    optional_flags: parts[3] ? parts[3].split("+") : [],
    interaction_type: parts[4] || "",
    actions: [],
  };

  ElMessage.success(
    "Unmatched scenario loaded. Switch to Visual Editor to add actions."
  );
};

const formatDate = (dateString) => {
  if (!dateString) return "Unknown";

  try {
    return new Date(dateString).toLocaleString();
  } catch {
    return "Invalid date";
  }
};

const refreshCharts = async () => {
  await nextTick();
  createRoomChart();
  createTimeChart();
  createInteractionChart();
  createDayTypeChart();
};

// Log viewer methods
const loadLogs = async () => {
  try {
    const response = await fetch("/api/logs");
    if (response.ok) {
      const logs = await response.json();
      allLogs.value = logs.sort(
        (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
      );
      filterLogs();
    }
  } catch (error) {
    console.error("Failed to load logs:", error);
    // Generate mock logs for demo
    allLogs.value = generateMockLogs();
    filterLogs();
  }
};

const generateMockLogs = () => {
  const levels = ["INFO", "WARNING", "ERROR", "DEBUG"];
  const sources = ["NodalinkEngine", "ScenarioMatcher", "API", "WebSocket"];
  const messages = [
    "Scenario triggered successfully",
    "Failed to match scenario pattern",
    "WebSocket connection established",
    "Unmatched scenario logged",
    "Configuration reloaded",
    "Service call executed",
    "Validation error detected",
    "Fallback scenario used",
  ];

  return Array.from({ length: 50 }, (_, i) => ({
    timestamp: new Date(Date.now() - i * 60000).toISOString(),
    level: levels[Math.floor(Math.random() * levels.length)],
    source: sources[Math.floor(Math.random() * sources.length)],
    message: messages[Math.floor(Math.random() * messages.length)],
    data:
      Math.random() > 0.7
        ? { scenario_id: "kitchen|08-09|weekday|single_press", action_count: 2 }
        : null,
  }));
};

const filterLogs = () => {
  let filtered = [...allLogs.value];

  // Filter by level
  if (logFilter.value.level) {
    filtered = filtered.filter((log) => log.level === logFilter.value.level);
  }

  // Filter by search term
  if (logFilter.value.search) {
    const search = logFilter.value.search.toLowerCase();
    filtered = filtered.filter(
      (log) =>
        log.message.toLowerCase().includes(search) ||
        log.source.toLowerCase().includes(search)
    );
  }

  // Limit number of entries
  filtered = filtered.slice(0, logFilter.value.maxLines);

  filteredLogs.value = filtered;
};

const clearLogs = () => {
  allLogs.value = [];
  filteredLogs.value = [];
  ElMessage.success("Logs cleared");
};

const toggleAutoRefresh = (enabled) => {
  if (enabled) {
    logRefreshInterval.value = setInterval(loadLogs, 5000); // Refresh every 5 seconds
    ElMessage.info("Auto-refresh enabled");
  } else {
    if (logRefreshInterval.value) {
      clearInterval(logRefreshInterval.value);
      logRefreshInterval.value = null;
    }
    ElMessage.info("Auto-refresh disabled");
  }
};

const getLogTagType = (level) => {
  const types = {
    INFO: "info",
    WARNING: "warning",
    ERROR: "danger",
    DEBUG: "info",
  };
  return types[level] || "info";
};

const formatLogTime = (timestamp) => {
  try {
    return new Date(timestamp).toLocaleTimeString();
  } catch {
    return "Invalid time";
  }
};

onMounted(async () => {
  await loadStats();
  await loadUnmatchedScenarios();
  await loadLogs();

  if (scenarioStore.scenarios.length === 0) {
    await scenarioStore.fetchScenarios();
  }

  await refreshCharts();
});

onUnmounted(() => {
  if (logRefreshInterval.value) {
    clearInterval(logRefreshInterval.value);
  }
});
</script>

<style scoped>
.analytics {
  height: calc(100vh - 140px);
  overflow: auto;
}

.metric-card {
  text-align: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Log viewer styles */
.log-controls {
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 15px;
}

.log-viewer {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #f8f9fa;
}

.log-entry {
  border-bottom: 1px solid #e8e8e8;
  padding: 12px;
  transition: background-color 0.2s;
}

.log-entry:hover {
  background-color: #f0f0f0;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 12px;
}

.log-timestamp {
  color: #909399;
  font-family: monospace;
}

.log-source {
  color: #606266;
  font-weight: 500;
}

.log-message {
  font-family: monospace;
  font-size: 13px;
  color: #303133;
  margin-bottom: 8px;
  word-break: break-all;
}

.log-data {
  margin-top: 8px;
}

.log-data pre {
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  margin: 0;
  max-height: 200px;
  overflow-y: auto;
}

.log-info {
  border-left: 3px solid #409eff;
}

.log-warning {
  border-left: 3px solid #e6a23c;
  background-color: #fef9e7;
}

.log-error {
  border-left: 3px solid #f56c6c;
  background-color: #fef0f0;
}

.log-debug {
  border-left: 3px solid #909399;
  background-color: #f4f4f5;
}

:deep(.el-statistic__content) {
  font-size: 2rem;
  font-weight: bold;
  color: #409eff;
}

:deep(.el-statistic__title) {
  color: #666;
  margin-bottom: 10px;
}

:deep(.el-collapse-item__header) {
  font-size: 12px;
  padding: 8px 12px;
}

:deep(.el-collapse-item__content) {
  padding: 8px 12px;
}
</style>
