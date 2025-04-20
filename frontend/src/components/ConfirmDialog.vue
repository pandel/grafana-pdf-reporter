<!-- src/components/ConfirmDialog.vue -->
<template>
  <v-dialog
    v-model="dialogVisible"
    :max-width="width"
    @keydown.esc="cancel"
  >
    <v-card>
      <v-card-title>
        {{ title }}
      </v-card-title>
      
      <v-card-text>
        {{ message }}
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          :color="cancelColor"
          @click="cancel"
        >
          {{ cancelText || $t('common.cancel') }}
        </v-btn>
        <v-btn
          :color="confirmColor"
          @click="confirm"
          :loading="loading"
        >
          {{ confirmText || $t('common.confirm') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    default: ''
  },
  confirmText: {
    type: String,
    default: ''
  },
  cancelText: {
    type: String,
    default: ''
  },
  confirmColor: {
    type: String,
    default: 'primary'
  },
  cancelColor: {
    type: String,
    default: 'grey-darken-1'
  },
  width: {
    type: [Number, String],
    default: 400
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const confirm = () => {
  emit('confirm')
}

const cancel = () => {
  emit('cancel')
  dialogVisible.value = false
}
</script>
