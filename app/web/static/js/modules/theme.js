/**
 * ============================================================================
 * Wenjin-Lens (文津·选刊助手) — 主题与色调管理模块 (Theme Manager)
 * 职责：管理浅色宣纸/深墨雅夜模式切换、本地存储持久化与微动效响应。
 * ============================================================================
 */

(function (window) {
  'use strict';

  const THEME_STORAGE_KEY = 'wenjin_theme';

  class ThemeManager {
    constructor() {
      this.listeners = [];
      this.currentTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'light';
    }

    /**
     * 初始化应用主题状态
     */
    init() {
      this.apply(this.currentTheme === 'dark');
    }

    /**
     * 判断当前是否为深色模式
     * @returns {boolean}
     */
    isDark() {
      return this.currentTheme === 'dark';
    }

    /**
     * 切换明暗主题
     * @returns {boolean} 切换后的 isDark 状态
     */
    toggle() {
      const nextDark = !this.isDark();
      this.apply(nextDark);
      return nextDark;
    }

    /**
     * 应用指定主题并通知观察者
     * @param {boolean} dark
     */
    apply(dark) {
      this.currentTheme = dark ? 'dark' : 'light';
      localStorage.setItem(THEME_STORAGE_KEY, this.currentTheme);

      if (dark) {
        document.documentElement.classList.add('dark');
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.setAttribute('data-theme', 'light');
      }

      this._notify(dark);
    }

    /**
     * 订阅主题变更事件
     * @param {Function} callback
     */
    onThemeChange(callback) {
      if (typeof callback === 'function') {
        this.listeners.push(callback);
      }
    }

    _notify(isDark) {
      this.listeners.forEach((fn) => {
        try {
          fn(isDark);
        } catch (e) {
          console.error('[ThemeManager] 监听回调异常:', e);
        }
      });
    }
  }

  window.WenjinTheme = new ThemeManager();

})(window);
