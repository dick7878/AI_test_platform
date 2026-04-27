<script setup>
import * as monaco from 'monaco-editor'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  language: {
    type: String,
    default: 'python',
  },
  height: {
    type: Number,
    default: 320,
  },
})

const emit = defineEmits(['update:modelValue'])

const containerRef = ref(null)
let editor = null
let syncingFromProps = false

onMounted(() => {
  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: props.language,
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 13,
    scrollBeyondLastLine: false,
  })

  editor.onDidChangeModelContent(() => {
    if (syncingFromProps) {
      return
    }
    emit('update:modelValue', editor.getValue())
  })
})

watch(
  () => props.modelValue,
  (newValue) => {
    if (!editor) return
    const current = editor.getValue()
    if (newValue === current) return
    syncingFromProps = true
    editor.setValue(newValue)
    syncingFromProps = false
  },
)

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
    editor = null
  }
})
</script>

<template>
  <div ref="containerRef" :style="{ height: `${height}px`, width: '100%' }"></div>
</template>
