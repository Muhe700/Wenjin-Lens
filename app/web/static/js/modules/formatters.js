/**
 * ============================================================================
 * Wenjin-Lens (文津·选刊助手) — 学术数据格式化与排版工具模块 (Formatters)
 * 职责：纯函数式处理期刊刊号拼接、分级标签计算、简报文本生成与剪贴板复制。
 * ============================================================================
 */

(function (window) {
  'use strict';

  const Formatters = {
    /**
     * 根据级别代码映射 Element Plus 标签类型
     * @param {string} level - 如 'A1', 'A2', 'A3', 'A4', 'B'
     * @returns {string} danger | warning | primary | success | info
     */
    getLevelTagType(level) {
      const map = {
        A1: 'danger',
        A2: 'warning',
        A3: 'primary',
        A4: 'success',
        B: 'info'
      };
      return map[level] || 'info';
    },

    /**
     * 根据级别描述文本匹配标签类型
     * @param {string} label - 如 'A类1级 (顶尖权威)'
     * @returns {string}
     */
    getLevelTagTypeFromLabel(label) {
      if (!label) return 'info';
      if (label.includes('A类1级') || label.includes('A1')) return 'danger';
      if (label.includes('A类2级') || label.includes('A2')) return 'warning';
      if (label.includes('A类3级') || label.includes('A3')) return 'primary';
      if (label.includes('A类4级') || label.includes('A4')) return 'success';
      return 'info';
    },

    /**
     * 获取规范化 ISSN 与 CN 联合显示字符串
     * @param {Object} jData - 统一期刊数据对象
     * @returns {string}
     */
    getIssnCnDisplay(jData) {
      if (!jData) return '待核验';
      const c = jData.catalog || {};
      const k = (jData.kb && jData.kb.basic) || {};
      const items = [];
      const issn = c.issn || k.issn;
      const cn = c.cn || k.cn;

      if (issn) items.push(`ISSN ${issn}`);
      if (cn) items.push(`CN ${cn}`);
      return items.length ? items.join(' | ') : '待核验';
    },

    getPublisher(jData) {
      if (!jData) return '未明';
      const c = jData.catalog || {};
      const k = (jData.kb && jData.kb.basic) || {};
      return c.publisher || k.publisher || '未明';
    },

    getLevelLabel(jData) {
      if (!jData || !jData.level_info) return '待核验';
      return jData.level_info.label || '待核验';
    },

    getLevelCode(jData) {
      if (!jData || !jData.level_info) return '';
      return jData.level_info.level || '';
    },

    getReasons(jData) {
      if (!jData || !jData.level_info || !Array.isArray(jData.level_info.reasons)) return [];
      return jData.level_info.reasons;
    },

    isUpgraded(jData) {
      return !!(jData && jData.level_info && jData.level_info.upgraded);
    },

    isWarned(jData) {
      return !!(jData && jData.warning_info && jData.warning_info.is_warned);
    },

    getWarningDetail(jData) {
      return (jData && jData.warning_info) || {};
    },

    getIndexesVerified(jData) {
      return !!(jData && jData.kb && jData.kb.indexes && jData.kb.indexes.indexes_verified);
    },

    getIndexesNote(jData) {
      return (jData && jData.kb && jData.kb.indexes_note) || '';
    },

    getImpactNote(jData) {
      return (jData && jData.kb && jData.kb.impact_factor && jData.kb.impact_factor.note) || '';
    },

    getEditorName(jData) {
      return (jData && jData.kb && jData.kb.editor_in_chief && jData.kb.editor_in_chief.name) || '待检索核验';
    },

    getEditorAffiliation(jData) {
      return (jData && jData.kb && jData.kb.editor_in_chief && jData.kb.editor_in_chief.affiliation) || '';
    },

    getScope(jData) {
      return (jData && jData.kb && jData.kb.scope) || '知识库暂无收稿方向，可点击上方联网深度查证';
    },

    getReviewCycle(jData) {
      return (jData && jData.kb && jData.kb.review_cycle) || '知识库暂无，待联网查证';
    },

    getPublicationMode(jData) {
      return (jData && jData.kb && jData.kb.publication_mode) || '未明确';
    },

    getApcFee(jData) {
      return (jData && jData.kb && jData.kb.apc_fee) || '知识库暂无版面费数据，待联网查证';
    },

    getSubmissionUrl(jData) {
      return (jData && jData.kb && jData.kb.submission_url) || '';
    },

    isHttpUrl(url) {
      return typeof url === 'string' && url.indexOf('http') === 0;
    },

    /**
     * 获取影响因子与中科院分区展示字符串
     * @param {Object} jData
     * @returns {string}
     */
    getScoreDisplay(jData) {
      if (!jData) return '待核验/未收录';
      const if_ = (jData.kb && jData.kb.impact_factor) || {};
      const parts = [];
      if (if_.jcr_if) parts.push(`JCR IF: ${if_.jcr_if}`);
      if (if_.cas_zone) parts.push(`中科院分区: ${if_.cas_zone}`);
      return parts.length ? parts.join(' | ') : '待核验/未收录';
    },

    /**
     * 提取已确认收录的权威核心索引标签数组
     * @param {Object} jData
     * @returns {string[]}
     */
    getKnownIndexes(jData) {
      if (!jData) return [];
      const idx = (jData.kb && jData.kb.indexes) || {};
      const list = [];
      if (idx.scie_zone) list.push(`SCIE (${idx.scie_zone}区)`);
      if (idx.ssci_zone) list.push(`SSCI (${idx.ssci_zone}区)`);
      if (idx.cscd_core) list.push('CSCD核心版');
      if (idx.cscd_ext) list.push('CSCD扩展版');
      if (idx.cssci_core) list.push('CSSCI核心版');
      if (idx.pkucore) list.push('北大核心');
      if (idx.extra && Array.isArray(idx.extra)) {
        list.push(...idx.extra);
      }
      return list;
    },

    /**
     * 生成供学者一键复制的标准化决策简报文本
     * @param {Object} data
     * @returns {string}
     */
    generateBriefText(data) {
      if (!data) return '';
      const lvl = data.level_info || {};
      const kb = data.kb || {};
      const warn = data.warning_info || {};

      return [
        `【文津·选刊助手决策核验简报】`,
        `----------------------------------------`,
        `期刊名称：《${data.name}》`,
        `广中医认定级别：${lvl.label || '待核验'}`,
        `认定依据：${(lvl.reasons || []).join('；')}`,
        `刊号信息：${this.getIssnCnDisplay(data)}`,
        `影响因子/分区：${this.getScoreDisplay(data)}`,
        `审稿周期时效：${kb.review_cycle || '未明确'}`,
        `出版模式与版面费：${kb.publication_mode || '未明'} | ${kb.apc_fee || '未明'}`,
        `中科院预警排查：${
          warn.is_warned
            ? `⚠️ 已列入${warn.year}年预警名单（${warn.reason}）`
            : '✓ 正常（未列入中科院预警名单）'
        }`,
        `官方在线采编：${kb.submission_url || '详见主办机构官网'}`,
        `----------------------------------------`,
        `生成时间：${new Date().toLocaleDateString('zh-CN')} | 依据广州中医药大学校办〔2020〕308号目录`
      ].join('\n');
    },

    /**
     * 兼容现代 Clipboard API 与备用降级方案的通用剪贴板写入
     * @param {string} text
     * @returns {Promise<boolean>}
     */
    async copyToClipboard(text) {
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch (_) {
          // fallback
        }
      }

      // 降级使用 textarea 选区复制
      try {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        return success;
      } catch (e) {
        console.error('[Formatters] 复制失败:', e);
        return false;
      }
    }
  };

  window.WenjinFormatters = Formatters;

})(window);
