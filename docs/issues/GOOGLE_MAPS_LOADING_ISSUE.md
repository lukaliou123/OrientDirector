# Google Maps API 加载失败问题分析

## 🔍 问题描述

用户报告Google Maps API未能成功加载，导致街景功能无法使用：
```
[21:04:26] ⚠️ 跳过街景显示：Google Maps API未加载
[21:04:26] ⚠️ Google Maps API未加载
```

## 🎯 问题分析

### 1. API配置正确
后端返回了有效的API配置：
```json
{
    "apiKey": "AIzaSyC3fc8-5r4SWOISs0IIduiE4TOvE8-aFC0",
    "enabled": true,
    "message": "Google Maps配置已加载"
}
```

### 2. 时序问题分析

<xml>
<加载流程>
  <步骤1>
    <时间>DOMContentLoaded</时间>
    <操作>await loadAppConfig() - 从后端获取API key</操作>
    <状态>异步操作，需要时间</状态>
  </步骤1>
  
  <步骤2>
    <时间>loadAppConfig完成后</时间>
    <操作>loadGoogleMapsAPI() - 检查API key并加载script</操作>
    <状态>创建script标签，异步加载</状态>
  </步骤2>
  
  <步骤3>
    <时间>Google Maps script加载完成</时间>
    <操作>触发initGoogleMaps回调</操作>
    <状态>初始化streetViewService</状态>
  </步骤3>
  
  <步骤4>
    <时间>用户到达场景</时间>
    <操作>showStreetViewForLocation() 检查API是否加载</操作>
    <问题>如果步骤3还未完成，检查会失败</问题>
  </步骤4>
</加载流程>
</xml>

### 3. 可能的原因

1. **加载时间延迟**
   - Google Maps API script可能还在下载中
   - 网络延迟导致加载缓慢

2. **加载错误**
   - API key无效或权限不足
   - 网络连接问题
   - CSP（内容安全策略）阻止

3. **回调未触发**
   - script加载失败但onerror也没触发
   - 回调函数名称冲突

## 🛠 调试方案

### 1. 添加详细日志
在index.html中修改loadGoogleMapsAPI函数：

```javascript
function loadGoogleMapsAPI() {
    const apiKey = window.appConfig.googleMapsApiKey;
    
    console.log('🔍 开始加载Google Maps API');
    console.log('   API Key:', apiKey);
    
    if (!apiKey || apiKey === 'YOUR_GOOGLE_MAPS_API_KEY') {
        console.warn('⚠️ Google Maps API Key 未配置');
        return false;
    }
    
    // 检查是否已经加载过
    if (window.google && window.google.maps) {
        console.log('✅ Google Maps API 已存在');
        window.initGoogleMaps();
        return true;
    }
    
    console.log('🔄 创建script标签...');
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initGoogleMaps&v=weekly&libraries=geometry`;
    script.async = true;
    script.defer = true;
    
    // 添加加载成功事件
    script.onload = function() {
        console.log('✅ Google Maps script标签加载完成');
    };
    
    script.onerror = function(error) {
        console.error('❌ Google Maps API 加载失败:', error);
        console.log('可能的原因：');
        console.log('1. API Key无效');
        console.log('2. 网络连接问题');
        console.log('3. API配额用尽');
    };
    
    document.head.appendChild(script);
    console.log('📌 Script标签已添加到页面');
    return true;
}
```

### 2. 检查浏览器控制台

打开浏览器开发者工具，检查：
1. **Console标签** - 查看错误信息
2. **Network标签** - 查看Google Maps API请求是否成功
3. **Elements标签** - 确认script标签是否被添加

### 3. 使用调试页面

我创建了一个调试页面 `debug_google_maps.html`，可以：
1. 在浏览器中打开它
2. 查看Google Maps API的加载状态
3. 确认API key是否有效

### 4. 可能的修复方案

#### 方案A：增加重试机制
```javascript
let googleMapsLoadAttempts = 0;
const maxLoadAttempts = 3;

function ensureGoogleMapsLoaded(callback) {
    if (window.google && window.google.maps) {
        callback();
    } else if (googleMapsLoadAttempts < maxLoadAttempts) {
        googleMapsLoadAttempts++;
        console.log(`⏳ 等待Google Maps加载... (尝试 ${googleMapsLoadAttempts}/${maxLoadAttempts})`);
        setTimeout(() => ensureGoogleMapsLoaded(callback), 1000);
    } else {
        console.error('❌ Google Maps加载超时');
    }
}
```

#### 方案B：使用Promise包装
```javascript
let googleMapsPromise = null;

function loadGoogleMapsAPIAsync() {
    if (googleMapsPromise) return googleMapsPromise;
    
    googleMapsPromise = new Promise((resolve, reject) => {
        window.initGoogleMaps = function() {
            console.log('✅ Google Maps API 已加载');
            if (typeof initGoogleMapsAPI === 'function') {
                initGoogleMapsAPI();
            }
            resolve();
        };
        
        // 加载script的代码...
    });
    
    return googleMapsPromise;
}
```

## 🔍 立即检查事项

1. **打开浏览器控制台查看是否有错误**
2. **在Network标签中查找maps.googleapis.com的请求**
3. **检查返回的HTTP状态码**
4. **查看是否有CORS或CSP错误**

## 💡 临时解决方案

如果API key有问题，可以：
1. 在Google Cloud Console检查API key的配置
2. 确保启用了Maps JavaScript API和Street View API
3. 检查API key的使用限制和配额

---
*分析时间: 2025年8月31日*
