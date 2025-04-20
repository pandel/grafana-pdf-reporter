<!-- src/components/PanelItem.vue -->
<template>
  <div 
    class="panel-item"
    :style="panelStyle"
    @mousedown.prevent="$emit('drag-start', $event)"
  >
    <div class="panel-header" :class="{ 'panel-header--dark': isDark }">
      <span>{{ panel.title }}</span>
      <v-btn
        variant="text"
        icon="mdi-close"
        size="small"
        color="error"
        class="remove-btn"
        @click.stop="$emit('remove')"
        :aria-label="$t('reportDesigner.remove')"
      ></v-btn>
    </div>
    <div class="panel-content" :class="{ 'panel-content--dark': isDark }">
      <v-icon size="large">{{ panelIcon }}</v-icon>
      <div>{{ panel.title }}</div>
    </div>
    <div class="resize-handle" @mousedown.prevent.stop="$emit('resize-start', $event)"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from 'vuetify'

const props = defineProps({
  panel: {
    type: Object,
    required: true
  },
  gridConfig: {
    type: Object,
    required: true,
    default: () => ({
      columns: 2,
      rows: 2
    })
  },
  isActive: {
    type: Boolean,
    default: false
  }
})

defineEmits(['drag-start', 'resize-start', 'remove'])

const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)

const panelStyle = computed(() => {
  const { columns, rows } = props.gridConfig
  const { x, y, w, h } = props.panel
  const cellWidth = 100 / columns
  const cellHeight = 100 / rows
  
  return {
    position: 'absolute',
    left: `${x * cellWidth}%`,
    top: `${y * cellHeight}%`,
    width: `${w * cellWidth}%`,
    height: `${h * cellHeight}%`,
    backgroundColor: isDark.value ? '#1E1E1E' : 'white',
    border: isDark.value ? '1px solid #333' : '1px solid #ddd',
    borderRadius: '4px',
    boxShadow: props.isActive ? 
      (isDark.value ? '0 2px 8px rgba(0,0,0,0.5)' : '0 2px 8px rgba(0,0,0,0.2)') : 
      (isDark.value ? '0 1px 3px rgba(0,0,0,0.5)' : '0 1px 3px rgba(0,0,0,0.12)'),
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    zIndex: props.isActive ? 10 : 1
  }
})

const panelIcon = computed(() => {
  const icons = {
    'graph': 'mdi-chart-line',
    'bargauge': 'mdi-gauge',
    'gauge': 'mdi-gauge',
    'singlestat': 'mdi-numeric',
    'table': 'mdi-table',
    'text': 'mdi-format-text',
    'heatmap': 'mdi-grid',
    'stat': 'mdi-numeric',
    'timeseries': 'mdi-chart-timeline'
  }
  
  return icons[props.panel.type] || 'mdi-chart-box'
})
</script>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f5f5f5;
  color: #333;
  padding: 4px 8px;
  font-size: 0.9rem;
  font-weight: 500;
  border-bottom: 1px solid #ddd;
  cursor: move;
}

.panel-header--dark {
  background-color: #2c2c2c;
  color: #fff;
  border-bottom: 1px solid #444;
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 8px;
  overflow: hidden;
  color: #333;
}

.panel-content--dark {
  color: #eee;
}

.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  background: linear-gradient(135deg, transparent 0%, transparent 50%, #ddd 50%, #ddd 100%);
}

.panel-item .panel-header .remove-btn {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.panel-item:hover .panel-header .remove-btn {
  opacity: 1;
}
</style>
