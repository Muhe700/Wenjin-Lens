/**
 * ============================================================================
 * Wenjin-Lens (文津·选刊助手) — 多维横向对比管理模块 (Comparison Manager)
 * 职责：管理学者选中的横向对比期刊矩阵列表，约束容量上限与本地持久化。
 * ============================================================================
 */

(function (window) {
  'use strict';

  const COMPARISON_STORAGE_KEY = 'wenjin_comparison';
  const MAX_COMPARISON_LIMIT = 3;

  class ComparisonManager {
    constructor() {
      this.list = this._loadFromStorage();
    }

    _loadFromStorage() {
      try {
        const raw = localStorage.getItem(COMPARISON_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
      } catch (e) {
        console.warn('[ComparisonManager] 解析本地对比缓存失败:', e);
        return [];
      }
    }

    _saveToStorage() {
      try {
        localStorage.setItem(COMPARISON_STORAGE_KEY, JSON.stringify(this.list));
      } catch (e) {
        console.error('[ComparisonManager] 保存本地对比缓存失败:', e);
      }
    }

    /**
     * 获取当前对比列表副本
     * @returns {Array}
     */
    getList() {
      return [...this.list];
    }

    /**
     * 添加期刊至对比矩阵
     * @param {Object} journalData
     * @returns {{ success: boolean, reason?: string }}
     */
    add(journalData) {
      if (!journalData || !journalData.name) {
        return { success: false, reason: '期刊数据无效' };
      }

      const alreadyExists = this.list.some((item) => item.name === journalData.name);
      if (alreadyExists) {
        return { success: false, reason: `《${journalData.name}》已在对比列表中` };
      }

      if (this.list.length >= MAX_COMPARISON_LIMIT) {
        return {
          success: false,
          reason: `对比列表上限为 ${MAX_COMPARISON_LIMIT} 本期刊，请先移除部分期刊后再添加`
        };
      }

      this.list.push(journalData);
      this._saveToStorage();
      return { success: true };
    }

    /**
     * 从对比列表中移除指定索引条目
     * @param {number} index
     */
    remove(index) {
      if (index >= 0 && index < this.list.length) {
        this.list.splice(index, 1);
        this._saveToStorage();
      }
    }

    /**
     * 清空全部对比列表
     */
    clear() {
      this.list = [];
      this._saveToStorage();
    }
  }

  window.WenjinComparison = new ComparisonManager();

})(window);
