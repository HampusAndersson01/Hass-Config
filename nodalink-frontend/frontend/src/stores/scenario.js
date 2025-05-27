import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useScenarioStore = defineStore("scenario", () => {
  // State
  const scenarios = ref([]);
  const currentScenario = ref({
    room: "",
    time_bucket: "",
    day_type: "",
    optional_flags: [],
    interaction_type: "",
    actions: [],
  });
  const loading = ref(false);
  const error = ref(null);

  // Getters
  const scenarioCount = computed(() => scenarios.value.length);
  const actionCount = computed(() =>
    scenarios.value.reduce(
      (total, scenario) => total + scenario.actions.length,
      0
    )
  );
  const roomsList = computed(() =>
    [...new Set(scenarios.value.map((s) => s.room))].sort()
  );

  // Actions
  const fetchScenarios = async () => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch("/api/scenarios");
      if (!response.ok) throw new Error("Failed to fetch scenarios");

      scenarios.value = await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const createScenario = async (scenarioData) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch("/api/scenarios", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(scenarioData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create scenario");
      }

      const result = await response.json();
      await fetchScenarios(); // Refresh the list
      return result;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const updateScenario = async (scenarioId, scenarioData) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/scenarios/${scenarioId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(scenarioData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update scenario");
      }

      const result = await response.json();
      await fetchScenarios(); // Refresh the list
      return result;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const deleteScenario = async (scenarioId) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/scenarios/${scenarioId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete scenario");
      }

      await fetchScenarios(); // Refresh the list
      return true;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const validateScenarios = async () => {
    try {
      const response = await fetch("/api/validate", {
        method: "POST",
      });

      if (!response.ok) throw new Error("Validation request failed");

      return await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  };

  const exportScenarios = async () => {
    try {
      const response = await fetch("/api/export", {
        method: "POST",
      });

      if (!response.ok) throw new Error("Export request failed");

      return await response.json();
    } catch (err) {
      error.value = err.message;
      throw err;
    }
  };

  const importScenarios = async (data) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch("/api/import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to import scenarios");
      }

      const result = await response.json();
      await fetchScenarios(); // Refresh the list
      return result;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const resetCurrentScenario = () => {
    currentScenario.value = {
      room: "",
      time_bucket: "",
      day_type: "",
      optional_flags: [],
      interaction_type: "",
      actions: [],
    };
  };

  const buildScenarioId = (scenario = currentScenario.value) => {
    const parts = [scenario.room, scenario.time_bucket];

    if (scenario.day_type) {
      parts.push(scenario.day_type);
    }

    if (scenario.optional_flags && scenario.optional_flags.length > 0) {
      parts.push(scenario.optional_flags.join("+"));
    }

    if (scenario.interaction_type) {
      parts.push(scenario.interaction_type);
    }

    return parts.filter((part) => part).join("|");
  };

  return {
    // State
    scenarios,
    currentScenario,
    loading,
    error,

    // Getters
    scenarioCount,
    actionCount,
    roomsList,

    // Actions
    fetchScenarios,
    createScenario,
    updateScenario,
    deleteScenario,
    validateScenarios,
    exportScenarios,
    importScenarios,
    resetCurrentScenario,
    buildScenarioId,
  };
});
