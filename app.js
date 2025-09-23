// 🌍 环境配置：智能检测本地开发vs云部署
const API_CONFIG = {
    // 检测是否为本地开发环境
    isLocalDev: window.location.hostname === 'localhost' && window.location.port === '3000',
    
    // 根据环境返回API基础URL
    getApiBaseUrl() {
        if (this.isLocalDev) {
            return 'http://localhost:8000';  // 本地开发：后端在8000端口
        } else {
            return '';  // 云环境：使用相对路径
        }
    },
    
    // 构建完整的API URL
    getApiUrl(endpoint) {
        return this.getApiBaseUrl() + endpoint;
    }
};

console.log('🌍 环境检测:', {
    hostname: window.location.hostname,
    port: window.location.port,
    isLocalDev: API_CONFIG.isLocalDev,
    apiBaseUrl: API_CONFIG.getApiBaseUrl()
});

// 全局变量
let currentPosition = null;
let currentHeading = 0;

// 预设地址数据 - 全球知名景点
const PRESET_LOCATIONS = {
    tokyo: {
        name: "东京浅草寺区域",
        latitude: 35.7148,
        longitude: 139.7967,
        country: "日本",
        description: "传统与现代交融的东京文化中心，浅草寺历史悠久"
    },
    paris: {
        name: "巴黎埃菲尔铁塔",
        latitude: 48.8584,
        longitude: 2.2945,
        country: "法国",
        description: "浪漫之都的标志性建筑，艺术与文化的圣地"
    },
    newyork: {
        name: "纽约时代广场",
        latitude: 40.7580,
        longitude: -73.9855,
        country: "美国",
        description: "世界十字路口，国际化大都市的繁华中心"
    },
    london: {
        name: "伦敦大本钟",
        latitude: 51.4994,
        longitude: -0.1245,
        country: "英国",
        description: "历史悠久的英伦象征，泰晤士河畔的经典地标"
    },
    sydney: {
        name: "悉尼歌剧院",
        latitude: -33.8568,
        longitude: 151.2153,
        country: "澳大利亚",
        description: "南半球璀璨明珠，现代建筑艺术的杰作"
    },
    sanfrancisco: {
        name: "旧金山金门大桥",
        latitude: 37.8199,
        longitude: -122.4783,
        country: "美国",
        description: "科技与自然完美结合的西海岸明珠"
    },
    rome: {
        name: "罗马斗兽场",
        latitude: 41.9028,
        longitude: 12.4964,
        country: "意大利",
        description: "永恒之城的历史见证，古罗马帝国的辉煌"
    },
    constantinople: {
        name: "君士坦丁堡圣索菲亚大教堂",
        latitude: 41.0082,
        longitude: 28.9784,
        country: "土耳其",
        description: "连接欧亚的古都，拜占庭帝国的辉煌中心"
    },
    beijing: {
        name: "北京故宫",
        latitude: 39.9042,
        longitude: 116.4074,
        country: "中国",
        description: "中华文明的瑰宝，紫禁城见证千年历史变迁"
    },
    amsterdam: {
        name: "阿姆斯特丹运河区",
        latitude: 52.3676,
        longitude: 4.9041,
        country: "荷兰",
        description: "欧洲独特水城风情，艺术与自由的完美融合"
    }
};

// 当前位置来源类型
let currentLocationSource = 'gps'; // 'gps', 'preset', 'manual'

// 历史模式相关变量
let isHistoricalMode = false;           // 是否启用历史模式
let selectedHistoricalYear = null;     // 选择的历史年份
let currentHistoricalInfo = null;      // 当前历史查询结果
let historicalSceneData = null;        // 当前历史场景数据

// Google街景相关变量
let streetViewPanorama = null;
let streetViewService = null;
let currentStreetViewLocation = null;
let isStreetViewFullscreen = false;
let settings = {
    segmentDistance: 10,
    timeMode: 'present',
    speed: 120,
    dataSource: 'real'  // 只使用真实数据
};

// 场景管理状态
let sceneManagement = {
    allScenes: [],          // 所有场景列表
    selectedScenes: [],     // 用户选中的场景
    rejectedScenes: [],     // 用户划掉的场景
    isSelectionMode: false, // 是否处于选择模式
    // 🆕 跟踪当前正在确认到达的场景，用于处理"返回"按钮
    currentlyVisitingScene: null
};

// 旅程管理状态
let journeyManagement = {
    currentJourneyId: null,     // 当前旅程ID
    isJourneyActive: false,     // 是否有活跃旅程
    startLocation: null,        // 起始位置
    visitedScenes: [],          // 已访问的场景
    totalDistance: 0,           // 总行程距离
    historyScenes: []           // 历史场景显示数据
};

// 日志系统
class Logger {
    constructor() {
        this.logs = [];
        this.maxLogs = 100;
    }
    
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = {
            timestamp,
            message,
            type,
            id: Date.now()
        };
        
        this.logs.unshift(logEntry);
        if (this.logs.length > this.maxLogs) {
            this.logs.pop();
        }
        
        this.displayLog(logEntry);
        console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
    }
    
    info(message) { this.log(message, 'info'); }
    success(message) { this.log(message, 'success'); }
    warning(message) { this.log(message, 'warning'); }
    error(message) { this.log(message, 'error'); }
    
    displayLog(logEntry) {
        const container = document.getElementById('logContainer');
        if (!container) return;
        
        const logElement = document.createElement('div');
        logElement.className = `log-entry ${logEntry.type}`;
        logElement.innerHTML = `
            <span class="log-timestamp">[${logEntry.timestamp}]</span>
            <span class="log-message">${logEntry.message}</span>
        `;
        
        container.insertBefore(logElement, container.firstChild);
        
        // 限制显示的日志数量
        const entries = container.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[entries.length - 1].remove();
        }
    }
    
    clear() {
        this.logs = [];
        const container = document.getElementById('logContainer');
        if (container) {
            container.innerHTML = '';
        }
        console.clear();
    }
}

const logger = new Logger();

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    logger.info('🧭 方向探索派对应用启动');
    logger.info('正在初始化应用组件...');
    
    // 检查浏览器支持
    if (!checkBrowserSupport()) {
        const errorMsg = '您的浏览器不支持所需功能，请使用现代浏览器访问';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    logger.success('浏览器兼容性检查通过');
    
    // 请求权限并获取位置
    await requestPermissions();
    
    // 初始化传感器
    initializeCompass();
    
    // 初始化点击指南针功能
    initializeCompassClick();
    
    // 获取初始位置
    refreshLocation();
    
    logger.success('应用初始化完成');
}

// 初始化点击指南针功能
function initializeCompassClick() {
    const compass = document.getElementById('compass');
    if (compass) {
        // 添加点击事件
        compass.style.cursor = 'pointer';
        compass.addEventListener('click', function(event) {
            const rect = compass.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            // 计算点击位置相对于中心的角度
            const x = event.clientX - centerX;
            const y = event.clientY - centerY;
            
            // 计算角度（从北开始顺时针）
            let angle = Math.atan2(x, -y) * (180 / Math.PI);
            if (angle < 0) angle += 360;
            
            // 设置新的方向
            currentHeading = Math.round(angle);
            updateCompassDisplay(currentHeading);
            logger.success(`通过点击设置方向: ${currentHeading}°`);
            
            // 隐藏手动输入框（如果存在）
            const manualInput = document.querySelector('.manual-heading-input');
            if (manualInput) {
                manualInput.style.display = 'none';
            }
        });
        
        // 添加鼠标悬停提示
        compass.title = '点击设置方向';
    }
}

// 启用手动输入方向功能
function enableManualHeadingInput() {
    logger.info('启用手动方向输入模式');
    
    // 查找合适的位置插入手动输入控件
    const statusDisplay = document.querySelector('.status-display');
    const compassContainer = document.querySelector('.compass-container');
    const targetElement = compassContainer || statusDisplay;
    
    if (targetElement && !document.querySelector('.manual-heading-input')) {
        const manualInput = document.createElement('div');
        manualInput.className = 'manual-heading-input';
        manualInput.style.cssText = 'background: #fff3cd; border: 1px solid #ffecc0; border-radius: 8px; padding: 15px; margin: 10px 0;';
        manualInput.innerHTML = `
            <p style="color: #856404; margin: 0 0 10px 0; font-weight: bold;">📍 无法自动获取方向</p>
            <p style="color: #856404; margin: 0 0 10px 0;">请点击指南针设置方向，或手动输入：</p>
            <div style="display: flex; align-items: center; gap: 10px;">
                <input type="number" id="manualHeading" min="0" max="359" value="${currentHeading || 0}" 
                       placeholder="方向角度" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 120px;">
                <button onclick="setManualHeading()" style="padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">设置</button>
            </div>
            <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">💡 提示：0°=北, 90°=东, 180°=南, 270°=西</p>
        `;
        targetElement.parentNode.insertBefore(manualInput, targetElement.nextSibling);
    }
}

// 设置手动方向
window.setManualHeading = function() {
    const input = document.getElementById('manualHeading');
    if (input) {
        const heading = parseInt(input.value);
        if (!isNaN(heading) && heading >= 0 && heading <= 359) {
            currentHeading = heading;
            updateCompassDisplay(heading);
            logger.success(`手动设置方向: ${heading}°`);
            
            // 隐藏输入框
            const manualInput = document.querySelector('.manual-heading-input');
            if (manualInput) {
                manualInput.style.display = 'none';
            }
        } else {
            logger.error('请输入有效的方向角度 (0-359)');
        }
    }
}

function checkBrowserSupport() {
    return 'geolocation' in navigator && 
           'DeviceOrientationEvent' in window &&
           typeof fetch !== 'undefined';
}

async function requestPermissions() {
    try {
        // 请求地理位置权限
        if ('permissions' in navigator) {
            const geoPermission = await navigator.permissions.query({name: 'geolocation'});
            logger.info(`地理位置权限状态: ${geoPermission.state}`);
        }
        
        // 请求设备方向权限 (iOS 13+)
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            logger.info('检测到iOS设备，需要请求方向权限');
            try {
            const permission = await DeviceOrientationEvent.requestPermission();
                logger.info(`设备方向权限: ${permission}`);
            if (permission !== 'granted') {
                    logger.warning('需要设备方向权限才能使用指南针功能');
                showError('需要设备方向权限才能使用指南针功能');
                }
            } catch (error) {
                logger.error('设备方向权限请求失败: ' + error.message);
            }
        } else {
            logger.info('设备支持方向检测，无需额外权限');
        }
    } catch (error) {
        logger.error('权限请求失败: ' + error.message);
    }
}

function initializeCompass() {
    logger.info('初始化指南针...');
    
    // 监听设备方向变化
    if (window.DeviceOrientationEvent) {
        logger.info('设备支持方向检测，正在添加事件监听器...');
        
        // 添加deviceorientation事件监听
        window.addEventListener('deviceorientation', function(event) {
            if (event.alpha !== null || event.webkitCompassHeading !== undefined) {
                logger.success('方向事件触发成功');
                handleOrientation(event);
            } else {
                logger.warning('方向事件触发但没有数据');
            }
        }, true);
        
        // 添加deviceorientationabsolute事件监听（某些设备）
        window.addEventListener('deviceorientationabsolute', function(event) {
            if (event.absolute && event.alpha !== null) {
                logger.info('绝对方向事件触发');
                handleOrientation(event);
            }
        }, true);
        
        // 测试是否能获取方向
        setTimeout(() => {
            if (currentHeading === 0) {
                logger.warning('未检测到方向数据，可能需要移动设备或检查权限');
                // 提供手动输入方向的选项
                enableManualHeadingInput();
            }
        }, 1000);  // 缩短到1秒
    } else {
        logger.error('设备不支持方向检测');
        showError('设备不支持方向检测功能');
        enableManualHeadingInput();
    }
}

function handleOrientation(event) {
    // 获取指南针方向
    let heading = event.alpha;
    
    // iOS Safari 使用 webkitCompassHeading
    if (event.webkitCompassHeading) {
        heading = event.webkitCompassHeading;
    }
    
    if (heading !== null) {
        // 标准化角度 (0-360)
        heading = (360 - heading) % 360;
        currentHeading = heading;
        updateCompassDisplay(heading);
    }
}

function updateCompassDisplay(heading) {
    const compassNeedle = document.getElementById('compassNeedle');
    const compassDirection = document.getElementById('compassDirection');
    const directionText = document.getElementById('directionText');
    
    if (compassNeedle) {
        // 围绕中心旋转指南针
        compassNeedle.style.transform = `translate(-50%, -50%) rotate(${heading}deg)`;
    }
    
    if (compassDirection) {
        compassDirection.textContent = `${Math.round(heading)}°`;
    }
    
    if (directionText) {
        directionText.textContent = getDirectionText(heading);
    }
    
    logger.info(`方向更新: ${Math.round(heading)}° (${getDirectionText(heading)})`);
}

function getDirectionText(heading) {
    const directions = [
        { name: '北', min: 0, max: 22.5 },
        { name: '东北', min: 22.5, max: 67.5 },
        { name: '东', min: 67.5, max: 112.5 },
        { name: '东南', min: 112.5, max: 157.5 },
        { name: '南', min: 157.5, max: 202.5 },
        { name: '西南', min: 202.5, max: 247.5 },
        { name: '西', min: 247.5, max: 292.5 },
        { name: '西北', min: 292.5, max: 337.5 },
        { name: '北', min: 337.5, max: 360 }
    ];
    
    for (const dir of directions) {
        if (heading >= dir.min && heading < dir.max) {
            return dir.name;
        }
    }
    return '北';
}

function refreshLocation() {
    logger.info('开始获取位置信息...');
    
    const locationElement = document.getElementById('currentLocation');
    const coordinatesElement = document.getElementById('coordinates');
    const accuracyElement = document.getElementById('accuracy');
    
    locationElement.textContent = '获取中...';
    coordinatesElement.textContent = '获取中...';
    accuracyElement.textContent = '获取中...';
    
    // 检查浏览器支持
    if (!navigator.geolocation) {
        const errorMsg = '❌ 浏览器不支持地理位置功能';
        logger.error(errorMsg);
        showError(errorMsg);
        showManualLocationInput();
        return;
    }
    
    // 检查是否为安全上下文（HTTPS 或 localhost）
    const isSecureContext = window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost';
    if (!isSecureContext) {
        logger.warning('⚠️ 非安全上下文，地理位置功能可能受限');
        showError('⚠️ 建议使用 HTTPS 或 localhost 访问以获得最佳体验');
    }
    
    // 首先检查权限状态
    if ('permissions' in navigator) {
        navigator.permissions.query({name: 'geolocation'}).then(function(permissionStatus) {
            logger.info(`地理位置权限状态: ${permissionStatus.state}`);
            
            if (permissionStatus.state === 'denied') {
                logger.error('❌ 地理位置权限被拒绝');
                showLocationPermissionHelp();
                return;
            }
            
            // 继续获取位置
            doGetCurrentPosition();
        }).catch(() => {
            // 权限API不支持，直接尝试获取位置
            logger.info('权限API不支持，直接尝试获取位置');
            doGetCurrentPosition();
        });
    } else {
        logger.info('浏览器不支持权限查询API，直接尝试获取位置');
        doGetCurrentPosition();
    }
}

function doGetCurrentPosition() {
    const options = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000
    };
    
    logger.info(`位置获取选项: 高精度=${options.enableHighAccuracy}, 超时=${options.timeout}ms`);
    logger.info('📍 正在请求地理位置权限...');
    
    navigator.geolocation.getCurrentPosition(
        handleLocationSuccess,
        handleLocationError,
        options
    );
}

async function handleLocationSuccess(position) {
    currentPosition = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
        timestamp: position.timestamp
    };
    
    logger.success(`位置获取成功: ${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`);
    logger.info(`位置精度: ${Math.round(currentPosition.accuracy)}米`);
    
    // 更新坐标显示
    document.getElementById('coordinates').textContent = 
        `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
    
    // 更新精度显示
    document.getElementById('accuracy').textContent = `±${Math.round(currentPosition.accuracy)}m`;
    
    // 更新位置显示
    try {
        logger.info('正在获取地址信息...');
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        logger.warning(`地址获取失败: ${error.message}`);
        document.getElementById('currentLocation').textContent = 
            `${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)}`;
    }
    
    // 记录额外的位置信息
    if (currentPosition.altitude !== null) {
        logger.info(`海拔高度: ${Math.round(currentPosition.altitude)}米`);
    }
    if (currentPosition.speed !== null) {
        logger.info(`移动速度: ${Math.round(currentPosition.speed * 3.6)}km/h`);
    }
    
    // 启用探索按钮
    document.getElementById('exploreBtn').disabled = false;
    logger.success('位置信息更新完成，探索功能已启用');
}

function handleLocationError(error) {
    let errorMessage = '无法获取位置信息';
    let errorDetails = '';
    let showManualInput = false;
    
    switch(error.code) {
        case error.PERMISSION_DENIED:
            errorMessage = '❌ 地理位置权限被拒绝';
            errorDetails = '请重新授权或使用手动输入位置';
            showManualInput = true;
            logger.error('用户拒绝了地理位置权限请求');
            break;
        case error.POSITION_UNAVAILABLE:
            errorMessage = '❌ 位置信息不可用';
            errorDetails = '设备无法确定位置，请检查GPS或网络连接';
            showManualInput = true;
            break;
        case error.TIMEOUT:
            errorMessage = '⏰ 获取位置超时';
            errorDetails = '位置获取时间过长，请重试或手动输入';
            showManualInput = true;
            break;
        default:
            errorMessage = '❓ 未知的位置获取错误';
            errorDetails = `错误代码: ${error.code}`;
            showManualInput = true;
    }
    
    logger.error(`${errorMessage}: ${errorDetails}`);
    logger.error(`错误详情: ${error.message}`);
    
    // 更新UI显示
    document.getElementById('currentLocation').textContent = '获取失败';
    document.getElementById('coordinates').textContent = '无法获取';
    document.getElementById('accuracy').textContent = '无法获取';
    
    // 显示错误信息
    showError(`${errorMessage}\n${errorDetails}`);
    
    // 根据错误类型显示相应的帮助信息
    if (error.code === error.PERMISSION_DENIED) {
        showLocationPermissionHelp();
    }
    
    if (showManualInput) {
        setTimeout(() => {
            showManualLocationInput();
        }, 2000); // 2秒后显示手动输入选项
    }
}

async function getLocationName(lat, lng) {
    // 使用反向地理编码获取地点名称
    // 这里使用一个简单的实现，实际项目中可以使用更好的地理编码服务
    try {
        const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=zh`);
        const data = await response.json();
        
        if (data.city && data.countryName) {
            return `${data.city}, ${data.countryName}`;
        } else if (data.locality && data.countryName) {
            return `${data.locality}, ${data.countryName}`;
        } else {
            return data.countryName || '未知位置';
        }
    } catch (error) {
        console.error('获取地点名称失败:', error);
        throw error;
    }
}

async function startExploration() {
    logger.info('开始方向探索...');
    
    if (!currentPosition) {
        const errorMsg = '请先获取当前位置';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    if (currentHeading === null || currentHeading === undefined || currentHeading === 0) {
        const errorMsg = '未检测到方向信息，请移动设备或手动输入方向';
        logger.error(errorMsg);
        showError(errorMsg);
        // 尝试启用手动输入
        enableManualHeadingInput();
        return;
    }
    
    // 记录探索参数
    const exploreParams = {
        latitude: currentPosition.latitude,
        longitude: currentPosition.longitude,
        heading: currentHeading,
        segment_distance: settings.segmentDistance,
        time_mode: settings.timeMode,
        speed: settings.speed
    };
    
    logger.info(`探索参数: 位置(${exploreParams.latitude.toFixed(4)}, ${exploreParams.longitude.toFixed(4)})`);
    logger.info(`方向: ${exploreParams.heading}° (${getDirectionText(exploreParams.heading)})`);
    logger.info(`分段距离: ${exploreParams.segment_distance}km, 时间模式: ${exploreParams.time_mode}, 速度: ${exploreParams.speed}km/h`);
    
    // 显示加载状态
    showLoading(true);
    document.getElementById('exploreBtn').disabled = true;
    
    try {
        logger.info('正在向后端发送探索请求...');
        const startTime = Date.now();
        
                // 使用真实数据API端点
        const apiEndpoint = API_CONFIG.getApiUrl('/api/explore-real');  // 智能环境适配
        logger.info('使用真实数据源');
        
        // 调用后端API计算路径
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(exploreParams)
        });
        
        const requestTime = Date.now() - startTime;
        logger.info(`API请求耗时: ${requestTime}ms`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        logger.success(`探索完成! 找到 ${data.places.length} 个地点`);
        logger.info(`总距离: ${data.total_distance}km, 计算时间: ${(data.calculation_time * 1000).toFixed(1)}ms`);
        
        // 保存场景数据并进入选择模式
        sceneManagement.allScenes = data.places;
        sceneManagement.selectedScenes = [];
        sceneManagement.rejectedScenes = [];
        
        displayPlaces(data.places);
        
        // 🎒 自动创建旅程（如果还没有活跃旅程）
        if (!journeyManagement.isJourneyActive && currentPosition) {
            try {
                const locationName = `位置 ${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)}`;
                await startJourney(
                    currentPosition.latitude, 
                    currentPosition.longitude, 
                    locationName,
                    `探索之旅 ${new Date().toLocaleString()}`
                );
                
                // 显示结束旅程按钮
                showEndJourneyButton();
            } catch (error) {
                logger.warning('自动创建旅程失败，将继续不记录旅程');
            }
        }
        
        // 自动进入选择模式
        enableSelectionMode();
        
        // 🆕 强制显示结束旅程按钮（无论旅程是否成功创建）
        showEndJourneyButton();
        
    } catch (error) {
        logger.error(`探索请求失败: ${error.message}`);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('无法连接到服务器，请确保后端服务正在运行');
        } else {
            showError(`探索请求失败: ${error.message}`);
        }
    } finally {
        showLoading(false);
        document.getElementById('exploreBtn').disabled = false;
        logger.info('探索操作结束');
    }
}

function displayPlaces(places) {
    const container = document.getElementById('placesContainer');
    
    if (!container) {
        logger.error('❌ 找不到地点容器元素 (placesContainer)');
        showError('页面结构错误：缺少地点显示容器');
        return;
    }
    
    // 🔧 关键修复：确保容器可见
    container.style.display = 'block';
    container.innerHTML = '';
    
    if (!places || places.length === 0) {
        container.innerHTML = '<div class="error-message">没有找到相关地点信息</div>';
        return;
    }
    
    places.forEach((place, index) => {
        const placeCard = createPlaceCard(place, index);
        if (placeCard && container) {
            container.appendChild(placeCard);
        } else {
            logger.error(`❌ 无法添加地点卡片 ${index}: container=${!!container}, placeCard=${!!placeCard}`);
        }
    });
}

function createPlaceCard(place, index) {
    const card = document.createElement('div');
    
    // 检查场景的选择状态
    const isSelected = sceneManagement.selectedScenes.some(s => s.index === index);
    const isRejected = sceneManagement.rejectedScenes.some(s => s.index === index);
    
    card.className = `place-card ${isSelected ? 'selected' : ''} ${isRejected ? 'rejected' : ''}`;
    card.dataset.placeIndex = index;
    
    const modeText = {
        'present': '现代',
        'past': '历史',
        'future': '未来'
    }[settings.timeMode] || '现代';
    
    // 格式化价格显示
    const formatPrice = (price) => {
        if (!price) return '暂无信息';
        if (price.includes('免费')) {
            return `<span class="free-price">${price}</span>`;
        }
        return `<span class="price-highlight">${price}</span>`;
    };
    
    card.innerHTML = `
        ${sceneManagement.isSelectionMode ? `
        <div class="scene-selector">
            <input type="radio" name="scene-selection" class="scene-radio" id="scene-${index}" 
                   ${isSelected ? 'checked' : ''} ${isRejected ? 'disabled' : ''}
                   onchange="toggleSceneSelection(${index})">
            <label for="scene-${index}" class="scene-radio-label" title="选择这个目的地">
                <span class="radio-indicator ${isSelected ? 'selected' : ''}">
                    ${isSelected ? '🎯' : '⭕'}
                </span>
            </label>
            <button class="reject-btn ${isRejected ? 'active' : ''}" 
                    onclick="toggleSceneRejection(${index})"
                    title="${isRejected ? '恢复场景' : '划掉场景'}">
                <span class="icon">${isRejected ? '↻' : '✕'}</span>
            </button>
        </div>
        ` : ''}
        <img src="${place.image || 'https://via.placeholder.com/400x200?text=暂无图片'}" 
             alt="${place.name}" 
             class="place-image"
             onerror="this.src='https://via.placeholder.com/400x200?text=暂无图片'">
        <div class="place-content">
            <div class="place-header">
                <h3 class="place-name">${place.name}</h3>
                <span class="place-distance">${place.distance}km</span>
            </div>
            
            ${place.category ? `<div class="place-category">🏷️ ${place.category}</div>` : ''}
            
            <div class="place-location-info">
                📍 ${place.latitude.toFixed(4)}°, ${place.longitude.toFixed(4)}°
                ${place.country ? `| ${place.country}` : ''}
                ${place.city ? ` - ${place.city}` : ''}
            </div>
            
            <p class="place-description">${place.description}</p>
            
            <div class="place-details">
                <div class="detail-item">
                    <div class="detail-label">🕒 开放时间</div>
                    <div class="detail-value">${place.opening_hours || '暂无信息'}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">💰 门票价格</div>
                    <div class="detail-value">${formatPrice(place.ticket_price)}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">🎫 购票方式</div>
                    <div class="detail-value">${place.booking_method || '暂无信息'}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">📍 精确坐标</div>
                    <div class="detail-value">${place.latitude.toFixed(6)}, ${place.longitude.toFixed(6)}</div>
                </div>
            </div>
            
            <span class="place-mode">${modeText}模式</span>
        </div>
    `;
    
    return card;
}

function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('show');
}

function updateSettings() {
    settings.segmentDistance = parseInt(document.getElementById('segmentDistance').value);
    settings.timeMode = document.getElementById('timeMode').value;
    settings.speed = parseInt(document.getElementById('speed').value);
    
    logger.info(`设置已更新: ${settings.segmentDistance}km, ${settings.timeMode}模式, ${settings.speed}km/h`);
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'block' : 'none';
}

function showError(message) {
    // 移除现有的错误消息
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 创建新的错误消息
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // 插入到状态区域后面
    const statusSection = document.querySelector('.status-section');
    statusSection.insertAdjacentElement('afterend', errorDiv);
    
    // 5秒后自动移除
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

function showSuccess(message) {
    // 移除现有的成功消息
    const existingSuccess = document.querySelector('.success-message');
    if (existingSuccess) {
        existingSuccess.remove();
    }
    
    // 创建新的成功消息
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    
    // 插入到状态区域后面
    const statusSection = document.querySelector('.status-section');
    statusSection.insertAdjacentElement('afterend', successDiv);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 3000);
}

// 清空日志函数
function clearLogs() {
    logger.clear();
    logger.info('日志已清空');
}

// 调试功能：模拟方向（用于桌面测试）
function simulateHeading(degrees) {
    currentHeading = degrees;
    updateCompassDisplay(degrees);
    logger.info(`模拟方向设置为: ${degrees}° (${getDirectionText(degrees)})`);
}

// 调试信息函数
function debugInfo() {
    logger.info('=== 调试信息 ===');
    logger.info(`当前位置: ${currentPosition ? `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}` : '未获取'}`);
    logger.info(`位置精度: ${currentPosition ? `±${Math.round(currentPosition.accuracy)}m` : '未知'}`);
    logger.info(`当前方向: ${currentHeading !== null ? `${Math.round(currentHeading)}° (${getDirectionText(currentHeading)})` : '未检测'}`);
    logger.info(`设置: 分段${settings.segmentDistance}km, ${settings.timeMode}模式, ${settings.speed}km/h`);
    logger.info(`浏览器: ${navigator.userAgent}`);
    logger.info(`屏幕: ${screen.width}x${screen.height}`);
    logger.info('===============');
}

// 获取系统状态
function getSystemStatus() {
    const status = {
        hasPosition: !!currentPosition,
        hasHeading: currentHeading !== null && currentHeading !== undefined,
        geolocationSupported: 'geolocation' in navigator,
        orientationSupported: 'DeviceOrientationEvent' in window,
        isSecureContext: window.isSecureContext,
        userAgent: navigator.userAgent
    };
    
    logger.info('系统状态检查:');
    Object.entries(status).forEach(([key, value]) => {
        const type = value ? 'success' : 'warning';
        logger.log(`${key}: ${value}`, type);
    });
    
    return status;
}

// 场景选择管理函数 - 单选模式（背包客模式）
function toggleSceneSelection(index) {
    const place = sceneManagement.allScenes[index];
    if (!place) return;
    
    // 检查是否已被划掉
    if (sceneManagement.rejectedScenes.some(s => s.index === index)) {
        logger.warning(`场景 ${place.name} 已被划掉，无法选择`);
        return;
    }
    
    const currentSelected = sceneManagement.selectedScenes.find(s => s.index === index);
    
    if (currentSelected) {
        // 如果点击的是已选中的场景，取消选择
        sceneManagement.selectedScenes = [];
        logger.info(`取消选择场景: ${place.name}`);
        
        // 隐藏到达确认界面
        const confirmationDiv = document.getElementById('arrivalConfirmation');
        if (confirmationDiv) {
            confirmationDiv.remove();
        }
        // 显示所有场景
        showAllScenes();
    } else {
        // 单选模式：清空之前的选择，选择当前场景
        const previousSelection = sceneManagement.selectedScenes[0];
        if (previousSelection) {
            logger.info(`取消之前的选择: ${previousSelection.place.name}`);
            updateSceneCard(previousSelection.index);
        }
        
        sceneManagement.selectedScenes = [{ index, place }];
        logger.success(`🎯 选择目的地: ${place.name}`);
        
        // 🎯 新功能：直接进入到达确认流程
        logger.info('🚶‍♂️ 准备前往目的地...');
        
        // 🎯 关键修复：立即更新当前位置为选择的场景位置
        if (place.latitude && place.longitude) {
            currentPosition = {
                latitude: parseFloat(place.latitude),
                longitude: parseFloat(place.longitude)
            };
            
            // 更新UI显示的当前位置（异步处理）
            updateLocationDisplayAsync(place);
            
            // 🆕 添加到历史场景显示
            addToHistoryScenes(place);
        }
        
        // 隐藏其他场景，专注当前目标
        hideOtherScenes(index);
        
        // 直接显示"到达确认"界面
        showArrivalConfirmation({ index, place });
    }
    
    // 更新所有场景卡片的显示状态
    sceneManagement.allScenes.forEach((_, i) => {
        updateSceneCard(i);
    });
}

function toggleSceneRejection(index) {
    const place = sceneManagement.allScenes[index];
    if (!place) return;
    
    const rejectedIndex = sceneManagement.rejectedScenes.findIndex(s => s.index === index);
    
    if (rejectedIndex > -1) {
        // 取消划掉
        sceneManagement.rejectedScenes.splice(rejectedIndex, 1);
        logger.info(`恢复场景: ${place.name}`);
    } else {
        // 划掉场景
        sceneManagement.rejectedScenes.push({ index, place });
        // 同时从选中列表中移除
        const selectedIndex = sceneManagement.selectedScenes.findIndex(s => s.index === index);
        if (selectedIndex > -1) {
            sceneManagement.selectedScenes.splice(selectedIndex, 1);
        }
        logger.info(`划掉场景: ${place.name}`);
    }
    
    updateSceneCard(index);
}

function updateSceneCard(index) {
    const card = document.querySelector(`[data-place-index="${index}"]`);
    if (!card) return;
    
    const isSelected = sceneManagement.selectedScenes.some(s => s.index === index);
    const isRejected = sceneManagement.rejectedScenes.some(s => s.index === index);
    
    card.classList.toggle('selected', isSelected);
    card.classList.toggle('rejected', isRejected);
    
    const checkbox = card.querySelector('.scene-checkbox');
    if (checkbox) {
        checkbox.checked = isSelected;
        checkbox.disabled = isRejected;
    }
    
    const rejectBtn = card.querySelector('.reject-btn');
    if (rejectBtn) {
        rejectBtn.classList.toggle('active', isRejected);
        rejectBtn.querySelector('.icon').textContent = isRejected ? '↻' : '✕';
        rejectBtn.title = isRejected ? '恢复场景' : '划掉场景';
    }
}



function enableSelectionMode() {
    sceneManagement.isSelectionMode = true;
    document.body.classList.add('selection-mode');
    
    // 重新渲染所有卡片
    const places = sceneManagement.allScenes;
    displayPlaces(places);
    
    logger.info('进入场景选择模式');
}

function disableSelectionMode() {
    sceneManagement.isSelectionMode = false;
    document.body.classList.remove('selection-mode');
    
    // 重新渲染所有卡片
    const places = sceneManagement.allScenes;
    displayPlaces(places);
    
    logger.info('退出场景选择模式');
}







// 隐藏其他场景，只显示选中的场景
function hideOtherScenes(selectedIndex) {
    const allCards = document.querySelectorAll('.place-card');
    allCards.forEach((card, index) => {
        if (index !== selectedIndex) {
            card.style.display = 'none';
            card.classList.add('hidden-scene');
        } else {
            card.classList.add('focused-scene');
            const selector = card.querySelector('.scene-selector');
            if (selector) {
                selector.style.display = 'none'; // 隐藏选择器
            }
        }
    });
    
    // 隐藏选择控制面板
    const selectionPanel = document.querySelector('.selection-panel');
    if (selectionPanel) {
        selectionPanel.style.display = 'none';
    }
}

// 显示所有场景
function showAllScenes() {
    const allCards = document.querySelectorAll('.place-card');
    allCards.forEach((card) => {
        card.style.display = 'block';
        card.classList.remove('hidden-scene', 'focused-scene');
        const selector = card.querySelector('.scene-selector');
        if (selector && sceneManagement.isSelectionMode) {
            selector.style.display = 'block'; // 显示选择器
        }
    });
    
    // 显示选择控制面板
    const selectionPanel = document.querySelector('.selection-panel');
    if (selectionPanel && sceneManagement.isSelectionMode) {
        selectionPanel.style.display = 'block';
    }
}

// 显示到达确认界面
function showArrivalConfirmation(selectedScene) {
    // 🆕 设置当前正在确认到达的场景，用于处理"返回"按钮
    sceneManagement.currentlyVisitingScene = selectedScene.place;

    // 尝试多个可能的容器
    let resultsContainer = document.getElementById('results') ||
                          document.getElementById('placesContainer') ||
                          document.querySelector('.places-container');

    if (!resultsContainer) {
        logger.error('❌ 找不到结果容器，无法显示到达确认界面');
        return;
    }

    // 移除可能存在的旧确认界面
    const existingConfirmation = document.getElementById('arrivalConfirmation');
    if (existingConfirmation) {
        existingConfirmation.remove();
    }

    logger.info(`🎯 显示到达确认界面: ${selectedScene.place.name}`);
    
    // 在选中的场景卡片下方添加到达确认区域
    const confirmationHtml = `
        <div class="arrival-confirmation" id="arrivalConfirmation" style="
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            border: 2px solid #667eea;
        ">
            <div class="arrival-actions">
                <h3 style="color: #667eea; margin-bottom: 15px;">🎯 当前目标：${selectedScene.place.name}</h3>
                <p style="color: #4a5568; margin-bottom: 20px;">你正在前往这个目的地...</p>
                <div class="arrival-buttons" style="display: flex; gap: 15px; justify-content: center;">
                    <button class="btn btn-primary arrival-btn" onclick="confirmArrival(${selectedScene.index})" style="
                        padding: 15px 30px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                        transition: all 0.3s ease;
                    ">
                        📍 我已到达
                    </button>
                    <button class="btn btn-secondary back-btn" onclick="backToSelection()" style="
                        padding: 15px 30px;
                        background: rgba(255, 255, 255, 0.9);
                        color: #4a5568;
                        border: 2px solid #e2e8f0;
                        border-radius: 12px;
                        font-size: 16px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    ">
                        ↶ 重新选择
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultsContainer.insertAdjacentHTML('beforeend', confirmationHtml);
    
    // 滚动到确认界面
    setTimeout(() => {
        const confirmationDiv = document.getElementById('arrivalConfirmation');
        if (confirmationDiv) {
            confirmationDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

// 确认到达目的地
async function confirmArrival(index) {
    const arrivedScene = sceneManagement.allScenes[index];
    if (!arrivedScene) return;

    logger.success(`🏁 已到达: ${arrivedScene.name}`);

    // 🆕 清空当前访问的场景标记，因为已经正式到达
    sceneManagement.currentlyVisitingScene = null;
    
    // 🎯 关键功能：更新用户当前位置为到达的场景位置
    if (arrivedScene.latitude && arrivedScene.longitude) {
        currentPosition = {
            latitude: parseFloat(arrivedScene.latitude),
            longitude: parseFloat(arrivedScene.longitude)
        };
        
        // 更新UI显示的当前位置
        try {
            const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
            document.getElementById('currentLocation').textContent = locationName;
            document.getElementById('coordinates').textContent = 
                `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
            logger.success(`📍 当前位置已更新为: ${arrivedScene.name}`);
        } catch (error) {
            document.getElementById('currentLocation').textContent = arrivedScene.name;
            document.getElementById('coordinates').textContent = 
                `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
            logger.success(`📍 当前位置已更新为: ${arrivedScene.name}`);
        }
    }
    
    // 🎒 记录用户访问的场景到旅程中
    if (journeyManagement.isJourneyActive && journeyManagement.currentJourneyId) {
        try {
            await recordSceneVisit(
                journeyManagement.currentJourneyId,
                arrivedScene,
                null, // 暂时不收集用户评分
                `通过OrientDiscover探索发现的场景` // 自动备注
            );
            logger.info('✅ 场景访问记录已保存到旅程中');
            
            // 🆕 添加到历史场景显示
            addToHistoryScenes(arrivedScene);
            
        } catch (error) {
            logger.warning('记录场景访问失败，但不影响继续使用');
            // 即使API失败，也添加到本地历史记录
            addToHistoryScenes(arrivedScene);
        }
    } else {
        logger.warning('当前没有活跃旅程，场景访问未被记录');
        // 没有活跃旅程时也保存历史记录
        addToHistoryScenes(arrivedScene);
    }
    
    // 🤖 生成AI场景锐评
    await generateAndShowSceneReview(arrivedScene);
    
    showSuccess(`🎉 欢迎来到 ${arrivedScene.name}！`);
    
    // 显示继续探索的选项
    showContinueExplorationOptions(arrivedScene);

    // 🆕 显示Google街景（如果可用）
    showStreetViewForLocation(arrivedScene);
}

// 显示继续探索的选项
function showContinueExplorationOptions(currentScene) {
    const confirmationDiv = document.getElementById('arrivalConfirmation');
    if (confirmationDiv) {
        confirmationDiv.innerHTML = `
            <div class="continue-exploration">
                <h3>🎉 已到达：${currentScene.name}</h3>
                <p>你现在在这里，想要继续探索吗？</p>
                <div class="continue-buttons">
                    <button class="btn btn-primary continue-btn" onclick="continueExploration(${currentScene.latitude}, ${currentScene.longitude})">
                        🗺️ 从这里继续探索
                    </button>
                    <button class="btn btn-secondary end-btn" onclick="endJourney()">
                        🏠 结束今天的旅程
                    </button>
                </div>
            </div>
        `;
    }
}

// 从当前位置继续探索
async function continueExploration(lat, lng) {
    logger.info('🧭 准备从新位置继续探索...');
    
    // 🎯 关键修复：更新当前位置（使用正确的属性名）
    currentPosition = {
        latitude: parseFloat(lat),
        longitude: parseFloat(lng),
        accuracy: 100, // 设置默认精度
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now()
    };
    
    logger.success(`📍 位置已更新为: ${lat}, ${lng}`);
    
    // 🎯 立即更新UI显示
    document.getElementById('coordinates').textContent = 
        `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
    document.getElementById('accuracy').textContent = '±100m (继续探索)';
    
    // 获取并更新地址显示
    try {
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        document.getElementById('currentLocation').textContent = `新位置 ${lat}, ${lng}`;
        logger.warning('地址获取失败，使用坐标显示');
    }
    
    // 只清除待选择的目的地，保留已访问场景
    clearPendingDestinations();
    
    showSuccess('📍 位置已更新！请设置新的探索方向并点击"开始探索"');
    
    // 回到探索界面 - 使用正确的选择器和防御性检查
    const controlsElement = document.querySelector('.controls');
    if (controlsElement) {
        controlsElement.style.display = 'block';
    } else {
        logger.warning('⚠️ 未找到controls元素，可能已被清除');
    }
}

// 结束旅程
async function endJourney() {
    logger.info('🏠 准备结束旅程...');
    
    // 🎒 调用后端API结束旅程并显示总结
    if (journeyManagement.isJourneyActive && journeyManagement.currentJourneyId) {
        try {
            const result = await endCurrentJourney(journeyManagement.currentJourneyId);
            
            // 显示旅程摘要 - 不要在显示后立即清除！
            await showModernJourneySummary(result);
            
            logger.success('🏠 旅程结束，感谢使用背包客探索工具！');
            showSuccess('✨ 期待您的下次探索！');
            
        } catch (error) {
            logger.warning('结束旅程API调用失败:', error);
            // API失败时也显示本地总结
            await showLocalJourneySummary();
        }
    } else {
        // 没有活跃旅程时也显示本地总结
        logger.info('💡 没有活跃的旅程，显示本地总结');
        await showLocalJourneySummary();
    }
    
    // 隐藏结束旅程按钮
    hideEndJourneyButton();
    
    // ⚠️ 注意：不要在这里清除结果，让用户查看总结后再手动重置
    // 用户可以通过"开始新旅程"按钮来重置状态
}

// 只清除待选择的目的地（用于继续探索）
function clearPendingDestinations() {
    logger.info('🧹 清除待选择的目的地...');
    
    // 只清除地点容器（待选择的目的地）
    const placesContainer = document.getElementById('placesContainer');
    if (placesContainer) {
        placesContainer.innerHTML = '';
        placesContainer.style.display = 'none';
    }
    
    // 重置选择相关状态，但保留已访问场景
    sceneManagement.allScenes = [];
    sceneManagement.selectedScenes = [];
    sceneManagement.rejectedScenes = [];
    sceneManagement.isSelectionMode = false;
    
    logger.success('✅ 待选择目的地已清除，已访问场景已保留');
}

// 清除页面显示结果（完全重置，用于新旅程）
function clearResults() {
    logger.info('🧹 清除页面显示结果...');
    
    // 清除地点容器
    const placesContainer = document.getElementById('placesContainer');
    if (placesContainer) {
        placesContainer.innerHTML = '';
        placesContainer.style.display = 'none';
    }
    
    // 清除旅程总结容器
    const summaryContainer = document.getElementById('journeySummaryContainer');
    if (summaryContainer) {
        summaryContainer.innerHTML = '';
        summaryContainer.style.display = 'none';
    }
    
    // 清除历史访问场景
    const historyContainer = document.getElementById('historyPlacesContainer');
    if (historyContainer) {
        historyContainer.innerHTML = '';
    }
    
    // 隐藏历史访问区域
    const historySection = document.getElementById('journeyHistorySection');
    if (historySection) {
        historySection.style.display = 'none';
    }
    
    // 清除加载状态
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
    
    // 清除历史模式面板显示
    const historicalPanel = document.getElementById('historicalSelfiePanel');
    if (historicalPanel) {
        historicalPanel.style.display = 'none';
    }
    
    logger.success('✅ 页面结果已清除');
}

// 显示本地旅程总结（备用方案）
async function showLocalJourneySummary() {
    logger.info('📊 显示本地旅程总结...');
    
    // 计算本地统计数据
    const stats = calculateJourneyStats();
    
    const summaryHtml = `
        <div class="journey-summary-card" style="
            margin: 20px 0;
            padding: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
            animation: slideUp 0.5s ease-out;
        ">
            <h2 style="margin: 0 0 20px 0; font-size: 1.8rem;">🎉 旅程完成！</h2>
            <div style="display: flex; justify-content: center; gap: 40px; margin: 20px 0; flex-wrap: wrap;">
                <div>
                    <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700;">${stats.scenesCount}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">访问场景</div>
                </div>
                <div>
                    <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700;">${stats.totalDistance.toFixed(1)}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">总距离(km)</div>
                </div>
                <div>
                    <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700;">${Math.round(stats.totalTimeMinutes)}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">探索时间(分钟)</div>
                </div>
            </div>
            <p style="font-size: 1.1rem; opacity: 0.95; margin: 20px 0; line-height: 1.5;">
                🎊 恭喜完成这次精彩的探索之旅！每一步都是独特的发现，感谢您选择方向探索派对！
            </p>
            <div style="margin-top: 20px;">
                <button onclick="startNewJourney()" style="
                    background: rgba(255,255,255,0.2);
                    border: 2px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-size: 1rem;
                    cursor: pointer;
                    margin: 5px;
                    transition: all 0.3s ease;
                " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                    🚀 开始新旅程
                </button>
                <button onclick="shareJourney()" style="
                    background: rgba(255,255,255,0.2);
                    border: 2px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-size: 1rem;
                    cursor: pointer;
                    margin: 5px;
                    transition: all 0.3s ease;
                " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                    🔗 分享旅程
                </button>
            </div>
        </div>
    `;
    
    // 显示总结卡片
    const container = document.getElementById('journeySummaryContainer');
    if (container) {
        container.innerHTML = summaryHtml;
        container.style.display = 'block';
        
        // 滚动到总结区域
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        logger.success('✅ 旅程总结卡片显示成功');
    } else {
        logger.error('❌ 找不到journeySummaryContainer');
    }
}

// ❌ 已删除简单版本的现代旅程总结函数，使用增强版本

// 返回场景选择
function backToSelection() {
    // 🆕 如果有当前正在访问的场景，从历史记录中移除它
    if (sceneManagement.currentlyVisitingScene) {
        // 从历史场景列表中移除当前场景
        const sceneIndex = journeyManagement.historyScenes.findIndex(
            scene => scene.name === sceneManagement.currentlyVisitingScene.name
        );

        if (sceneIndex !== -1) {
            const removedScene = journeyManagement.historyScenes.splice(sceneIndex, 1)[0];
            logger.info(`🗑️ 已从历史记录中移除场景: ${removedScene.name}`);

            // 重新编号访问顺序
            journeyManagement.historyScenes.forEach((scene, index) => {
                scene.visitOrder = index + 1;
            });

            // 重新显示历史场景
            displayHistoryScenes();
        }

        // 清空当前访问的场景
        sceneManagement.currentlyVisitingScene = null;
    }

    // 恢复所有场景的显示
    const allCards = document.querySelectorAll('.place-card');
    allCards.forEach(card => {
        card.style.display = 'block';
        card.classList.remove('hidden-scene', 'focused-scene');

        // 恢复选择器
        const selector = card.querySelector('.scene-selector');
        if (selector) {
            selector.style.display = 'block';
        }
    });

    // 移除到达确认区域
    const confirmationDiv = document.getElementById('arrivalConfirmation');
    if (confirmationDiv) {
        confirmationDiv.remove();
    }

    // 恢复选择控制面板
    const selectionPanel = document.querySelector('.selection-panel');
    if (selectionPanel) {
        selectionPanel.style.display = 'block';
    }

    // 清空当前选择，让用户重新选择
    sceneManagement.selectedScenes = [];

    // 更新所有卡片状态
    sceneManagement.allScenes.forEach((_, i) => {
        updateSceneCard(i);
    });

    logger.info('↶ 已返回场景选择，已清除历史记录');
}

// 重置到初始状态
function resetToInitialState() {
    // 重置场景管理状态
    sceneManagement.allScenes = [];
    sceneManagement.selectedScenes = [];
    sceneManagement.rejectedScenes = [];
    sceneManagement.isSelectionMode = false;
    sceneManagement.currentlyVisitingScene = null; // 🆕 重置当前访问场景标记
    
    // 🎒 重置旅程管理状态
    journeyManagement.currentJourneyId = null;
    journeyManagement.isJourneyActive = false;
    journeyManagement.startLocation = null;
    journeyManagement.visitedScenes = [];
    journeyManagement.totalDistance = 0;
    
    // 清除历史场景显示
    journeyManagement.historyScenes = [];
    const historySection = document.getElementById('journeyHistorySection');
    if (historySection) {
        historySection.style.display = 'none';
    }
    
    // 清除结果显示
    clearResults();
    
    // 显示控制面板 - 使用正确的选择器
    const controls = document.querySelector('.controls');
    if (controls) {
        controls.style.display = 'block';
    }
    
    logger.info('🔄 已重置到初始状态');
}



// ========== 旅程管理功能 ==========

/**
 * 开始新的旅程
 * @param {number} lat - 起始纬度
 * @param {number} lng - 起始经度
 * @param {string} locationName - 起始位置名称
 * @param {string} journeyTitle - 旅程标题（可选）
 */
async function startJourney(lat, lng, locationName, journeyTitle = null) {
    try {
        logger.info('🎒 开始创建新旅程...');
        
        const response = await fetch(API_CONFIG.getApiUrl('/api/journey/start'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_lat: lat,
                start_lng: lng,
                start_name: locationName,
                journey_title: journeyTitle || `探索之旅 ${new Date().toLocaleString()}`
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 更新旅程状态
            journeyManagement.currentJourneyId = data.journey_id;
            journeyManagement.isJourneyActive = true;
            journeyManagement.startLocation = {
                lat: lat,
                lng: lng,
                name: locationName
            };
            journeyManagement.visitedScenes = [];
            
            logger.success(data.message);
            logger.info(`旅程ID: ${data.journey_id}`);
            
            return data.journey_id;
        } else {
            throw new Error('创建旅程失败');
        }
        
    } catch (error) {
        logger.error(`创建旅程失败: ${error.message}`);
        showError('创建旅程失败，请重试');
        throw error;
    }
}

/**
 * 记录访问场景
 * @param {string} journeyId - 旅程ID
 * @param {object} scene - 场景对象
 * @param {number} rating - 用户评分（可选）
 * @param {string} notes - 用户备注（可选）
 */
async function recordSceneVisit(journeyId, scene, rating = null, notes = null) {
    try {
        logger.info(`📍 记录场景访问: ${scene.name}`);
        
        const response = await fetch(API_CONFIG.getApiUrl('/api/journey/visit'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                journey_id: journeyId,
                scene_name: scene.name,
                scene_lat: scene.latitude,
                scene_lng: scene.longitude,
                scene_address: scene.address || scene.description,
                user_rating: rating,
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 更新本地状态
            journeyManagement.visitedScenes.push({
                name: scene.name,
                location: { lat: scene.latitude, lng: scene.longitude },
                visitTime: new Date().toISOString()
            });
            
            logger.success(data.message);
            logger.info(`已访问场景数: ${data.visited_scenes_count}`);
            
            return data;
        } else {
            throw new Error('记录访问失败');
        }
        
    } catch (error) {
        logger.error(`记录场景访问失败: ${error.message}`);
        showError('记录访问失败，请重试');
        throw error;
    }
}

/**
 * 结束当前旅程
 * @param {string} journeyId - 旅程ID
 */
async function endCurrentJourney(journeyId) {
    try {
        logger.info('🏠 结束当前旅程...');
        
        const response = await fetch(API_CONFIG.getApiUrl(`/api/journey/${journeyId}/end`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 重置旅程状态
            journeyManagement.currentJourneyId = null;
            journeyManagement.isJourneyActive = false;
            journeyManagement.visitedScenes = [];
            
            logger.success(data.message);
            logger.info(`总访问场景: ${data.visited_scenes_count}`);
            
            return data;
        } else {
            throw new Error('结束旅程失败');
        }
        
    } catch (error) {
        logger.error(`结束旅程失败: ${error.message}`);
        showError('结束旅程失败，请重试');
        throw error;
    }
}

/**
 * 获取当前旅程信息
 * @param {string} journeyId - 旅程ID
 */
async function getCurrentJourneyInfo(journeyId) {
    try {
        const response = await fetch(API_CONFIG.getApiUrl(`/api/journey/${journeyId}`));
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.journey;
        } else {
            throw new Error('获取旅程信息失败');
        }
        
    } catch (error) {
        logger.error(`获取旅程信息失败: ${error.message}`);
        return null;
    }
}

// 在控制台中暴露调试函数
window.simulateHeading = simulateHeading;
window.debugInfo = debugInfo;
window.clearLogs = clearLogs;
window.getSystemStatus = getSystemStatus;
window.logger = logger;
// 显示结束旅程按钮
function showEndJourneyButton() {
    const endJourneyBtn = document.getElementById('endJourneyBtn');
    if (endJourneyBtn) {
        endJourneyBtn.style.display = 'block';
        logger.info('🏠 结束旅程按钮已显示');
        
        // 如果旅程没有激活，也要显示按钮（用户可能想手动管理旅程）
        if (!journeyManagement.isJourneyActive) {
            logger.warning('⚠️ 旅程未激活但显示结束按钮，建议检查旅程创建逻辑');
        }
    }
}

// 隐藏结束旅程按钮
function hideEndJourneyButton() {
    const endJourneyBtn = document.getElementById('endJourneyBtn');
    if (endJourneyBtn) {
        endJourneyBtn.style.display = 'none';
    }
}

// 添加场景到历史记录
function addToHistoryScenes(scene, reviewData = null) {
    // 避免重复添加
    const exists = journeyManagement.historyScenes.find(h => h.name === scene.name);
    if (!exists) {
        const historyScene = {
            ...scene,
            visitTime: new Date().toLocaleString(),
            visitOrder: journeyManagement.historyScenes.length + 1,
            reviewData: reviewData // 保存锐评数据
        };
        journeyManagement.historyScenes.push(historyScene);
        displayHistoryScenes();
        logger.info(`📚 场景 "${scene.name}" 已添加到历史记录`);
    } else if (reviewData && !exists.reviewData) {
        // 如果场景已存在但没有锐评数据，则添加锐评数据
        exists.reviewData = reviewData;
        displayHistoryScenes();
        logger.info(`📝 为场景 "${scene.name}" 添加了锐评数据`);
    }
}

// 显示历史访问场景
function displayHistoryScenes() {
    const historySection = document.getElementById('journeyHistorySection');
    const historyContainer = document.getElementById('historyPlacesContainer');
    
    if (!historySection || !historyContainer) return;
    
    if (journeyManagement.historyScenes.length === 0) {
        historySection.style.display = 'none';
        return;
    }
    
    historySection.style.display = 'block';
    historyContainer.innerHTML = '';
    
    journeyManagement.historyScenes.forEach((scene, index) => {
        const historyCard = document.createElement('div');
        historyCard.className = `history-place-card ${scene.reviewData ? 'has-review' : 'no-review'}`;
        historyCard.style.cursor = scene.reviewData ? 'pointer' : 'default';
        
        historyCard.innerHTML = `
            <img src="${scene.image || 'https://via.placeholder.com/400x200?text=暂无图片'}" 
                 alt="${scene.name}" 
                 class="place-image"
                 onerror="this.src='https://via.placeholder.com/400x200?text=暂无图片'">
            <div class="place-content">
                <div class="place-header">
                    <h3 class="place-name">${scene.name}</h3>
                    <span class="visit-order">#${scene.visitOrder}</span>
                </div>
                <p class="place-description">${scene.description}</p>
                <div class="place-meta">
                    <span class="visit-time">🕒 ${scene.visitTime}</span>
                    <span class="place-coordinates">📍 ${scene.latitude.toFixed(4)}, ${scene.longitude.toFixed(4)}</span>
                </div>
                ${scene.reviewData ? `
                    <div class="review-indicator" style="
                        position: absolute;
                        top: 10px;
                        left: 10px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 0.8rem;
                        font-weight: 600;
                        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                        z-index: 5;
                    ">
                        🤖 有锐评
                    </div>
                ` : ''}
            </div>
        `;
        
        // 添加点击事件
        if (scene.reviewData) {
            historyCard.addEventListener('click', () => {
                showSceneReviewModal(scene.reviewData, scene);
            });
            historyCard.title = '点击查看AI锐评';
        }
        
        if (historyContainer && historyCard) {
            historyContainer.appendChild(historyCard);
        } else {
            logger.error(`❌ 无法添加历史卡片: historyContainer=${!!historyContainer}, historyCard=${!!historyCard}`);
        }
    });
}

// 显示场景锐评弹窗（独立弹窗，可重复查看）
function showSceneReviewModal(reviewData, scene) {
    // 移除已存在的弹窗
    const existingModal = document.getElementById('reviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modalHtml = `
        <div class="review-modal" id="reviewModal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        ">
            <div class="review-modal-content" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 20px;
                max-width: 90%;
                max-height: 90%;
                overflow-y: auto;
                box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
                position: relative;
                animation: slideUp 0.3s ease;
            ">
                <button class="close-modal-btn" onclick="closeReviewModal()" style="
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    font-size: 24px;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                ">✕</button>
                
                <div class="review-header" style="text-align: center; margin-bottom: 25px;">
                    <h2 style="margin: 0 0 10px 0; font-size: 1.8rem;">🤖 ${reviewData.title}</h2>
                    <div style="opacity: 0.9; font-size: 1rem;">AI智能锐评 - ${scene.name}</div>
                    <div style="opacity: 0.8; font-size: 0.9rem; margin-top: 5px;">访问时间: ${scene.visitTime}</div>
                </div>
                
                <div class="review-content" style="margin-bottom: 25px;">
                    <p style="line-height: 1.8; font-size: 1.1rem; margin: 0;">
                        ${reviewData.review}
                    </p>
                </div>
                
                ${reviewData.highlights && reviewData.highlights.length > 0 ? `
                    <div class="review-highlights" style="margin-bottom: 20px;">
                        <h4 style="margin: 0 0 15px 0; font-size: 1.2rem;">✨ 亮点推荐</h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                            ${reviewData.highlights.map(highlight => 
                                `<span style="background: rgba(255, 255, 255, 0.2); padding: 8px 15px; border-radius: 25px; font-size: 0.9rem; font-weight: 500;">
                                    ${highlight}
                                </span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="review-footer" style="
                    display: grid; 
                    grid-template-columns: 1fr 1fr; 
                    gap: 20px; 
                    background: rgba(255, 255, 255, 0.1); 
                    padding: 20px; 
                    border-radius: 15px;
                ">
                    ${reviewData.tips ? `
                        <div>
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">💡 小贴士</div>
                            <div style="font-size: 1rem; opacity: 0.9; line-height: 1.5;">${reviewData.tips}</div>
                        </div>
                    ` : ''}
                    
                    <div>
                        <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">🎯 推荐理由</div>
                        <div style="font-size: 1rem; opacity: 0.9; line-height: 1.5;">${reviewData.rating_reason}</div>
                    </div>
                </div>
                
                ${reviewData.mood ? `
                    <div style="text-align: center; margin-top: 20px; font-size: 1rem; opacity: 0.9;">
                        适合心情：${reviewData.mood} 🎭
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from { 
                opacity: 0;
                transform: translateY(50px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        .close-modal-btn:hover {
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.1);
        }
    `;
    document.head.appendChild(style);
    
    logger.info(`📖 显示场景锐评弹窗: ${scene.name}`);
}

// 关闭锐评弹窗
function closeReviewModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => modal.remove(), 300);
        logger.info('📖 锐评弹窗已关闭');
    }
}

// 全局暴露关闭函数
window.closeReviewModal = closeReviewModal;

// 计算两个坐标之间的距离（使用Haversine公式）
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // 地球半径（公里）
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    return distance;
}

// 计算旅程统计数据
function calculateJourneyStats() {
    const scenes = journeyManagement.historyScenes;
    
    if (scenes.length === 0) {
        return {
            totalDistance: 0,
            totalTimeMinutes: 0,
            scenesCount: 0
        };
    }
    
    // 计算总距离
    let totalDistance = 0;
    for (let i = 1; i < scenes.length; i++) {
        const prevScene = scenes[i - 1];
        const currentScene = scenes[i];
        const distance = calculateDistance(
            prevScene.latitude, prevScene.longitude,
            currentScene.latitude, currentScene.longitude
        );
        totalDistance += distance;
    }
    
    // 计算总时长（基于访问时间）
    let totalTimeMinutes = 0;
    if (scenes.length >= 2) {
        const startTime = new Date(scenes[0].visitTime);
        const endTime = new Date(scenes[scenes.length - 1].visitTime);
        totalTimeMinutes = Math.round((endTime - startTime) / (1000 * 60)); // 转换为分钟
        
        // 确保时间是正数
        if (totalTimeMinutes < 0) {
            totalTimeMinutes = Math.round(scenes.length * 5); // 默认每个场景5分钟
        }
    }
    
    return {
        totalDistance: Math.round(totalDistance * 10) / 10, // 保留1位小数
        totalTimeMinutes: Math.max(totalTimeMinutes, scenes.length * 2), // 最少每个场景2分钟
        scenesCount: scenes.length
    };
}

// 现代探索旅程总结功能
async function showModernJourneySummary(journeyResult) {
    // 🔧 使用本地计算的统计数据，而不是依赖后端返回的数据
    const stats = calculateJourneyStats();
    
    // 生成旅程亮点
    const highlights = generateJourneyHighlights();
    
    // 🤖 生成AI旅程总结数据
    let aiSummaryData = {
        summary: '🎉 恭喜完成这次精彩的探索之旅！每一步都是独特的发现，感谢您选择方向探索派对！',
        highlights: [],
        recommendation: '继续探索更多精彩地点'
    };
    
    try {
        logger.info('🤖 开始生成AI旅程总结...');
        const aiSummary = await generateAIJourneySummary(stats);
        if (aiSummary && typeof aiSummary === 'object') {
            aiSummaryData = aiSummary;
        } else if (typeof aiSummary === 'string') {
            aiSummaryData.summary = aiSummary;
        }
    } catch (error) {
        logger.warning('AI旅程总结生成失败，使用默认内容');
    }
    
    const summaryHtml = `
        <div class="journey-summary" id="journeySummary" style="
            margin: 20px 0;
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        ">
            <button class="close-summary-btn" onclick="closeSummary()" style="
                position: absolute;
                top: 15px;
                right: 15px;
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                font-size: 24px;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                z-index: 10;
            " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" 
               onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">✕</button>
            
            <div style="position: relative; z-index: 2;">
                <h2 style="margin: 0 0 20px 0; font-size: 2rem;">🎉 旅程完成！</h2>
                <div style="
                    display: grid; 
                    grid-template-columns: repeat(3, 1fr); 
                    gap: 20px; 
                    margin: 20px 0;
                ">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 5px;">
                            ${stats.scenesCount}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">访问场景</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 5px;">
                            ${stats.totalDistance}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">总距离(km)</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 5px;">
                            ${stats.totalTimeMinutes}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">旅程时长(分钟)</div>
                    </div>
                </div>
                
                <!-- AI生成的旅程总结 -->
                <div class="ai-summary-section" style="
                    margin: 25px 0;
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                ">
                    <!-- 主要总结 -->
                    <div style="
                        background: rgba(255, 255, 255, 0.15);
                        border-radius: 15px;
                        padding: 20px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    ">
                        <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 12px; text-align: center; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            🤖 <span>AI旅程回顾</span>
                        </div>
                        <p style="
                            margin: 0;
                            font-size: 1.1rem;
                            line-height: 1.6;
                            font-style: italic;
                            text-align: center;
                        ">${aiSummaryData.summary}</p>
                    </div>
                    
                    <!-- 旅程亮点 -->
                    ${aiSummaryData.highlights && aiSummaryData.highlights.length > 0 ? `
                        <div style="
                            background: rgba(255, 255, 255, 0.12);
                            border-radius: 15px;
                            padding: 20px;
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.15);
                        ">
                            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 12px; text-align: center; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                ✨ <span>旅程亮点</span>
                            </div>
                            <div style="
                                display: flex;
                                flex-direction: column;
                                gap: 8px;
                                font-size: 0.95rem;
                                line-height: 1.5;
                            ">
                                ${aiSummaryData.highlights.map(highlight => 
                                    `<div style="
                                        background: rgba(255, 255, 255, 0.1);
                                        padding: 12px 16px;
                                        border-radius: 10px;
                                        border-left: 4px solid rgba(255, 255, 255, 0.4);
                                        text-align: left;
                                    ">• ${highlight}</div>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- 探索建议 -->
                    ${aiSummaryData.recommendation ? `
                        <div style="
                            background: rgba(255, 255, 255, 0.1);
                            border-radius: 15px;
                            padding: 18px;
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.1);
                        ">
                            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 10px; text-align: center; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                🚀 <span>下次探索建议</span>
                            </div>
                            <p style="
                                margin: 0;
                                font-size: 1rem;
                                line-height: 1.5;
                                text-align: center;
                                opacity: 0.95;
                            ">${aiSummaryData.recommendation}</p>
                        </div>
                    ` : ''}
                </div>
                
                <div style="margin-top: 20px; font-size: 1.1rem; opacity: 0.9;">
                    感谢您选择方向探索派对！期待下次旅程 🧭
                </div>
                
                <div style="margin-top: 15px; font-size: 0.85rem; opacity: 0.7;">
                    💡 提示：此总结将保持显示，您可以点击右上角 ✕ 关闭
                </div>
            </div>
        </div>
    `;
    
    const summaryContainer = document.getElementById('journeySummaryContainer');
    if (summaryContainer) {
        summaryContainer.style.display = 'block';
        summaryContainer.innerHTML = summaryHtml;
        
        // 隐藏地点容器
        const placesContainer = document.getElementById('placesContainer');
        if (placesContainer) {
            placesContainer.style.display = 'none';
        }
        
        // 滚动到总结位置
        summaryContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        logger.success(`📊 旅程总结已生成: ${stats.scenesCount}个场景, ${stats.totalDistance}km, ${stats.totalTimeMinutes}分钟`);
    }
}

// 关闭旅程总结
function closeSummary() {
    const summaryContainer = document.getElementById('journeySummaryContainer');
    const placesContainer = document.getElementById('placesContainer');
    
    if (summaryContainer) {
        summaryContainer.style.display = 'none';
        summaryContainer.innerHTML = '';
        logger.info('📊 旅程总结已关闭');
    }
    
    // 恢复地点容器显示
    if (placesContainer) {
        placesContainer.style.display = 'block';
    }
}

// 全局暴露关闭函数
window.closeSummary = closeSummary;

// ================ 预设地址功能 ================

/**
 * 处理预设地址选择变化
 */
function handlePresetLocationChange() {
    const selector = document.getElementById('presetLocationSelect');
    const selectedValue = selector.value;
    
    logger.info(`📍 预设地址选择: ${selectedValue}`);
    
    if (!selectedValue || selectedValue === '') {
        // 未选择任何选项
        return;
    }
    
    if (selectedValue === 'current') {
        // 选择使用当前GPS位置
        currentLocationSource = 'gps';
        logger.info('📱 切换到GPS定位模式');
        refreshLocation();
        
    } else if (selectedValue === 'manual') {
        // 选择手动输入
        currentLocationSource = 'manual';
        logger.info('✋ 切换到手动输入模式');
        showManualLocationInput();
        
    } else if (PRESET_LOCATIONS[selectedValue]) {
        // 选择预设地址
        currentLocationSource = 'preset';
        setPresetLocation(selectedValue);
    }
}

/**
 * 设置预设地址位置
 * @param {string} locationKey - 预设地址键名
 */
async function setPresetLocation(locationKey) {
    const location = PRESET_LOCATIONS[locationKey];
    
    if (!location) {
        logger.error(`❌ 未找到预设地址: ${locationKey}`);
        return;
    }
    
    logger.info(`🌍 设置预设地址: ${location.name}`);
    
    // 设置位置信息
    currentPosition = {
        latitude: location.latitude,
        longitude: location.longitude,
        accuracy: 100, // 预设地址精度设为100米
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now(),
        source: 'preset'
    };
    
    // 更新UI显示
    document.getElementById('coordinates').textContent = 
        `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;
    document.getElementById('accuracy').textContent = '±100m (预设)';
    document.getElementById('currentLocation').textContent = location.name;
    
    // 启用探索按钮
    const exploreBtn = document.getElementById('exploreBtn');
    if (exploreBtn) {
        exploreBtn.disabled = false;
    }
    
    logger.success(`✅ 预设地址设置完成: ${location.name} (${location.country})`);
    logger.info(`坐标: ${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`);
    
    showSuccess(`📍 已切换到: ${location.name}`);
    
    // 可选：显示地址描述信息
    if (location.description) {
        setTimeout(() => {
            logger.info(`🏛️ ${location.description}`);
        }, 500);
    }
}

/**
 * 快速切换位置功能
 * 在几个常用预设地址之间快速循环切换
 */
function quickSwitchLocation() {
    const quickSwitchOrder = ['tokyo', 'paris', 'newyork', 'london', 'sydney'];
    const selector = document.getElementById('presetLocationSelect');
    
    let currentIndex = quickSwitchOrder.indexOf(selector.value);
    
    // 如果当前不在快速切换列表中，从第一个开始
    if (currentIndex === -1) {
        currentIndex = 0;
    } else {
        // 切换到下一个
        currentIndex = (currentIndex + 1) % quickSwitchOrder.length;
    }
    
    const nextLocation = quickSwitchOrder[currentIndex];
    
    logger.info(`🔄 快速切换到: ${PRESET_LOCATIONS[nextLocation].name}`);
    
    // 更新选择器并触发变化
    selector.value = nextLocation;
    handlePresetLocationChange();
    
    // 显示切换提示
    const location = PRESET_LOCATIONS[nextLocation];
    showSuccess(`🔄 快速切换: ${location.name}`);
}

/**
 * 获取当前位置的来源类型和描述
 */
function getCurrentLocationInfo() {
    const selector = document.getElementById('presetLocationSelect');
    const selectedValue = selector.value;
    
    let sourceInfo = {
        type: currentLocationSource,
        name: '未知',
        description: ''
    };
    
    switch(currentLocationSource) {
        case 'gps':
            sourceInfo.name = 'GPS定位';
            sourceInfo.description = '使用设备GPS获取当前真实位置';
            break;
        case 'preset':
            if (PRESET_LOCATIONS[selectedValue]) {
                const location = PRESET_LOCATIONS[selectedValue];
                sourceInfo.name = location.name;
                sourceInfo.description = location.description;
            }
            break;
        case 'manual':
            sourceInfo.name = '手动输入';
            sourceInfo.description = '用户手动输入的坐标位置';
            break;
    }
    
    return sourceInfo;
}

/**
 * 重置预设地址选择器到默认状态
 */
function resetPresetLocationSelector() {
    const selector = document.getElementById('presetLocationSelect');
    if (selector) {
        selector.value = 'current';
        currentLocationSource = 'gps';
        logger.info('🔄 预设地址选择器已重置为GPS模式');
    }
}

// 生成旅程亮点
function generateJourneyHighlights() {
    const highlights = [];
    const scenes = journeyManagement.historyScenes;
    
    if (scenes.length > 0) {
        highlights.push(`🎯 首站探索：${scenes[0].name}`);
        
        if (scenes.length > 1) {
            highlights.push(`🏁 终点到达：${scenes[scenes.length - 1].name}`);
        }
        
        if (scenes.length >= 3) {
            highlights.push(`🌟 成就解锁：探索达人（访问${scenes.length}个地点）`);
        }
        
        // 计算旅程总时长（基于访问时间）
        if (scenes.length >= 2) {
            const startTime = new Date(scenes[0].visitTime);
            const endTime = new Date(scenes[scenes.length - 1].visitTime);
            const duration = Math.round((endTime - startTime) / (1000 * 60)); // 分钟
            if (duration > 0) {
                highlights.push(`⏱️ 旅程时长：${duration}分钟`);
            }
        }
    }
    
    return highlights;
}

// 显示地理位置权限帮助信息
function showLocationPermissionHelp() {
    const helpHtml = `
        <div class="location-permission-help" style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            max-width: 90%;
            text-align: center;
        ">
            <h3 style="color: #e53e3e; margin-bottom: 15px;">🔒 需要位置权限</h3>
            <p style="margin-bottom: 15px; color: #4a5568;">
                OrientDiscover 需要访问您的位置来提供探索服务
            </p>
            <div style="margin-bottom: 20px; text-align: left; font-size: 14px; color: #666;">
                <strong>解决方法：</strong><br>
                1. 点击浏览器地址栏左侧的锁图标<br>
                2. 选择"位置" → "允许"<br>
                3. 刷新页面重新尝试<br>
                <br>
                <strong>或者：</strong><br>
                • 使用下方的手动输入位置功能
            </div>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button onclick="this.parentElement.parentElement.remove(); refreshLocation();" 
                        style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    🔄 重新尝试
                </button>
                <button onclick="this.parentElement.parentElement.remove(); showManualLocationInput();" 
                        style="padding: 10px 20px; background: #f093fb; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    ✋ 手动输入
                </button>
                <button onclick="this.parentElement.parentElement.remove();" 
                        style="padding: 10px 20px; background: #cbd5e0; color: #4a5568; border: none; border-radius: 8px; cursor: pointer;">
                    ❌ 关闭
                </button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', helpHtml);
}

// 显示手动位置输入界面
function showManualLocationInput() {
    const inputHtml = `
        <div class="manual-location-input" style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            max-width: 90%;
            min-width: 350px;
        ">
            <h3 style="color: #667eea; margin-bottom: 15px; text-align: center;">📍 手动输入位置</h3>
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">纬度 (Latitude):</label>
                <input type="number" id="manualLat" placeholder="例如: 40.0888" step="0.000001" 
                       style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 16px;">
            </div>
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">经度 (Longitude):</label>
                <input type="number" id="manualLng" placeholder="例如: 116.3964" step="0.000001" 
                       style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 16px;">
            </div>
            <div style="margin-bottom: 20px; padding: 10px; background: #f7fafc; border-radius: 8px; font-size: 14px; color: #4a5568;">
                <strong>💡 提示：</strong><br>
                • 北京市中心大约：40.0888, 116.3964<br>
                • 可以在地图应用中查看当前位置的坐标<br>
                • 或者使用"获取我的位置"按钮再次尝试
            </div>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button onclick="setManualLocation();" 
                        style="padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                    ✅ 确认位置
                </button>
                <button onclick="this.parentElement.parentElement.remove(); refreshLocation();" 
                        style="padding: 12px 24px; background: #f093fb; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    🔄 重新获取
                </button>
                <button onclick="this.parentElement.parentElement.remove();" 
                        style="padding: 12px 24px; background: #cbd5e0; color: #4a5568; border: none; border-radius: 8px; cursor: pointer;">
                    ❌ 取消
                </button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', inputHtml);
}

// 设置手动输入的位置
async function setManualLocation() {
    const latInput = document.getElementById('manualLat');
    const lngInput = document.getElementById('manualLng');
    
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    
    // 验证输入
    if (isNaN(lat) || isNaN(lng)) {
        alert('❌ 请输入有效的经纬度数值');
        return;
    }
    
    if (lat < -90 || lat > 90) {
        alert('❌ 纬度应该在 -90 到 90 之间');
        return;
    }
    
    if (lng < -180 || lng > 180) {
        alert('❌ 经度应该在 -180 到 180 之间');
        return;
    }
    
    // 设置位置
    currentPosition = {
        latitude: lat,
        longitude: lng,
        accuracy: 1000, // 手动输入精度设为1000米
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now()
    };
    
    logger.success(`📍 手动设置位置: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    
    // 更新UI
    document.getElementById('coordinates').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    document.getElementById('accuracy').textContent = '±1000m (手动)';
    
    // 获取地址名称
    try {
        const locationName = await getLocationName(lat, lng);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        document.getElementById('currentLocation').textContent = `手动位置 ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        logger.warning('地址获取失败，使用坐标显示');
    }
    
    // 启用探索按钮
    document.getElementById('exploreBtn').disabled = false;
    logger.success('✅ 手动位置设置完成，探索功能已启用');
    
    // 关闭输入界面
    document.querySelector('.manual-location-input').remove();
}

// 异步更新位置显示
async function updateLocationDisplayAsync(place) {
    try {
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        document.getElementById('coordinates').textContent = 
            `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
        logger.success(`📍 位置已更新为: ${place.name} (${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)})`);
    } catch (error) {
        document.getElementById('currentLocation').textContent = place.name;
        document.getElementById('coordinates').textContent = 
            `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
        logger.success(`📍 位置已更新为: ${place.name}`);
    }
}

// 生成并显示场景锐评
async function generateAndShowSceneReview(scene) {
    try {
        logger.info(`🤖 开始为场景 "${scene.name}" 生成AI锐评...`);
        
        // 准备用户上下文
        const userContext = {
            visit_count: journeyManagement.historyScenes.length,
            time_of_day: new Date().toLocaleTimeString(),
            previous_places: journeyManagement.historyScenes.map(h => h.name),
            journey_active: journeyManagement.isJourneyActive
        };
        
        // 调用后端API生成锐评
        const response = await fetch(API_CONFIG.getApiUrl('/api/scene-review'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scene_name: scene.name,
                scene_description: scene.description,
                scene_type: scene.category || "自然景观",
                scene_lat: scene.latitude,
                scene_lng: scene.longitude,
                user_context: userContext
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            displaySceneReview(data.review_data, scene);
            // 🆕 将锐评数据保存到历史场景
            addToHistoryScenes(scene, data.review_data);
            logger.success(`🤖 AI锐评生成成功，耗时: ${data.generation_time.toFixed(2)}秒`);
        } else {
            displaySceneReview(data.review_data, scene);
            // 🆕 即使失败也保存锐评数据（可能是降级版本）
            addToHistoryScenes(scene, data.review_data);
            logger.warning(`⚠️ ${data.message}`);
        }
        
    } catch (error) {
        logger.error(`❌ AI锐评生成失败: ${error.message}`);
        
        // 显示备用锐评
        const fallbackReview = {
            title: `探索发现：${scene.name}`,
            review: `恭喜您发现了${scene.name}！这是一个值得记录的精彩时刻。每一次探索都是独特的体验，每一个地方都有其独特的故事等待您去发现。`,
            highlights: ["独特的探索体验", "值得纪念的时刻", "真实的地理发现"],
            tips: "保持好奇心，享受探索的过程",
            rating_reason: "探索的乐趣",
            mood: "发现"
        };
        
        displaySceneReview(fallbackReview, scene);
        // 🆕 备用锐评也要保存到历史
        addToHistoryScenes(scene, fallbackReview);
    }
}

// 显示场景锐评
function displaySceneReview(reviewData, scene) {
    // 🧹 清理旧的独立锐评容器，避免重复显示
    const oldIndependentContainer = document.getElementById('independentReviewContainer');
    if (oldIndependentContainer) {
        oldIndependentContainer.remove();
        logger.info('🧹 清理旧的独立锐评容器');
    }
    
    // 🔧 修复：优先查找现有容器，如果不存在则创建独立显示区域
    let targetContainer = document.getElementById('arrivalConfirmation');
    
    if (!targetContainer) {
        // 创建独立的锐评显示容器
        targetContainer = createIndependentReviewContainer(scene);
    }
    
    if (!targetContainer) {
        logger.error('❌ 无法创建锐评显示区域');
        return;
    }
    
    const reviewHtml = `
        <div class="scene-review" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        ">
            <div class="review-header" style="text-align: center; margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0; font-size: 1.5rem;">🤖 ${reviewData.title}</h3>
                <div style="opacity: 0.9; font-size: 0.9rem;">AI智能锐评</div>
            </div>
            
            <div class="review-content" style="margin-bottom: 20px;">
                <p style="line-height: 1.6; font-size: 1rem; margin: 0;">
                    ${reviewData.review}
                </p>
            </div>
            
            ${reviewData.highlights && reviewData.highlights.length > 0 ? `
                <div class="review-highlights" style="margin-bottom: 15px;">
                    <h4 style="margin: 0 0 10px 0; font-size: 1.1rem;">✨ 亮点推荐</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${reviewData.highlights.map(highlight => 
                            `<span style="background: rgba(255, 255, 255, 0.2); padding: 5px 12px; border-radius: 20px; font-size: 0.85rem;">
                                ${highlight}
                            </span>`
                        ).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="review-footer" style="
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 15px; 
                background: rgba(255, 255, 255, 0.1); 
                padding: 15px; 
                border-radius: 10px;
            ">
                ${reviewData.tips ? `
                    <div>
                        <div style="font-weight: bold; margin-bottom: 5px;">💡 小贴士</div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">${reviewData.tips}</div>
                    </div>
                ` : ''}
                
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px;">🎯 推荐理由</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">${reviewData.rating_reason}</div>
                </div>
            </div>
            
            ${reviewData.mood ? `
                <div style="text-align: center; margin-top: 15px; font-size: 0.9rem; opacity: 0.8;">
                    适合心情：${reviewData.mood} 🎭
                </div>
            ` : ''}
        </div>
    `;
    
    // 在目标容器前插入锐评，如果是独立容器则直接插入
    if (targetContainer.id === 'independentReviewContainer') {
        targetContainer.innerHTML = reviewHtml;
    } else {
        targetContainer.insertAdjacentHTML('beforebegin', reviewHtml);
    }
    
    // 滚动到锐评位置
    setTimeout(() => {
        const reviewDiv = document.querySelector('.scene-review');
        if (reviewDiv) {
            reviewDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
    
    logger.info('🎨 场景锐评已显示');
}

// 创建独立的锐评显示容器（当原容器不存在时）
function createIndependentReviewContainer(scene) {
    try {
        // 查找一个合适的父容器来插入锐评
        const placesContainer = document.getElementById('placesContainer');
        const historyContainer = document.getElementById('journeyHistorySection');
        const mainContainer = document.querySelector('.app-container');
        
        const parentContainer = placesContainer || historyContainer || mainContainer;
        
        if (!parentContainer) {
            logger.error('❌ 找不到合适的父容器来显示锐评');
            return null;
        }
        
        // 创建独立的锐评容器
        const reviewContainer = document.createElement('div');
        reviewContainer.id = 'independentReviewContainer';
        reviewContainer.style.cssText = `
            margin: 20px 0;
            padding: 0;
            position: relative;
            z-index: 10;
        `;
        
        // 添加标题提示
        const titleHtml = `
            <div style="
                background: rgba(102, 126, 234, 0.1);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                text-align: center;
                font-weight: bold;
                color: #667eea;
            ">
                🎯 场景锐评已生成 - ${scene.name}
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 5px;">
                    AI分析完成，精彩内容如下 ↓
                </div>
            </div>
        `;
        reviewContainer.innerHTML = titleHtml;
        
        // 插入到合适位置
        if (placesContainer) {
            // 插入到地点容器后面
            placesContainer.parentNode.insertBefore(reviewContainer, placesContainer.nextSibling);
        } else {
            // 插入到父容器开头
            parentContainer.insertBefore(reviewContainer, parentContainer.firstChild);
        }
        
        logger.info(`✅ 创建独立锐评容器成功，位置: ${parentContainer.id || 'app-container'}`);
        return reviewContainer;
        
    } catch (error) {
        logger.error(`❌ 创建独立锐评容器失败: ${error.message}`);
        return null;
    }
}

// 解析AI旅程总结数据结构
function parseAIJourneySummary(rawSummary) {
    try {
        // 尝试解析结构化数据
        let parsedData = {
            summary: '',
            highlights: [],
            recommendation: ''
        };
        
        // 情况1: 如果是纯文本，直接返回
        if (typeof rawSummary === 'string' && !rawSummary.includes('summary=') && !rawSummary.includes('highlights=')) {
            return { summary: rawSummary, highlights: [], recommendation: '' };
        }
        
        // 情况2: 解析类似 "summary='...' highlights=[...] recommendation='...'" 的格式
        const summaryMatch = rawSummary.match(/summary='(.*?)'\s*highlights=/);
        if (summaryMatch) {
            parsedData.summary = summaryMatch[1];
        } else {
            // 备用匹配
            const altSummaryMatch = rawSummary.match(/summary='([^']*?)'/);
            if (altSummaryMatch) {
                parsedData.summary = altSummaryMatch[1];
            }
        }
        
        const highlightsMatch = rawSummary.match(/highlights=\[(.*?)\]\s*recommendation=/);
        if (highlightsMatch) {
            // 解析数组内容 - 处理单引号包围的内容
            let highlightsStr = highlightsMatch[1];
            // 分割并清理每个项目
            let highlights = [];
            const matches = highlightsStr.match(/'([^']*)'/g);
            if (matches) {
                highlights = matches.map(match => match.slice(1, -1)); // 去除引号
            }
            parsedData.highlights = highlights;
        }
        
        const recommendationMatch = rawSummary.match(/recommendation='(.*?)'\s*(?:\w+|$)/);
        if (recommendationMatch) {
            parsedData.recommendation = recommendationMatch[1];
        } else {
            // 备用匹配 - 匹配到字符串结尾
            const altRecommendationMatch = rawSummary.match(/recommendation='(.*)$/);
            if (altRecommendationMatch) {
                let rec = altRecommendationMatch[1];
                // 去除末尾可能的引号和其他字符
                rec = rec.replace(/'\s*\w*\s*$/, '');
                parsedData.recommendation = rec;
            }
        }
        
        console.log('📝 解析AI总结数据:', parsedData);
        return parsedData;
        
    } catch (error) {
        console.error('❌ AI总结解析失败:', error);
        return {
            summary: rawSummary,
            highlights: [],
            recommendation: '继续探索更多精彩地点'
        };
    }
}

// 生成AI旅程总结
async function generateAIJourneySummary(stats) {
    try {
        const response = await fetch(API_CONFIG.getApiUrl('/api/journey-summary'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                visited_scenes: journeyManagement.historyScenes,
                total_distance: stats.totalDistance,
                journey_duration: `${stats.totalTimeMinutes}分钟`,
                scenes_count: stats.scenesCount
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success && data.summary) {
            logger.success('🤖 AI旅程总结生成成功');
            // 解析AI返回的结构化数据
            return parseAIJourneySummary(data.summary);
        } else {
            throw new Error(data.message || '生成失败');
        }
        
    } catch (error) {
        logger.error(`❌ AI旅程总结生成失败: ${error.message}`);
        return null;
    }
}

// ================ Google街景功能 ================

// 初始化Google Maps API
function initGoogleMapsAPI() {
    if (typeof google !== 'undefined' && google.maps) {
        // 初始化Street View服务
        streetViewService = new google.maps.StreetViewService();
        logger.info('✅ Google Maps Street View服务已初始化');
        return true;
    } else {
        logger.warning('⚠️ Google Maps API未加载');
        return false;
    }
}

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

    // 检查位置坐标是否有效
    if (!scene.latitude || !scene.longitude) {
        logger.warning('⚠️ 跳过街景显示：场景位置坐标无效');
        return;
    }

    const location = {
        lat: parseFloat(scene.latitude),
        lng: parseFloat(scene.longitude)
    };

    // 保存当前场景信息
    currentStreetViewLocation = {
        scene: scene,
        location: location
    };

    logger.info(`🏙️ 开始为 ${scene.name} 加载街景...`);

    // 显示街景模态框
    showStreetViewModal(scene);

    // 查找附近的街景数据
    streetViewService.getPanorama({
        location: location,
        radius: 1000, // 搜索半径1公里
        source: google.maps.StreetViewSource.OUTDOOR
    })
    .then((result) => {
        if (result.data && result.data.location) {
            // 有街景数据，显示街景
            displayStreetViewPanorama(result.data, scene);
        } else {
            // 无街景数据，显示错误信息
            showStreetViewError('该位置附近暂无街景数据', 'NO_STREET_VIEW');
        }
    })
    .catch((error) => {
        logger.error(`❌ 街景加载失败: ${error.message}`);
        showStreetViewError(`街景加载失败: ${error.message}`, 'API_ERROR');
    });
}

// 显示街景模态框
function showStreetViewModal(scene) {
    const modal = document.getElementById('streetviewModal');
    const overlay = document.getElementById('streetviewOverlay');
    const title = document.getElementById('streetviewTitle');

    if (modal && overlay && title) {
        // 更新标题
        title.textContent = `🏙️ ${scene.name} - 街景视图`;

        // 显示模态框和遮罩
        modal.style.display = 'block';
        overlay.style.display = 'block';

        // 显示加载状态
        showStreetViewLoading();

        // 添加ESC键关闭功能
        document.addEventListener('keydown', handleStreetViewKeydown);

        logger.info('🏙️ 街景模态框已显示');
    }
}

// 显示街景全景图
function displayStreetViewPanorama(streetViewData, scene) {
    const container = document.getElementById('streetviewContainer');
    if (!container) {
        logger.error('❌ 找不到街景容器');
        return;
    }

    // 隐藏加载状态
    hideStreetViewLoading();

    try {
        // 创建Street View全景图
        streetViewPanorama = new google.maps.StreetViewPanorama(container, {
            position: streetViewData.location.latLng,
            pov: {
                heading: 0,
                pitch: 0
            },
            zoom: 1,
            enableCloseButton: false,
            addressControl: false,
            fullscreenControl: false,
            linksControl: true,
            panControl: true,
            zoomControl: true,
            motionTracking: false,
            motionTrackingControl: false
        });

        // 更新信息显示
        updateStreetViewInfo(streetViewData, scene);

        // 监听全景图事件
        streetViewPanorama.addListener('pano_changed', () => {
            logger.info('📍 街景全景图已更改');
        });

        streetViewPanorama.addListener('position_changed', () => {
            const position = streetViewPanorama.getPosition();
            if (position) {
                logger.info(`📍 街景位置已更改: ${position.lat()}, ${position.lng()}`);
            }
        });

        logger.success(`✅ ${scene.name} 街景加载成功`);

    } catch (error) {
        logger.error(`❌ 街景全景图创建失败: ${error.message}`);
        showStreetViewError(`创建街景失败: ${error.message}`, 'PANORAMA_ERROR');
    }
}

// 更新街景信息显示
function updateStreetViewInfo(streetViewData, scene) {
    const locationEl = document.getElementById('streetviewLocation');
    const coordsEl = document.getElementById('streetviewCoords');
    const dateEl = document.getElementById('streetviewDate');

    if (locationEl) {
        locationEl.textContent = scene.name || '未知位置';
    }

    if (coordsEl && streetViewData.location && streetViewData.location.latLng) {
        const lat = streetViewData.location.latLng.lat();
        const lng = streetViewData.location.latLng.lng();
        coordsEl.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }

    if (dateEl && streetViewData.imageDate) {
        const date = new Date(streetViewData.imageDate);
        dateEl.textContent = date.toLocaleDateString('zh-CN');
    }
}

// 显示加载状态
function showStreetViewLoading() {
    const loadingEl = document.getElementById('streetviewLoading');
    const errorEl = document.getElementById('streetviewError');

    if (loadingEl) loadingEl.style.display = 'block';
    if (errorEl) errorEl.style.display = 'none';
}

// 隐藏加载状态
function hideStreetViewLoading() {
    const loadingEl = document.getElementById('streetviewLoading');
    if (loadingEl) loadingEl.style.display = 'none';
}

// 显示街景错误
function showStreetViewError(message, errorType) {
    hideStreetViewLoading();

    const errorEl = document.getElementById('streetviewError');
    const errorTextEl = document.getElementById('streetviewErrorText');

    if (errorEl) {
        errorEl.style.display = 'block';

        if (errorTextEl) {
            errorTextEl.textContent = message;
        }

        logger.warning(`⚠️ 街景错误: ${message} (${errorType})`);
    }
}

// 关闭街景模态框
function closeStreetView() {
    const modal = document.getElementById('streetviewModal');
    const overlay = document.getElementById('streetviewOverlay');

    if (modal) modal.style.display = 'none';
    if (overlay) overlay.style.display = 'none';

    // 清理街景实例
    if (streetViewPanorama) {
        streetViewPanorama = null;
    }

    // 重置全屏状态
    if (isStreetViewFullscreen) {
        toggleStreetViewFullscreen();
    }

    // 移除键盘事件监听
    document.removeEventListener('keydown', handleStreetViewKeydown);

    // 重置变量
    currentStreetViewLocation = null;

    logger.info('🏙️ 街景模态框已关闭');
}

// 重置街景视角
function resetStreetViewHeading() {
    if (streetViewPanorama) {
        streetViewPanorama.setPov({
            heading: 0,
            pitch: 0
        });
        logger.info('🧭 街景视角已重置');
    }
}

// 切换全屏模式
function toggleStreetViewFullscreen() {
    const modal = document.getElementById('streetviewModal');

    if (modal) {
        if (isStreetViewFullscreen) {
            modal.classList.remove('fullscreen');
            isStreetViewFullscreen = false;
            logger.info('🔽 已退出全屏模式');
        } else {
            modal.classList.add('fullscreen');
            isStreetViewFullscreen = true;
            logger.info('🔼 已进入全屏模式');
        }
    }
}

// 分享街景位置
function shareStreetView() {
    if (currentStreetViewLocation && navigator.share) {
        const shareData = {
            title: `${currentStreetViewLocation.scene.name} - 街景视图`,
            text: `查看 ${currentStreetViewLocation.scene.name} 的街景`,
            url: `https://www.google.com/maps/@${currentStreetViewLocation.location.lat},${currentStreetViewLocation.location.lng},3a,75y,90t/data=!3m8!1e2!3m6!1s!2s!3s!4s!5s!6s`
        };

        navigator.share(shareData)
            .then(() => logger.info('📤 街景位置已分享'))
            .catch((error) => logger.warning(`⚠️ 分享失败: ${error.message}`));
    } else if (currentStreetViewLocation) {
        // 复制到剪贴板
        const shareUrl = `https://www.google.com/maps/@${currentStreetViewLocation.location.lat},${currentStreetViewLocation.location.lng},3a,75y,90t/data=!3m8!1e2!3m6!1s!2s!3s!4s!5s!6s`;
        navigator.clipboard.writeText(shareUrl)
            .then(() => {
                showSuccess('📤 街景链接已复制到剪贴板');
                logger.info('📤 街景链接已复制');
            })
            .catch((error) => logger.warning(`⚠️ 复制失败: ${error.message}`));
    }
}

// 重试加载街景
function retryStreetView() {
    if (currentStreetViewLocation) {
        logger.info('🔄 重试加载街景...');
        showStreetViewForLocation(currentStreetViewLocation.scene);
    }
}

// 处理键盘事件
function handleStreetViewKeydown(event) {
    if (event.key === 'Escape') {
        closeStreetView();
    } else if (event.key === 'f' || event.key === 'F') {
        toggleStreetViewFullscreen();
    } else if (event.key === 'r' || event.key === 'R') {
        resetStreetViewHeading();
    }
}

// 页面加载完成后初始化Google Maps
window.addEventListener('load', function() {
    // 等待Google Maps API加载
    if (typeof window.initGoogleMaps === 'function') {
        window.initGoogleMaps();
    }
});

// 全局暴露街景函数
window.closeStreetView = closeStreetView;
window.resetStreetViewHeading = resetStreetViewHeading;
window.toggleStreetViewFullscreen = toggleStreetViewFullscreen;
window.shareStreetView = shareStreetView;
window.retryStreetView = retryStreetView;

window.startJourney = startJourney;
window.journeyManagement = journeyManagement;
window.setManualLocation = setManualLocation;
window.generateAndShowSceneReview = generateAndShowSceneReview;

// 全局暴露预设地址功能
window.handlePresetLocationChange = handlePresetLocationChange;
window.quickSwitchLocation = quickSwitchLocation;
window.setPresetLocation = setPresetLocation;
window.getCurrentLocationInfo = getCurrentLocationInfo;
window.resetPresetLocationSelector = resetPresetLocationSelector;
window.PRESET_LOCATIONS = PRESET_LOCATIONS;

// ================ 历史模式功能 ================

/**
 * 切换历史模式开关
 */
function toggleHistoricalMode() {
    const controls = document.getElementById('historicalControls');
    const toggleBtn = document.getElementById('historicalToggle');
    const modeIndicator = document.getElementById('modeIndicator');
    
    isHistoricalMode = !isHistoricalMode;
    
    if (isHistoricalMode) {
        // 启用历史模式
        controls.style.display = 'block';
        toggleBtn.textContent = '🌍 常规探索模式';
        toggleBtn.classList.add('active');
        modeIndicator.textContent = '历史模式';
        
        logger.info('✅ 已切换到历史模式');
        showSuccess('🏛️ 历史模式已启用！选择时期开始时空探索');
        
        // 隐藏常规探索按钮
        const exploreBtn = document.getElementById('exploreBtn');
        if (exploreBtn) {
            exploreBtn.style.display = 'none';
        }
        
    } else {
        // 关闭历史模式
        controls.style.display = 'none';
        toggleBtn.textContent = '🕰️ 启用历史探索';
        toggleBtn.classList.remove('active');
        modeIndicator.textContent = '常规模式';
        
        logger.info('📍 已切换到常规模式');
        showSuccess('🌍 已返回常规探索模式');
        
        // 恢复常规探索按钮
        const exploreBtn = document.getElementById('exploreBtn');
        if (exploreBtn) {
            exploreBtn.style.display = 'block';
        }
        
        // 清理历史模式数据
        selectedHistoricalYear = null;
        currentHistoricalInfo = null;
        historicalSceneData = null;
        visitedHistoricalScenes = [];  // 🚀 清空本轮旅程的场景记录
        clearHistoricalResults();
    }
}

/**
 * 更新历史年份选择
 */
function updateHistoricalYear() {
    const periodSelect = document.getElementById('historicalPeriod');
    const customYearDiv = document.getElementById('customYearDiv');
    const selectedYearSpan = document.getElementById('selectedYear');
    const timeTravelBtn = document.getElementById('timeTravelBtn');
    const templateSelection = document.getElementById('historicalSceneTemplateSelection');
    
    const selectedValue = periodSelect.value;
    
    if (selectedValue === 'custom') {
        // 显示自定义年份输入
        customYearDiv.style.display = 'block';
        selectedYearSpan.textContent = '自定义年份';
        selectedHistoricalYear = null;
        timeTravelBtn.disabled = true;
        templateSelection.style.display = 'none';
        
        // 监听自定义年份输入变化
        const customInput = document.getElementById('customYearInput');
        customInput.oninput = function() {
            const year = parseInt(this.value);
            if (!isNaN(year) && year >= -3000 && year <= 2024) {
                selectedHistoricalYear = year;
                selectedYearSpan.textContent = year < 0 ? `公元前${Math.abs(year)}年` : `公元${year}年`;
                timeTravelBtn.disabled = false;
                // 显示场景模板选择并加载模板
                templateSelection.style.display = 'block';
                loadHistoricalSceneTemplates();
            } else {
                selectedHistoricalYear = null;
                selectedYearSpan.textContent = '自定义年份';
                timeTravelBtn.disabled = true;
                templateSelection.style.display = 'none';
            }
        };
        
    } else if (selectedValue) {
        // 选择预设年份
        customYearDiv.style.display = 'none';
        selectedHistoricalYear = parseInt(selectedValue);
        
        // 格式化显示年份
        if (selectedHistoricalYear < 0) {
            selectedYearSpan.textContent = `公元前${Math.abs(selectedHistoricalYear)}年`;
        } else {
            selectedYearSpan.textContent = `公元${selectedHistoricalYear}年`;
        }
        
        timeTravelBtn.disabled = false;
        // 显示场景模板选择并加载模板
        templateSelection.style.display = 'block';
        loadHistoricalSceneTemplates();
        logger.info(`📅 选择历史年份: ${selectedHistoricalYear}`);
        
    } else {
        // 未选择
        customYearDiv.style.display = 'none';
        templateSelection.style.display = 'none';
        selectedHistoricalYear = null;
        selectedYearSpan.textContent = '未选择';
        timeTravelBtn.disabled = true;
    }
}

/**
 * 开始历史探索
 */
async function startHistoricalExploration() {
    if (!currentPosition) {
        showError('请先选择位置或获取当前位置');
        return;
    }
    
    if (!selectedHistoricalYear) {
        showError('请先选择历史年份');
        return;
    }
    
    if (!selectedHistoricalTemplate) {
        showError('请先选择一个历史场景风格模板');
        return;
    }
    
    logger.info(`🏛️ 开始历史探索: ${selectedHistoricalYear}年`);
    logger.info(`📍 探索坐标: ${currentPosition.latitude}, ${currentPosition.longitude}`);
    logger.info(`🎨 使用场景模板: ${selectedHistoricalTemplate}`);
    
    showLoading(true, '正在查询历史信息并生成自定义场景...');
    
    try {
        const startTime = Date.now();
        let historicalData = null; // 存储第一步查询到的历史信息
        
        // 第一步：先查询历史信息
        logger.info('🔍 第一步：查询历史信息...');
        
        const historicalQueryData = {
            latitude: currentPosition.latitude,
            longitude: currentPosition.longitude,
            year: selectedHistoricalYear
        };
        
        const historicalResponse = await fetch(API_CONFIG.getApiUrl('/api/query-historical-info'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(historicalQueryData)
        });
        
        if (!historicalResponse.ok) {
            throw new Error(`历史信息查询失败: HTTP ${historicalResponse.status}`);
        }
        
        historicalData = await historicalResponse.json();
        logger.info(`✅ 历史信息查询完成: ${historicalData.historical_info.political_entity}`);
        
        // 更新加载提示
        showLoading(true, `正在为${historicalData.historical_info.political_entity}生成场景模板...`);
        
        // 第二步：使用完整的历史信息生成自定义场景
        logger.info('🎨 第二步：生成自定义历史场景...');
        
        const requestData = {
            historical_info: historicalData.historical_info, // 使用查询到的完整历史信息
            template_id: selectedHistoricalTemplate,
            custom_prompt: "" // 使用模板默认prompt
        };
        
        const response = await fetch(API_CONFIG.getApiUrl('/api/generate-custom-historical-scene'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        const requestTime = Date.now() - startTime;
        logger.info(`历史场景API请求耗时: ${requestTime}ms`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 自定义场景生成的返回格式处理
            const templateResult = data;
            
            // 构建与原始格式兼容的数据结构
            const compatibleData = {
                success: true,
                historical_info: historicalData.historical_info, // 使用第一步查询到的历史信息
                generated_scene: {
                    images: [templateResult.image_url], // 转换为images数组格式
                    scene_description: templateResult.scene_description || `使用${selectedHistoricalTemplate}模板生成的历史场景`,
                    generation_time: templateResult.generation_time || 0,
                    generation_model: 'Custom Template Generation',
                    demo_mode: false,
                    image_count: 1
                }
            };
            
            logger.success(`🎉 模板场景生成成功！发现：${historicalData.historical_info.political_entity}`);
            
            // 保存历史数据
            currentHistoricalInfo = compatibleData.historical_info;
            historicalSceneData = compatibleData.generated_scene;
            
            // 显示历史场景
            displayHistoricalScene(compatibleData);
            
        } else {
            throw new Error(data.error || '历史探索返回失败结果');
        }
        
    } catch (error) {
        logger.error(`❌ 时空探索失败: ${error.message}`);
        showError(`时空探索失败: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

/**
 * 添加场景到已访问历史场景记录
 * @param {Object} historicalInfo - 历史信息
 * @param {Object} sceneData - 场景数据  
 */
function addToVisitedScenes(historicalInfo, sceneData) {
    // 只在历史模式活跃时收集场景
    if (!isHistoricalMode || !historicalInfo || !sceneData) {
        return;
    }
    
    // 生成场景唯一标识
    const sceneId = `${historicalInfo.political_entity}_${historicalInfo.query_year}`;
    
    // 检查是否已存在相同场景（避免重复添加）
    const existingIndex = visitedHistoricalScenes.findIndex(scene => 
        scene.political_entity === historicalInfo.political_entity && 
        scene.year === historicalInfo.query_year
    );
    
    if (existingIndex === -1) {
        // 添加新场景到访问记录
        const sceneRecord = {
            id: sceneId,
            political_entity: historicalInfo.political_entity,
            year: historicalInfo.query_year,
            coordinates: historicalInfo.coordinates,
            description: historicalInfo.description,
            cultural_region: historicalInfo.cultural_region,
            time_period: historicalInfo.time_period,
            scene_data: sceneData,
            visit_time: new Date().toISOString(),
            visit_order: visitedHistoricalScenes.length + 1
        };
        
        visitedHistoricalScenes.push(sceneRecord);
        
        logger.success(`✅ 场景已收集: ${historicalInfo.political_entity} (${historicalInfo.query_year}年)`);
        logger.info(`🗂️ 当前旅程已访问 ${visitedHistoricalScenes.length} 个历史场景`);
        
        // 在开发者控制台显示详细信息
        console.log('📊 已访问场景列表:', visitedHistoricalScenes.map(s => 
            `${s.political_entity}(${s.year}年)`).join(', ')
        );
    } else {
        logger.info(`🔄 场景已存在: ${historicalInfo.political_entity} (${historicalInfo.query_year}年)`);
    }
}

/**
 * 显示历史场景结果
 */
function displayHistoricalScene(data) {
    const container = document.getElementById('placesContainer');
    
    if (!container) {
        logger.error('❌ 找不到显示容器');
        return;
    }
    
    const historicalInfo = data.historical_info;
    const sceneData = data.generated_scene;
    
    // 构建历史场景显示HTML
    const sceneHtml = `
        <div class="historical-scene-container">
            <!-- 历史信息卡片 -->
            <div class="historical-info-card">
                <div class="info-header">
                    <h2>🏛️ ${historicalInfo.political_entity}</h2>
                    <div class="year-badge">${historicalInfo.query_year}年</div>
                </div>
                
                <div class="historical-details">
                    <div class="detail-row">
                        <span class="label">👑 统治者:</span>
                        <span class="value">${historicalInfo.ruler_or_power || '未知'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">🌍 文化圈:</span>
                        <span class="value">${historicalInfo.cultural_region}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">📍 坐标:</span>
                        <span class="value">${historicalInfo.latitude ? historicalInfo.latitude.toFixed(4) : '--'}, ${historicalInfo.longitude ? historicalInfo.longitude.toFixed(4) : '--'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">📊 边界精度:</span>
                        <span class="value">${historicalInfo.border_precision || '未知'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="label">🎭 时代:</span>
                        <span class="value">${historicalInfo.time_period || '古典时期'}</span>
                    </div>
                </div>
                
                <div class="historical-description">
                    <h4>📜 历史背景</h4>
                    <p>${historicalInfo.description || `古典时期(${historicalInfo.query_year}年)，这里是古代文明的${historicalInfo.political_entity}，属于${historicalInfo.cultural_region}文化圈。这是文字、哲学和艺术蓬勃发展的黄金时代`}</p>
                </div>
            </div>
            
            <!-- AI生成的历史场景 -->
            ${sceneData ? `
                <div class="generated-scene-card">
                    <div class="scene-header">
                        <h3>🎨 AI重现历史场景</h3>
                        <div class="generation-info">
                            <span class="model-badge">${sceneData.generation_model}</span>
                            ${sceneData.demo_mode ? '<span class="demo-badge">演示模式</span>' : ''}
                        </div>
                    </div>
                    
                    ${sceneData.images && sceneData.images.length > 0 ? `
                        <div class="scene-image-container">
                            <img src="${sceneData.images[0]}" 
                                 alt="Historical scene of ${historicalInfo.political_entity}" 
                                 class="historical-scene-image"
                                 onclick="openHistoricalImageModal('${sceneData.images[0]}', '${historicalInfo.political_entity}', ${historicalInfo.query_year})">
                            <div class="image-watermark">🔒 SynthID Protected</div>
                            <div class="image-overlay">
                                <span class="zoom-hint">🔍 点击查看大图</span>
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="scene-description">
                        <h4>📝 AI场景解析</h4>
                        <div class="description-text">${sceneData.scene_description}</div>
                    </div>
                    
                    <div class="generation-stats">
                        <div class="stat-item">
                            <span class="stat-label">⚡ 生成耗时:</span>
                            <span class="stat-value">${sceneData.generation_time ? sceneData.generation_time.toFixed(2) : '0.00'}秒</span>
                        </div>
                        ${sceneData.image_count ? `
                            <div class="stat-item">
                                <span class="stat-label">🖼️ 图片数量:</span>
                                <span class="stat-value">${sceneData.image_count}张</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : `
                <div class="scene-error-card">
                    <h3>❌ 场景生成失败</h3>
                    <p>${sceneData ? sceneData.error : '未知错误'}</p>
                    <button onclick="retryHistoricalExploration()" class="retry-btn">
                        🔄 重新生成
                    </button>
                </div>
            `}
            
            <!-- AI历史锐评 -->
            ${data.ai_review ? `
                <div class="historical-review-card">
                    <div class="review-header">
                        <h3>🤖 AI历史文化锐评</h3>
                        <span class="ai-badge">Powered by Langchain</span>
                    </div>
                    <div class="review-content">
                        <h4 class="review-title">${data.ai_review.title || '历史文化分析'}</h4>
                        <div class="review-text">${data.ai_review.review || ''}</div>
                        
                        ${data.ai_review.highlights && data.ai_review.highlights.length > 0 ? `
                            <div class="review-highlights">
                                <h5>✨ 文化亮点</h5>
                                <div class="highlights-list">
                                    ${data.ai_review.highlights.map(highlight => 
                                        `<span class="highlight-tag">${highlight}</span>`
                                    ).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="review-footer">
                            ${data.ai_review.tips ? `
                                <div class="review-tips">
                                    <span class="tips-label">💡 历史小贴士:</span>
                                    <span class="tips-content">${data.ai_review.tips}</span>
                                </div>
                            ` : ''}
                            
                            ${data.ai_review.rating_reason ? `
                                <div class="review-rating">
                                    <span class="rating-label">🎯 推荐理由:</span>
                                    <span class="rating-content">${data.ai_review.rating_reason}</span>
                                </div>
                            ` : ''}
                            
                            ${data.ai_review.mood ? `
                                <div class="review-mood">
                                    <span class="mood-label">🎭 适合心情:</span>
                                    <span class="mood-content">${data.ai_review.mood}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <!-- 操作按钮 -->
            <div class="historical-actions">
                <button class="action-btn featured" onclick="endHistoricalJourney()">
                    🏁 结束旅途
                </button>
                <button class="action-btn primary" onclick="exploreAnotherPeriod()">
                    ⏰ 探索其他时期
                </button>
                <button class="action-btn secondary" onclick="shareHistoricalScene()">
                    📤 分享发现
                </button>
                <button class="action-btn" onclick="returnToRegularMode()">
                    🌍 返回常规模式
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = sceneHtml;
    
    // 🚀 新增：自动收集当前历史场景到旅程记录
    addToVisitedScenes(historicalInfo, sceneData);
    
    // 滚动到结果
    setTimeout(() => {
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    logger.success('🎨 历史场景展示完成');
}

/**
 * 自定义年份输入处理
 */
function handleCustomYearInput() {
    const customYearInput = document.getElementById('customYearInput');
    const selectedYearSpan = document.getElementById('selectedYear');
    const timeTravelBtn = document.getElementById('timeTravelBtn');
    
    if (customYearInput) {
        customYearInput.addEventListener('input', function() {
            const year = parseInt(this.value);
            
            if (!isNaN(year) && year >= -3000 && year <= 2024) {
                selectedHistoricalYear = year;
                
                if (year < 0) {
                    selectedYearSpan.textContent = `公元前${Math.abs(year)}年`;
                } else {
                    selectedYearSpan.textContent = `公元${year}年`;
                }
                
                timeTravelBtn.disabled = false;
                logger.info(`📅 自定义历史年份: ${selectedHistoricalYear}`);
            } else {
                selectedHistoricalYear = null;
                selectedYearSpan.textContent = '无效年份';
                timeTravelBtn.disabled = true;
            }
        });
    }
}

/**
 * 重试历史探索
 */
async function retryHistoricalExploration() {
    logger.info('🔄 重试历史探索...');
    await startHistoricalExploration();
}

/**
 * 探索其他时期
 */
function exploreAnotherPeriod() {
    // 清理当前结果
    clearHistoricalResults();
    
    // 重置年份选择
    document.getElementById('historicalPeriod').value = '';
    document.getElementById('selectedYear').textContent = '未选择';
    document.getElementById('timeTravelBtn').disabled = true;
    selectedHistoricalYear = null;
    
    logger.info('🔄 准备探索其他历史时期');
    showSuccess('📅 请选择新的历史时期继续探索');
}

/**
 * 分享历史场景
 */
function shareHistoricalScene() {
    if (!currentHistoricalInfo || !historicalSceneData) {
        showError('没有可分享的历史场景');
        return;
    }
    
    const shareText = `🏛️ 发现了${currentHistoricalInfo.query_year}年的${currentHistoricalInfo.political_entity}！
    
📍 位置: ${currentHistoricalInfo.coordinates.lat.toFixed(4)}, ${currentHistoricalInfo.coordinates.lng.toFixed(4)}
🎭 时代: ${currentHistoricalInfo.time_period}
👑 统治者: ${currentHistoricalInfo.ruler_or_power}

通过OrientDiscover的时光机功能，我穿越到了${currentHistoricalInfo.query_year}年，体验了真实的历史场景！

#OrientDiscover #时空探索 #历史可视化`;
    
    if (navigator.share) {
        navigator.share({
            title: `时空探索发现：${currentHistoricalInfo.political_entity}`,
            text: shareText,
            url: window.location.href
        }).then(() => {
            logger.info('📤 历史场景已分享');
        }).catch((error) => {
            logger.warning(`分享失败: ${error.message}`);
            copyToClipboard(shareText);
        });
    } else {
        copyToClipboard(shareText);
    }
}

/**
 * 返回常规模式
 */
function returnToRegularMode() {
    // 关闭历史模式
    if (isHistoricalMode) {
        toggleHistoricalMode();
    }
    
    // 清理历史结果
    clearHistoricalResults();
    
    logger.info('🌍 已返回常规探索模式');
}

/**
 * 清理历史结果显示
 */
function clearHistoricalResults() {
    const container = document.getElementById('placesContainer');
    if (container) {
        container.innerHTML = '';
    }
    
    currentHistoricalInfo = null;
    historicalSceneData = null;
}

/**
 * 打开历史图片模态框
 */
function openHistoricalImageModal(imageUrl, entityName, year) {
    // 创建图片查看模态框
    const modalHtml = `
        <div class="historical-image-modal" id="historicalImageModal" onclick="closeHistoricalImageModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>🏛️ ${entityName} - ${year}年</h3>
                    <button class="close-btn" onclick="closeHistoricalImageModal()">✕</button>
                </div>
                <div class="modal-body">
                    <img src="${imageUrl}" alt="Historical scene" class="modal-image">
                    <div class="image-caption">
                        <p>🎨 由Nano Banana AI生成的历史场景</p>
                        <p>🔒 包含SynthID水印保护</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    logger.info(`🖼️ 打开历史图片查看: ${entityName}`);
}

/**
 * 关闭历史图片模态框
 */
function closeHistoricalImageModal() {
    const modal = document.getElementById('historicalImageModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * 复制到剪贴板
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('📤 内容已复制到剪贴板');
        logger.info('📤 历史场景信息已复制');
    }).catch((error) => {
        logger.warning(`复制失败: ${error.message}`);
    });
}

/**
 * 获取历史边界精度文本
 */
function getHistoricalPrecisionText(precision) {
    switch(precision) {
        case 1: return '大致边界 (历史记录模糊)';
        case 2: return '中等精度 (有一定史料支撑)';
        case 3: return '高精度 (国际法或条约确定)';
        default: return `未知精度 (${precision})`;
    }
}

// 页面加载完成后初始化历史模式
document.addEventListener('DOMContentLoaded', function() {
    // 初始化自定义年份输入处理
    setTimeout(() => {
        handleCustomYearInput();
    }, 100);
});

// 全局暴露历史模式功能
window.toggleHistoricalMode = toggleHistoricalMode;
window.updateHistoricalYear = updateHistoricalYear;
window.startHistoricalExploration = startHistoricalExploration;
window.retryHistoricalExploration = retryHistoricalExploration;
window.exploreAnotherPeriod = exploreAnotherPeriod;
window.shareHistoricalScene = shareHistoricalScene;
window.returnToRegularMode = returnToRegularMode;
window.openHistoricalImageModal = openHistoricalImageModal;
window.closeHistoricalImageModal = closeHistoricalImageModal;

// ================ 历史场景模板选择功能 ================

// 场景模板全局变量
let selectedHistoricalTemplate = null;
let historicalSceneTemplates = [];

/**
 * 加载历史场景模板
 */
async function loadHistoricalSceneTemplates() {
    try {
        const response = await fetch(API_CONFIG.getApiUrl('/api/scene-templates'));
        const data = await response.json();
        
        if (data.success) {
            historicalSceneTemplates = data.templates;
            displayHistoricalSceneTemplateButtons(data.templates);
            logger.info('✅ 历史场景模板加载成功:', data.templates.length + '个模板');
        } else {
            console.error('❌ 历史场景模板加载失败');
            document.getElementById('historicalSceneTemplateButtons').innerHTML = '<div style="color: #999;">暂无可用模板</div>';
        }
    } catch (error) {
        console.error('❌ 历史场景模板加载错误:', error);
        document.getElementById('historicalSceneTemplateButtons').innerHTML = '<div style="color: #999;">模板加载失败</div>';
    }
}

/**
 * 显示历史场景模板按钮
 */
function displayHistoricalSceneTemplateButtons(templates) {
    const container = document.getElementById('historicalSceneTemplateButtons');
    container.innerHTML = '';
    
    templates.forEach(template => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'historical-template-btn';
        button.setAttribute('data-template-id', template.id);
        
        button.innerHTML = `
            <div class="template-name">${template.name}</div>
            <div class="template-desc">${template.description}</div>
        `;
        
        button.onclick = () => selectHistoricalTemplate(template.id, template.name);
        
        container.appendChild(button);
    });
    
    logger.info('🎨 历史场景模板按钮显示完成:', templates.length + '个');
}

/**
 * 选择历史场景模板
 */
function selectHistoricalTemplate(templateId, templateName) {
    selectedHistoricalTemplate = templateId;
    
    // 更新UI显示选中状态
    document.querySelectorAll('.historical-template-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    const selectedBtn = document.querySelector(`[data-template-id="${templateId}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }
    
    // 显示选中的模板
    document.getElementById('selectedHistoricalTemplate').textContent = templateName;
    
    logger.info('📋 已选择历史场景模板:', templateName + ' (' + templateId + ')');
}

/**
 * 清除历史场景模板选择
 */
function clearHistoricalTemplate() {
    selectedHistoricalTemplate = null;
    
    // 清除选中状态
    document.querySelectorAll('.historical-template-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // 更新显示
    document.getElementById('selectedHistoricalTemplate').textContent = '无';
    
    logger.info('🧹 已清除历史场景模板选择');
}

// 暴露历史场景模板功能到全局
window.loadHistoricalSceneTemplates = loadHistoricalSceneTemplates;
window.selectHistoricalTemplate = selectHistoricalTemplate;
window.clearHistoricalTemplate = clearHistoricalTemplate;

// ================ 时光自拍功能 ================

// 自拍功能全局变量
let visitedHistoricalScenes = []; // 已访问的历史场景记录
let currentSelfieData = null;     // 当前自拍数据
let journeyStartTime = null;      // 旅途开始时间

// 新的meme创作流程变量
let selectedSceneForMeme = null;  // 选中的场景数据
let extractedSceneElements = [];  // 提取的场景元素
let selectedMemeTemplate = null;  // 选中的meme模板
let uploadedCharacterImage = null; // 上传的角色图片
let uploadedCompositionImage = null; // 上传的构图图片
let uploadedCompanionImage = null;   // 上传的虚拟伙伴图片

// 异步场景分析状态管理
let sceneAnalysisPromise = null;  // 场景分析的Promise
let isSceneAnalysisComplete = false; // 分析是否完成
let analysisStartTime = null;     // 分析开始时间

// 互动选择状态管理
let selectedInteractionId = null; // 选中的互动ID
let selectedInteractionName = null; // 选中的互动名称
let availableInteractions = null;  // 可用的互动数据

/**
 * 结束历史旅途，直接进入场景选择
 */
function endHistoricalJourney() {
    logger.info('🏁 用户选择结束历史旅途，开始meme创作流程');
    
    // 显示自拍面板，隐藏当前场景
    const container = document.getElementById('placesContainer');
    const selfiePanel = document.getElementById('historicalSelfiePanel');
    
    if (container) container.style.display = 'none';
    if (selfiePanel) selfiePanel.style.display = 'block';
    
    // 直接显示步骤1：场景选择
    showStep('step1SceneSelection');
    
    // 填充已访问的场景
    populateVisitedScenes();
    
    logger.info('🏛️ 开始步骤1：场景选择');
}

/**
 * 步骤管理函数（3步流程：场景选择→模板选择→图片上传）
 */
function showStep(stepId) {
    // 隐藏所有步骤
    const steps = ['step1SceneSelection', 'step2TemplateSelection', 'step3ImageUpload'];
    steps.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.style.display = 'none';
    });
    
    // 显示指定步骤
    const targetStep = document.getElementById(stepId);
    if (targetStep) {
        targetStep.style.display = 'block';
        logger.info(`📋 切换到步骤: ${stepId}`);
    }
}

/**
 * 开始历史自拍流程（兼容旧版本调用）
 */
function startHistoricalSelfie() {
    logger.info('📸 用户选择进行时光自拍（通过新流程）');
    
    // 使用新的步骤流程
    showStep('step1SceneSelection');
    
    // 填充已访问的场景
    populateVisitedScenes();
}

/**
 * 跳过自拍，直接进入旅途总结
 */
function skipSelfie() {
    logger.info('❌ 用户跳过自拍，直接总结旅途');
    
    // 直接显示旅途总结
    showHistoricalJourneySummary();
}

/**
 * 填充已访问的历史场景选择器
 */
function populateVisitedScenes() {
    const container = document.getElementById('visitedScenes');
    
    if (!container) {
        logger.error('❌ 找不到场景选择器容器');
        return;
    }
    
    // 场景已通过 addToVisitedScenes() 自动收集，无需手动添加
    if (visitedHistoricalScenes.length === 0) {
        container.innerHTML = `
            <div class="no-scenes-message">
                <h4>🏃‍♂️ 开始您的历史之旅</h4>
                <p>访问历史场景后，这里将显示您的旅程记录</p>
            </div>
        `;
        return;
    }
    
    const scenesHtml = visitedHistoricalScenes.map((scene, index) => `
        <div class="scene-card selectable" onclick="selectSelfieScene(${index})">
            <div class="scene-preview">
                ${scene.scene_data && scene.scene_data.images ? 
                    `<img src="${scene.scene_data.images[0]}" alt="${scene.political_entity}" class="scene-thumb">` :
                    `<div class="scene-placeholder">🏛️</div>`
                }
            </div>
            <div class="scene-info">
                <h5>${scene.political_entity}</h5>
                <p>${scene.year}年</p>
                <p class="scene-desc">${scene.description.substring(0, 50)}...</p>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = scenesHtml;
    logger.info(`🏛️ 显示 ${visitedHistoricalScenes.length} 个已访问场景`);
}

/**
 * 选择场景进行meme创作（异步分析版本）
 */
function selectSelfieScene(sceneIndex) {
    const scene = visitedHistoricalScenes[sceneIndex];
    if (!scene) {
        logger.error('❌ 无效的场景索引');
        return;
    }
    
    selectedSceneForMeme = scene;
    logger.info(`🎯 用户选择场景: ${scene.political_entity} (${scene.year}年)`);
    
    // 🔄 启动后台异步场景分析（用户无感知）
    startBackgroundSceneAnalysis(scene);
    
    // 🚀 直接进入模板选择步骤（跳过分析界面）
    showStep('step2TemplateSelection'); // 更新步骤编号
    loadMemeTemplatesForHistory();
    
    logger.info('🎨 直接进入模板选择，场景分析在后台进行');
}

/**
 * 启动后台场景分析（异步，用户无感知）
 */
function startBackgroundSceneAnalysis(scene) {
    if (!scene.scene_data || !scene.scene_data.images) {
        logger.warning('⚠️ 场景没有图片，跳过分析');
        isSceneAnalysisComplete = true;
        extractedSceneElements = ['历史建筑', '传统服饰', '古代氛围']; // 使用默认元素
        return;
    }
    
    const imageUrl = scene.scene_data.images[0];
    analysisStartTime = Date.now();
    isSceneAnalysisComplete = false;
    extractedSceneElements = [];
    
    logger.info(`🔍 后台启动场景分析: ${imageUrl}`);
    
    // 创建异步分析Promise
    sceneAnalysisPromise = analyzeSceneInBackground(imageUrl)
        .then(elements => {
            extractedSceneElements = elements;
            isSceneAnalysisComplete = true;
            const analysisTime = (Date.now() - analysisStartTime) / 1000;
            logger.success(`✅ 后台场景分析完成 (${analysisTime.toFixed(1)}s)，提取到 ${elements.length} 个元素`);
            
            // 可选：在控制台显示分析结果（开发调试用）
            console.log('🎨 分析元素:', elements.join(', '));
        })
        .catch(error => {
            logger.warning(`⚠️ 后台场景分析失败，使用默认元素: ${error.message}`);
            extractedSceneElements = ['历史建筑', '传统服饰', '古代氛围', '历史场景']; // 使用后备元素
            isSceneAnalysisComplete = true;
        });
}

/**
 * 后台场景分析的实际执行函数
 */
async function analyzeSceneInBackground(imageUrl) {
    const response = await fetch(API_CONFIG.getApiUrl('/api/analyze-scene-elements'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_url: imageUrl
        })
    });
    
    if (!response.ok) {
        throw new Error(`分析失败: HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.success) {
        return data.elements;
    } else {
        throw new Error(data.error || '场景分析失败');
    }
}

/**
 * 显示选中场景的预览
 */
function displaySelectedScenePreview(scene) {
    const previewContainer = document.getElementById('selectedScenePreview');
    if (!previewContainer) return;
    
    const imageUrl = scene.scene_data && scene.scene_data.images ? scene.scene_data.images[0] : null;
    
    previewContainer.innerHTML = `
        <div class="scene-preview-card">
            ${imageUrl ? 
                `<img src="${imageUrl}" alt="${scene.political_entity}" />` :
                `<div class="scene-placeholder">🏛️ ${scene.political_entity}</div>`
            }
            <h4>${scene.political_entity}</h4>
            <p>${scene.year}年 • ${scene.description.substring(0, 80)}...</p>
        </div>
    `;
}


/**
 * 生成历史自拍（调用后端API）
 */
async function generateHistoricalSelfie(scene) {
    try {
        showLoading(true, '🤳 正在生成您的时光自拍...');
        
        // 🔍 调试：检查scene数据结构
        console.log('🔍 Scene数据结构:', scene);
        console.log('🔍 Political entity:', scene.political_entity);
        console.log('🔍 Year:', scene.year);
        console.log('🔍 Query year:', scene.query_year);
        
        // 调用后端自拍生成API
        const requestData = {
            scene_id: `${scene.political_entity}_${scene.year || scene.query_year}`,
            political_entity: scene.political_entity,
            year: scene.year || scene.query_year,  // 兼容两种字段名
            user_image: null  // 演示模式不需要用户图片
        };
        
        console.log('📤 发送请求数据:', requestData);
        
        const response = await fetch(API_CONFIG.getApiUrl('/api/generate-historical-selfie'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 🔍 调试：检查返回数据
        console.log('📤 后端返回数据:', data);
        console.log('📤 Scene info:', data.scene_info);
        
        if (data.success) {
            const selfieImage = document.getElementById('selfieImage');
            const selfieDescription = document.getElementById('selfieDescription');
            
            // 显示生成的自拍照片
            if (selfieImage && data.selfie_url) {
                selfieImage.src = data.selfie_url;
                selfieImage.style.display = 'block';
            }
            
            // 更新描述信息
            if (selfieDescription && data.scene_info) {
                // 🛡️ 防御性编程：确保数据不为undefined
                const politicalEntity = data.scene_info.political_entity || scene.political_entity || 'Unknown';
                const year = data.scene_info.year || scene.year || scene.query_year || 'Unknown';
                
                selfieDescription.innerHTML = `
                    <p>🎉 太棒了！您与 <strong>${politicalEntity}</strong> (${year}年) 的时光自拍已生成！</p>
                    <p class="selfie-note">✨ ${data.demo_mode ? '演示模式：使用预设时光旅行者角色' : '实时生成模式'}</p>
                    <p class="selfie-note">⚡ 生成时间: ${data.generation_time ? data.generation_time.toFixed(2) : '0.10'}秒</p>
                `;
            }
            
            // 保存自拍数据
            currentSelfieData = {
                scene: scene,
                image_url: data.selfie_url,
                generated_time: new Date().toISOString(),
                demo_mode: data.demo_mode,
                api_response: data
            };
            
            logger.success(`🤳 ${scene.political_entity} 时光自拍生成完成`);
            
        } else {
            throw new Error(data.error || '自拍生成失败');
        }
        
    } catch (error) {
        logger.error(`❌ 自拍生成失败: ${error.message}`);
        showError(`自拍生成失败: ${error.message}`);
        
        // 演示模式失败时的备用方案
        const selfieImage = document.getElementById('selfieImage');
        const selfieDescription = document.getElementById('selfieDescription');
        
        if (selfieImage) {
            selfieImage.src = API_CONFIG.getApiUrl('/static/take_photo/0b8459cf-b5ce-4c44-b3e3-352abe04d2de.jpg');
            selfieImage.style.display = 'block';
        }
        
        if (selfieDescription) {
            // 🛡️ 防御性编程：确保备用方案也不显示undefined
            const politicalEntity = scene.political_entity || 'Unknown';
            const year = scene.year || scene.query_year || 'Unknown';
            
            selfieDescription.innerHTML = `
                <p>🎭 使用备用演示自拍（API调用失败）</p>
                <p class="selfie-note">✨ 与 ${politicalEntity} (${year}年) 的时光合影</p>
            `;
        }
        
    } finally {
        showLoading(false);
    }
}

/**
 * 继续到旅途总结
 */
function continueToSummary() {
    logger.info('📖 进入旅途总结');
    showHistoricalJourneySummary();
}

/**
 * 显示历史时光旅途总结
 */
function showHistoricalJourneySummary() {
    // 隐藏所有meme创作步骤
    const steps = ['step1SceneSelection', 'step2TemplateSelection', 'step3ImageUpload'];
    steps.forEach(stepId => {
        const element = document.getElementById(stepId);
        if (element) element.style.display = 'none';
    });
    
    // 隐藏自拍结果
    const selfieResult = document.getElementById('selfieResult');
    if (selfieResult) selfieResult.style.display = 'none';
    
    // 显示总结界面
    const journeySummary = document.getElementById('journeySummary');
    if (journeySummary) {
        journeySummary.style.display = 'block';
        // 填充总结内容
        populateJourneySummary();
        logger.info('📖 历史旅途总结已显示');
    } else {
        logger.error('❌ 找不到journeySummary元素');
    }
}

/**
 * 填充旅途总结内容
 */
function populateJourneySummary() {
    // 填充访问地点
    const placesContainer = document.getElementById('summaryPlaces');
    const selfieContainer = document.getElementById('journeySelfie');
    const textContainer = document.getElementById('journeyText');
    
    // 访问地点总结
    if (placesContainer && visitedHistoricalScenes.length > 0) {
        const placesHtml = `
            <h4>🗺️ 时空足迹</h4>
            <div class="visited-places-grid">
                ${visitedHistoricalScenes.map(scene => `
                    <div class="summary-scene-card">
                        <div class="scene-year">${scene.year}年</div>
                        <div class="scene-name">${scene.political_entity}</div>
                    </div>
                `).join('')}
            </div>
        `;
        placesContainer.innerHTML = placesHtml;
    }
    
    // 自拍照片
    if (selfieContainer && currentSelfieData) {
        const selfieHtml = `
            <h4>📸 时光留影</h4>
            <div class="summary-selfie">
                <img src="${currentSelfieData.image_url}" alt="时光自拍" class="summary-selfie-image">
                <p class="selfie-caption">与 ${currentSelfieData.scene.political_entity} (${currentSelfieData.scene.year}年) 的珍贵合影</p>
            </div>
        `;
        selfieContainer.innerHTML = selfieHtml;
    }
    
    // AI生成的旅途总结文字
    if (textContainer) {
        const summaryText = generateJourneySummaryText();
        textContainer.innerHTML = `
            <h4>✨ 旅途感悟</h4>
            <div class="journey-summary-text">
                ${summaryText}
            </div>
        `;
    }
    
    logger.success('📖 旅途总结已生成');
}

/**
 * 生成旅途总结文字
 */
function generateJourneySummaryText() {
    if (visitedHistoricalScenes.length === 0) {
        return '<p>这是一次短暂但精彩的时空探索之旅！</p>';
    }
    
    const totalScenes = visitedHistoricalScenes.length;
    const yearSpan = visitedHistoricalScenes.length > 1 ? 
        Math.abs(visitedHistoricalScenes[visitedHistoricalScenes.length-1].year - visitedHistoricalScenes[0].year) : 0;
    
    const hasSelfie = currentSelfieData ? '还与历史时刻留下了珍贵合影' : '体验了历史文化的魅力';
    
    return `
        <p>🌟 在这次奇妙的时光穿越之旅中，您探索了 <strong>${totalScenes}</strong> 个历史时空点，${yearSpan > 0 ? `跨越了 ${yearSpan} 年的历史长河，` : ''}${hasSelfie}。</p>
        
        <p>💫 从 ${visitedHistoricalScenes.map(s => `${s.political_entity}(${s.year}年)`).join(' 到 ')}，每一个历史瞬间都诉说着人类文明的辉煌篇章。</p>
        
        ${currentSelfieData ? `
            <p>📸 特别值得纪念的是，您与 <strong>${currentSelfieData.scene.political_entity}</strong> 的时光合影将永远见证这次跨越时空的奇妙邂逅！</p>
        ` : ''}
        
        <p>🚀 感谢您使用 OrientDiscover 进行时光探索，期待下次与您一起穿越历史的长河！</p>
    `;
}

/**
 * 分享自拍照片
 */
function shareSelfie() {
    if (!currentSelfieData) {
        showError('没有可分享的自拍照片');
        return;
    }
    
    const shareText = `我刚刚与${currentSelfieData.scene.political_entity}(${currentSelfieData.scene.year}年)进行了时光自拍！#OrientDiscover #时光穿越`;
    
    if (navigator.share) {
        navigator.share({
            title: '时光自拍 - OrientDiscover',
            text: shareText,
            url: currentSelfieData.image_url
        });
    } else {
        copyToClipboard(shareText + ' ' + currentSelfieData.image_url);
        showSuccess('🔗 自拍信息已复制到剪贴板');
    }
    
    logger.info('📤 用户分享时光自拍');
}

/**
 * 开始新旅途
 */
function startNewJourney() {
    // 重置所有状态
    visitedHistoricalScenes = [];
    currentSelfieData = null;
    journeyStartTime = new Date();
    
    // 隐藏自拍面板
    document.getElementById('historicalSelfiePanel').style.display = 'none';
    
    // 显示主界面
    const container = document.getElementById('placesContainer');
    if (container) {
        container.style.display = 'block';
        container.innerHTML = '<p>🚀 准备开始新的时光探索之旅...</p>';
    }
    
    logger.info('🚀 开始新的历史探索旅途');
    showSuccess('🌟 新的时光探索之旅即将开始！');
}

/**
 * 分享完整旅途
 */
function shareJourney() {
    const scenesText = visitedHistoricalScenes.map(s => `${s.political_entity}(${s.year}年)`).join(', ');
    const shareText = `我刚完成了一次精彩的时光穿越！探索了：${scenesText}。${currentSelfieData ? '还留下了珍贵的时光自拍！' : ''} #OrientDiscover #历史探索`;
    
    if (navigator.share) {
        navigator.share({
            title: '时光穿越旅途 - OrientDiscover',
            text: shareText
        });
    } else {
        copyToClipboard(shareText);
        showSuccess('🔗 旅途信息已复制到剪贴板');
    }
    
    logger.info('📤 用户分享完整旅途');
}

/**
 * 返回自拍询问
 */
function backToSelfieQuestion() {
    // 在新流程中，这个函数等同于返回场景选择
    showStep('step1SceneSelection');
    logger.info('🔙 返回场景选择');
}

// ========================================
// 头像上传功能
// ========================================

/**
 * 触发头像文件选择
 */
function triggerAvatarUpload() {
    const fileInput = document.getElementById('avatarUpload');
    if (fileInput) {
        fileInput.click();
    }
}

/**
 * 处理头像文件上传
 * @param {Event} event - 文件选择事件
 */
async function handleAvatarUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 文件大小检查 (最大5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('文件大小不能超过5MB，请选择较小的图片！');
        return;
    }

    // 文件类型检查
    if (!file.type.startsWith('image/')) {
        alert('请选择有效的图片文件！');
        return;
    }

    try {
        console.log('📸 开始上传头像...', file.name);

        // 创建FormData
        const formData = new FormData();
        formData.append('avatar', file);

        // 显示上传中的状态
        const avatarImage = document.getElementById('avatarImage');
        const originalSrc = avatarImage.src;
        avatarImage.style.opacity = '0.5';
        
        // 上传到后端
        const response = await fetch(API_CONFIG.getApiUrl('/api/upload-avatar'), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`上传失败: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ 头像上传成功:', result);

        // 更新头像显示
        if (result.avatar_url) {
            avatarImage.src = result.avatar_url;
            avatarImage.style.opacity = '1';
            
            // 添加时间戳防止缓存
            const timestamp = new Date().getTime();
            avatarImage.src = `${result.avatar_url}?t=${timestamp}`;
            
            console.log('🖼️ 头像已更新:', avatarImage.src);
        }
        
        // 成功提示
        showNotification('头像上传成功！✨', 'success');

    } catch (error) {
        console.error('❌ 头像上传失败:', error);
        
        // 恢复原始状态
        const avatarImage = document.getElementById('avatarImage');
        avatarImage.style.opacity = '1';
        
        // 错误提示
        showNotification('头像上传失败，请重试！😢', 'error');
    }

    // 清空input值，允许重复选择同一文件
    event.target.value = '';
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        opacity: 0;
        transition: all 0.3s ease;
        ${type === 'success' ? 'background: linear-gradient(45deg, #4CAF50, #45a049);' : ''}
        ${type === 'error' ? 'background: linear-gradient(45deg, #f44336, #da190b);' : ''}
        ${type === 'info' ? 'background: linear-gradient(45deg, #2196F3, #0b7dda);' : ''}
    `;
    
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 100);
    
    // 3秒后自动消失
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// ================ 新的meme创作步骤功能 ================

/**
 * 进入模板选择步骤
 */
function proceedToTemplateSelection() {
    showStep('step2TemplateSelection');
    loadMemeTemplatesForHistory();
    logger.info('🎨 进入步骤2：meme模板选择');
}

/**
 * 返回场景选择（移除了场景分析步骤）
 */
function backToSceneSelection() {
    showStep('step1SceneSelection');
    selectedMemeTemplate = null;
    selectedSceneForMeme = null;
    extractedSceneElements = [];
    isSceneAnalysisComplete = false;
    sceneAnalysisPromise = null;
    
    // 清除互动选择
    selectedInteractionId = null;
    selectedInteractionName = null;
    
    // 清除图片上传状态
    uploadedCharacterImage = null;
    uploadedCompositionImage = null;
    uploadedCompanionImage = null;
    
    // 隐藏模板选择信息
    document.getElementById('selectedTemplateInfo').style.display = 'none';
    
    logger.info('🔄 已重置到场景选择，清除所有状态');
}

/**
 * 加载历史模式的meme模板
 */
async function loadMemeTemplatesForHistory() {
    try {
        const response = await fetch(API_CONFIG.getApiUrl('/api/meme-templates'));
        const data = await response.json();
        
        if (data.success) {
            displayHistoricalMemeTemplateButtons(data.templates);
            logger.info('✅ 历史meme模板加载成功:', data.templates.length + '个模板');
        } else {
            console.error('❌ meme模板加载失败');
            document.getElementById('historicalMemeTemplateButtons').innerHTML = '<div style="color: #999;">暂无可用模板</div>';
        }
    } catch (error) {
        console.error('❌ meme模板加载错误:', error);
        document.getElementById('historicalMemeTemplateButtons').innerHTML = '<div style="color: #999;">模板加载失败</div>';
    }
}

/**
 * 显示历史meme模板按钮
 */
function displayHistoricalMemeTemplateButtons(templates) {
    const container = document.getElementById('historicalMemeTemplateButtons');
    container.innerHTML = '';
    
    templates.forEach(template => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'meme-template-btn-new';
        button.setAttribute('data-meme-template-id', template.id);
        
        button.innerHTML = `
            <div class="template-name-new">${template.name}</div>
            <div class="template-desc-new">${template.description}</div>
        `;
        
        button.onclick = () => selectMemeTemplateForHistory(template.id, template.name);
        
        container.appendChild(button);
    });
    
    logger.info('🎨 历史meme模板按钮显示完成:', templates.length + '个');
}

/**
 * 选择meme模板
 */
function selectMemeTemplateForHistory(templateId, templateName) {
    selectedMemeTemplate = templateId;
    
    // 更新UI显示选中状态
    document.querySelectorAll('.meme-template-btn-new').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    const selectedBtn = document.querySelector(`[data-meme-template-id="${templateId}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }
    
    // 显示选中信息
    const infoDiv = document.getElementById('selectedTemplateInfo');
    const displaySpan = document.getElementById('selectedTemplateDisplay');
    displaySpan.textContent = templateName;
    infoDiv.style.display = 'block';
    
    logger.info('📋 已选择meme模板:', templateName + ' (' + templateId + ')');
    
    // 🎭 特殊处理：不同模板的特殊逻辑
    if (templateId === 'interactive_selfie') {
        logger.info('🎭 检测到强互动模板，打开互动选择窗口');
        // 先禁用下一步按钮，等待互动选择
        document.getElementById('nextToUploadBtn').disabled = true;
        openInteractionModal();
    } else if (templateId === 'anime_selfie') {
        logger.info('🎨 检测到二次元模板，打开互动选择窗口');
        console.log('🔍 Debug: anime_selfie 模板被选中，即将打开互动模态框');
        // 先禁用下一步按钮，等待互动选择
        document.getElementById('nextToUploadBtn').disabled = true;
        openInteractionModal();
    } else if (templateId === 'selfie_with_anime') {
        logger.info('🎭 检测到和二次元穿越模板，打开专用互动选择窗口');
        // 先禁用下一步按钮，等待互动选择
        document.getElementById('nextToUploadBtn').disabled = true;
        openInteractionModalWithAnime();
    } else if (templateId === 'virtual_companion') {
        logger.info('🧸 检测到虚拟伙伴模板，将在图片上传步骤显示虚拟伙伴上传区域');
        // 直接启用下一步按钮
        document.getElementById('nextToUploadBtn').disabled = false;
        // 清除之前的互动选择
        selectedInteractionId = null;
        selectedInteractionName = null;
    } else {
        // 其他模板直接启用下一步按钮
        document.getElementById('nextToUploadBtn').disabled = false;
        // 清除之前的互动选择
        selectedInteractionId = null;
        selectedInteractionName = null;
    }
}

/**
 * 清除meme模板选择
 */
function clearMemeTemplateSelection() {
    selectedMemeTemplate = null;
    
    // 清除选中状态
    document.querySelectorAll('.meme-template-btn-new').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // 隐藏选中信息
    document.getElementById('selectedTemplateInfo').style.display = 'none';
    
    // 清除互动选择
    selectedInteractionId = null;
    selectedInteractionName = null;
    
    // 清除图片上传状态
    uploadedCharacterImage = null;
    uploadedCompositionImage = null;
    uploadedCompanionImage = null;
    
    // 禁用下一步按钮
    document.getElementById('nextToUploadBtn').disabled = true;
    
    logger.info('🧹 已清除meme模板、互动选择和图片上传状态');
}

/**
 * 返回模板选择
 */
function backToTemplateSelection() {
    showStep('step2TemplateSelection');
    
    // 重置所有图片状态
    uploadedCharacterImage = null;
    uploadedCompositionImage = null;
    uploadedCompanionImage = null;
    
    // 重置人物素材上传区域
    const characterUploadArea = document.getElementById('characterUploadArea');
    const characterPreviewArea = document.getElementById('characterPreviewArea');
    if (characterUploadArea) characterUploadArea.classList.remove('has-image');
    if (characterPreviewArea) {
        characterPreviewArea.innerHTML = `
            <p>📁 点击上传人物图片</p>
            <small>支持 JPG, PNG 格式</small>
        `;
    }
    
    // 重置构图素材上传区域
    const compositionUploadArea = document.getElementById('compositionUploadArea');
    const compositionPreviewArea = document.getElementById('compositionPreviewArea');
    if (compositionUploadArea) compositionUploadArea.classList.remove('has-image');
    if (compositionPreviewArea) {
        compositionPreviewArea.innerHTML = `
            <p>📁 点击上传构图图片</p>
            <small>可选，用于指定构图风格</small>
        `;
    }
    
    // 重置虚拟伙伴素材上传区域
    const companionUploadArea = document.getElementById('companionUploadArea');
    const companionPreviewArea = document.getElementById('companionPreviewArea');
    if (companionUploadArea) companionUploadArea.classList.remove('has-image');
    if (companionPreviewArea) {
        companionPreviewArea.innerHTML = `
            <p>🎭 点击上传虚拟伙伴图片</p>
            <small>将制作成玩偶娃娃，推荐卡通角色、宠物或任何想要娃娃化的图片</small>
        `;
    }
    
    logger.info('🔄 已重置所有图片上传状态');
}

/**
 * 进入图片上传步骤
 */
function proceedToImageUpload() {
    showStep('step3ImageUpload');
    
    // 🧸 根据模板类型显示相应的上传区域
    const companionSection = document.getElementById('companionUploadSection');
    
    if (selectedMemeTemplate === 'virtual_companion') {
        // 显示虚拟伙伴上传区域
        if (companionSection) {
            companionSection.style.display = 'block';
            logger.info('🧸 虚拟伙伴模板：显示虚拟伙伴上传区域');
        }
    } else {
        // 隐藏虚拟伙伴上传区域
        if (companionSection) {
            companionSection.style.display = 'none';
        }
    }
    
    logger.info('📷 进入步骤3：图片上传');
}

/**
 * 处理角色图片上传
 */
function handleCharacterImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedCharacterImage = e.target.result;
        
        // 更新预览
        const uploadArea = document.getElementById('characterUploadArea');
        const previewArea = document.getElementById('characterPreviewArea');
        
        uploadArea.classList.add('has-image');
        previewArea.innerHTML = `
            <img src="${e.target.result}" style="max-width: 100%; max-height: 150px; border-radius: 8px;">
            <p style="margin-top: 8px; color: #28a745; font-weight: bold; font-size: 0.8rem;">✅ 人物素材已上传</p>
        `;
        
        // 检查生成按钮状态
        checkMemeGenerationReady();
        
        logger.info('📷 人物素材上传成功');
    };
    reader.readAsDataURL(file);
}

/**
 * 处理构图图片上传
 */
function handleCompositionImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedCompositionImage = e.target.result;
        
        // 更新预览
        const uploadArea = document.getElementById('compositionUploadArea');
        const previewArea = document.getElementById('compositionPreviewArea');
        
        uploadArea.classList.add('has-image');
        previewArea.innerHTML = `
            <img src="${e.target.result}" style="max-width: 100%; max-height: 150px; border-radius: 8px;">
            <p style="margin-top: 8px; color: #007bff; font-weight: bold; font-size: 0.8rem;">✅ 构图素材已上传</p>
        `;
        
        logger.info('🖼️ 构图素材上传成功');
    };
    reader.readAsDataURL(file);
}

/**
 * 处理虚拟伙伴图片上传
 */
function handleCompanionImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedCompanionImage = e.target.result;
        
        // 更新预览
        const uploadArea = document.getElementById('companionUploadArea');
        const previewArea = document.getElementById('companionPreviewArea');
        
        uploadArea.classList.add('has-image');
        previewArea.innerHTML = `
            <img src="${e.target.result}" style="max-width: 100%; max-height: 150px; border-radius: 8px;">
            <p style="margin-top: 8px; color: #ff9800; font-weight: bold; font-size: 0.8rem;">✅ 虚拟伙伴素材已上传</p>
        `;
        
        // 检查生成按钮状态
        checkMemeGenerationReady();
        
        logger.info('🧸 虚拟伙伴素材上传成功');
    };
    reader.readAsDataURL(file);
}

/**
 * 检查meme生成准备状态
 */
function checkMemeGenerationReady() {
    const generateBtn = document.getElementById('generateMemeBtn');
    if (!generateBtn) return;
    
    let isReady = false;
    
    if (selectedMemeTemplate === 'virtual_companion') {
        // 虚拟伙伴模板需要人物素材和虚拟伙伴素材
        isReady = uploadedCharacterImage && uploadedCompanionImage;
    } else {
        // 其他模板只需要人物素材
        isReady = uploadedCharacterImage;
    }
    
    generateBtn.disabled = !isReady;
    
    if (isReady) {
        logger.info('✅ meme生成条件已满足');
    }
}

/**
 * 生成历史meme（智能等待版本）
 */
async function generateHistoricalMeme() {
    if (!selectedSceneForMeme || !selectedMemeTemplate || !uploadedCharacterImage) {
        logger.error('❌ 缺少必要的数据');
        return;
    }
    
    logger.info('🚀 开始生成历史meme');
    
    try {
        // 显示生成进度
        const generateBtn = document.getElementById('generateMemeBtn');
        generateBtn.disabled = true;
        
        // 🎯 智能等待场景分析完成
        if (!isSceneAnalysisComplete) {
            logger.info('⏳ 场景分析尚未完成，等待分析结果...');
            generateBtn.textContent = '⏳ 等待场景分析完成...';
            
            // 等待后台分析完成
            if (sceneAnalysisPromise) {
                await sceneAnalysisPromise;
            }
            
            // 检查是否成功完成
            if (!isSceneAnalysisComplete || extractedSceneElements.length === 0) {
                logger.warning('⚠️ 场景分析超时或失败，使用默认元素');
                extractedSceneElements = ['历史建筑', '传统服饰', '古代氛围', '历史场景'];
            }
            
            const waitTime = (Date.now() - analysisStartTime) / 1000;
            logger.success(`✅ 场景分析等待完成 (${waitTime.toFixed(1)}s)`);
        }
        
        // 现在开始实际的meme生成
        generateBtn.textContent = '🎨 正在生成meme...';
        logger.info(`🎨 使用 ${extractedSceneElements.length} 个场景元素生成meme`);
        
        // 构建请求数据
        const formData = new FormData();
        
        // 🖼️ 人物素材（必需）
        const characterBlob = dataURLtoBlob(uploadedCharacterImage);
        formData.append('character_image', characterBlob);
        logger.info('📷 添加人物素材到请求');
        
        // 🖼️ 构图素材（可选）
        if (uploadedCompositionImage) {
            const compositionBlob = dataURLtoBlob(uploadedCompositionImage);
            formData.append('composition_image', compositionBlob);
            logger.info('🖼️ 添加构图素材到请求');
        }
        
        // 🧸 虚拟伙伴素材（虚拟伙伴模板专用）
        if (uploadedCompanionImage && selectedMemeTemplate === 'virtual_companion') {
            const companionBlob = dataURLtoBlob(uploadedCompanionImage);
            formData.append('companion_image', companionBlob);
            logger.info('🧸 添加虚拟伙伴素材到请求');
        }
        
        formData.append('scene_elements', JSON.stringify(extractedSceneElements));
        formData.append('meme_prompt', `使用${selectedMemeTemplate}模板生成历史meme`);
        formData.append('historical_info', JSON.stringify({
            political_entity: selectedSceneForMeme.political_entity,
            query_year: selectedSceneForMeme.year,
            cultural_region: selectedSceneForMeme.cultural_region || ''
        }));
        formData.append('template_id', selectedMemeTemplate);
        
        // 🎭 如果选择了互动动作，添加到请求中
        if (selectedInteractionId) {
            formData.append('interaction_id', selectedInteractionId);
            logger.info(`🎭 使用互动动作: ${selectedInteractionName} (${selectedInteractionId})`);
        }
        
        const response = await fetch(API_CONFIG.getApiUrl('/api/generate-historical-meme'), {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`meme生成失败: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 保存生成结果
            currentSelfieData = {
                scene: selectedSceneForMeme,
                image_url: data.meme_url,
                generated_time: new Date().toISOString(),
                template_used: selectedMemeTemplate,
                interaction_used: selectedInteractionName,
                elements_used: extractedSceneElements,
                materials_used: {
                    character_image: uploadedCharacterImage ? true : false,
                    composition_image: uploadedCompositionImage ? true : false,
                    companion_image: uploadedCompanionImage ? true : false
                }
            };
            
            // 显示生成结果
            displayMemeResult(data.meme_url);
            
            logger.success('🎉 历史meme生成成功！');
        } else {
            throw new Error(data.error || 'meme生成失败');
        }
        
    } catch (error) {
        logger.error(`❌ meme生成失败: ${error.message}`);
        showError(`meme生成失败: ${error.message}`);
    } finally {
        // 恢复按钮状态
        const generateBtn = document.getElementById('generateMemeBtn');
        generateBtn.textContent = '🚀 生成历史meme';
        generateBtn.disabled = false;
    }
}

/**
 * 显示meme生成结果
 */
function displayMemeResult(memeUrl) {
    // 修改现有的selfieResult来显示meme结果
    const resultDiv = document.getElementById('selfieResult');
    const imageElement = document.getElementById('selfieImage');
    const descElement = document.getElementById('selfieDescription');
    
    if (imageElement) {
        imageElement.src = memeUrl;
        imageElement.alt = '历史meme';
    }
    
    if (descElement) {
        descElement.textContent = `您的专属历史meme创作完成！融合了${selectedSceneForMeme.political_entity}的历史元素。`;
    }
    
    // 修改标题
    const titleElement = resultDiv.querySelector('h4');
    if (titleElement) {
        titleElement.textContent = '🎨 您的历史meme';
    }
    
    resultDiv.style.display = 'block';
    
    // 隐藏步骤3
    showStep('');
    document.getElementById('step3ImageUpload').style.display = 'none';
}

/**
 * base64转blob工具函数
 */
function dataURLtoBlob(dataURL) {
    const arr = dataURL.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], { type: mime });
}

// 全局暴露时光自拍功能
window.endHistoricalJourney = endHistoricalJourney;
window.startHistoricalSelfie = startHistoricalSelfie;
window.skipSelfie = skipSelfie;
window.selectSelfieScene = selectSelfieScene;
window.generateHistoricalSelfie = generateHistoricalSelfie;
window.continueToSummary = continueToSummary;
window.shareSelfie = shareSelfie;
window.startNewJourney = startNewJourney;
window.shareJourney = shareJourney;
window.backToSelfieQuestion = backToSelfieQuestion;
window.triggerAvatarUpload = triggerAvatarUpload;
window.handleAvatarUpload = handleAvatarUpload;
window.clearResults = clearResults;

// 全局暴露新的meme创作功能
window.showStep = showStep;
window.backToSceneSelection = backToSceneSelection;
window.proceedToTemplateSelection = proceedToTemplateSelection;
window.selectMemeTemplateForHistory = selectMemeTemplateForHistory;
window.clearMemeTemplateSelection = clearMemeTemplateSelection;
window.backToTemplateSelection = backToTemplateSelection;
window.proceedToImageUpload = proceedToImageUpload;
window.handleCharacterImageUpload = handleCharacterImageUpload;
window.handleCompositionImageUpload = handleCompositionImageUpload;
window.handleCompanionImageUpload = handleCompanionImageUpload;
window.generateHistoricalMeme = generateHistoricalMeme;

// ================ 互动选择模态框功能 ================

/**
 * 打开互动选择模态框
 */
async function openInteractionModal() {
    console.log('🔍 Debug: openInteractionModal 被调用');
    const modalOverlay = document.getElementById('interactionModalOverlay');
    if (!modalOverlay) {
        console.error('❌ 找不到互动模态框元素: interactionModalOverlay');
        logger.error('❌ 找不到互动模态框元素');
        return;
    }
    
    console.log('🔍 Debug: 模态框元素找到，正在显示');
    // 显示模态框
    modalOverlay.style.display = 'flex';
    
    console.log('🔍 Debug: 开始加载互动数据');
    // 加载互动数据
    await loadInteractionData();
    
    logger.info('🎭 互动选择模态框已打开');
}

/**
 * 打开和二次元穿越专用互动选择模态框
 */
async function openInteractionModalWithAnime() {
    console.log('🔍 Debug: openInteractionModalWithAnime 被调用');
    const modalOverlay = document.getElementById('interactionModalOverlay');
    if (!modalOverlay) {
        console.error('❌ 找不到互动模态框元素: interactionModalOverlay');
        logger.error('❌ 找不到互动模态框元素');
        return;
    }
    
    console.log('🔍 Debug: 模态框元素找到，正在显示');
    // 显示模态框
    modalOverlay.style.display = 'flex';
    
    console.log('🔍 Debug: 开始加载和二次元穿越互动数据');
    // 加载和二次元穿越专用互动数据
    await loadInteractionWithAnimeData();
    
    logger.info('🎭 和二次元穿越互动选择模态框已打开');
}

/**
 * 关闭互动选择模态框
 */
function closeInteractionModal() {
    const modalOverlay = document.getElementById('interactionModalOverlay');
    if (modalOverlay) {
        modalOverlay.style.display = 'none';
    }
    
    // 清理临时选择变量
    delete window.tempSelectedInteractionId;
    delete window.tempSelectedInteractionName;
    
    // 重置模态框内的选择状态
    document.querySelectorAll('.interaction-option-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    document.getElementById('selectedInteractionDisplay').style.display = 'none';
    document.getElementById('confirmInteractionBtn').disabled = true;
    
    // 🎭 如果是强互动模板但没有选择互动动作，重置模板选择
    if (selectedMemeTemplate === 'interactive_selfie' && !selectedInteractionId) {
        clearMemeTemplateSelection();
        logger.info('🚫 用户未选择互动动作，已重置强互动模板');
    }
    
    logger.info('🎭 互动选择模态框已关闭');
}

/**
 * 加载互动数据
 */
async function loadInteractionData() {
    console.log('🔍 Debug: loadInteractionData 被调用');
    if (availableInteractions) {
        console.log('🔍 Debug: 使用缓存的互动数据');
        // 如果已经加载过，直接显示
        displayInteractionCategories(availableInteractions);
        return;
    }
    
    try {
        console.log('🔍 Debug: 请求互动数据从 API');
        const response = await fetch(API_CONFIG.getApiUrl('/api/meme-templates'));
        const data = await response.json();
        
        console.log('🔍 Debug: API 响应:', data);
        if (data.success && data.interactions) {
            console.log('🔍 Debug: 互动数据结构:', Object.keys(data.interactions));
            availableInteractions = data.interactions;
            displayInteractionCategories(data.interactions);
            logger.info('✅ 互动数据加载成功');
        } else {
            throw new Error('互动数据加载失败: success=' + data.success + ', interactions=' + !!data.interactions);
        }
    } catch (error) {
        console.error('🔍 Debug: 互动数据加载错误:', error);
        logger.error(`❌ 互动数据加载失败: ${error.message}`);
        const container = document.getElementById('interactionCategoriesContainer');
        container.innerHTML = '<div class="loading-interactions">❌ 互动数据加载失败</div>';
    }
}

/**
 * 加载和二次元穿越专用互动数据
 */
async function loadInteractionWithAnimeData() {
    console.log('🔍 Debug: loadInteractionWithAnimeData 被调用');
    
    try {
        console.log('🔍 Debug: 请求和二次元穿越互动数据从 API');
        const response = await fetch(API_CONFIG.getApiUrl('/api/meme-templates'));
        const data = await response.json();
        
        console.log('🔍 Debug: API 响应:', data);
        if (data.success && data.interaction_with_anime) {
            console.log('🔍 Debug: 和二次元穿越互动数据结构:', Object.keys(data.interaction_with_anime));
            displayInteractionCategories(data.interaction_with_anime);
            logger.info('✅ 和二次元穿越互动数据加载成功');
        } else {
            throw new Error('和二次元穿越互动数据加载失败: success=' + data.success + ', interaction_with_anime=' + !!data.interaction_with_anime);
        }
    } catch (error) {
        console.error('🔍 Debug: 和二次元穿越互动数据加载错误:', error);
        logger.error(`❌ 和二次元穿越互动数据加载失败: ${error.message}`);
        const container = document.getElementById('interactionCategoriesContainer');
        if (container) {
            container.innerHTML = '<div class="loading-interactions">❌ 和二次元穿越互动数据加载失败</div>';
        }
    }
}

/**
 * 显示互动分类和按钮
 */
function displayInteractionCategories(interactions) {
    console.log('🔍 Debug: displayInteractionCategories 被调用，数据:', interactions);
    const container = document.getElementById('interactionCategoriesContainer');
    if (!container) {
        console.error('❌ 找不到 interactionCategoriesContainer 元素');
        return;
    }
    container.innerHTML = '';
    
    console.log('🔍 Debug: 开始渲染互动分类，共 ' + Object.keys(interactions).length + ' 个分类');
    Object.keys(interactions).forEach(categoryName => {
        // 创建分类容器
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'interaction-category';
        
        // 分类标题
        const titleElement = document.createElement('h4');
        titleElement.textContent = categoryName;
        categoryDiv.appendChild(titleElement);
        
        // 创建按钮网格容器
        const gridContainer = document.createElement('div');
        gridContainer.className = 'interaction-buttons-grid';
        
        // 添加该分类的互动按钮
        interactions[categoryName].forEach(interaction => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'interaction-option-btn';
            button.setAttribute('data-interaction-id', interaction.id);
            
            button.innerHTML = `
                <div class="interaction-name">${interaction.name}</div>
                <div class="interaction-desc">${interaction.description}</div>
            `;
            
            button.onclick = () => selectInteractionOption(interaction.id, interaction.name);
            
            gridContainer.appendChild(button);
        });
        
        categoryDiv.appendChild(gridContainer);
        container.appendChild(categoryDiv);
    });
    
    logger.info(`🎭 显示互动选项，共 ${Object.keys(interactions).length} 个分类`);
}

/**
 * 选择互动选项
 */
function selectInteractionOption(interactionId, interactionName) {
    // 清除之前的选中状态
    document.querySelectorAll('.interaction-option-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // 设置新的选中状态
    const selectedBtn = document.querySelector(`[data-interaction-id="${interactionId}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }
    
    // 更新选中信息显示
    const displayDiv = document.getElementById('selectedInteractionDisplay');
    const textSpan = document.getElementById('selectedInteractionText');
    
    textSpan.textContent = interactionName;
    displayDiv.style.display = 'block';
    
    // 启用确认按钮
    document.getElementById('confirmInteractionBtn').disabled = false;
    
    // 暂存选择（实际选择在确认时保存）
    window.tempSelectedInteractionId = interactionId;
    window.tempSelectedInteractionName = interactionName;
    
    logger.info(`🎯 暂选互动动作: ${interactionName} (${interactionId})`);
}

/**
 * 确认互动选择
 */
function confirmInteractionSelection() {
    if (!window.tempSelectedInteractionId) {
        logger.error('❌ 没有选择互动动作');
        return;
    }
    
    // 保存选择
    selectedInteractionId = window.tempSelectedInteractionId;
    selectedInteractionName = window.tempSelectedInteractionName;
    
    // 更新模板显示信息，包含互动动作
    const displaySpan = document.getElementById('selectedTemplateDisplay');
    displaySpan.textContent = `强互动自拍梗图 (${selectedInteractionName})`;
    
    // 启用下一步按钮
    document.getElementById('nextToUploadBtn').disabled = false;
    
    // 关闭模态框
    closeInteractionModal();
    
    // 清理临时变量
    delete window.tempSelectedInteractionId;
    delete window.tempSelectedInteractionName;
    
    logger.success(`✅ 已确认互动选择: ${selectedInteractionName} (${selectedInteractionId})`);
}

// 全局暴露互动功能
window.openInteractionModal = openInteractionModal;
window.openInteractionModalWithAnime = openInteractionModalWithAnime;
window.closeInteractionModal = closeInteractionModal;
window.selectInteractionOption = selectInteractionOption;
window.confirmInteractionSelection = confirmInteractionSelection;