<template>
  <div class="settings-container">
    <el-card class="header-card">
      <div class="header-content">
        <h1>
          <el-icon><Setting /></el-icon> Settings
        </h1>
        <p>Configure Nodalink engine parameters and system preferences</p>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- Engine Settings -->
      <el-col :span="12">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Tools /></el-icon>
              <span>Engine Configuration</span>
            </div>
          </template>

          <el-form
            ref="engineForm"
            :model="engineSettings"
            :rules="engineRules"
            label-width="140px"
          >
            <el-form-item label="Test Mode" prop="testMode">
              <el-switch
                v-model="engineSettings.testMode"
                active-text="Enabled"
                inactive-text="Disabled"
              />
              <div class="help-text">
                When enabled, scenarios are validated but not executed
              </div>
            </el-form-item>

            <el-form-item label="Fallback" prop="fallbackEnabled">
              <el-switch
                v-model="engineSettings.fallbackEnabled"
                active-text="Enabled"
                inactive-text="Disabled"
              />
              <div class="help-text">
                Enable intelligent fallback matching for scenarios
              </div>
            </el-form-item>

            <el-form-item label="Time Bucket" prop="timeBucketMinutes">
              <el-input-number
                v-model="engineSettings.timeBucketMinutes"
                :min="1"
                :max="120"
                :step="5"
              />
              <span class="unit">minutes</span>
              <div class="help-text">
                Time window for grouping similar triggers
              </div>
            </el-form-item>

            <el-form-item label="Log Level" prop="logLevel">
              <el-select v-model="engineSettings.logLevel" style="width: 100%">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Room Mappings -->
      <el-col :span="12">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><House /></el-icon>
              <span>Room Mappings</span>
              <el-button
                type="primary"
                size="small"
                @click="addRoomMapping"
                style="margin-left: auto"
              >
                <el-icon><Plus /></el-icon>
                Add Room
              </el-button>
            </div>
          </template>

          <div class="room-mappings">
            <div
              v-for="(mapping, index) in roomMappings"
              :key="index"
              class="room-mapping-item"
            >
              <el-input
                v-model="mapping.room"
                placeholder="Room name"
                style="width: 40%"
              />
              <el-input
                v-model="mapping.entity"
                placeholder="Entity ID"
                style="width: 50%"
              />
              <el-button
                type="danger"
                size="small"
                @click="removeRoomMapping(index)"
                style="width: 8%"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>

            <div v-if="roomMappings.length === 0" class="empty-state">
              <el-empty description="No room mappings configured" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- Conditional Entities (Flags) -->
      <el-col :span="24">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Flag /></el-icon>
              <span>Conditional Entities (Optional Flags)</span>
              <el-button
                type="primary"
                size="small"
                @click="addConditionalEntity"
                style="margin-left: auto"
              >
                <el-icon><Plus /></el-icon>
                Add Flag
              </el-button>
            </div>
          </template>

          <div class="conditional-entities">
            <div
              v-for="(entity, index) in conditionalEntities"
              :key="index"
              class="conditional-entity-item"
            >
              <el-input
                v-model="entity.flag"
                placeholder="Flag name (e.g., night_mode)"
                style="width: 30%"
              />
              <el-input
                v-model="entity.entity"
                placeholder="Entity ID (e.g., input_boolean.night_mode)"
                style="width: 45%"
              />
              <el-input
                v-model="entity.description"
                placeholder="Description"
                style="width: 20%"
              />
              <el-button
                type="danger"
                size="small"
                @click="removeConditionalEntity(index)"
                style="width: 3%"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>

            <div v-if="conditionalEntities.length === 0" class="empty-state">
              <el-empty description="No conditional entities configured" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- System Status -->
      <el-col :span="8">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>System Status</span>
            </div>
          </template>

          <div class="status-item">
            <span class="status-label">Engine Status:</span>
            <el-tag :type="systemStatus.engineRunning ? 'success' : 'danger'">
              {{ systemStatus.engineRunning ? "Running" : "Stopped" }}
            </el-tag>
          </div>

          <div class="status-item">
            <span class="status-label">Scenarios Loaded:</span>
            <span class="status-value">{{ systemStatus.scenariosLoaded }}</span>
          </div>

          <div class="status-item">
            <span class="status-label">Last Execution:</span>
            <span class="status-value">{{
              formatTimestamp(systemStatus.lastExecution)
            }}</span>
          </div>
        </el-card>
      </el-col>

      <!-- File Management -->
      <el-col :span="8">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Folder /></el-icon>
              <span>File Management</span>
            </div>
          </template>

          <div class="file-actions">
            <el-button type="primary" @click="exportScenarios">
              <el-icon><Download /></el-icon>
              Export Scenarios
            </el-button>

            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleFileImport"
              accept=".json"
              style="margin-top: 10px"
            >
              <el-button type="success">
                <el-icon><Upload /></el-icon>
                Import Scenarios
              </el-button>
            </el-upload>

            <el-button
              type="warning"
              @click="showBackupDialog = true"
              style="margin-top: 10px"
            >
              <el-icon><DocumentCopy /></el-icon>
              Backup Configuration
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- Maintenance -->
      <el-col :span="8">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <el-icon><Tools /></el-icon>
              <span>Maintenance</span>
            </div>
          </template>

          <div class="maintenance-actions">
            <el-button type="info" @click="clearLogs" :loading="clearingLogs">
              <el-icon><Delete /></el-icon>
              Clear Logs
            </el-button>

            <el-button
              type="warning"
              @click="reloadEngine"
              :loading="reloadingEngine"
              style="margin-top: 10px"
            >
              <el-icon><Refresh /></el-icon>
              Reload Engine
            </el-button>

            <el-button
              type="success"
              @click="validateScenarios"
              :loading="validatingScenarios"
              style="margin-top: 10px"
            >
              <el-icon><CircleCheck /></el-icon>
              Validate All
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <el-button type="primary" @click="saveSettings" :loading="saving">
        <el-icon><Check /></el-icon>
        Save Settings
      </el-button>
      <el-button @click="resetSettings">
        <el-icon><RefreshLeft /></el-icon>
        Reset to Defaults
      </el-button>
    </div>

    <!-- Backup Dialog -->
    <el-dialog v-model="showBackupDialog" title="Create Backup" width="500px">
      <el-form :model="backupForm" label-width="120px">
        <el-form-item label="Backup Name">
          <el-input v-model="backupForm.name" placeholder="Enter backup name" />
        </el-form-item>
        <el-form-item label="Include">
          <el-checkbox-group v-model="backupForm.include">
            <el-checkbox label="scenarios">Scenarios</el-checkbox>
            <el-checkbox label="settings">Settings</el-checkbox>
            <el-checkbox label="logs">Logs</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showBackupDialog = false">Cancel</el-button>
        <el-button type="primary" @click="createBackup"
          >Create Backup</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Setting,
  Tools,
  House,
  Flag,
  Monitor,
  Folder,
  Plus,
  Delete,
  Download,
  Upload,
  DocumentCopy,
  Refresh,
  CircleCheck,
  Check,
  RefreshLeft,
} from "@element-plus/icons-vue";
import { useScenarioStore } from "../stores/scenario";

const scenarioStore = useScenarioStore();

// Engine settings
const engineSettings = reactive({
  testMode: false,
  fallbackEnabled: true,
  timeBucketMinutes: 60,
  logLevel: "INFO",
});

const engineRules = {
  timeBucketMinutes: [
    { required: true, message: "Time bucket is required", trigger: "blur" },
    {
      type: "number",
      min: 1,
      max: 120,
      message: "Must be between 1 and 120",
      trigger: "blur",
    },
  ],
};

// Room mappings
const roomMappings = ref([
  { room: "living_room", entity: "binary_sensor.presence_detector" },
  { room: "bedroom", entity: "binary_sensor.bedroom_motion" },
]);

// Conditional entities (flags)
const conditionalEntities = ref([
  {
    flag: "christmas_mode",
    entity: "input_boolean.christmas_mode",
    description: "Christmas festive mode",
  },
  {
    flag: "night_mode",
    entity: "input_boolean.night_mode",
    description: "Night time mode",
  },
  {
    flag: "focus_mode",
    entity: "input_boolean.desk_focus_lights",
    description: "Focus work mode",
  },
  {
    flag: "presence_mode",
    entity: "input_boolean.presence_mode",
    description: "Presence detection mode",
  },
]);

// System status
const systemStatus = reactive({
  engineRunning: true,
  scenariosLoaded: 0,
  lastExecution: Date.now(),
});

// Loading states
const saving = ref(false);
const clearingLogs = ref(false);
const reloadingEngine = ref(false);
const validatingScenarios = ref(false);

// Backup dialog
const showBackupDialog = ref(false);
const backupForm = reactive({
  name: "",
  include: ["scenarios", "settings"],
});

// File upload
const uploadRef = ref();

onMounted(async () => {
  await loadSettings();
  await loadSystemStatus();
});

const addRoomMapping = () => {
  roomMappings.value.push({ room: "", entity: "" });
};

const removeRoomMapping = (index) => {
  roomMappings.value.splice(index, 1);
};

const addConditionalEntity = () => {
  conditionalEntities.value.push({ flag: "", entity: "", description: "" });
};

const removeConditionalEntity = (index) => {
  conditionalEntities.value.splice(index, 1);
};

const loadSettings = async () => {
  try {
    // Load current configuration from API
    const response = await fetch("/config");
    if (response.ok) {
      const config = await response.json();

      // Update engine settings
      Object.assign(engineSettings, {
        testMode: config.system_settings.test_mode,
        fallbackEnabled: config.system_settings.fallback_enabled,
        timeBucketMinutes: config.system_settings.time_bucket_minutes,
        logLevel: "INFO", // Default since not in system_settings
      });

      // Update room mappings
      roomMappings.value = Object.entries(config.room_mappings).map(
        ([room, data]) => ({
          room: room,
          entity: typeof data === "string" ? data : data.entity_id,
        })
      );

      // Update conditional entities
      conditionalEntities.value = Object.entries(
        config.conditional_entities
      ).map(([flag, data]) => ({
        flag: flag,
        entity: typeof data === "string" ? data : data.entity_id,
        description: typeof data === "object" ? data.description || "" : "",
      }));
    }
  } catch (error) {
    console.error("Failed to load settings:", error);
  }
};

const loadSystemStatus = async () => {
  try {
    const response = await fetch("/api/status");
    if (response.ok) {
      const status = await response.json();
      Object.assign(systemStatus, status);
    }
  } catch (error) {
    console.error("Failed to load system status:", error);
  }
};

const saveSettings = async () => {
  saving.value = true;
  try {
    // Build room mappings object
    const room_mappings = {};
    roomMappings.value
      .filter((m) => m.room && m.entity)
      .forEach((mapping) => {
        room_mappings[mapping.room] = {
          label: mapping.room
            .replace("_", " ")
            .split(" ")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" "),
          entity_id: mapping.entity,
          entity_type: mapping.entity.startsWith("binary_sensor.")
            ? "binary_sensor"
            : "sensor",
          description: "",
        };
      });

    // Build conditional entities object
    const conditional_entities = {};
    conditionalEntities.value
      .filter((e) => e.flag && e.entity)
      .forEach((entity) => {
        conditional_entities[entity.flag] = {
          label: entity.flag
            .replace("_", " ")
            .split(" ")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" "),
          entity_id: entity.entity,
          entity_type: entity.entity.startsWith("input_boolean.")
            ? "input_boolean"
            : "input_select",
          description: entity.description || "",
          icon: "",
        };
      });

    const configRequest = {
      room_mappings,
      conditional_entities,
      system_settings: {
        time_bucket_minutes: engineSettings.timeBucketMinutes,
        fallback_enabled: engineSettings.fallbackEnabled,
        test_mode: engineSettings.testMode,
        auto_reload_config: true,
        allowed_domains: [
          "light",
          "switch",
          "scene",
          "script",
          "automation",
          "media_player",
          "climate",
          "cover",
          "fan",
          "vacuum",
          "notify",
        ],
      },
    };

    const response = await fetch("/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(configRequest),
    });

    if (response.ok) {
      ElMessage.success("Configuration saved successfully");

      // Trigger engine reload
      try {
        await fetch("/config/reload", { method: "POST" });
        ElMessage.success("Engine configuration reloaded");
      } catch (reloadError) {
        ElMessage.warning("Configuration saved but engine reload failed");
      }
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to save configuration");
    }
  } catch (error) {
    ElMessage.error("Failed to save settings: " + error.message);
  } finally {
    saving.value = false;
  }
};

const resetSettings = async () => {
  try {
    await ElMessageBox.confirm(
      "This will reset all settings to their default values. Continue?",
      "Reset Settings",
      { type: "warning" }
    ); // Reset to defaults
    Object.assign(engineSettings, {
      testMode: false,
      fallbackEnabled: true,
      timeBucketMinutes: 60,
      logLevel: "INFO",
    });

    roomMappings.value = [];
    conditionalEntities.value = [];
    ElMessage.success("Settings reset to defaults");
  } catch (error) {
    // User cancelled
  }
};

const exportScenarios = async () => {
  try {
    const response = await fetch("/api/scenarios/export");
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `nodalink-scenarios-${
        new Date().toISOString().split("T")[0]
      }.json`;
      a.click();
      window.URL.revokeObjectURL(url);
      ElMessage.success("Scenarios exported successfully");
    }
  } catch (error) {
    ElMessage.error("Failed to export scenarios: " + error.message);
  }
};

const handleFileImport = async (file) => {
  try {
    const text = await file.raw.text();
    const scenarios = JSON.parse(text);

    await ElMessageBox.confirm(
      `Import ${
        scenarios.length || Object.keys(scenarios).length
      } scenarios? This will replace existing scenarios.`,
      "Import Scenarios",
      { type: "warning" }
    );

    const response = await fetch("/api/scenarios/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: text,
    });

    if (response.ok) {
      ElMessage.success("Scenarios imported successfully");
      await scenarioStore.loadScenarios();
    } else {
      throw new Error("Failed to import scenarios");
    }
  } catch (error) {
    if (error.message !== "cancel") {
      ElMessage.error("Failed to import scenarios: " + error.message);
    }
  }
};

const clearLogs = async () => {
  clearingLogs.value = true;
  try {
    await ElMessageBox.confirm(
      "This will permanently delete all log files. Continue?",
      "Clear Logs",
      { type: "warning" }
    );

    const response = await fetch("/api/logs/clear", { method: "POST" });
    if (response.ok) {
      ElMessage.success("Logs cleared successfully");
    } else {
      throw new Error("Failed to clear logs");
    }
  } catch (error) {
    if (error.message !== "cancel") {
      ElMessage.error("Failed to clear logs: " + error.message);
    }
  } finally {
    clearingLogs.value = false;
  }
};

const reloadEngine = async () => {
  reloadingEngine.value = true;
  try {
    const response = await fetch("/api/engine/reload", { method: "POST" });
    if (response.ok) {
      ElMessage.success("Engine reloaded successfully");
      await loadSystemStatus();
    } else {
      throw new Error("Failed to reload engine");
    }
  } catch (error) {
    ElMessage.error("Failed to reload engine: " + error.message);
  } finally {
    reloadingEngine.value = false;
  }
};

const validateScenarios = async () => {
  validatingScenarios.value = true;
  try {
    const response = await fetch("/api/scenarios/validate");
    if (response.ok) {
      const result = await response.json();
      if (result.valid) {
        ElMessage.success(`All scenarios are valid (${result.count} checked)`);
      } else {
        ElMessage.warning(`${result.errors.length} validation errors found`);
      }
    } else {
      throw new Error("Failed to validate scenarios");
    }
  } catch (error) {
    ElMessage.error("Failed to validate scenarios: " + error.message);
  } finally {
    validatingScenarios.value = false;
  }
};

const createBackup = async () => {
  try {
    const response = await fetch("/api/backup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(backupForm),
    });

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `nodalink-backup-${backupForm.name || "default"}.zip`;
      a.click();
      window.URL.revokeObjectURL(url);

      showBackupDialog.value = false;
      ElMessage.success("Backup created successfully");
    } else {
      throw new Error("Failed to create backup");
    }
  } catch (error) {
    ElMessage.error("Failed to create backup: " + error.message);
  }
};

const formatTimestamp = (timestamp) => {
  if (!timestamp) return "Never";
  return new Date(timestamp).toLocaleString();
};
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-content h1 {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
}

.header-content p {
  margin: 8px 0 0 0;
  opacity: 0.9;
}

.settings-card,
.status-card {
  height: fit-content;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.room-mappings {
  max-height: 300px;
  overflow-y: auto;
}

.room-mapping-item {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
}

.conditional-entities {
  max-height: 300px;
  overflow-y: auto;
}

.conditional-entity-item {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
}

.empty-state {
  padding: 20px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-label {
  font-weight: 500;
  color: #606266;
}

.status-value {
  color: #303133;
}

.file-actions,
.maintenance-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.el-card :deep(.el-card__header) {
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}

.header-card :deep(.el-card__header) {
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.header-card :deep(.el-card__body) {
  padding: 20px;
}
</style>
