<!-- src/components/TemplatePreview.vue -->
<template>
  <div class="template-preview">
    <div class="preview-page" :style="pageStyle">
      <div class="preview-header" :style="headerStyle">
        <div class="header-title">{{ template.header.title }}</div>
        <div v-if="template.header.logoUrl" class="header-logo">
          <img :src="template.header.logoUrl" alt="Logo">
        </div>
      </div>
      
      <div class="preview-content" :style="contentStyle">
        <slot>
          <div class="content-placeholder">
            {{ $t('templates.contentArea') }}
          </div>
        </slot>
      </div>
      
      <div class="preview-footer" :style="footerStyle">
        <div class="footer-text">{{ template.footer.text }}</div>
        <div class="footer-page">{{ template.footer.pageNumberFormat.replace('(page)', currentPage).replace('(total)', totalPages) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  template: {
    type: Object,
    required: true
  },
  currentPage: {
    type: [Number, String],
    default: 1
  },
  totalPages: {
    type: [Number, String],
    default: 1
  },
  scale: {
    type: Number,
    default: 0.4
  }
})

const pageStyle = computed(() => {
  const { orientation } = props.template.page
  
  return {
    width: orientation === 'portrait' ? '210mm' : '297mm',
    height: orientation === 'portrait' ? '297mm' : '210mm',
    position: 'relative',
    backgroundColor: 'white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    transform: `scale(${props.scale})`,
    transformOrigin: 'top left',
    marginBottom: props.scale < 1 ? `-${(1 - props.scale) * (orientation === 'portrait' ? 297 : 210)}mm` : '0'
  }
})

const headerStyle = computed(() => {
  const { backgroundColor, textColor, height } = props.template.header
  const { marginLeft, marginRight, marginTop } = props.template.page
  
  return {
    position: 'absolute',
    top: `${marginTop}mm`,
    left: `${marginLeft}mm`,
    right: `${marginRight}mm`,
    height: `${height}mm`,
    backgroundColor,
    color: textColor,
    padding: '8px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  }
})

const contentStyle = computed(() => {
  const { marginLeft, marginRight, marginTop, marginBottom } = props.template.page
  const headerHeight = props.template.header.height
  const footerHeight = props.template.footer.height
  
  return {
    position: 'absolute',
    top: `${Number(marginTop) + Number(headerHeight)}mm`,
    left: `${marginLeft}mm`,
    right: `${marginRight}mm`,
    bottom: `${Number(marginBottom) + Number(footerHeight)}mm`,
    backgroundColor: '#f5f5f5',
    border: '1px dashed #ccc',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    color: '#666'
  }
})

const footerStyle = computed(() => {
  const { backgroundColor, textColor, height } = props.template.footer
  const { marginLeft, marginRight, marginBottom } = props.template.page
  
  return {
    position: 'absolute',
    bottom: `${marginBottom}mm`,
    left: `${marginLeft}mm`,
    right: `${marginRight}mm`,
    height: `${height}mm`,
    backgroundColor,
    color: textColor,
    padding: '8px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  }
})
</script>

<style scoped>
.template-preview {
  overflow: hidden;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.preview-page {
  margin: 0 auto;
}

.header-title, .footer-text {
  font-weight: 500;
}

.header-logo img {
  max-height: 80%;
  max-width: 100px;
}

.content-placeholder {
  font-size: 24px;
  color: #ccc;
}

.footer-page {
  font-size: 0.9em;
}
</style>
