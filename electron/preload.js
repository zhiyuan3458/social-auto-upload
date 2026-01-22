const { contextBridge, ipcRenderer } = require('electron')

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 获取应用信息
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  
  // 平台信息
  platform: process.platform,
  
  // 检查是否在 Electron 环境
  isElectron: true
})
