# Google Maps API 修复测试指南

## 🧪 测试步骤

### 1. 启动应用
确保前后端服务都在运行：
- 后端: http://localhost:8000
- 前端: http://localhost:3000

### 2. 打开浏览器控制台
按 F12 打开开发者工具，切换到 Console 标签

### 3. 刷新页面并观察日志
刷新页面后，您应该看到以下日志：
- `🚀 OrientDiscover 应用启动`
- `✅ 从后端获取到API配置`
- `🔍 开始加载Google Maps API`
- `🔄 正在加载 Google Maps API...`
- `✅ Google Maps script标签加载完成`
- `✅ Google Maps API 已加载`
- `🏙️ Street View 服务已准备就绪`

### 4. 测试街景功能
1. 点击"开始探索"按钮
2. 选择一个场景并点击"出发"
3. 到达场景后，观察控制台是否出现：
   - `⏳ 等待Google Maps API加载...`（如果API还在加载中）
   - `🏙️ 开始为 [场景名] 加载街景...`

### 5. 预期结果
- 街景模态框应该正常显示
- 如果该位置有街景数据，会显示360度全景图
- 如果没有街景数据，会显示友好的错误提示

## 🔍 故障排查

### 如果街景仍然无法显示：

1. **检查Network标签**
   - 查找 `maps.googleapis.com` 的请求
   - 确认返回状态码是 200

2. **检查Console错误**
   - 查看是否有红色错误信息
   - 特别注意 API key 相关的错误

3. **验证API加载状态**
   在控制台输入：
   ```javascript
   console.log('API加载状态:', window.googleMapsLoadStatus);
   console.log('Google对象:', typeof window.google);
   console.log('Google Maps:', typeof window.google?.maps);
   ```

4. **手动测试API**
   在控制台输入：
   ```javascript
   // 测试Street View服务是否可用
   if (window.google && window.google.maps) {
       const sv = new google.maps.StreetViewService();
       console.log('Street View服务已创建:', sv);
   }
   ```

## ✅ 修复验证成功的标志

1. 不再出现 "Google Maps API未加载" 的警告
2. 街景功能可以正常使用
3. 即使快速操作也不会错过API加载

---
*测试文档创建时间: 2025年8月31日*
