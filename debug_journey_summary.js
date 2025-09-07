// 旅途总结调试脚本
// 在浏览器控制台中运行，或者作为脚本插入到页面

console.log('🔍 开始旅途总结功能调试...');

// 1. 检查HTML容器
console.log('1. 检查HTML容器...');
const journeyContainer = document.getElementById('journeySummaryContainer');
const historicalContainer = document.getElementById('journeySummary'); 
const endButton = document.getElementById('endJourneyBtn');

console.log('journeySummaryContainer存在:', !!journeyContainer);
console.log('journeySummary存在:', !!historicalContainer);
console.log('endJourneyBtn存在:', !!endButton);
console.log('endJourneyBtn可见:', endButton ? endButton.style.display : 'N/A');

// 2. 检查旅程管理状态
console.log('\\n2. 检查旅程状态...');
if (typeof journeyManagement !== 'undefined') {
    console.log('旅程激活状态:', journeyManagement.isJourneyActive);
    console.log('当前旅程ID:', journeyManagement.currentJourneyId);
    console.log('历史场景数量:', journeyManagement.historyScenes ? journeyManagement.historyScenes.length : 'N/A');
    
    if (journeyManagement.historyScenes) {
        console.log('访问的场景:');
        journeyManagement.historyScenes.forEach((scene, index) => {
            console.log(`  ${index + 1}. ${scene.name} (${scene.category})`);
        });
    }
} else {
    console.log('❌ journeyManagement 变量未定义');
}

// 3. 检查函数定义
console.log('\\n3. 检查关键函数...');
console.log('endJourney函数存在:', typeof endJourney === 'function');
console.log('showJourneySummary函数存在:', typeof showJourneySummary === 'function');
console.log('endCurrentJourney函数存在:', typeof endCurrentJourney === 'function');
console.log('calculateJourneyStats函数存在:', typeof calculateJourneyStats === 'function');

// 4. 模拟点击结束旅程按钮
console.log('\\n4. 模拟功能测试...');

// 手动显示旅程总结（跳过API调用）
function testJourneySummary() {
    console.log('🧪 测试旅程总结显示...');
    
    // 创建模拟数据
    const mockJourneyResult = {
        visited_scenes_count: 3,
        total_distance_km: 2.5,
        journey_duration_minutes: 45,
        success: true
    };
    
    // 直接调用旅程总结函数
    if (typeof showJourneySummary === 'function') {
        try {
            showJourneySummary(mockJourneyResult);
            console.log('✅ showJourneySummary调用成功');
        } catch (error) {
            console.error('❌ showJourneySummary调用失败:', error);
        }
    }
    
    // 手动显示总结容器
    if (journeyContainer) {
        journeyContainer.style.display = 'block';
        journeyContainer.innerHTML = \`
            <div class="journey-summary-card" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 24px;
                border-radius: 16px;
                margin: 20px 0;
                text-align: center;
                box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
            ">
                <h2 style="margin: 0 0 20px 0; font-size: 1.8rem;">🎉 旅程完成！</h2>
                <div style="display: flex; justify-content: center; gap: 40px; margin: 20px 0;">
                    <div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700;">3</div>
                        <div style="opacity: 0.9;">访问场景</div>
                    </div>
                    <div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #FFD700;">2.5</div>
                        <div style="opacity: 0.9;">公里</div>
                    </div>
                </div>
                <p style="font-size: 1.1rem; opacity: 0.95; margin: 20px 0;">
                    🎊 恭喜完成这次精彩的探索之旅！每一步都是独特的发现，感谢您选择方向探索派对！
                </p>
                <button onclick="startNewJourney()" style="
                    background: rgba(255,255,255,0.2);
                    border: 2px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-size: 1rem;
                    cursor: pointer;
                    margin: 10px;
                ">
                    🚀 开始新旅程
                </button>
            </div>
        \`;
        console.log('✅ 手动显示旅程总结卡片成功');
    }
}

// 导出测试函数到全局作用域
window.testJourneySummary = testJourneySummary;

console.log('\\n🎯 调试建议:');
console.log('1. 在控制台运行: testJourneySummary() 来测试总结显示');
console.log('2. 检查是否有JavaScript错误阻止了函数执行');
console.log('3. 验证旅程状态管理是否正常');
console.log('4. 确认后端API是否正常响应');

console.log('\\n✅ 调试脚本加载完成');
