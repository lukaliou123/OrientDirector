// 多语言配置
const i18nConfig = {
  fallbackLng: 'zh',
  debug: false,
  
  interpolation: {
    escapeValue: false,
  },
  
  detection: {
    order: ['localStorage', 'navigator', 'htmlTag'],
    caches: ['localStorage'],
  },
  
  // 资源加载配置
  resources: {},
  load: 'languageOnly',
  preload: ['zh', 'en', 'es', 'fr', 'de', 'ja', 'ko', 'it', 'pt', 'ru', 'ar', 'hi', 'tr', 'nl', 'he', 'bg'],
};

// 支持的语言列表
const supportedLanguages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'ar', name: 'العربية', flag: '🇦🇪' },
  { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
  { code: 'tr', name: 'Türkçe', flag: '🇹🇷' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'he', name: 'עברית', flag: '🇮🇱' },
  { code: 'bg', name: 'Български', flag: '🇧🇬' },
];

// 语言检测和切换函数
function detectLanguage() {
  // 1. 检查localStorage
  const storedLang = localStorage.getItem('i18nextLng');
  if (storedLang && supportedLanguages.find(lang => lang.code === storedLang)) {
    return storedLang;
  }
  
  // 2. 检查浏览器语言
  const browserLang = navigator.language.split('-')[0];
  if (supportedLanguages.find(lang => lang.code === browserLang)) {
    return browserLang;
  }
  
  // 3. 默认返回中文
  return 'zh';
}

function changeLanguage(langCode) {
  if (supportedLanguages.find(lang => lang.code === langCode)) {
    localStorage.setItem('i18nextLng', langCode);
    // 触发语言切换事件
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: langCode } }));
    return true;
  }
  return false;
}

function getCurrentLanguage() {
  return detectLanguage();
}

function getSupportedLanguages() {
  return supportedLanguages;
}

// 动态加载翻译文件
async function loadTranslations(langCode) {
  try {
    const response = await fetch(`/i18n/locales/${langCode}.json`);
    if (response.ok) {
      const translations = await response.json();
      if (!window.translations) {
        window.translations = {};
      }
      window.translations[langCode] = translations;
      return translations;
    }
  } catch (error) {
    console.warn(`Failed to load translations for ${langCode}:`, error);
  }
  return null;
}

// 预加载所有翻译文件
async function preloadAllTranslations() {
  const loadPromises = supportedLanguages.map(lang => loadTranslations(lang.code));
  await Promise.all(loadPromises);
}

// 翻译函数（增强版，支持动态加载）
async function t(key, options = {}) {
  const currentLang = getCurrentLanguage();
  
  // 确保当前语言的翻译已加载
  if (!window.translations || !window.translations[currentLang]) {
    await loadTranslations(currentLang);
  }
  
  const translations = window.translations || {};
  const langTranslations = translations[currentLang] || translations['zh'] || {};
  
  let value = langTranslations;
  const keys = key.split('.');
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return key; // 返回key本身作为fallback
    }
  }
  
  if (typeof value === 'string') {
    // 简单的变量替换
    if (options) {
      return value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
        return options[varName] || match;
      });
    }
    return value;
  }
  
  return key;
}

// 同步翻译函数（用于已加载的翻译）
function tSync(key, options = {}) {
  const currentLang = getCurrentLanguage();
  const translations = window.translations || {};
  const langTranslations = translations[currentLang] || translations['zh'] || {};
  
  let value = langTranslations;
  const keys = key.split('.');
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return key; // 返回key本身作为fallback
    }
  }
  
  if (typeof value === 'string') {
    // 简单的变量替换
    if (options) {
      return value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
        return options[varName] || match;
      });
    }
    return value;
  }
  
  return key;
}

// 导出
window.i18n = {
  config: i18nConfig,
  supportedLanguages,
  detectLanguage,
  changeLanguage,
  getCurrentLanguage,
  getSupportedLanguages,
  loadTranslations,
  preloadAllTranslations,
  t,
  tSync
};
