# 🚀 OrientDiscover 开发计划 - 场景选择和旅程管理

## 📅 开发时间线

### 第一周：基础功能实现
- [ ] Day 1-2: 场景列表选择UI（第4条）
- [ ] Day 3: 场景锐评生成（第5条）
- [ ] Day 4-5: 旅程记录后端API（第6-7条）

### 第二周：核心功能完善
- [ ] Day 6-7: 场景详情卡展示（第8条）
- [ ] Day 8-9: 继续探索功能（第9条）
- [ ] Day 10: 旅程总结功能（第10-11条）

## 🔧 技术实现细节

### 1. 前端状态管理
```javascript
// 新增全局状态
const journeyState = {
    journeyId: null,
    isActive: false,
    startLocation: null,
    currentLocation: null,
    visitedScenes: [],
    selectedScenes: [],
    rejectedScenes: [],
    totalDistance: 0,
    startTime: null
};
```

### 2. 场景选择交互
```javascript
// 场景卡片模板
function createSceneCard(scene, index) {
    return `
        <div class="scene-card ${scene.selected ? 'selected' : ''} ${scene.rejected ? 'rejected' : ''}" 
             data-scene-id="${index}">
            <div class="scene-selector">
                <input type="checkbox" id="scene-${index}" 
                       ${scene.selected ? 'checked' : ''}>
                <button class="reject-btn" onclick="rejectScene(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <img src="${scene.image}" alt="${scene.name}">
            <h3>${scene.name}</h3>
            <p>${scene.description}</p>
            <div class="scene-info">
                <span>📍 ${scene.distance}km</span>
                <span>🎫 ${scene.ticket_price || '免费'}</span>
            </div>
        </div>
    `;
}
```

### 3. 后端API设计
```python
# 场景锐评生成
@app.post("/api/scene-review")
async def generate_scene_review(request: SceneReviewRequest):
    """
    根据选中的场景生成个性化锐评
    """
    scenes = request.selected_scenes
    review = await generate_smart_review(scenes)
    return {"review": review}

# 旅程管理
@app.post("/api/journey/start")
async def start_journey(request: StartJourneyRequest):
    """
    开始新旅程
    """
    journey_id = create_new_journey(request)
    return {"journey_id": journey_id}

@app.post("/api/journey/arrive")
async def arrive_at_scene(request: ArriveSceneRequest):
    """
    记录到达场景
    """
    update_journey_location(request.journey_id, request.scene)
    return {"status": "success"}
```

### 4. 数据结构设计
```python
# 旅程数据模型
class Journey(BaseModel):
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    start_location: Location
    current_location: Location
    visited_scenes: List[SceneVisit]
    total_distance: float
    status: str  # active, completed

class SceneVisit(BaseModel):
    scene: PlaceInfo
    arrival_time: datetime
    duration: Optional[int]  # 停留时间（分钟）
    user_note: Optional[str]
```

### 5. UI/UX改进
- 添加场景选择动画效果
- 实现拖拽排序功能
- 添加场景预览模式
- 优化移动端交互体验

## 🎯 关键功能实现

### 场景选择功能
1. **多选模式**
   - 支持批量选择
   - 快速全选/全不选
   - 选中计数显示

2. **划掉功能**
   - 删除线动画
   - 恢复选项
   - 自动重排列

3. **确认流程**
   - 选择预览
   - 二次确认
   - 加载过渡

### 旅程记录功能
1. **实时追踪**
   - 位置更新
   - 路径绘制
   - 时间记录

2. **数据持久化**
   - 本地存储备份
   - 服务器同步
   - 离线支持

### 场景展示优化
1. **沉浸式体验**
   - 全屏展示
   - 手势操作
   - 音效反馈

2. **信息层次**
   - 基础信息优先
   - 详细信息展开
   - 相关推荐

## 🔍 测试计划

### 功能测试
- [ ] 场景选择交互测试
- [ ] 旅程记录准确性测试
- [ ] 位置更新测试
- [ ] 数据持久化测试

### 性能测试
- [ ] 大量场景渲染性能
- [ ] API响应时间
- [ ] 内存使用监控

### 兼容性测试
- [ ] 移动设备测试
- [ ] 不同浏览器测试
- [ ] 离线功能测试

## 📊 进度跟踪

使用此文档跟踪开发进度，每完成一项请打勾并记录完成时间。
