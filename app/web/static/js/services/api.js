/**
 * ============================================================================
 * Wenjin-Lens (文津·选刊助手) — 前端数据接口服务层 (API Client Interface)
 * 职责：负责前端与后端 RESTful API 之间所有的数据传输与网络异常处理。
 * 杜绝在 UI 视图组件中内嵌直接的 fetch/HTTP 散落调用。
 * ============================================================================
 */

(function (window) {
  'use strict';

  class WenjinAPIClient {
    constructor(baseURL = '') {
      if (!baseURL && typeof window !== 'undefined' && window.location) {
        if (window.location.pathname.startsWith('/wenjin')) {
          baseURL = '/wenjin';
        }
      }
      this.baseURL = baseURL;
    }

    /**
     * 获取当前用户/台账ID（支持本地持久化隔离）
     */
    getUserId() {
      if (typeof window === 'undefined' || !window.localStorage) {
        return 'default';
      }
      let uid = window.localStorage.getItem('wenjin_user_id');
      if (!uid) {
        // 自动为首次访问的用户生成唯一台账ID，例如 user_a9f3b2c1
        const randStr = Math.random().toString(36).substring(2, 10);
        uid = `user_${randStr}`;
        window.localStorage.setItem('wenjin_user_id', uid);
      }
      return uid;
    }

    /**
     * 设置/切换当前用户台账ID
     */
    setUserId(newId) {
      if (typeof window !== 'undefined' && window.localStorage) {
        const clean = (newId || '').trim();
        if (clean) {
          window.localStorage.setItem('wenjin_user_id', clean);
        }
      }
    }

    /**
     * 基础 HTTP 请求封装器
     * @private
     */
    async _request(endpoint, options = {}) {
      const url = `${this.baseURL}${endpoint}`;
      const defaultOptions = {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-User-ID': this.getUserId()
        }
      };

      const mergedOptions = { ...defaultOptions, ...options };
      if (options.headers) {
        mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };
      }

      try {
        const response = await fetch(url, mergedOptions);
        if (!response.ok) {
          let errDetail = `HTTP ${response.status} ${response.statusText}`;
          try {
            const errData = await response.json();
            if (errData && errData.detail) {
              errDetail = errData.detail;
            }
          } catch (_) {
            // response was not JSON
          }
          throw new Error(errDetail);
        }
        return await response.json();
      } catch (error) {
        console.error(`[WenjinAPI] 请求失败 [${url}]:`, error);
        throw error;
      }
    }

    /**
     * 1. 核心选刊综合检索
     * @param {string} query - 期刊名称、ISSN、CN 或 收录规则
     * @returns {Promise<Object>}
     */
    async search(query) {
      const q = encodeURIComponent((query || '').trim());
      return await this._request(`/api/search?q=${q}`);
    }

    /**
     * 2. 联网深度查证与指标核验 (Gemini + OpenAlex + DOAJ)
     * @param {string} journalName - 待核验期刊全称
     * @returns {Promise<Object>}
     */
    async refresh(journalName) {
      const q = encodeURIComponent((journalName || '').trim());
      return await this._request(`/api/refresh?q=${q}`, {
        method: 'POST'
      });
    }

    /**
     * 3. 获取系统运行指标与资产统计
     * @returns {Promise<Object>}
     */
    async getStats() {
      return await this._request('/api/stats');
    }

    /**
     * 4. 获取选刊决策追踪台账数据
     * @returns {Promise<Object>}
     */
    async getTrack() {
      return await this._request('/api/track');
    }

    /**
     * 4.1 从台账中删除指定期刊
     * @param {string} journalName - 期刊名称
     * @returns {Promise<Object>}
     */
    async deleteTrack(journalName) {
      const name = encodeURIComponent((journalName || '').trim());
      return await this._request(`/api/track?name=${name}`, {
        method: 'DELETE'
      });
    }

    /**
     * 4.2 清空当前用户的选刊决策台账
     * @returns {Promise<Object>}
     */
    async clearTrack() {
      return await this._request('/api/track/clear', {
        method: 'DELETE'
      });
    }

    /**
     * 4.3 手动将指定期刊收录入当前用户的台账
     * @param {string} journalName - 期刊名称
     * @returns {Promise<Object>}
     */
    async addToTrack(journalName) {
      const name = encodeURIComponent((journalName || '').trim());
      return await this._request(`/api/track?name=${name}`, {
        method: 'POST'
      });
    }

    /**
     * 5. 获取标准 Excel 台账导出下载 URL
     * @returns {string}
     */
    getExportTrackUrl() {
      const uid = encodeURIComponent(this.getUserId());
      return `${this.baseURL}/api/track/export?user_id=${uid}`;
    }

    /**
     * 6. 多维条件复合筛选台账与官方分级目录
     * @param {string} expr - 筛选表达式，如 "level=A1,oa=是"
     * @param {string} scope - 筛选范围: official(官方全量) / track(个人台账) / all
     * @returns {Promise<Object>}
     */
    async filterTrack(expr, scope = 'official') {
      const encoded = encodeURIComponent(expr || 'all');
      return await this._request(`/api/filter?expr=${encoded}&scope=${encodeURIComponent(scope)}`);
    }

    /**
     * 7. 获取官方目录全量分级与期刊数据
     * @returns {Promise<Object>}
     */
    async getCatalog() {
      return await this._request('/api/catalog');
    }

    /**
     * 8. 获取全量权威索引目录全景聚合数据 (广中医308号、CSCD、北大核心、中科院预警)
     * @returns {Promise<Object>}
     */
    async getAllIndexes() {
      return await this._request('/api/indexes/all');
    }

    /**
     * 9. 跨所有权威索引目录精准定位期刊具体位置
     * @param {string} query - 待定位的期刊全称、ISSN、CN 或 关键词
     * @returns {Promise<Object>}
     */
    async locateInIndexes(query) {
      const q = encodeURIComponent((query || '').trim());
      return await this._request(`/api/indexes/locate?q=${q}`);
    }

    /**
     * 10. 获取中科院1~4区开源历史镜像期刊列表 (支持分区、学科分类、Top、搜索、分页)
     * @param {Object} params - 筛选参数对象
     * @returns {Promise<Object>}
     */
    async getCasJournals(params = {}) {
      const queryParams = new URLSearchParams();
      if (params.zone) queryParams.append('zone', params.zone);
      if (params.category && params.category !== 'ALL') queryParams.append('category', params.category);
      if (params.is_top !== undefined && params.is_top !== '') queryParams.append('is_top', params.is_top);
      if (params.wos_type && params.wos_type !== 'ALL') queryParams.append('wos_type', params.wos_type);
      if (params.q) queryParams.append('q', params.q);
      if (params.page) queryParams.append('page', params.page);
      if (params.page_size) queryParams.append('page_size', params.page_size);
      return await this._request(`/api/indexes/cas/journals?${queryParams.toString()}`);
    }

    /**
     * 11. 获取中科院分区所有学科大类列表
     * @returns {Promise<Object>}
     */
    async getCasCategories() {
      return await this._request('/api/indexes/cas/categories');
    }

    /**
     * 12. 服务健康状态检查
     * @returns {Promise<Object>}
     */
    async checkHealth() {
      return await this._request('/api/health');
    }
  }

  // 挂载单例至全局命名空间
  window.WenjinAPI = new WenjinAPIClient();

})(window);
