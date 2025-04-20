<!-- src/components/SaveLayoutDialog.vue -->
<template>
  <v-dialog v-model="dialogVisible" max-width="600px">
    <v-card>
      <v-card-title>
        {{ isEditing ? $t('layouts.editLayout') : $t('layouts.saveLayout') }}
      </v-card-title>
      
      <v-card-text>
        <v-form ref="form" v-model="valid">
          <v-text-field
            v-model="layoutData.name"
            :label="$t('layouts.layoutName')"
            :rules="[v => !!v || $t('common.name') + ' ' + $t('common.isRequired')]"
            required
          ></v-text-field>
          
          <v-textarea
            v-model="layoutData.description"
            :label="$t('layouts.layoutDescription')"
            rows="3"
            :hint="$t('layouts.layoutDescriptionHint')"
          ></v-textarea>
        </v-form>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="close">{{ $t('common.cancel') }}</v-btn>
        <v-btn 
          color="primary" 
          :disabled="!valid || loading" 
          :loading="loading"
          @click="save"
        >
          {{ $t('common.save') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  layout: {
    type: Object,
    default: () => ({
      name: '',
      description: '',
      rows: 2,
      columns: 2,
      panels: []
    })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'save', 'cancel'])

const form = ref(null)
const valid = ref(false)
const layoutData = ref({
  name: '',
  description: '',
  rows: 2,
  columns: 2,
  panels: []
})

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isEditing = computed(() => !!layoutData.value.id)

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    // When dialog opens, initialize form with layout data
    layoutData.value = JSON.parse(JSON.stringify(props.layout))
  }
})

const close = () => {
  dialogVisible.value = false
  emit('cancel')
}

const save = () => {
  if (!valid.value) return
  
  emit('save', layoutData.value)
}
</script>
