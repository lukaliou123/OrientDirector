-- OrientDiscover Prompt & Generation Database Schema
-- 创建用于记录prompt使用和图片生成的核心数据表

-- 1. 基础Prompt记录表
CREATE TABLE IF NOT EXISTS prompt_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,                    -- prompt内容
    type VARCHAR(20) NOT NULL CHECK (type IN ('scene', 'meme')), -- 类型：场景或梗图
    
    -- 使用统计
    used_count INTEGER DEFAULT 1,           -- 使用频次
    success_count INTEGER DEFAULT 0,        -- 成功生成次数
    avg_generation_time REAL DEFAULT 0.0,   -- 平均生成时间（秒）
    
    -- 历史场景相关信息
    historical_period VARCHAR(100),         -- 历史时期（如：1600年）
    political_entity VARCHAR(100),          -- 政治实体（如：德川幕府）
    cultural_region VARCHAR(100),           -- 文化区域（如：东亚）
    
    -- 状态管理
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    notes TEXT,                             -- 备注说明
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 生成历史表
CREATE TABLE IF NOT EXISTS generation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,             -- 关联prompt_records表
    
    -- 生成结果
    image_path TEXT NOT NULL,               -- 生成的图片相对路径
    image_url TEXT NOT NULL,                -- 图片访问URL
    success BOOLEAN DEFAULT TRUE,           -- 生成是否成功
    error_message TEXT,                     -- 错误信息（如果失败）
    
    -- 生成参数和性能
    generation_time REAL,                   -- 单次生成耗时（秒）
    model_version VARCHAR(50) DEFAULT 'gemini-2.5-flash-image-preview', -- 使用的模型版本
    api_parameters TEXT,                    -- API参数（JSON格式）
    
    -- 历史场景特定信息
    scene_elements TEXT,                    -- 场景元素（JSON格式，用于meme生成）
    historical_context TEXT,               -- 历史背景信息（JSON格式）
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (prompt_id) REFERENCES prompt_records(id) ON DELETE CASCADE
);

-- 3. 图片质量评价表
CREATE TABLE IF NOT EXISTS image_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_id INTEGER NOT NULL,        -- 关联generation_history表
    
    -- 评分系统（1-5分制）
    quality_score INTEGER CHECK(quality_score BETWEEN 1 AND 5),           -- 图片质量
    creativity_score INTEGER CHECK(creativity_score BETWEEN 1 AND 5),     -- 创意性
    historical_accuracy_score INTEGER CHECK(historical_accuracy_score BETWEEN 1 AND 5), -- 历史准确性
    overall_rating REAL,                   -- 综合评分（自动计算平均值）
    
    -- 详细反馈
    feedback TEXT,                          -- 文字反馈和评价
    is_recommended BOOLEAN DEFAULT FALSE,   -- 是否推荐（优质prompt）
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (generation_id) REFERENCES generation_history(id) ON DELETE CASCADE
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_prompt_type ON prompt_records(type);
CREATE INDEX IF NOT EXISTS idx_prompt_status ON prompt_records(status);
CREATE INDEX IF NOT EXISTS idx_prompt_used_count ON prompt_records(used_count);
CREATE INDEX IF NOT EXISTS idx_generation_prompt_id ON generation_history(prompt_id);
CREATE INDEX IF NOT EXISTS idx_generation_success ON generation_history(success);
CREATE INDEX IF NOT EXISTS idx_generation_created_at ON generation_history(created_at);
CREATE INDEX IF NOT EXISTS idx_rating_generation_id ON image_ratings(generation_id);
CREATE INDEX IF NOT EXISTS idx_rating_overall ON image_ratings(overall_rating);
CREATE INDEX IF NOT EXISTS idx_rating_recommended ON image_ratings(is_recommended);

-- 创建视图方便查询
-- 1. 带评分的生成历史视图
CREATE VIEW IF NOT EXISTS generation_with_ratings AS
SELECT 
    gh.id,
    gh.prompt_id,
    pr.prompt,
    pr.type,
    pr.historical_period,
    pr.political_entity,
    pr.cultural_region,
    gh.image_path,
    gh.image_url,
    gh.success,
    gh.generation_time,
    gh.created_at as generation_date,
    ir.quality_score,
    ir.creativity_score,
    ir.historical_accuracy_score,
    ir.overall_rating,
    ir.feedback,
    ir.is_recommended
FROM generation_history gh
LEFT JOIN prompt_records pr ON gh.prompt_id = pr.id
LEFT JOIN image_ratings ir ON gh.id = ir.generation_id;

-- 2. Prompt统计视图
CREATE VIEW IF NOT EXISTS prompt_statistics AS
SELECT 
    pr.id,
    pr.prompt,
    pr.type,
    pr.used_count,
    pr.success_count,
    pr.avg_generation_time,
    COUNT(gh.id) as total_generations,
    COUNT(ir.id) as rated_generations,
    AVG(ir.overall_rating) as avg_rating,
    COUNT(CASE WHEN ir.is_recommended = 1 THEN 1 END) as recommended_count
FROM prompt_records pr
LEFT JOIN generation_history gh ON pr.id = gh.prompt_id
LEFT JOIN image_ratings ir ON gh.id = ir.generation_id
GROUP BY pr.id, pr.prompt, pr.type, pr.used_count, pr.success_count, pr.avg_generation_time;
