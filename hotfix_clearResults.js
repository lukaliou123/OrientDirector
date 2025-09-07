// 临时热修复：手动添加 clearResults 函数
console.log('🔧 应用 clearResults 热修复...');

// 如果函数不存在，手动添加
if (typeof clearResults === 'undefined') {
    console.log('⚠️ clearResults 未定义，正在添加...');
    
    window.clearResults = function clearResults() {
        console.log('🧹 清除页面显示结果...');
        
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
        
        console.log('✅ 页面结果已清除');
    };
    
    // 同时添加到全局作用域
    window.clearResults = clearResults;
    
    console.log('✅ clearResults 函数热修复完成！');
} else {
    console.log('✅ clearResults 函数已存在');
}

// 验证修复
console.log('🧪 验证函数状态:');
console.log('   typeof clearResults:', typeof clearResults);
console.log('   window.clearResults:', typeof window.clearResults);

console.log('💡 现在可以安全点击"结束今天的旅程"按钮了');
console.log('🔄 建议强制刷新页面 (Ctrl+Shift+R) 以加载最新代码');
