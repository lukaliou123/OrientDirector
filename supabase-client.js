/**
 * Supabase客户端配置
 * 用于前端认证和数据库操作
 */

// Supabase配置
const SUPABASE_URL = 'https://uobwbhvwrciaxloqdizc.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcwNzEyNjYsImV4cCI6MjA2MjY0NzI2Nn0.x9Tti06ZF90B2YPg-AeVvT_tf4qOcOYcHWle6L3OVtc';

// 动态加载Supabase客户端
let supabaseClient = null;
let isSupabaseLoaded = false;

/**
 * 初始化Supabase客户端
 */
async function initializeSupabase() {
    if (isSupabaseLoaded && supabaseClient) {
        return supabaseClient;
    }

    try {
        // 动态导入Supabase
        const { createClient } = await import('https://cdn.skypack.dev/@supabase/supabase-js@2');
        
        supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            auth: {
                flowType: 'pkce',              // 使用PKCE流程增强安全性
                persistSession: true,          // 持久化会话
                autoRefreshToken: true,        // 自动刷新令牌
                detectSessionInUrl: true,      // 自动检测URL中的会话参数
                storage: {
                    getItem: (key) => localStorage.getItem(key),
                    setItem: (key, value) => localStorage.setItem(key, value),
                    removeItem: (key) => {
                        localStorage.removeItem(key);
                        sessionStorage.removeItem(key);
                    }
                }
            }
        });

        isSupabaseLoaded = true;
        console.log('✅ Supabase客户端初始化成功');
        return supabaseClient;
    } catch (error) {
        console.error('❌ Supabase客户端初始化失败:', error);
        return null;
    }
}

/**
 * 获取Supabase客户端实例
 */
async function getSupabaseClient() {
    if (!supabaseClient) {
        await initializeSupabase();
    }
    return supabaseClient;
}

/**
 * 用户认证类
 */
class SupabaseAuth {
    constructor() {
        this.client = null;
        this.currentUser = null;
        this.isAuthenticated = false;
        this.authListeners = [];
    }

    /**
     * 初始化认证系统
     */
    async initialize() {
        this.client = await getSupabaseClient();
        if (!this.client) {
            console.warn('⚠️ Supabase客户端不可用，使用本地认证');
            return false;
        }

        // 监听认证状态变化
        this.client.auth.onAuthStateChange((event, session) => {
            console.log('🔐 认证状态变化:', event, session?.user?.email);
            
            if (session?.user) {
                this.currentUser = session.user;
                this.isAuthenticated = true;
            } else {
                this.currentUser = null;
                this.isAuthenticated = false;
            }

            // 通知所有监听器
            this.authListeners.forEach(listener => {
                try {
                    listener(this.isAuthenticated, this.currentUser, event);
                } catch (error) {
                    console.error('认证状态监听器错误:', error);
                }
            });
        });

        // 检查当前会话
        const { data: { session } } = await this.client.auth.getSession();
        if (session?.user) {
            this.currentUser = session.user;
            this.isAuthenticated = true;
        }

        return true;
    }

    /**
     * 添加认证状态监听器
     */
    onAuthStateChange(callback) {
        this.authListeners.push(callback);
        
        // 立即调用一次回调
        callback(this.isAuthenticated, this.currentUser, 'INITIAL_SESSION');
        
        // 返回取消监听的函数
        return () => {
            const index = this.authListeners.indexOf(callback);
            if (index > -1) {
                this.authListeners.splice(index, 1);
            }
        };
    }

    /**
     * 用户登录
     */
    async signIn(email, password) {
        if (!this.client) {
            throw new Error('Supabase客户端不可用');
        }

        try {
            console.log('🔐 尝试登录:', email);
            
            const { data, error } = await this.client.auth.signInWithPassword({
                email,
                password,
            });

            if (error) {
                console.error('❌ 登录失败:', error);
                throw error;
            }

            console.log('✅ 登录成功:', data.user?.email);
            return data;
        } catch (error) {
            console.error('❌ 登录过程中发生错误:', error);
            throw error;
        }
    }

    /**
     * 用户注册
     */
    async signUp(email, password, username) {
        if (!this.client) {
            throw new Error('Supabase客户端不可用');
        }

        try {
            console.log('📝 尝试注册:', email);
            
            const { data, error } = await this.client.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        username: username,
                        display_name: username
                    }
                }
            });

            if (error) {
                console.error('❌ 注册失败:', error);
                throw error;
            }

            console.log('✅ 注册成功:', data.user?.email);
            return data;
        } catch (error) {
            console.error('❌ 注册过程中发生错误:', error);
            throw error;
        }
    }

    /**
     * 用户登出
     */
    async signOut() {
        if (!this.client) {
            return;
        }

        try {
            console.log('🚪 用户登出');
            const { error } = await this.client.auth.signOut();
            if (error) {
                console.error('❌ 登出失败:', error);
                throw error;
            }
            console.log('✅ 登出成功');
        } catch (error) {
            console.error('❌ 登出过程中发生错误:', error);
            throw error;
        }
    }

    /**
     * 获取当前用户
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * 检查是否已认证
     */
    isUserAuthenticated() {
        return this.isAuthenticated;
    }

    /**
     * 获取访问令牌
     */
    async getAccessToken() {
        if (!this.client) {
            return null;
        }

        try {
            const { data: { session } } = await this.client.auth.getSession();
            return session?.access_token || null;
        } catch (error) {
            console.error('获取访问令牌失败:', error);
            return null;
        }
    }

    /**
     * 刷新会话
     */
    async refreshSession() {
        if (!this.client) {
            return null;
        }

        try {
            const { data, error } = await this.client.auth.refreshSession();
            if (error) {
                console.error('刷新会话失败:', error);
                return null;
            }
            return data;
        } catch (error) {
            console.error('刷新会话过程中发生错误:', error);
            return null;
        }
    }
}

// 创建全局认证实例
const supabaseAuth = new SupabaseAuth();

// 导出API
window.SupabaseAuth = SupabaseAuth;
window.supabaseAuth = supabaseAuth;
window.getSupabaseClient = getSupabaseClient;
window.initializeSupabase = initializeSupabase;

// 自动初始化
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await supabaseAuth.initialize();
        console.log('🚀 Supabase认证系统初始化完成');
    } catch (error) {
        console.error('❌ Supabase认证系统初始化失败:', error);
    }
});

console.log('📦 Supabase客户端模块加载完成');
