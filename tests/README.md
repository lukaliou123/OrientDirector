# 🧪 OrientDiscover 测试中心

本目录包含OrientDiscover项目的所有测试文件，按前后端分类整理。

## 📁 目录结构

### 🖥️ [backend/](backend/) - 后端Python测试
Python后端API和服务的测试文件

- **test_api.py** - 后端API接口测试
- **test_current_deployment.py** - 当前部署状态测试
- **test_journey_summary.py** - 旅程摘要功能测试

### 🌐 [frontend/](frontend/) - 前端JavaScript测试  
JavaScript前端功能和UI的测试文件

- **test_back_selection_fix.js** - 返回选择功能测试
- **test_streetview.js** - Google街景功能测试

## 🚀 运行测试

### 后端测试运行
```bash
# 进入项目根目录
cd /path/to/OrientDiscover

# 激活虚拟环境
source venv/bin/activate

# 运行单个测试
python tests/backend/test_api.py
python tests/backend/test_journey_summary.py

# 运行所有后端测试
python -m pytest tests/backend/ -v
```

### 前端测试运行
```bash
# 在浏览器中打开测试文件
# 或者在开发者工具的Console中执行

# 加载测试文件
<script src="tests/frontend/test_streetview.js"></script>
<script src="tests/frontend/test_back_selection_fix.js"></script>

# 运行测试函数
testStreetViewBasic();
testBackSelectionFix();
```

## 📝 测试文件说明

### 后端测试详情

#### **test_api.py**
- 测试基础API端点
- 验证数据返回格式
- 检查响应时间和状态码

#### **test_journey_summary.py**  
- 测试旅程创建和结束功能
- 验证场景访问记录
- 检查旅程统计计算

#### **test_current_deployment.py**
- 测试当前部署环境
- 验证服务器状态
- 检查配置和依赖

### 前端测试详情

#### **test_streetview.js**
- Google街景模态框测试
- 街景API加载验证
- 交互功能测试

#### **test_back_selection_fix.js**
- 返回选择功能测试
- 场景状态管理验证
- UI状态切换测试

## 🔧 测试环境要求

### 后端测试环境
- Python 3.8+
- FastAPI应用运行中
- 必需的环境变量配置
- 网络连接（用于API测试）

### 前端测试环境
- 现代浏览器（支持ES6+）
- 本地开发服务器运行
- Google Maps API Key配置
- 开发者工具可用

## 📊 测试覆盖目标

### 当前测试覆盖
- ✅ 基础API功能测试
- ✅ 旅程管理功能测试
- ✅ Google街景集成测试
- ✅ UI交互功能测试

### 计划新增测试
- 🔲 历史模式功能测试
- 🔲 预设地址功能测试
- 🔲 AI图像生成功能测试
- 🔲 数据缓存功能测试

---

## 📝 测试最佳实践

### 编写测试的原则
1. **测试命名清晰**：使用描述性的测试函数名
2. **独立性**：每个测试应该独立运行
3. **覆盖关键路径**：重点测试核心功能和边界情况
4. **易于维护**：测试代码应该简洁明了

### 新增测试指南
- 后端新功能测试放入 `backend/`
- 前端新功能测试放入 `frontend/`
- 复杂集成测试可创建单独的子目录
- 测试数据和Mock放入对应的 `fixtures/` 目录

---

*文档创建时间：2024年12月20日*  
*测试文件整理完成：5个测试文件已分类*
