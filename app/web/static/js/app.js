/**
 * ============================================================================
 * Wenjin-Lens (文津·选刊助手) — 前端核心应用调度器 (Application Bootstrap)
 * 职责：组装 Vue 3 响应式上下文，协调 WenjinAPI、WenjinTheme、WenjinFormatters、
 *       WenjinCatalogChart 及 WenjinComparison 模块，驱动四重视图切换与用户交互。
 * ============================================================================
 */

(function (window) {
  'use strict';

  const { createApp, ref, reactive, computed, onMounted, nextTick, watch } = Vue;
  const { ElMessage, ElNotification } = ElementPlus;

  const app = createApp({
    setup() {
      // 1. 核心导航与主题状态
      const activeTab = ref('search');
      const isDark = ref(window.WenjinTheme.isDark());
      const stats = reactive({
        catalog_journals: 136,
        chinese_core_count: 27,
        cas_warning_count: 38,
        track_records: 0
      });

      // 2. 选刊检索模块状态
      const searchQuery = ref('');
      const searching = ref(false);
      const refreshing = ref(false);
      const ruleResult = ref(null);
      const candidatesResult = ref([]);

      // 允许通过 ?mock=1 路由参数瞬时载入样本期刊以供视觉核验，默认按用户检索驱动
      const urlParams = new URLSearchParams(window.location.search);
      const isMockPreview = urlParams.get('mock') === '1';

      const currentJournal = ref(isMockPreview ? {
        type: 'journal',
        name: '中国中药杂志',
        in_catalog: true,
        catalog: {
          name: '中国中药杂志',
          level: 'A2',
          category: 'A类2级（CSCD核心版）',
          publisher: '中国科学技术协会 / 中国药学会、中国中医科学院中药研究所',
          issn: '1001-5302',
          cn: '11-2272/R'
        },
        kb: {
          basic: {
            name: '中国中药杂志',
            issn: '1001-5302',
            cn: '11-2272/R',
            publisher: '中国药学会 / 中国中医科学院中药研究所'
          },
          indexes: {
            indexes_verified: true,
            cscd_core: true,
            pkucore: true,
            extra: ['中国科技期刊卓越行动计划', '中国科技核心(CSTPCD)', '北大核心(第10版)']
          },
          indexes_note: '全国中文核心期刊库确认：CSCD核心库(2023-2024)；北大中文核心',
          impact_factor: { if_val: '4.852', jcr_zone: 'Q1' },
          editor_in_chief: {
            name: '黄璐琦',
            affiliation: '中国工程院院士 / 中国中医科学院院所'
          },
          scope: '中药资源、鉴定、栽培、中药化学与分析、制剂工艺、药理毒理及临床合理用药。重点资助国家级重大课题论著。',
          review_cycle: '官方初审约1-2周，同行评议约1-2个月，全流程约3-5个月',
          publication_mode: '传统订阅制 (非OA)；半月刊',
          apc_fee: '常规版面审理费与版面费（根据排版页数核算）',
          submission_url: 'http://www.cjcmm.com.cn'
        },
        warning_info: null,
        level_info: {
          level: 'A2',
          label: 'A类2级 (重点期刊)',
          reasons: [
            '索引命中：《中国科学引文数据库(CSCD)》核心版 → A2',
            '索引命中：《中文核心期刊要目总览》 → A3'
          ],
          upgraded: false
        }
      } : null);

      if (isMockPreview) {
        searchQuery.value = '中国中药杂志';
      }

      // 3. 智能筛选模块状态与分页
      const filterScopeSource = ref('official'); // 'official' | 'track' | 'all'
      const filterLevel = ref('');
      const filterOA = ref('');
      const filterScope = ref('');
      const filterRecords = ref([]);
      const filterLoading = ref(false);
      const filterPage = ref(1);
      const filterPageSize = ref(20);

      const pagedFilterRecords = computed(() => {
        const start = (filterPage.value - 1) * filterPageSize.value;
        return filterRecords.value.slice(start, start + filterPageSize.value);
      });

      // 4. 决策台账模块状态 (支持多用户独立隔离与分页)
      const currentUserId = ref(window.WenjinAPI.getUserId());
      const trackRecords = ref([]);
      const trackSearch = ref('');
      const trackLoading = ref(false);
      const trackPage = ref(1);
      const trackPageSize = ref(20);
      const userDialogVisible = ref(false);
      const newUserIdInput = ref('');

      const gzucmsPage = ref(1);
      const gzucmsPageSize = ref(20);

      // 5. 官方目录与权威索引全景定位器状态
      const catalogCategories = ref([]);
      const catalogLevelFilter = ref('ALL');
      const catalogSearch = ref('');
      const catalogLoading = ref(false);

      const catalogModalVisible = ref(false);
      const activeIndexTab = ref('gzucms'); // 'gzucms' | 'cscd' | 'pkucore' | 'cas_zone' | 'cas_warning' | 'rules'
      const locatorQuery = ref('');
      const locatorLoading = ref(false);
      const locatorResult = ref(null);

      // 中科院 1~4 区国际期刊开源历史镜像状态 (21,772 本)
      const casJournals = ref([]);
      const casTotal = ref(0);
      const casPage = ref(1);
      const casPageSize = ref(20);
      const casZoneFilter = ref('');
      const casCatFilter = ref('ALL');
      const casTopFilter = ref('');
      const casWosFilter = ref(''); // '' | 'SCIE' | 'SSCI' | 'AHCI' | 'ESCI'
      const casSearch = ref('');
      const casLoading = ref(false);
      const casCategories = ref([]);
      const casDisclaimer = ref('⚠️ 本中科院分区数据来源于公开历史开源镜像整理版，其中科院分区在线服务已于2026-09-30关停。仅供选刊参考，实际成果认定请以论文发表当年中国科学院文献情报中心官方最新版本为准。');

      // 北大中文核心与 CSCD 交互分页与学科筛选状态
      const pkuPage = ref(1);
      const pkuPageSize = ref(20);
      const pkuSubjectFilter = ref('ALL');
      const pkuSearch = ref('');

      const cscdPage = ref(1);
      const cscdPageSize = ref(20);
      const cscdTypeFilter = ref('ALL'); // 'ALL' | 'core' | 'ext'
      const cscdSearch = ref('');

      const allIndexes = reactive({
        gzucms: { meta: {}, categories: [], journals: [], rules: [] },
        chinese_core: { meta: {}, journals: [] },
        cas_warning: { meta: {}, journals: [] }
      });

      // 6. 多维对比矩阵状态
      const comparisonList = ref(window.WenjinComparison.getList());
      const comparisonDialogVisible = ref(false);

      // ========================================================================
      // 主题与动效驱动
      // ========================================================================
      const toggleTheme = () => {
        isDark.value = window.WenjinTheme.toggle();
        ElMessage.info(`已切换至${isDark.value ? '深墨雅夜' : '宣纸温润'}学术模式`);
        if (catalogCategories.value && catalogCategories.value.length) {
          window.WenjinCatalogChart.render('catalogChartCanvas', catalogCategories.value, isDark.value);
        }
      };

      // ========================================================================
      // 数据接口层交互 (WenjinAPI)
      // ========================================================================

      // 统计概览加载
      const fetchStats = async () => {
        try {
          const data = await window.WenjinAPI.getStats();
          Object.assign(stats, data);
        } catch (e) {
          console.warn('[App] 统计数据读取异常:', e);
        }
      };

      // 核心级联检索
      const handleSearch = async () => {
        const q = searchQuery.value.trim();
        if (!q) {
          ElMessage.warning('请输入期刊全称、ISSN、CN 或 检索规则');
          return;
        }

        searching.value = true;
        currentJournal.value = null;
        ruleResult.value = null;
        candidatesResult.value = [];

        try {
          const data = await window.WenjinAPI.search(q);
          searching.value = false;

          if (data.type === 'journal') {
            currentJournal.value = data;
            fetchStats();
            if (data.level_info && data.level_info.level === 'A1' && window.confetti) {
              window.confetti({ particleCount: 80, spread: 65, origin: { y: 0.6 } });
            }
          } else if (data.type === 'rule') {
            ruleResult.value = data;
          } else if (data.type === 'rule_need_zone') {
            ElMessage.warning(data.message);
          } else if (data.type === 'candidates') {
            candidatesResult.value = data.candidates || [];
          } else {
            ElMessage.error(data.message || '未在目录及知识库中检索到该期刊');
          }
        } catch (e) {
          searching.value = false;
          ElMessage.error(e.message || '检索请求异常，请检查服务连接');
        }
      };

      // 联网查证与深度核验 (Gemini + OpenAlex + DOAJ)
      const handleRefresh = async () => {
        const q = (currentJournal.value ? currentJournal.value.name : searchQuery.value).trim();
        if (!q) {
          ElMessage.warning('请输入期刊全称后再进行联网查证');
          return;
        }

        refreshing.value = true;
        try {
          const data = await window.WenjinAPI.refresh(q);
          refreshing.value = false;

          if (data.status === 'success') {
            const successMsg = data.message || `✓ 成功联网查证《${data.journal}》并已同步回写知识库！`;
            ElMessage.success(successMsg);
            searchQuery.value = data.journal;
            await handleSearch();
            await loadTrackRecords();
            await loadStats();
          } else {
            ElMessage.warning(data.message || '联网核验未完成');
          }
        } catch (e) {
          refreshing.value = false;
          ElMessage.error(e.message || '联网查证失败，请确保本地网络畅通');
        }
      };

      // 快捷点击检索
      const quickSearch = (name) => {
        searchQuery.value = name.replace(/（.*?）/g, '').trim();
        activeTab.value = 'search';
        handleSearch();
      };

      // 选刊决策简报复制
      const copyBrief = async () => {
        if (!currentJournal.value) return;
        const text = window.WenjinFormatters.generateBriefText(currentJournal.value);
        const ok = await window.WenjinFormatters.copyToClipboard(text);
        if (ok) {
          ElMessage.success('已成功生成并复制选刊决策简报至剪贴板！');
        } else {
          ElMessage.error('复制简报失败，请手动选取');
        }
      };

      // 通用文本复制
      const copyText = async (text) => {
        const ok = await window.WenjinFormatters.copyToClipboard(text);
        if (ok) {
          ElMessage.success('已复制到剪贴板！');
        } else {
          ElMessage.error('复制失败');
        }
      };

      // 多维横向对比管理
      const addToComparison = (journalData) => {
        if (!journalData) return;
        const res = window.WenjinComparison.add(journalData);
        comparisonList.value = window.WenjinComparison.getList();

        if (res.success) {
          ElMessage.success(`已将《${journalData.name}》加入对比列表`);
        } else {
          ElMessage.warning(res.reason);
          comparisonDialogVisible.value = true;
        }
      };

      const removeFromComparison = (index) => {
        window.WenjinComparison.remove(index);
        comparisonList.value = window.WenjinComparison.getList();
      };

      // 通用防抖工具函数
      const debounce = (fn, delay = 250) => {
        let timer = null;
        return (...args) => {
          if (timer) clearTimeout(timer);
          timer = setTimeout(() => fn(...args), delay);
        };
      };

      // 统计兼容性别名
      const loadStats = fetchStats;

      // 筛选数据加载
      const loadFilterRecords = async () => {
        const conds = [];
        if (filterLevel.value) conds.push(`level=${filterLevel.value}`);
        if (filterOA.value) conds.push(`oa=${filterOA.value}`);
        if (filterScope.value) conds.push(`scope=${filterScope.value.trim()}`);

        filterLoading.value = true;
        try {
          const data = await window.WenjinAPI.filterTrack(conds.join(',') || 'all', filterScopeSource.value);
          filterRecords.value = data.records || [];
          filterPage.value = 1;
        } catch (e) {
          ElMessage.error('筛选数据加载失败');
        } finally {
          filterLoading.value = false;
        }
      };

      // 防抖触发的筛选检索
      const debouncedLoadFilterRecords = debounce(() => {
        loadFilterRecords();
      }, 300);

      // 中科院 1~4 区开源历史镜像数据加载与检索
      const fetchCasCategories = async () => {
        try {
          const res = await window.WenjinAPI.getCasCategories();
          casCategories.value = res.categories || [];
        } catch (e) {
          console.warn('[App] 加载中科院学科分类异常:', e);
        }
      };

      const fetchCasJournals = async () => {
        casLoading.value = true;
        try {
          const res = await window.WenjinAPI.getCasJournals({
            zone: casZoneFilter.value || undefined,
            category: casCatFilter.value !== 'ALL' ? casCatFilter.value : undefined,
            is_top: casTopFilter.value !== '' ? casTopFilter.value : undefined,
            wos_type: (casWosFilter.value && casWosFilter.value !== 'ALL') ? casWosFilter.value : undefined,
            q: casSearch.value || undefined,
            page: casPage.value,
            page_size: casPageSize.value,
          });
          casJournals.value = res.journals || [];
          casTotal.value = res.total || 0;
          if (res.disclaimer) casDisclaimer.value = res.disclaimer;
        } catch (e) {
          ElMessage.error('国际期刊列表加载失败');
        } finally {
          casLoading.value = false;
        }
      };

      const openCasZoneFullList = (zone, wosType = '') => {
        casZoneFilter.value = zone ? String(zone) : '';
        casWosFilter.value = wosType || '';
        casPage.value = 1;
        catalogModalVisible.value = true;
        activeIndexTab.value = 'cas_zone';
        fetchCasJournals();
      };

      // 台账数据加载
      const loadTrackRecords = async () => {
        trackLoading.value = true;
        try {
          const data = await window.WenjinAPI.getTrack();
          trackRecords.value = data.records || [];
        } catch (e) {
          ElMessage.error('台账数据加载失败');
        } finally {
          trackLoading.value = false;
        }
      };

      // 台账本地搜索过滤与分页
      const filteredTrackRecords = computed(() => {
        const q = trackSearch.value.trim().toLowerCase();
        if (!q) return trackRecords.value;
        return trackRecords.value.filter(
          (r) =>
            (r['期刊名称'] || '').toLowerCase().includes(q) ||
            (r['ISSN / CN'] || '').toLowerCase().includes(q) ||
            (r['广中医认定级别'] || '').toLowerCase().includes(q)
        );
      });

      watch(trackSearch, () => {
        trackPage.value = 1;
      });

      const pagedTrackRecords = computed(() => {
        const start = (trackPage.value - 1) * trackPageSize.value;
        return filteredTrackRecords.value.slice(start, start + trackPageSize.value);
      });

      // 从当前台账中删除指定期刊
      const handleDeleteTrack = async (journalName) => {
        if (!journalName) return;
        try {
          const res = await window.WenjinAPI.deleteTrack(journalName);
          ElMessage.success(res.message || `已从台账中移出《${journalName}》`);
          await loadTrackRecords();
          await loadStats();
        } catch (e) {
          ElMessage.error(e.message || '删除期刊失败');
        }
      };

      // 清空当前用户的台账
      const handleClearTrack = async () => {
        try {
          const res = await window.WenjinAPI.clearTrack();
          ElMessage.success(res.message || '选刊决策台账已成功清空');
          await loadTrackRecords();
          await loadStats();
        } catch (e) {
          ElMessage.error(e.message || '清空台账失败');
        }
      };

      // 判断某期刊是否在当前台账中
      const isJournalInTrack = (journalName) => {
        if (!journalName) return false;
        const target = journalName.trim().toLowerCase();
        return trackRecords.value.some(
          (r) => (r['期刊名称'] || '').trim().toLowerCase() === target
        );
      };

      // 切换/添加期刊至台账
      const handleToggleTrack = async (journalName) => {
        if (!journalName) return;
        if (isJournalInTrack(journalName)) {
          await handleDeleteTrack(journalName);
        } else {
          try {
            const res = await window.WenjinAPI.addToTrack(journalName);
            ElMessage.success(res.message || `已成功将《${journalName}》收录至台账`);
            await loadTrackRecords();
            await loadStats();
          } catch (e) {
            ElMessage.error(e.message || '收录台账失败');
          }
        }
      };

      // 用户台账账户切换与新建
      const openUserDialog = () => {
        newUserIdInput.value = currentUserId.value;
        userDialogVisible.value = true;
      };

      const handleSwitchUser = async () => {
        const uid = (newUserIdInput.value || '').trim();
        if (!uid) {
          ElMessage.warning('请输入有效的台账账户名称或标识');
          return;
        }
        window.WenjinAPI.setUserId(uid);
        currentUserId.value = window.WenjinAPI.getUserId();
        userDialogVisible.value = false;
        ElMessage.success(`已切换至台账账户: ${currentUserId.value}`);
        await loadTrackRecords();
        await loadStats();
      };

      const handleCreateNewUser = async () => {
        const randStr = Math.random().toString(36).substring(2, 10);
        const newUid = `user_${randStr}`;
        window.WenjinAPI.setUserId(newUid);
        currentUserId.value = newUid;
        userDialogVisible.value = false;
        ElMessage.success(`已新建独立台账账户: ${currentUserId.value}`);
        await loadTrackRecords();
        await loadStats();
      };

      // 官方目录数据加载
      const loadCatalog = async () => {
        catalogLoading.value = true;
        try {
          const data = await window.WenjinAPI.getCatalog();
          catalogCategories.value = data.categories || [];
          nextTick(() => {
            window.WenjinCatalogChart.render('catalogChartCanvas', catalogCategories.value, isDark.value);
          });
        } catch (e) {
          ElMessage.error('官方目录加载失败');
        } finally {
          catalogLoading.value = false;
        }
      };

      // 官方目录本地层级与关键字过滤
      const filteredCatalogCategories = computed(() => {
        const lvl = catalogLevelFilter.value;
        const search = catalogSearch.value.trim().toLowerCase();

        return catalogCategories.value
          .map((cat) => {
            if (lvl !== 'ALL' && cat.level !== lvl) {
              return { ...cat, items: [] };
            }
            const filteredItems = (cat.items || []).filter(
              (item) => !search || item.name.toLowerCase().includes(search)
            );
            return { ...cat, items: filteredItems };
          })
          .filter((cat) => cat.items.length > 0);
      });

      // ========================================================================
      // 权威索引目录全景预览与跨目录期刊精准定位引擎
      // ========================================================================
      const catalogModalFilter = ref('ALL');

      let indexesLoaded = false;
      const loadAllIndexes = async () => {
        if (indexesLoaded) return;
        try {
          const data = await window.WenjinAPI.getAllIndexes();
          if (data) {
            if (data.gzucms) Object.assign(allIndexes.gzucms, data.gzucms);
            if (data.chinese_core) {
              allIndexes.chinese_core.meta = data.chinese_core.meta || {};
              allIndexes.chinese_core.journals = (window.Vue && window.Vue.markRaw)
                ? window.Vue.markRaw(data.chinese_core.journals || [])
                : (data.chinese_core.journals || []);
            }
            if (data.cas_warning) Object.assign(allIndexes.cas_warning, data.cas_warning);
            indexesLoaded = true;
          }
        } catch (e) {
          console.warn('[App] 权威索引库全景数据加载异常:', e);
        }
      };

      const performLocate = async (targetQuery = null, preferredTab = null) => {
        const q = (targetQuery !== null ? targetQuery : locatorQuery.value).trim();
        if (!q) {
          locatorResult.value = null;
          return;
        }
        locatorQuery.value = q;
        locatorLoading.value = true;
        try {
          const res = await window.WenjinAPI.locateInIndexes(q);
          locatorResult.value = res;
          if (preferredTab) {
            activeIndexTab.value = preferredTab;
          } else if (res && res.found && res.matches) {
            if (res.matches.gzucms && res.matches.gzucms.length > 0) {
              activeIndexTab.value = 'gzucms';
            } else if (res.matches.cscd && res.matches.cscd.length > 0) {
              activeIndexTab.value = 'cscd';
            } else if (res.matches.pkucore && res.matches.pkucore.length > 0) {
              activeIndexTab.value = 'pkucore';
            } else if (res.matches.cas_warning && res.matches.cas_warning.length > 0) {
              activeIndexTab.value = 'cas_warning';
            } else if (res.matches.rules && res.matches.rules.length > 0) {
              activeIndexTab.value = 'rules';
            }
          }
        } catch (e) {
          ElMessage.error('目录定位检索异常，请重试');
        } finally {
          locatorLoading.value = false;
        }
      };

      const openCatalogModal = async (tab = 'gzucms', targetName = '', levelFilter = 'ALL', wosType = '') => {
        loadAllIndexes(); // 弹窗展开时按需加载
        catalogModalVisible.value = true;
        activeIndexTab.value = tab;
        if (levelFilter) {
          catalogModalFilter.value = levelFilter;
        }
        if (wosType) {
          casWosFilter.value = wosType;
        }
        if (tab === 'cas_zone') {
          fetchCasJournals();
        }
        if (targetName) {
          locatorQuery.value = targetName;
          await performLocate(targetName, tab);
        }
      };

      const handleTabChange = (tabName) => {
        if (tabName === 'cas_zone' && casJournals.value.length === 0) {
          fetchCasJournals();
        }
      };

      watch(activeIndexTab, (newTab) => {
        if (newTab === 'cas_zone' && casJournals.value.length === 0) {
          fetchCasJournals();
        }
      });

      const locateCurrentJournal = async () => {
        if (currentJournal.value && currentJournal.value.name) {
          await performLocate(currentJournal.value.name);
        } else {
          ElMessage.info('当前未检索期刊，请输入刊名进行定位');
        }
      };

      const clearLocator = () => {
        locatorQuery.value = '';
        locatorResult.value = null;
      };

      const jumpFromCatalogToSearch = (journalName) => {
        if (!journalName) return;
        catalogModalVisible.value = false;
        activeTab.value = 'search';
        searchQuery.value = journalName;
        handleSearch();
      };

      // 辅助判断某一行是否在当前匹配结果中 (O(1) 哈希索引优化)
      const locatedMatchesSet = computed(() => {
        if (!locatorResult.value || !locatorResult.value.matches) return new Set();
        let key = activeIndexTab.value;
        if (key === 'chinese_core') key = 'cscd';
        const matches = locatorResult.value.matches[key] || [];
        const s = new Set();
        matches.forEach((m) => {
          const mName = (m.name || '').trim().toLowerCase();
          const mIssn = (m.issn || '').replace(/[^0-9Xx]/g, '').toUpperCase();
          if (mName) s.add(mName);
          if (mIssn) s.add(mIssn);
        });
        return s;
      });

      const isRowLocated = (row, catalogKey) => {
        if (!locatedMatchesSet.value.size) return false;
        const rowName = (row.name || '').trim().toLowerCase();
        const rowIssn = (row.issn || '').replace(/[^0-9Xx]/g, '').toUpperCase();
        return (rowName && locatedMatchesSet.value.has(rowName)) || (rowIssn && locatedMatchesSet.value.has(rowIssn));
      };

      const catalogTableRowClass = ({ row }) => {
        let key = activeIndexTab.value;
        if (key === 'chinese_core') key = 'cscd';
        return isRowLocated(row, key) ? 'row-located-highlight' : '';
      };

      // 广中医308号全量期刊扁平化列表（附带官方序号与分类）
      const filteredGzucmsFlat = computed(() => {
        const cats = allIndexes.gzucms.categories || catalogCategories.value || [];
        const lvl = catalogModalFilter.value;
        const q = locatorQuery.value.trim().toLowerCase();
        let list = [];
        cats.forEach(cat => {
          if (lvl !== 'ALL' && cat.level !== lvl) return;
          (cat.items || []).forEach((item, idx) => {
            list.push({
              ...item,
              level: cat.level,
              category: cat.name,
              position_index: idx + 1,
              official_serial: item.serial || String(idx + 1),
              position_desc: `【${cat.name}】第 ${item.serial || (idx + 1)} 项`
            });
          });
        });
        if (q && (!locatorResult.value || !locatorResult.value.found)) {
          list = list.filter(item => 
            item.name.toLowerCase().includes(q) ||
            (item.publisher && item.publisher.toLowerCase().includes(q)) ||
            (item.remark && item.remark.toLowerCase().includes(q))
          );
        }
        return list;
      });

      watch(catalogModalFilter, () => {
        gzucmsPage.value = 1;
      });

      const pagedGzucmsFlat = computed(() => {
        const start = (gzucmsPage.value - 1) * gzucmsPageSize.value;
        return filteredGzucmsFlat.value.slice(start, start + gzucmsPageSize.value);
      });

      // CSCD 核心与扩展库列表
      const filteredCscdList = computed(() => {
        const journals = allIndexes.chinese_core.journals || [];
        const q = (cscdSearch.value || locatorQuery.value || '').trim().toLowerCase();
        const typeF = cscdTypeFilter.value;
        let list = journals.filter(j => j.cscd_core || j.cscd_ext);
        if (typeF === 'core') {
          list = list.filter(j => j.cscd_core);
        } else if (typeF === 'ext') {
          list = list.filter(j => j.cscd_ext);
        }
        let mapped = list.map((j, idx) => ({
          ...j,
          position_index: idx + 1,
          cscd_type: j.cscd_core ? 'CSCD核心库 (从高升A2)' : 'CSCD扩展库 (认定A4)',
          position_desc: `CSCD 数据库第 ${idx + 1} 项`
        }));
        if (q && (!locatorResult.value || !locatorResult.value.found || cscdSearch.value)) {
          mapped = mapped.filter(j => 
            (j.name && j.name.toLowerCase().includes(q)) || 
            (j.issn && j.issn.toLowerCase().includes(q)) ||
            (j.cn && j.cn.toLowerCase().includes(q)) ||
            (j.publisher && j.publisher.toLowerCase().includes(q)) ||
            (j.subject && j.subject.toLowerCase().includes(q))
          );
        }
        return mapped;
      });

      const pagedCscdList = computed(() => {
        const start = (cscdPage.value - 1) * cscdPageSize.value;
        return filteredCscdList.value.slice(start, start + cscdPageSize.value);
      });

      // 北大中文核心目录学科分类
      const pkuSubjects = computed(() => {
        const journals = allIndexes.chinese_core.journals || [];
        const set = new Set();
        journals.filter(j => j.pkucore && j.subject).forEach(j => set.add(j.subject));
        return Array.from(set).sort();
      });

      // 北大中文核心目录列表
      const filteredPkuList = computed(() => {
        const journals = allIndexes.chinese_core.journals || [];
        const q = (pkuSearch.value || locatorQuery.value || '').trim().toLowerCase();
        const subj = pkuSubjectFilter.value;
        let list = journals.filter(j => j.pkucore);
        if (subj !== 'ALL') {
          list = list.filter(j => j.subject === subj);
        }
        let mapped = list.map((j, idx) => ({
          ...j,
          position_index: idx + 1,
          pku_version: '北大核心 (第10版/2023-2024最新版)',
          position_desc: `北大中文核心第 ${idx + 1} 项`
        }));
        if (q && (!locatorResult.value || !locatorResult.value.found || pkuSearch.value)) {
          mapped = mapped.filter(j => 
            (j.name && j.name.toLowerCase().includes(q)) || 
            (j.issn && j.issn.toLowerCase().includes(q)) ||
            (j.cn && j.cn.toLowerCase().includes(q)) ||
            (j.publisher && j.publisher.toLowerCase().includes(q)) ||
            (j.subject && j.subject.toLowerCase().includes(q))
          );
        }
        return mapped;
      });

      const pagedPkuList = computed(() => {
        const start = (pkuPage.value - 1) * pkuPageSize.value;
        return filteredPkuList.value.slice(start, start + pkuPageSize.value);
      });

      // 中科院国际预警期刊名单列表
      const filteredCasWarningList = computed(() => {
        const journals = allIndexes.cas_warning.journals || [];
        const q = locatorQuery.value.trim().toLowerCase();
        let list = journals.map((j, idx) => ({
          ...j,
          position_index: idx + 1,
          position_desc: `中科院预警名单第 ${idx + 1} 项`
        }));
        if (q && (!locatorResult.value || !locatorResult.value.found)) {
          list = list.filter(j => 
            (j.name && j.name.toLowerCase().includes(q)) ||
            (j.issn && j.issn.toLowerCase().includes(q)) ||
            (j.publisher && j.publisher.toLowerCase().includes(q)) ||
            (j.reason && j.reason.toLowerCase().includes(q))
          );
        }
        return list;
      });

      // 广中医重要期刊折算规则对照列表
      const filteredRulesList = computed(() => {
        const rules = allIndexes.gzucms.rules || [];
        const q = locatorQuery.value.trim().toLowerCase();
        let list = rules.map((r, idx) => ({
          ...r,
          position_index: idx + 1,
          position_desc: `折算规则条目第 ${idx + 1} 条`
        }));
        if (q && (!locatorResult.value || !locatorResult.value.found)) {
          list = list.filter(r => 
            (r.name && r.name.toLowerCase().includes(q)) ||
            (r.desc && r.desc.toLowerCase().includes(q)) ||
            (r.level && r.level.toLowerCase().includes(q))
          );
        }
        return list;
      });

      // 生命周期钩子
      onMounted(() => {
        window.WenjinTheme.init();
        fetchStats();
        loadFilterRecords();
        loadTrackRecords();
        loadCatalog();
        fetchCasCategories();

        // 异步空闲加载全量索引库，避免阻塞首屏渲染与检索
        setTimeout(() => {
          loadAllIndexes();
        }, 150);

        // 支持 URL 路由参数驱动自动化与外链直达
        const params = new URLSearchParams(window.location.search);
        const queryJournal = params.get('q');
        const themeParam = params.get('theme');

        if (themeParam === 'dark' && !isDark.value) {
          toggleTheme();
        } else if (themeParam === 'light' && isDark.value) {
          toggleTheme();
        }

        if (queryJournal) {
          searchQuery.value = decodeURIComponent(queryJournal);
          handleSearch();
        }
      });

      return {
        activeTab,
        isDark,
        stats,
        searchQuery,
        searching,
        refreshing,
        currentJournal,
        ruleResult,
        candidatesResult,
        filterScopeSource,
        filterLevel,
        filterOA,
        filterScope,
        filterRecords,
        filterLoading,
        filterPage,
        filterPageSize,
        pagedFilterRecords,
        debouncedLoadFilterRecords,
        currentUserId,
        userDialogVisible,
        newUserIdInput,
        trackRecords,
        trackSearch,
        trackLoading,
        trackPage,
        trackPageSize,
        pagedTrackRecords,
        filteredTrackRecords,
        handleDeleteTrack,
        handleClearTrack,
        isJournalInTrack,
        handleToggleTrack,
        openUserDialog,
        handleSwitchUser,
        handleCreateNewUser,
        catalogCategories,
        catalogLevelFilter,
        catalogSearch,
        catalogLoading,
        filteredCatalogCategories,
        comparisonList,
        comparisonDialogVisible,

        // 权威索引全景预览与跨目录精准定位状态
        catalogModalVisible,
        activeIndexTab,
        locatorQuery,
        locatorLoading,
        locatorResult,
        allIndexes,
        catalogModalFilter,
        filteredGzucmsFlat,
        pagedGzucmsFlat,
        gzucmsPage,
        gzucmsPageSize,
        filteredCscdList,
        pagedCscdList,
        cscdPage,
        cscdPageSize,
        cscdTypeFilter,
        cscdSearch,
        filteredPkuList,
        pagedPkuList,
        pkuPage,
        pkuPageSize,
        pkuSubjectFilter,
        pkuSearch,
        pkuSubjects,
        filteredCasWarningList,
        filteredRulesList,

        // 中科院 1~4 区国际期刊开源历史镜像状态与方法
        casJournals,
        casTotal,
        casPage,
        casPageSize,
        casZoneFilter,
        casCatFilter,
        casTopFilter,
        casWosFilter,
        casSearch,
        casLoading,
        casCategories,
        casDisclaimer,
        fetchCasJournals,
        fetchCasCategories,
        openCasZoneFullList,

        // 交互动作
        toggleTheme,
        handleSearch,
        handleRefresh,
        quickSearch,
        copyBrief,
        copyText,
        addToComparison,
        removeFromComparison,
        loadFilterRecords,
        openCatalogModal,
        performLocate,
        locateCurrentJournal,
        clearLocator,
        jumpFromCatalogToSearch,
        handleTabChange,
        catalogTableRowClass,
        isRowLocated,
        openDocs: () => window.open('/docs', '_blank'),
        exportUrl: computed(() => window.WenjinAPI.getExportTrackUrl()),

        // 格式化与渲染适配器 (安全取值器)
        getLevelTagType: window.WenjinFormatters.getLevelTagType,
        getLevelTagTypeFromLabel: window.WenjinFormatters.getLevelTagTypeFromLabel,
        getIssnCnDisplay: window.WenjinFormatters.getIssnCnDisplay,
        getScoreDisplay: window.WenjinFormatters.getScoreDisplay,
        getKnownIndexes: window.WenjinFormatters.getKnownIndexes,
        getPublisher: window.WenjinFormatters.getPublisher,
        getLevelLabel: window.WenjinFormatters.getLevelLabel,
        getLevelCode: window.WenjinFormatters.getLevelCode,
        getReasons: window.WenjinFormatters.getReasons,
        isUpgraded: window.WenjinFormatters.isUpgraded,
        isWarned: window.WenjinFormatters.isWarned,
        getWarningDetail: window.WenjinFormatters.getWarningDetail,
        getIndexesVerified: window.WenjinFormatters.getIndexesVerified,
        getIndexesNote: window.WenjinFormatters.getIndexesNote,
        getImpactNote: window.WenjinFormatters.getImpactNote,
        getEditorName: window.WenjinFormatters.getEditorName,
        getEditorAffiliation: window.WenjinFormatters.getEditorAffiliation,
        getScope: window.WenjinFormatters.getScope,
        getReviewCycle: window.WenjinFormatters.getReviewCycle,
        getPublicationMode: window.WenjinFormatters.getPublicationMode,
        getApcFee: window.WenjinFormatters.getApcFee,
        getSubmissionUrl: window.WenjinFormatters.getSubmissionUrl,
        isHttpUrl: window.WenjinFormatters.isHttpUrl,

        // Element Plus 图标
        Search: ElementPlusIconsVue.Search,
        Operation: ElementPlusIconsVue.Operation,
        Filter: ElementPlusIconsVue.Filter,
        Document: ElementPlusIconsVue.Document,
        Notebook: ElementPlusIconsVue.Notebook,
        ScaleToOriginal: ElementPlusIconsVue.ScaleToOriginal,
        Connection: ElementPlusIconsVue.Connection,
        Refresh: ElementPlusIconsVue.Refresh,
        DocumentCopy: ElementPlusIconsVue.DocumentCopy,
        Download: ElementPlusIconsVue.Download,
        TopRight: ElementPlusIconsVue.TopRight,
        Sunny: ElementPlusIconsVue.Sunny,
        Moon: ElementPlusIconsVue.Moon,
        Link: ElementPlusIconsVue.Link,
        Star: ElementPlusIconsVue.Star,
        Reading: ElementPlusIconsVue.Reading,
        Warning: ElementPlusIconsVue.Warning,
        WarningFilled: ElementPlusIconsVue.WarningFilled,
        InfoFilled: ElementPlusIconsVue.InfoFilled,
        List: ElementPlusIconsVue.List,
        School: ElementPlusIconsVue.School,
        Tickets: ElementPlusIconsVue.Tickets,
        Medal: ElementPlusIconsVue.Medal,
        Calendar: ElementPlusIconsVue.Calendar,
        Collection: ElementPlusIconsVue.Collection,
        Grid: ElementPlusIconsVue.Grid,
        PieChart: ElementPlusIconsVue.PieChart,
        DataLine: ElementPlusIconsVue.DataLine,
        User: ElementPlusIconsVue.User,
        Timer: ElementPlusIconsVue.Timer,
        Coin: ElementPlusIconsVue.Coin,
        Promotion: ElementPlusIconsVue.Promotion,
        Position: ElementPlusIconsVue.Position || ElementPlusIconsVue.Location,
        Aim: ElementPlusIconsVue.Aim || ElementPlusIconsVue.Search,
        Check: ElementPlusIconsVue.Check,
        Close: ElementPlusIconsVue.Close,
        View: ElementPlusIconsVue.View,
        Compass: ElementPlusIconsVue.Compass,
        Location: ElementPlusIconsVue.Location,
        Delete: ElementPlusIconsVue.Delete,
        Edit: ElementPlusIconsVue.Edit,
        Plus: ElementPlusIconsVue.Plus
      };
    }
  });

  app.use(ElementPlus);
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
    app.component(key.toLowerCase(), component);
    const kebab = key.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase();
    app.component(kebab, component);
  }
  window.__vue_errors = [];
  window.__vue_warnings = [];
  app.config.errorHandler = (err, vm, info) => {
    window.__vue_errors.push({ message: err.message, stack: err.stack, info });
    console.error('=== VUE ERROR ===', err.message, info, err.stack);
  };
  app.config.warnHandler = (msg, vm, trace) => {
    window.__vue_warnings.push({ msg, trace });
    console.warn('=== VUE WARN ===', msg, trace);
  };
  window.__vm = app.mount('#app');

})(window);
