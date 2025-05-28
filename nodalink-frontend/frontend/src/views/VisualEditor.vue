<template>
  <div class="visual-editor">
    <el-row :gutter="20">
      <!-- Scenario Builder -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>🎨 Visual Scenario Builder</span>
              <div class="header-actions">
                <el-button
                  @click="clearEditor"
                  :icon="Delete"
                  type="danger"
                  plain
                >
                  Clear
                </el-button>
                <el-button
                  @click="testScenario"
                  :icon="VideoPlay"
                  type="success"
                  plain
                >
                  Test
                </el-button>
                <el-button @click="saveScenario" :icon="Check" type="primary">
                  Save Scenario
                </el-button>
              </div>
            </div>
          </template>

          <!-- Scenario ID Builder -->
          <div class="scenario-builder">
            <h3>📝 Scenario ID Builder</h3>
            <el-row :gutter="10" style="margin-bottom: 20px">
              <el-col :span="4">
                <el-select
                  v-model="scenarioComponents.room"
                  placeholder="Room"
                  @change="updateScenarioId"
                >
                  <el-option label="living_room" value="living_room" />
                  <el-option label="kitchen" value="kitchen" />
                  <el-option label="bedroom" value="bedroom" />
                  <el-option label="bathroom" value="bathroom" />
                  <el-option label="office" value="office" />
                  <el-option label="hallway" value="hallway" />
                </el-select>
              </el-col>
              <el-col :span="4">
                <el-select
                  v-model="scenarioComponents.timeBucket"
                  placeholder="Time"
                  @change="updateScenarioId"
                >
                  <el-option label="morning" value="morning" />
                  <el-option label="07-08" value="07-08" />
                  <el-option label="08-09" value="08-09" />
                  <el-option label="12-13" value="12-13" />
                  <el-option label="18-19" value="18-19" />
                  <el-option label="19-20" value="19-20" />
                  <el-option label="20-21" value="20-21" />
                  <el-option label="22-23" value="22-23" />
                  <el-option label="night" value="night" />
                </el-select>
              </el-col>
              <el-col :span="3">
                <el-select
                  v-model="scenarioComponents.dayType"
                  placeholder="Day Type"
                  @change="updateScenarioId"
                >
                  <el-option label="Any" value="" />
                  <el-option label="weekday" value="weekday" />
                  <el-option label="weekend" value="weekend" />
                </el-select>
              </el-col>
              <el-col :span="4">
                <el-select
                  v-model="scenarioComponents.flags"
                  placeholder="Flags"
                  multiple
                  @change="updateScenarioId"
                >
                  <el-option label="christmas_mode" value="christmas_mode" />
                  <el-option label="night_mode" value="night_mode" />
                  <el-option label="focus_mode" value="focus_mode" />
                  <el-option label="vacation_mode" value="vacation_mode" />
                </el-select>
              </el-col>
              <el-col :span="4">
                <el-select
                  v-model="scenarioComponents.interaction"
                  placeholder="Interaction"
                  @change="updateScenarioId"
                >
                  <el-option
                    label="presence_detected"
                    value="presence_detected"
                  />
                  <el-option label="single_press" value="single_press" />
                  <el-option label="double_press" value="double_press" />
                  <el-option label="long_press" value="long_press" />
                </el-select>
              </el-col>
            </el-row>

            <!-- Generated Scenario ID -->
            <el-alert
              :title="`Generated Scenario ID: ${currentScenarioId}`"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            />

            <!-- Validation Status -->
            <div v-if="validation" style="margin-bottom: 20px">
              <el-alert
                v-if="validation.valid"
                title="✅ Scenario ID is valid"
                type="success"
                :closable="false"
              />
              <el-alert
                v-else
                :title="`❌ Invalid Scenario ID: ${validation.errors.join(
                  ', '
                )}`"
                type="error"
                :closable="false"
              />
              <el-alert
                v-if="validation.warnings && validation.warnings.length > 0"
                :title="`⚠️ Warnings: ${validation.warnings.join(', ')}`"
                type="warning"
                :closable="false"
                style="margin-top: 10px"
              />
            </div>
          </div>

          <!-- Actions Builder -->
          <div class="actions-builder">
            <h3>⚡ Actions</h3>
            <div
              v-for="(action, index) in actions"
              :key="index"
              class="action-item"
            >
              <el-card shadow="hover" style="margin-bottom: 10px">
                <el-row :gutter="10">
                  <el-col :span="6">
                    <el-select
                      v-model="action.service"
                      placeholder="Service"
                      @change="updateServiceOptions(index)"
                    >
                      <el-option label="light.turn_on" value="light.turn_on" />
                      <el-option
                        label="light.turn_off"
                        value="light.turn_off"
                      />
                      <el-option
                        label="switch.turn_on"
                        value="switch.turn_on"
                      />
                      <el-option
                        label="switch.turn_off"
                        value="switch.turn_off"
                      />
                      <el-option label="scene.turn_on" value="scene.turn_on" />
                      <el-option
                        label="script.turn_on"
                        value="script.turn_on"
                      />
                      <el-option
                        label="media_player.play_media"
                        value="media_player.play_media"
                      />
                      <el-option
                        label="climate.set_temperature"
                        value="climate.set_temperature"
                      />
                    </el-select>
                  </el-col>
                  <el-col :span="8">
                    <el-input
                      v-model="action.entity_id"
                      placeholder="entity_id (e.g., light.living_room)"
                    />
                  </el-col>
                  <el-col :span="8">
                    <el-input
                      v-model="action.dataJson"
                      placeholder='data (JSON): {"brightness": 180}'
                      @blur="parseActionData(index)"
                    />
                  </el-col>
                  <el-col :span="2">
                    <el-button
                      @click="removeAction(index)"
                      :icon="Delete"
                      type="danger"
                      plain
                    />
                  </el-col>
                </el-row>
              </el-card>
            </div>

            <el-button @click="addAction" :icon="Plus" type="primary" plain>
              Add Action
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- Preview & Quick Actions -->
      <el-col :span="8">
        <el-card style="margin-bottom: 20px">
          <template #header>
            <span>👁️ Preview</span>
          </template>

          <div class="preview-content">
            <h4>Scenario ID:</h4>
            <el-tag size="large" type="primary">{{
              currentScenarioId || "Not configured"
            }}</el-tag>

            <h4 style="margin-top: 20px">Actions ({{ actions.length }}):</h4>
            <div
              v-for="(action, index) in actions"
              :key="index"
              class="preview-action"
            >
              <el-tag type="info" style="margin-bottom: 5px">
                {{ action.service }} → {{ action.entity_id }}
              </el-tag>
              <div
                v-if="action.data && Object.keys(action.data).length > 0"
                class="action-data"
              >
                <pre>{{ JSON.stringify(action.data, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </el-card>

        <el-card>
          <template #header>
            <span>🚀 Quick Templates</span>
          </template>

          <div class="template-buttons">
            <el-button
              @click="loadTemplate('morning_lights')"
              size="small"
              plain
            >
              🌅 Morning Lights
            </el-button>
            <el-button
              @click="loadTemplate('evening_scene')"
              size="small"
              plain
            >
              🌆 Evening Scene
            </el-button>
            <el-button @click="loadTemplate('night_mode')" size="small" plain>
              🌙 Night Mode
            </el-button>
            <el-button
              @click="loadTemplate('presence_lights')"
              size="small"
              plain
            >
              👤 Presence Lights
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Delete, VideoPlay, Check, Plus } from "@element-plus/icons-vue";
import { useScenarioStore } from "../stores/scenario";

const scenarioStore = useScenarioStore();

// Reactive data
const scenarioComponents = ref({
  room: "",
  timeBucket: "",
  dayType: "",
  flags: [],
  interaction: "",
});

const actions = ref([]);
const validation = ref(null);

// Computed
const currentScenarioId = computed(() => {
  const parts = [];

  if (scenarioComponents.value.room) parts.push(scenarioComponents.value.room);
  if (scenarioComponents.value.timeBucket)
    parts.push(scenarioComponents.value.timeBucket);
  if (scenarioComponents.value.dayType)
    parts.push(scenarioComponents.value.dayType);
  if (scenarioComponents.value.flags.length > 0)
    parts.push(scenarioComponents.value.flags.join("+"));
  if (scenarioComponents.value.interaction)
    parts.push(scenarioComponents.value.interaction);

  return parts.join("|");
});

// Methods
const updateScenarioId = async () => {
  if (currentScenarioId.value) {
    try {
      const response = await fetch("/api/scenarios/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: currentScenarioId.value }),
      });
      validation.value = await response.json();
    } catch (error) {
      console.error("Validation error:", error);
    }
  } else {
    validation.value = null;
  }
};

const addAction = () => {
  actions.value.push({
    service: "",
    entity_id: "",
    data: {},
    dataJson: "",
  });
};

const removeAction = (index) => {
  actions.value.splice(index, 1);
};

const parseActionData = (index) => {
  const action = actions.value[index];
  try {
    if (action.dataJson) {
      action.data = JSON.parse(action.dataJson);
    } else {
      action.data = {};
    }
  } catch (error) {
    ElMessage.error("Invalid JSON in action data");
    action.data = {};
  }
};

const updateServiceOptions = (index) => {
  const action = actions.value[index];
  // Auto-populate common data structures based on service
  if (action.service === "light.turn_on") {
    action.dataJson = '{"brightness": 180, "color_temp": 300}';
    parseActionData(index);
  } else if (action.service === "media_player.play_media") {
    action.dataJson =
      '{"media_content_id": "playlist_name", "media_content_type": "playlist"}';
    parseActionData(index);
  } else if (action.service === "climate.set_temperature") {
    action.dataJson = '{"temperature": 22}';
    parseActionData(index);
  }
};

const clearEditor = () => {
  scenarioComponents.value = {
    room: "",
    timeBucket: "",
    dayType: "",
    flags: [],
    interaction: "",
  };
  actions.value = [];
  validation.value = null;
  ElMessage.success("Editor cleared");
};

const testScenario = async () => {
  if (!currentScenarioId.value) {
    ElMessage.error("Please configure a scenario ID first");
    return;
  }

  if (actions.value.length === 0) {
    ElMessage.error("Please add at least one action");
    return;
  }

  try {
    const response = await fetch(`/api/test/${currentScenarioId.value}`, {
      method: "POST",
    });

    if (response.ok) {
      const result = await response.json();
      ElMessage.success(`Test successful: ${result.message}`);
    } else {
      ElMessage.error("Test failed");
    }
  } catch (error) {
    ElMessage.error("Error testing scenario");
  }
};

const saveScenario = async () => {
  if (!validation.value?.valid) {
    ElMessage.error("Please fix validation errors before saving");
    return;
  }

  if (actions.value.length === 0) {
    ElMessage.error("Please add at least one action");
    return;
  }

  try {
    const scenarioActions = actions.value.map((action) => ({
      service: action.service,
      entity_id: action.entity_id,
      data: action.data,
    }));

    const response = await fetch(`/api/scenarios/${currentScenarioId.value}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(scenarioActions),
    });

    if (response.ok) {
      ElMessage.success("Scenario saved successfully!");
      await scenarioStore.fetchScenarios(); // Refresh store
    } else {
      ElMessage.error("Failed to save scenario");
    }
  } catch (error) {
    ElMessage.error("Error saving scenario");
  }
};

const loadTemplate = (templateName) => {
  const templates = {
    morning_lights: {
      components: {
        room: "kitchen",
        timeBucket: "07-08",
        dayType: "weekday",
        flags: [],
        interaction: "presence_detected",
      },
      actions: [
        {
          service: "light.turn_on",
          entity_id: "light.kitchen_main",
          dataJson: '{"brightness": 200, "color_temp": 250}',
        },
        {
          service: "scene.turn_on",
          entity_id: "scene.kitchen_morning",
          dataJson: "{}",
        },
      ],
    },
    evening_scene: {
      components: {
        room: "living_room",
        timeBucket: "18-19",
        dayType: "",
        flags: [],
        interaction: "presence_detected",
      },
      actions: [
        {
          service: "scene.turn_on",
          entity_id: "scene.living_room_evening",
          dataJson: "{}",
        },
        {
          service: "light.turn_on",
          entity_id: "light.accent_lights",
          dataJson: '{"brightness": 150, "rgb_color": [255, 200, 100]}',
        },
      ],
    },
    night_mode: {
      components: {
        room: "hallway",
        timeBucket: "22-06",
        dayType: "",
        flags: ["night_mode"],
        interaction: "presence_detected",
      },
      actions: [
        {
          service: "light.turn_on",
          entity_id: "light.hallway_nightlight",
          dataJson: '{"brightness": 30, "rgb_color": [255, 150, 50]}',
        },
      ],
    },
    presence_lights: {
      components: {
        room: "bedroom",
        timeBucket: "",
        dayType: "",
        flags: [],
        interaction: "presence_detected",
      },
      actions: [
        {
          service: "light.turn_on",
          entity_id: "light.bedroom_main",
          dataJson: '{"brightness": 120}',
        },
      ],
    },
  };

  const template = templates[templateName];
  if (template) {
    scenarioComponents.value = { ...template.components };
    actions.value = template.actions.map((action) => ({
      ...action,
      data: action.dataJson ? JSON.parse(action.dataJson) : {},
    }));
    updateScenarioId();
    ElMessage.success(`Template "${templateName}" loaded`);
  }
};

// Initialize
onMounted(() => {
  addAction(); // Start with one empty action
});
</script>

<style scoped>
.visual-editor {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.scenario-builder,
.actions-builder {
  margin-bottom: 30px;
}

.scenario-builder h3,
.actions-builder h3 {
  color: #409eff;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-item {
  margin-bottom: 15px;
}

.action-data {
  margin-top: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
}

.action-data pre {
  margin: 0;
  font-family: "Courier New", monospace;
  color: #606266;
}

.preview-content h4 {
  color: #409eff;
  margin: 15px 0 8px 0;
}

.preview-content h4:first-child {
  margin-top: 0;
}

.preview-action {
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.template-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-buttons .el-button {
  text-align: left;
  justify-content: flex-start;
}

:deep(.el-card__body) {
  padding: 15px;
}

:deep(.el-alert) {
  border-radius: 6px;
}

:deep(.el-tag) {
  margin-right: 8px;
  margin-bottom: 4px;
}
</style>
