<template>
  <div class="scenario-manager">
    <el-row :gutter="20">
      <!-- Main Content -->
      <el-col :span="18">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>📋 Scenario Manager</span>
              <div class="header-actions">
                <el-button
                  @click="refreshScenarios"
                  :icon="Refresh"
                  type="primary"
                >
                  Refresh
                </el-button>
                <el-button
                  @click="showImportDialog = true"
                  :icon="Upload"
                  type="success"
                >
                  Import
                </el-button>
                <el-button
                  @click="exportScenarios"
                  :icon="Download"
                  type="info"
                >
                  Export
                </el-button>
              </div>
            </div>
          </template>

          <!-- Filters -->
          <div class="filters">
            <el-row :gutter="10">
              <el-col :span="6">
                <el-select
                  v-model="filters.room"
                  placeholder="Filter by Room"
                  clearable
                >
                  <el-option label="All Rooms" value="" />
                  <el-option
                    v-for="room in scenarioStore.roomsList"
                    :key="room"
                    :label="room"
                    :value="room"
                  />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-select
                  v-model="filters.dayType"
                  placeholder="Filter by Day Type"
                  clearable
                >
                  <el-option label="All Days" value="" />
                  <el-option label="Weekday" value="weekday" />
                  <el-option label="Weekend" value="weekend" />
                  <el-option label="Any Day" value="any" />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-select
                  v-model="filters.interactionType"
                  placeholder="Filter by Interaction"
                  clearable
                >
                  <el-option label="All Interactions" value="" />
                  <el-option
                    v-for="type in interactionTypes"
                    :key="type"
                    :label="type"
                    :value="type"
                  />
                </el-select>
              </el-col>
              <el-col :span="6">
                <el-input
                  v-model="filters.search"
                  placeholder="Search scenarios..."
                  :prefix-icon="Search"
                  clearable
                />
              </el-col>
            </el-row>
          </div>

          <!-- Scenarios Table -->
          <el-table
            :data="filteredScenarios"
            :loading="scenarioStore.loading"
            @selection-change="handleSelectionChange"
            style="width: 100%; margin-top: 20px"
          >
            <el-table-column type="selection" width="55" />

            <el-table-column
              prop="scenario_id"
              label="Scenario ID"
              min-width="200"
            >
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.scenario_id }}</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="room" label="Room" width="120">
              <template #default="{ row }">
                <el-tag type="primary" size="small">{{ row.room }}</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="time_bucket" label="Time" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.time_bucket" type="success" size="small">
                  {{ row.time_bucket }}
                </el-tag>
                <span v-else class="text-muted">Any</span>
              </template>
            </el-table-column>

            <el-table-column prop="day_type" label="Day" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.day_type" type="warning" size="small">
                  {{ row.day_type }}
                </el-tag>
                <span v-else class="text-muted">Any</span>
              </template>
            </el-table-column>

            <el-table-column prop="optional_flags" label="Flags" width="120">
              <template #default="{ row }">
                <el-tag
                  v-for="flag in row.optional_flags"
                  :key="flag"
                  type="info"
                  size="small"
                  style="margin-right: 5px"
                >
                  {{ flag }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column
              prop="interaction_type"
              label="Interaction"
              width="120"
            >
              <template #default="{ row }">
                <el-tag v-if="row.interaction_type" type="danger" size="small">
                  {{ row.interaction_type }}
                </el-tag>
                <span v-else class="text-muted">Any</span>
              </template>
            </el-table-column>

            <el-table-column prop="actions" label="Actions" width="80">
              <template #default="{ row }">
                <el-badge :value="row.actions.length" type="primary" />
              </template>
            </el-table-column>

            <el-table-column label="Actions" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  @click="editScenario(row)"
                  :icon="Edit"
                  size="small"
                  type="primary"
                />
                <el-button
                  @click="duplicateScenario(row)"
                  :icon="CopyDocument"
                  size="small"
                />
                <el-button
                  @click="deleteScenario(row)"
                  :icon="Delete"
                  size="small"
                  type="danger"
                />
              </template>
            </el-table-column>
          </el-table>

          <!-- Bulk Actions -->
          <div v-if="selectedScenarios.length > 0" class="bulk-actions">
            <el-alert
              :title="`${selectedScenarios.length} scenario(s) selected`"
              type="info"
              show-icon
              :closable="false"
            >
              <el-button
                @click="bulkDelete"
                type="danger"
                size="small"
                :icon="Delete"
              >
                Delete Selected
              </el-button>
              <el-button
                @click="bulkExport"
                type="info"
                size="small"
                :icon="Download"
              >
                Export Selected
              </el-button>
            </el-alert>
          </div>
        </el-card>
      </el-col>

      <!-- Side Panel -->
      <el-col :span="6">
        <!-- Quick Stats -->
        <el-card class="stats-card">
          <template #header>
            <span>📊 Quick Stats</span>
          </template>

          <el-statistic
            title="Total Scenarios"
            :value="scenarioStore.scenarioCount"
          />
          <el-statistic
            title="Total Actions"
            :value="scenarioStore.actionCount"
          />
          <el-statistic title="Rooms" :value="scenarioStore.roomsList.length" />
        </el-card>

        <!-- Suggestions -->
        <el-card class="suggestions-card" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>💡 Suggestions</span>
              <el-button
                @click="loadSuggestions"
                :icon="Refresh"
                size="small"
              />
            </div>
          </template>

          <div v-if="suggestions.length > 0">
            <div
              v-for="suggestion in suggestions.slice(0, 5)"
              :key="suggestion.scenario_id"
              class="suggestion-item"
            >
              <el-card class="suggestion-card">
                <template #header>
                  <div class="suggestion-header">
                    <span class="suggestion-id">{{
                      suggestion.scenario_id
                    }}</span>
                    <el-badge :value="suggestion.count" type="danger" />
                  </div>
                </template>
                <el-button
                  @click="createFromSuggestion(suggestion)"
                  size="small"
                  type="primary"
                >
                  Create Scenario
                </el-button>
              </el-card>
            </div>
          </div>

          <el-empty v-else description="No suggestions available" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Import Dialog -->
    <el-dialog
      v-model="showImportDialog"
      title="Import Scenarios"
      width="600px"
    >
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
        accept=".json"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          Drop JSON file here or <em>click to upload</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">Only JSON files are allowed</div>
        </template>
      </el-upload>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false">Cancel</el-button>
          <el-button
            @click="performImport"
            type="primary"
            :disabled="!importData"
          >
            Import
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Refresh,
  Upload,
  Download,
  Search,
  Edit,
  CopyDocument,
  Delete,
  UploadFilled,
} from "@element-plus/icons-vue";
import { useScenarioStore } from "../stores/scenario";

const scenarioStore = useScenarioStore();

// State
const filters = ref({
  room: "",
  dayType: "",
  interactionType: "",
  search: "",
});

const selectedScenarios = ref([]);
const suggestions = ref([]);
const showImportDialog = ref(false);
const importData = ref(null);

// Computed
const filteredScenarios = computed(() => {
  return scenarioStore.scenarios.filter((scenario) => {
    // Room filter
    if (filters.value.room && scenario.room !== filters.value.room) {
      return false;
    }

    // Day type filter
    if (filters.value.dayType) {
      if (filters.value.dayType === "any" && scenario.day_type) {
        return false;
      } else if (
        filters.value.dayType !== "any" &&
        scenario.day_type !== filters.value.dayType
      ) {
        return false;
      }
    }

    // Interaction type filter
    if (
      filters.value.interactionType &&
      scenario.interaction_type !== filters.value.interactionType
    ) {
      return false;
    }

    // Search filter
    if (filters.value.search) {
      const searchTerm = filters.value.search.toLowerCase();
      return (
        scenario.scenario_id.toLowerCase().includes(searchTerm) ||
        scenario.room.toLowerCase().includes(searchTerm)
      );
    }

    return true;
  });
});

const interactionTypes = computed(() => {
  const types = new Set();
  scenarioStore.scenarios.forEach((scenario) => {
    if (scenario.interaction_type) {
      types.add(scenario.interaction_type);
    }
  });
  return Array.from(types).sort();
});

// Methods
const refreshScenarios = async () => {
  try {
    await scenarioStore.fetchScenarios();
    ElMessage.success("Scenarios refreshed");
  } catch (error) {
    ElMessage.error("Failed to refresh scenarios");
  }
};

const handleSelectionChange = (selection) => {
  selectedScenarios.value = selection;
};

const editScenario = (scenario) => {
  // Load scenario into current scenario state
  scenarioStore.currentScenario = { ...scenario };

  // Navigate to visual editor
  ElMessage.info("Scenario loaded. Switch to Visual Editor to modify.");
};

const duplicateScenario = (scenario) => {
  // Create a copy with modified ID
  const copy = { ...scenario };
  copy.scenario_id = `${scenario.scenario_id}_copy`;

  // Load into current scenario
  scenarioStore.currentScenario = copy;

  ElMessage.info(
    "Scenario duplicated. Switch to Visual Editor to save with new ID."
  );
};

const deleteScenario = async (scenario) => {
  try {
    await ElMessageBox.confirm(
      `This will permanently delete the scenario "${scenario.scenario_id}". Continue?`,
      "Delete Scenario",
      {
        confirmButtonText: "Delete",
        cancelButtonText: "Cancel",
        type: "warning",
      }
    );

    await scenarioStore.deleteScenario(scenario.scenario_id);
    ElMessage.success("Scenario deleted");
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("Failed to delete scenario");
    }
  }
};

const bulkDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `This will permanently delete ${selectedScenarios.value.length} scenario(s). Continue?`,
      "Delete Scenarios",
      {
        confirmButtonText: "Delete",
        cancelButtonText: "Cancel",
        type: "warning",
      }
    );

    for (const scenario of selectedScenarios.value) {
      await scenarioStore.deleteScenario(scenario.scenario_id);
    }

    selectedScenarios.value = [];
    ElMessage.success(`${selectedScenarios.value.length} scenarios deleted`);
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("Failed to delete scenarios");
    }
  }
};

const bulkExport = async () => {
  try {
    const exportData = {
      metadata: {
        exported_at: new Date().toISOString(),
        total_scenarios: selectedScenarios.value.length,
        version: "1.0.0",
      },
      scenarios: {},
    };

    selectedScenarios.value.forEach((scenario) => {
      exportData.scenarios[scenario.scenario_id] = scenario.actions;
    });

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `nodalink_scenarios_${
      new Date().toISOString().split("T")[0]
    }.json`;
    link.click();

    URL.revokeObjectURL(url);
    ElMessage.success("Scenarios exported");
  } catch (error) {
    ElMessage.error("Failed to export scenarios");
  }
};

const exportScenarios = async () => {
  try {
    const data = await scenarioStore.exportScenarios();

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `nodalink_scenarios_${
      new Date().toISOString().split("T")[0]
    }.json`;
    link.click();

    URL.revokeObjectURL(url);
    ElMessage.success("All scenarios exported");
  } catch (error) {
    ElMessage.error("Failed to export scenarios");
  }
};

const loadSuggestions = async () => {
  try {
    const response = await fetch("/api/suggestions");
    const data = await response.json();
    suggestions.value = data.suggestions || [];
  } catch (error) {
    console.error("Failed to load suggestions:", error);
  }
};

const createFromSuggestion = (suggestion) => {
  // Parse scenario ID components
  const parts = suggestion.scenario_id.split("|");

  scenarioStore.currentScenario = {
    room: parts[0] || "",
    time_bucket: parts[1] || "",
    day_type: parts[2] || "",
    optional_flags: parts[3] ? parts[3].split("+") : [],
    interaction_type: parts[4] || "",
    actions: [],
  };

  ElMessage.success(
    "Suggestion loaded. Switch to Visual Editor to add actions."
  );
};

const handleFileChange = (file) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      importData.value = JSON.parse(e.target.result);
    } catch (error) {
      ElMessage.error("Invalid JSON file");
      importData.value = null;
    }
  };
  reader.readAsText(file.raw);
};

const performImport = async () => {
  try {
    await scenarioStore.importScenarios(importData.value);
    showImportDialog.value = false;
    importData.value = null;
    ElMessage.success("Scenarios imported successfully");
  } catch (error) {
    ElMessage.error(`Import failed: ${error.message}`);
  }
};

onMounted(async () => {
  if (scenarioStore.scenarios.length === 0) {
    await refreshScenarios();
  }
  await loadSuggestions();
});
</script>

<style scoped>
.scenario-manager {
  height: calc(100vh - 140px);
  overflow: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  margin-bottom: 20px;
}

.bulk-actions {
  margin-top: 20px;
}

.stats-card :deep(.el-statistic) {
  margin-bottom: 15px;
}

.suggestion-item {
  margin-bottom: 10px;
}

.suggestion-card {
  border: 1px solid #e4e7ed;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestion-id {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.text-muted {
  color: #999;
  font-style: italic;
}

.upload-demo {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
