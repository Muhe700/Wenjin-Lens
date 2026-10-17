/**
 * ============================================================================
 * Wenjin-Lens (文津·选刊助手) — 学术图表可视化模块 (Catalog Chart Visualizer)
 * 职责：封装 Chart.js 甜甜圈图表渲染，支持响应式布局与明暗主题自适应重绘。
 * ============================================================================
 */

(function (window) {
  'use strict';

  class CatalogChartService {
    constructor() {
      this.chartInstance = null;
    }

    /**
     * 渲染或更新官方目录分级分布环形图
     * @param {string} canvasId - 画布 DOM 元素 ID
     * @param {Array} categories - 分级分类数据
     * @param {boolean} isDark - 是否深色模式
     */
    render(canvasId, categories, isDark = false) {
      const canvas = document.getElementById(canvasId);
      if (!canvas || !window.Chart) return;

      this.destroy();

      const cats = categories || [];
      const labels = cats.map((c) => `${c.level} (${(c.name || '').split('（')[0]})`);
      const counts = cats.map((c) => (c.items || []).length);

      // 学术典雅色盘 (符合 DESIGN.md 规范)
      const colorPalette = ['#cc785c', '#c4841d', '#23689b', '#2d7a46', '#6c6a64'];

      this.chartInstance = new window.Chart(canvas, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [
            {
              data: counts,
              backgroundColor: colorPalette,
              borderWidth: 2,
              borderColor: isDark ? '#1a1b19' : '#ffffff'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: {
                font: {
                  family: "'Plus Jakarta Sans', -apple-system, sans-serif",
                  size: 12
                },
                color: isDark ? '#f5f4ef' : '#141413',
                padding: 12
              }
            },
            tooltip: {
              callbacks: {
                label(context) {
                  const label = context.label || '';
                  const value = context.parsed || 0;
                  const total = context.dataset.data.reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                  return ` ${label}: ${value} 种 (${percentage}%)`;
                }
              }
            }
          },
          cutout: '65%'
        }
      });
    }

    /**
     * 销毁现有图表实例，释放内存
     */
    destroy() {
      if (this.chartInstance) {
        this.chartInstance.destroy();
        this.chartInstance = null;
      }
    }
  }

  window.WenjinCatalogChart = new CatalogChartService();

})(window);
