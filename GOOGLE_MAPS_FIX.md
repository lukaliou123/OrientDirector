# Google Maps API 加载问题修复方案

## 🎯 问题确认

经过测试，API key是有效的，Google Maps API能正常返回内容。问题是**时序问题**：
- Google Maps API异步加载需要时间
- 用户可能在API加载完成前就到达场景并触发街景功能

## 🛠 修复方案

[[memory:5441768]] 根据您的要求，我提供以下修改建议供您参考：

### 修改文件列表
1. `index.html` - 改进API加载逻辑
2. `app.js` - 添加API状态检查和重试机制

### 具体修改内容

#### 1. index.html（第218-248行）
在`loadGoogleMapsAPI`函数中添加状态跟踪：

```javascript
// 添加全局状态变量
window.googleMapsLoadStatus = 'pending'; // pending, loading, loaded, failed

function loadGoogleMapsAPI() {
    const apiKey = window.appConfig.googleMapsApiKey;
    
    console.log('🔍 开始加载Google Maps API');
    console.log('   API Key:', apiKey ? apiKey.substring(0, 10) + '...' : '未设置');

    if (!apiKey || apiKey === 'YOUR_GOOGLE_MAPS_API_KEY') {
        console.warn('⚠️ Google Maps API Key 未配置');
        window.googleMapsLoadStatus = 'failed';
        return false;
    }

    // 检查是否已经加载过
    if (window.google && window.google.maps) {
        console.log('✅ Google Maps API 已存在');
        window.googleMapsLoadStatus = 'loaded';
        window.initGoogleMaps();
        return true;
    }

    window.googleMapsLoadStatus = 'loading';
    console.log('🔄 正在加载 Google Maps API...');
    
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initGoogleMaps&v=weekly&libraries=geometry`;
    script.async = true;
    script.defer = true;
    
    script.onload = function() {
        console.log('✅ Google Maps script标签加载完成');
    };
    
    script.onerror = function(error) {
        window.googleMapsLoadStatus = 'failed';
        console.error('❌ Google Maps API 加载失败');
        console.log('🔍 请检查:');
        console.log('   1. API Key 是否正确');
        console.log('   2. 网络连接是否正常');
        console.log('   3. API Key 是否有正确的权限');
        console.log('   4. 浏览器控制台是否有其他错误');
    };
    
    document.head.appendChild(script);
    return true;
}

// 修改回调函数
window.initGoogleMaps = function() {
    console.log('✅ Google Maps API 已加载');
    console.log('🏙️ Street View 服务已准备就绪');
    window.googleMapsLoadStatus = 'loaded';
    
    // 初始化街景相关变量
    if (typeof initGoogleMapsAPI === 'function') {
        initGoogleMapsAPI();
    }
    
    // 触发自定义事件，通知API已加载
    window.dispatchEvent(new Event('googleMapsLoaded'));
};
```

#### 2. app.js（第2512行附近）
修改`showStreetViewForLocation`函数，添加等待和重试机制：

```javascript
// 显示指定位置的Google街景
async function showStreetViewForLocation(scene) {
    // 等待Google Maps API加载
    const maxWaitTime = 10000; // 最多等待10秒
    const checkInterval = 500; // 每500ms检查一次
    let waitedTime = 0;
    
    while (window.googleMapsLoadStatus !== 'loaded' && waitedTime < maxWaitTime) {
        if (window.googleMapsLoadStatus === 'failed') {
            logger.error('❌ Google Maps API 加载失败，无法显示街景');
            return;
        }
        
        if (waitedTime === 0) {
            logger.info('⏳ 等待Google Maps API加载...');
        }
        
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        waitedTime += checkInterval;
    }
    
    if (window.googleMapsLoadStatus !== 'loaded') {
        logger.error('❌ Google Maps API 加载超时');
        return;
    }
    
    // 检查Google Maps API是否已加载
    if (!initGoogleMapsAPI()) {
        logger.warning('⚠️ 跳过街景显示：Google Maps API未正确初始化');
        return;
    }
    
    // 原有的街景显示逻辑...
    const location = {
        lat: scene.latitude,
        lng: scene.longitude
    };
    
    // 继续原有代码...
}

// 或者使用事件监听方式（替代方案）
function showStreetViewForLocationWithEvent(scene) {
    if (window.googleMapsLoadStatus === 'loaded') {
        // API已加载，直接显示
        doShowStreetView(scene);
    } else if (window.googleMapsLoadStatus === 'loading') {
        // API加载中，等待事件
        logger.info('⏳ 等待Google Maps API加载完成...');
        
        const handler = () => {
            window.removeEventListener('googleMapsLoaded', handler);
            doShowStreetView(scene);
        };
        
        window.addEventListener('googleMapsLoaded', handler);
    } else {
        logger.error('❌ Google Maps API 未加载或加载失败');
    }
}

function doShowStreetView(scene) {
    // 将原有的showStreetViewForLocation逻辑移到这里
    if (!initGoogleMapsAPI()) {
        logger.warning('⚠️ 跳过街景显示：Google Maps API未正确初始化');
        return;
    }
    
    // 继续原有的街景显示代码...
}
```

## 🧪 测试步骤

1. 修改代码后刷新页面
2. 打开浏览器控制台查看日志
3. 快速点击"开始探索"并到达场景
4. 观察是否出现"等待Google Maps API加载..."的提示
5. 确认街景功能是否正常显示

## 💡 其他建议

1. **预加载优化**：在用户开始探索前就加载Google Maps API
2. **加载指示器**：在等待API加载时显示加载动画
3. **降级方案**：如果API加载失败，提供静态图片作为替代

---
*修复方案完成时间: 2025年8月31日*
