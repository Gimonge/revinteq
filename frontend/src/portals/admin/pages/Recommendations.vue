<template>
  <div style="display:flex;flex-direction:column;gap:20px" class="fade-up">

    <div class="rv-page-header">
      <div>
        <div class="rv-page-title">Intelligence Centre</div>
        <div class="rv-page-sub">Actionable insights, recommendations and ad performance — admin only</div>
      </div>
    </div>

    <div class="rv-stat-grid">
      <div class="rv-sc card-reveal" style="cursor:pointer" :class="{active:tab==='recs'}" @click="tab='recs'">
        <span class="rv-sc-icon">💡</span>
        <div class="rv-sc-label">Recommendations</div>
        <div class="rv-sc-value">{{ recs.length }}</div>
        <div class="rv-sc-sub">{{ recs.filter(r=>r.priority==='HIGH').length }} high priority</div>
      </div>
      <div class="rv-sc b card-reveal" style="cursor:pointer;animation-delay:.05s" @click="tab='ads'">
        <span class="rv-sc-icon">📊</span>
        <div class="rv-sc-label">Ad Intelligence</div>
        <div class="rv-sc-value">{{ adAlerts.length }}</div>
        <div class="rv-sc-sub">{{ allCampaigns.length }} campaigns tracked</div>
      </div>
      <div class="rv-sc a card-reveal" style="cursor:pointer;animation-delay:.1s" @click="tab='goals'">
        <span class="rv-sc-icon">🎯</span>
        <div class="rv-sc-label">Goal Alerts</div>
        <div class="rv-sc-value">{{ goalAlerts.filter(g=>g.urgent).length }}</div>
        <div class="rv-sc-sub">{{ clients.filter(c=>c.goal_status==='behind').length }} clients behind goal</div>
      </div>
      <div class="rv-sc p card-reveal" style="cursor:pointer;animation-delay:.15s" @click="tab='pipeline'">
        <span class="rv-sc-icon">🔥</span>
        <div class="rv-sc-label">Pipeline Alerts</div>
        <div class="rv-sc-value">{{ pipelineAlerts.length }}</div>
        <div class="rv-sc-sub">Stale deals &amp; follow-ups needed</div>
      </div>
    </div>

    <div style="display:flex;gap:4px;background:var(--bg);border-radius:var(--r-lg);padding:5px;border:1px solid var(--border)">
      <button v-for="t in tabs" :key="t.key"
        @click="tab=t.key"
        :class="tab===t.key ? 'rv-btn rv-btn-p' : 'rv-btn rv-btn-s'"
        style="flex:1;justify-content:center;font-size:12px;padding:7px 10px">
        {{ t.icon }} {{ t.label }}
        <span v-if="t.count" class="rv-nav-badge" style="background:rgba(0,0,0,.1);color:inherit">{{ t.count }}</span>
      </button>
    </div>

    <!-- TAB 1 — RECOMMENDATIONS -->
    <div v-if="tab==='recs'">
      <div v-if="loadingRecs" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="recs.length===0" class="rv-empty">
        <div class="rv-empty-icon">✅</div>
        <div class="rv-empty-title">All clear — no pending recommendations</div>
        <div class="rv-empty-sub">Check back as clients log more activity</div>
      </div>
      <div v-else style="display:flex;flex-direction:column;gap:10px">
        <template v-for="priority in ['HIGH','MEDIUM','INFO']" :key="priority">
          <div v-if="recsByPriority[priority]?.length">
            <div class="rv-sec-lbl" style="margin-bottom:10px">
              {{ priorityIcon(priority) }} {{ priority }} PRIORITY
              <span class="rv-badge" :class="priority==='HIGH'?'rv-br':priority==='MEDIUM'?'rv-ba':'rv-bb'" style="font-size:10px;margin-left:4px">
                {{ recsByPriority[priority].length }}
              </span>
            </div>
            <div class="rv-card">
              <div v-for="r in recsByPriority[priority]" :key="r.id"
                style="display:flex;align-items:flex-start;gap:14px;padding:14px 18px;border-bottom:1px solid var(--border)">
                <div :style="{width:'4px',alignSelf:'stretch',borderRadius:'4px',flexShrink:0,
                  background:priority==='HIGH'?'var(--red)':priority==='MEDIUM'?'var(--amber)':'var(--blue)'}"></div>
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:3px">
                    <strong style="font-size:12.5px">{{ r.tenant_name }}</strong>
                    <span class="rv-badge rv-bg" style="font-size:10px">{{ r.rule_id }}</span>
                    <span v-if="r.platform" class="rv-badge" :class="r.platform==='instagram'?'rv-big':'rv-bb'" style="font-size:10px">{{ r.platform }}</span>
                  </div>
                  <div style="font-size:13px;font-weight:800;color:var(--slate);margin-bottom:4px">{{ r.title }}</div>
                  <div style="font-size:12px;color:var(--slate-mid);font-weight:600;line-height:1.5">{{ r.message }}</div>
                </div>
                <div style="display:flex;flex-direction:column;gap:5px;flex-shrink:0">
                  <button class="rv-btn rv-btn-b rv-btn-xs" @click="openClientByName(r.tenant_name)">View →</button>
                  <button class="rv-btn rv-btn-s rv-btn-xs" @click="dismiss(r)">Dismiss</button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- TAB 2 — AD INTELLIGENCE -->
    <div v-if="tab==='ads'">
      <div v-if="loadingAds && !adsInitialLoaded" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else-if="allCampaigns.length===0" class="rv-empty">
        <div class="rv-empty-icon">📊</div>
        <div class="rv-empty-title">No ad data</div>
        <div class="rv-empty-sub">Connect Meta accounts for clients to see campaign intelligence</div>
      </div>
      <div v-else style="display:flex;flex-direction:column;gap:12px">

        <!-- Token alerts -->
        <div v-if="tokenAlerts.length" style="display:flex;flex-direction:column;gap:6px">
          <div v-for="t in tokenAlerts" :key="t.account_id"
            class="rv-al" :class="t.status==='expired'?'rv-al-r':'rv-al-a'" style="margin:0;font-size:12px">
            {{ t.status==='expired'?'🔴':'🟡' }}
            <strong>{{ t.tenant_name }}</strong> —
            {{ t.status==='expired'?`Token EXPIRED for ${t.account_name}. Reconnect immediately.`:`Token expires in ${t.days_left} days for ${t.account_name}.` }}
          </div>
        </div>

        <!-- Action alerts -->
        <div v-if="adAlerts.length" style="display:flex;flex-direction:column;gap:6px">
          <div v-for="a in adAlerts" :key="a.key" class="rv-al" :class="a.type" style="margin:0">
            <div style="font-weight:800">{{ a.msg }}</div>
            <div v-if="a.affectedClients?.length" style="margin-top:3px;font-size:11px;color:var(--slate-mid)">
              {{ a.affectedClients.join(' · ') }}
            </div>
          </div>
        </div>

        <!-- Filters -->
        <div class="rv-card">
          <div class="rv-cb" style="padding:12px 16px">
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
              <div style="font-size:11px;font-weight:900;color:var(--slate-mid);text-transform:uppercase;letter-spacing:.5px">Filters</div>
              <select v-model="adFilterClient" class="rv-fs" style="font-size:12px;padding:5px 8px;min-width:140px">
                <option value="">All Clients</option>
                <option v-for="cl in adClientOptions" :key="cl" :value="cl">{{ cl }}</option>
              </select>
              <select v-model="adFilterStatus" class="rv-fs" style="font-size:12px;padding:5px 8px;min-width:120px">
                <option value="">All Status</option>
                <option value="ACTIVE">Active</option>
                <option value="PAUSED">Paused</option>
              </select>
              <select v-model="adFilterPlatform" class="rv-fs" style="font-size:12px;padding:5px 8px;min-width:120px">
                <option value="">All Platforms</option>
                <option value="facebook">Facebook</option>
                <option value="instagram">Instagram</option>
              </select>
              <input v-model="adSearch" class="rv-fi" placeholder="Search campaigns..." style="font-size:12px;padding:5px 8px;flex:1;min-width:160px">
              <button v-if="adFilterClient||adFilterStatus||adFilterPlatform||adSearch" class="rv-btn rv-btn-s rv-btn-xs" @click="clearAdFilters">✕ Clear</button>
              <span style="font-size:11px;color:var(--slate-mid);margin-left:auto;display:flex;align-items:center;gap:6px">
                <span v-if="loadingAds && adsInitialLoaded" class="rv-spin" style="width:10px;height:10px;border-width:2px;opacity:.5"></span>
                {{ adFiltered.length }} of {{ allCampaigns.length }} campaigns
              </span>
            </div>
          </div>
        </div>

        <!-- Summary totals — compact strip -->
        <div class="rv-card" style="overflow:hidden">
          <div style="display:grid;grid-template-columns:repeat(6,1fr);border-bottom:1px solid var(--border)">
            <div v-for="stat in adSummaryStats" :key="stat.label"
              style="padding:12px 14px;border-right:1px solid var(--border);last-child:border-right:none">
              <div style="font-size:9px;font-weight:900;color:var(--slate-light);text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px">{{ stat.label }}</div>
              <div style="font-size:16px;font-weight:900;letter-spacing:-.3px" :style="{color:stat.color||'var(--slate)'}">{{ stat.value }}</div>
              <div style="font-size:10px;color:var(--slate-light);font-weight:600;margin-top:1px">{{ stat.sub }}</div>
            </div>
          </div>
        </div>

        <!-- Platform comparison — compact -->
        <div v-if="!adFilterPlatform" class="rv-card" style="overflow:hidden">
          <div style="display:grid;grid-template-columns:1fr 1fr">
            <div style="padding:12px 16px;border-right:1px solid var(--border)">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <div style="width:8px;height:8px;border-radius:50%;background:var(--blue);flex-shrink:0"></div>
                <div style="font-size:11px;font-weight:900;color:var(--blue);text-transform:uppercase;letter-spacing:.4px">Facebook</div>
                <span style="font-size:10px;color:var(--slate-light);margin-left:auto">{{ platformStats.facebook.count }} campaigns</span>
              </div>
              <div style="display:flex;gap:12px;flex-wrap:wrap">
                <div v-for="m in platformMetrics(platformStats.facebook,'facebook')" :key="m.label" style="min-width:80px">
                  <div style="font-size:9px;font-weight:800;color:var(--slate-light);text-transform:uppercase;letter-spacing:.3px">{{ m.label }}</div>
                  <div style="font-size:14px;font-weight:900;margin-top:1px" :style="{color:m.color||'var(--slate)'}">{{ m.value }}</div>
                </div>
              </div>
            </div>
            <div style="padding:12px 16px">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <div style="width:8px;height:8px;border-radius:50%;background:#e1306c;flex-shrink:0"></div>
                <div style="font-size:11px;font-weight:900;color:#e1306c;text-transform:uppercase;letter-spacing:.4px">Instagram</div>
                <span style="font-size:10px;color:var(--slate-light);margin-left:auto">{{ platformStats.instagram.count }} campaigns</span>
              </div>
              <div style="display:flex;gap:12px;flex-wrap:wrap">
                <div v-for="m in platformMetrics(platformStats.instagram,'instagram')" :key="m.label" style="min-width:80px">
                  <div style="font-size:9px;font-weight:800;color:var(--slate-light);text-transform:uppercase;letter-spacing:.3px">{{ m.label }}</div>
                  <div style="font-size:14px;font-weight:900;margin-top:1px" :style="{color:m.color||'var(--slate)'}">{{ m.value }}</div>
                </div>
              </div>
            </div>
          </div>
          <div style="padding:8px 16px;background:var(--green-light);border-top:1px solid var(--border);font-size:11px;color:var(--green);font-weight:600">
            💡 {{ platformRecommendation }}
          </div>
        </div>

        <!-- Campaign table -->
        <div class="rv-card">
          <div class="rv-ch">
            <div class="rv-ct">All Campaigns</div>
            <span style="font-size:12px;color:var(--slate-mid)">Page {{ adPage }} of {{ adTotalPages }}</span>
          </div>
          <div class="rv-tw">
            <table class="rv-table" style="font-size:12px">
              <thead><tr>
                <th>Client</th>
                <th>Campaign</th>
                <th>Platform</th>
                <th>Status</th>
                <th>Spend</th>
                <th>Impressions</th>
                <th>CTR</th>
                <th>DMs</th>
                <th>CPR</th>
                <th>ROAS</th>
                <th>ROI</th>
                <th>Signals</th>
              </tr></thead>
              <tbody>
                <tr v-for="c in adPaginated" :key="c.id">
                  <td style="font-weight:800;white-space:nowrap">
                    <span style="display:inline-flex;align-items:center;gap:6px">
                      <span style="width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:900;color:#fff;flex-shrink:0"
                        :style="{background:gradientFor(c.client_name)}">{{ c.client_name[0] }}</span>
                      {{ c.client_name }}
                    </span>
                  </td>
                  <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                    <strong :title="c.name">{{ c.name }}</strong>
                  </td>
                  <td><span class="rv-badge" :class="c.platform==='instagram'?'rv-big':'rv-bb'" style="font-size:10px">{{ c.platform }}</span></td>
                  <td><span class="rv-badge" :class="c.status==='ACTIVE'?'rv-bg':'rv-bgy'" style="font-size:10px">{{ c.status }}</span></td>
                  <td>{{ fmtK(c.spend||0, c.currency) }}</td>
                  <td>{{ fmtNum(c.impressions||0) }}</td>
                  <td :style="{color:ctrColor(c.ctr),fontWeight:800}">{{ c.ctr||0 }}%</td>
                  <td>{{ c.conversations||0 }}</td>
                  <td :style="{color:cprColor(c.cpr,c.aov),fontWeight:700}">{{ fmtK(c.cpr||0, c.currency) }}</td>
                  <td style="font-weight:800" :style="{color:c.roas>=3?'var(--green)':c.roas>=1?'var(--amber)':'var(--red)'}">{{ c.roas ? c.roas.toFixed(2)+"x" : "—" }}</td>
                  <td :style="{color:roiColor(c.roi),fontWeight:800}">{{ c.roi||0 }}%</td>
                  <td>
                    <div style="display:flex;flex-wrap:wrap;gap:3px">
                      <span v-for="tag in campaignTags(c)" :key="tag.l" class="rv-badge" :class="tag.c" style="font-size:9px;padding:2px 4px">{{ tag.l }}</span>
                    </div>
                  </td>
                </tr>
                <tr v-if="!adPaginated.length">
                  <td colspan="11" style="text-align:center;padding:32px;color:var(--slate-light);font-weight:600">No campaigns match your filters.</td>
                </tr>
              </tbody>
              <!-- Totals row -->
              <tfoot v-if="adFiltered.length">
                <tr style="background:var(--bg);font-weight:900;border-top:2px solid var(--border)">
                  <td colspan="4" style="font-size:11px;color:var(--slate-mid)">TOTALS — {{ adFiltered.length }} campaigns</td>
                  <td>{{ fmtK(adTotals.spend) }}</td>
                  <td>{{ fmtNum(adTotals.impressions) }}</td>
                  <td :style="{color:ctrColor(adTotals.ctr)}">{{ adTotals.ctr.toFixed(2) }}%</td>
                  <td>{{ adTotals.conversations }}</td>
                  <td>{{ fmtK(adTotals.cpr) }}</td>
                  <td style="font-weight:900;color:var(--green)">{{ adTotals.roas ? adTotals.roas.toFixed(2)+"x" : "—" }}</td>
                  <td :style="{color:roiColor(adTotals.roi)}">{{ adTotals.roi.toFixed(1) }}%</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="adTotalPages>1" style="display:flex;gap:8px;align-items:center;justify-content:center;padding:14px;border-top:1px solid var(--border)">
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage=1" :disabled="adPage===1">««</button>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage--" :disabled="adPage===1">‹</button>
            <template v-for="p in adPageRange" :key="p">
              <button class="rv-btn rv-btn-xs" :class="p===adPage?'rv-btn-p':'rv-btn-s'" @click="adPage=p">{{ p }}</button>
            </template>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage++" :disabled="adPage===adTotalPages">›</button>
            <button class="rv-btn rv-btn-s rv-btn-xs" @click="adPage=adTotalPages" :disabled="adPage===adTotalPages">»»</button>
            <span style="font-size:12px;color:var(--slate-mid);margin-left:8px">
              {{ (adPage-1)*adPageSize+1 }}–{{ Math.min(adPage*adPageSize,adFiltered.length) }} of {{ adFiltered.length }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3 — GOAL INTELLIGENCE -->
    <div v-if="tab==='goals'">
      <div v-if="loadingClients" style="padding:40px;text-align:center"><span class="rv-spin"></span></div>
      <div v-else style="display:flex;flex-direction:column;gap:12px">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
          <div v-for="gs in goalSummary" :key="gs.label"
            style="background:var(--card);border-radius:var(--r-md);border:1px solid var(--border);padding:14px 16px;text-align:center">
            <div style="font-size:24px;margin-bottom:4px">{{ gs.icon }}</div>
            <div style="font-size:20px;font-weight:900;color:var(--slate)">{{ gs.count }}</div>
            <div style="font-size:11px;font-weight:700;color:var(--slate-mid)">{{ gs.label }}</div>
          </div>
        </div>
        <div v-for="status in ['behind','on_track','ahead','no_goal']" :key="status">
          <div v-if="clientsByGoalStatus[status]?.length">
            <div class="rv-sec-lbl" style="margin:12px 0 8px">
              {{ goalStatusIcon(status) }} {{ goalStatusLabel(status) }}
              ({{ clientsByGoalStatus[status].length }})
            </div>
            <div style="display:flex;flex-direction:column;gap:8px">
              <div v-for="c in clientsByGoalStatus[status]" :key="c.id" class="rv-card" style="padding:0;overflow:hidden">
                <div style="display:flex;align-items:center;gap:14px;padding:14px 18px">
                  <div class="rv-tenant-init" :style="{background:gradientFor(c.name)}">{{ c.name[0] }}</div>
                  <div style="flex:1;min-width:0">
                    <div style="font-size:13.5px;font-weight:800;color:var(--slate)">{{ c.name }}</div>
                    <div style="font-size:12px;color:var(--slate-mid);font-weight:600;margin-top:2px">
                      Revenue: <strong>{{ fmt(c.monthly_revenue||0) }}</strong>
                      <span v-if="c.monthly_goal"> / Goal: <strong>{{ fmt(c.monthly_goal) }}</strong>
                        · Gap: <strong :style="{color:c.goal_status==='behind'?'var(--red)':'var(--green)'}">
                          {{ fmt(Math.abs((c.monthly_goal||0)-(c.monthly_revenue||0))) }}
                          {{ c.goal_status==='behind'?' short':' ahead' }}
                        </strong>
                      </span>
                    </div>
                    <div v-if="c.monthly_goal" style="margin-top:8px;display:flex;align-items:center;gap:8px">
                      <div style="flex:1;background:var(--bg);border-radius:4px;height:8px;overflow:hidden;border:1px solid var(--border)">
                        <div :style="{width:Math.min(c.goal_progress||0,100)+'%',height:'100%',borderRadius:'4px',background:goalBarColor(c.goal_status)}"></div>
                      </div>
                      <span style="font-size:11px;font-weight:800;min-width:32px" :style="{color:goalColor(c.goal_status)}">
                        {{ c.goal_progress||0 }}%
                      </span>
                    </div>
                  </div>
                  <div style="display:flex;flex-direction:column;gap:5px;flex-shrink:0;align-items:flex-end">
                    <span class="rv-badge" :class="goalBadge(c.goal_status)">{{ goalStatusLabel(c.goal_status) }}</span>
                    <button class="rv-btn rv-btn-s rv-btn-xs" @click="openClientObj(c)">Open →</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4 — PIPELINE ALERTS -->
    <div v-if="tab==='pipeline'">
      <div v-if="pipelineAlerts.length===0" class="rv-empty">
        <div class="rv-empty-icon">🎯</div>
        <div class="rv-empty-title">Pipeline looks healthy</div>
        <div class="rv-empty-sub">No stale deals or urgent follow-ups at the moment</div>
      </div>
      <div v-else style="display:flex;flex-direction:column;gap:16px">
        <div v-for="alert in pipelineAlerts" :key="alert.key" class="rv-card">
          <div class="rv-ch">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-size:20px">{{ alert.icon }}</span>
              <div>
                <div class="rv-ct">{{ alert.title }}</div>
                <div class="rv-cst">{{ alert.sub }}</div>
              </div>
            </div>
            <span class="rv-badge" :class="alert.urgent?'rv-br':'rv-ba'">{{ alert.urgent?'Urgent':'Action needed' }}</span>
          </div>
          <div class="rv-cb">
            <div style="font-size:13px;color:var(--slate-mid);font-weight:600;line-height:1.6">{{ alert.msg }}</div>
            <div style="margin-top:10px;display:flex;gap:8px">
              <button class="rv-btn rv-btn-b rv-btn-sm" @click="openClientByName(alert.client)">View {{ alert.client }} →</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/api'
import { fmtK as _fmtK } from '@/utils/format'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const emit = defineEmits(['nav', 'open-client'])

const tab          = ref('recs')
const recs         = ref([])
const clients      = ref([])
const allCampaigns = ref([])
const loadingRecs  = ref(true)
const loadingAds   = ref(true)
const loadingClients = ref(true)
const tokenAlerts    = ref([])
const adFilterClient   = ref('')
const adFilterStatus   = ref('')
const adFilterPlatform = ref('')
const adSearch          = ref('')
const adSearchDebounced  = ref('')
let _adSearchTimer       = null
const adSearchDebounced = ref('')
let adSearchTimer = null
const adPage           = ref(1)
const adPageSize       = 20

const tabs = computed(() => [
  { key:'recs',     icon:'💡', label:'Recommendations', count: recs.value.length || null },
  { key:'ads',      icon:'📊', label:'Ad Intelligence',  count: adAlerts.value.length || null },
  { key:'goals',    icon:'🎯', label:'Goal Tracking',    count: clients.value.filter(c=>c.goal_status==='behind').length || null },
  { key:'pipeline', icon:'🔥', label:'Pipeline Alerts',  count: pipelineAlerts.value.length || null },
])

function fmtK(v, cur) { return _fmtK(v, cur || 'KES') }
function fmt(v)        { return _fmtK(v) }
function fmtNum(n)     { if (!n) return '0'; if (n>=1000) return `${(n/1000).toFixed(0)}K`; return String(n) }
function ctrColor(ctr)      { return ctr>=2?'var(--green)':ctr>=1?'var(--blue)':'var(--amber)' }
function cprColor(cpr, aov) { if (!cpr||!aov) return 'var(--slate)'; const r=cpr/aov; return r<0.2?'var(--green)':r<0.5?'var(--blue)':'var(--amber)' }
function roiColor(roi)      { return roi>=150?'var(--green)':roi>=50?'var(--blue)':'var(--amber)' }
function goalBarColor(s)    { return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)','no_goal':'var(--border-mid)'}[s]||'var(--border-mid)' }
function goalColor(s)       { return {'ahead':'var(--green)','on_track':'var(--blue)','behind':'var(--amber)'}[s]||'var(--slate-light)' }
function goalBadge(s)       { return {'ahead':'rv-bg','on_track':'rv-bb','behind':'rv-ba','no_goal':'rv-bgy'}[s]||'rv-bgy' }
function goalStatusLabel(s) { return {'ahead':'🚀 Ahead','on_track':'✅ On Track','behind':'⚠️ Behind','no_goal':'No Goal'}[s]||s }
function goalStatusIcon(s)  { return {'ahead':'🚀','on_track':'✅','behind':'⚠️','no_goal':'📍'}[s]||'' }
function priorityIcon(p)    { return {'HIGH':'🔴','MEDIUM':'🟡','INFO':'🔵'}[p]||'' }
const GRADS = [
  'linear-gradient(135deg,#1F7A4C,#2563EB)',
  'linear-gradient(135deg,#7C3AED,#DD2A7B)',
  'linear-gradient(135deg,#D97706,#f59e0b)',
  'linear-gradient(135deg,#059669,#34d399)',
  'linear-gradient(135deg,#dc2626,#f97316)',
]
function gradientFor(name) { return GRADS[name.charCodeAt(0)%GRADS.length] }

const recsByPriority = computed(() => ({
  HIGH:   recs.value.filter(r=>r.priority==='HIGH'),
  MEDIUM: recs.value.filter(r=>r.priority==='MEDIUM'),
  INFO:   recs.value.filter(r=>!['HIGH','MEDIUM'].includes(r.priority)),
}))

function campaignTags(c) {
  const t = []
  if ((c.ctr||0) < 1 && c.status==='ACTIVE') t.push({l:'Low CTR', c:'rv-ba'})
  if ((c.ctr||0) >= 2)                        t.push({l:'Strong CTR', c:'rv-bg'})
  if (c.cpr && c.aov && c.cpr > c.aov*0.5)   t.push({l:'High CPR', c:'rv-ba'})
  if ((c.roi||0) >= 150)                       t.push({l:'Scale ↑', c:'rv-bg'})
  if ((c.roi||0) > 0 && c.roi < 50 && c.spend>0) t.push({l:'Poor ROI', c:'rv-br'})
  if (!c.conversations && (c.spend||0)>0)     t.push({l:'No DMs', c:'rv-br'})
  return t
}

const campaignsByClient = computed(() => {
  const map = {}
  allCampaigns.value.forEach(c => {
    if (!map[c.client_name]) {
      map[c.client_name] = { name:c.client_name, currency:c.currency||'KES', campaigns:[], totalSpend:0, alerts:0 }
    }
    map[c.client_name].campaigns.push(c)
    map[c.client_name].totalSpend += (c.spend||0)
    map[c.client_name].alerts += campaignTags(c).length
  })
  return Object.values(map).sort((a,b)=>b.totalSpend-a.totalSpend)
})

const adAlerts = computed(() => {
  const alerts = []
  const low     = allCampaigns.value.filter(c=>(c.ctr||0)<1 && c.status==='ACTIVE')
  const scale   = allCampaigns.value.filter(c=>(c.roi||0)>=150)
  const noConv  = allCampaigns.value.filter(c=>!c.conversations && (c.spend||0)>0)
  const poorRoi = allCampaigns.value.filter(c=>(c.roi||0)>0 && c.roi<50 && (c.spend||0)>0)
  if (low.length)     alerts.push({key:'lowctr', type:'rv-al-a', affectedClients:[...new Set(low.map(c=>c.client_name))],    msg:`⚠️ ${low.length} active campaign(s) have CTR below 1%`})
  if (scale.length)   alerts.push({key:'scale',  type:'rv-al-g', affectedClients:[...new Set(scale.map(c=>c.client_name))],  msg:`🚀 ${scale.length} campaign(s) ROI ≥ 150% — ready to scale`})
  if (noConv.length)  alerts.push({key:'noconv', type:'rv-al-r', affectedClients:[...new Set(noConv.map(c=>c.client_name))], msg:`🔇 ${noConv.length} campaign(s) spending but zero DMs`})
  if (poorRoi.length) alerts.push({key:'poorroi',type:'rv-al-r', affectedClients:[...new Set(poorRoi.map(c=>c.client_name))],msg:`📉 ${poorRoi.length} campaign(s) ROI under 50%`})
  return alerts
})

const adClientOptions = computed(() => [...new Set(allCampaigns.value.map(c=>c.client_name))].sort())

const adFiltered = computed(() => {
  let list = allCampaigns.value
  if (adFilterClient.value)   list = list.filter(c=>c.client_name===adFilterClient.value)
  if (adFilterStatus.value)   list = list.filter(c=>c.status===adFilterStatus.value)
  if (adFilterPlatform.value) list = list.filter(c=>c.platform===adFilterPlatform.value)
  if (adSearch.value)         list = list.filter(c=>c.name?.toLowerCase().includes(adSearch.value.toLowerCase())||c.client_name?.toLowerCase().includes(adSearch.value.toLowerCase()))
  return list
})

// Debounce search input — avoids recomputing 579 campaigns on every keystroke
watch(adSearch, (val) => {
  clearTimeout(adSearchTimer)
  adSearchTimer = setTimeout(() => {
    adSearchDebounced.value = val
    adPage.value = 1
  }, 250)
})

watch(adSearch, (val) => {
  clearTimeout(_adSearchTimer)
  _adSearchTimer = setTimeout(() => { adSearchDebounced.value = val; adPage.value = 1 }, 300)
})

const adTotalPages = computed(() => Math.ceil(adFiltered.value.length/adPageSize)||1)
const adPaginated  = computed(() => adFiltered.value.slice((adPage.value-1)*adPageSize, adPage.value*adPageSize))
const adPageRange  = computed(() => { const t=adTotalPages.value,c=adPage.value,p=[]; for(let i=Math.max(1,c-2);i<=Math.min(t,c+2);i++) p.push(i); return p })

const adTotals = computed(() => {
  const list = adFiltered.value
  const spend         = list.reduce((s,c)=>s+Number(c.spend||0),0)
  const impressions   = list.reduce((s,c)=>s+Number(c.impressions||0),0)
  const clicks        = list.reduce((s,c)=>s+Number(c.clicks||0),0)
  const conversations = list.reduce((s,c)=>s+Number(c.conversations||0),0)
  const revenue       = list.reduce((s,c)=>s+Number(c.revenue||0),0)
  const roas          = spend > 0 ? revenue / spend : 0
  const cpa           = spend > 0 && list.length > 0 ? spend / list.filter(c=>Number(c.revenue||0)>0).length : 0
  return {
    spend, impressions, conversations, revenue, roas, cpa,
    ctr: impressions?(clicks/impressions*100):0,
    cpr: conversations?(spend/conversations):0,
    roi: spend?(((revenue-spend)/spend)*100):0,
  }
})

const adSummaryStats = computed(() => [
  { label:'Total Spend',  value: fmtK(adTotals.value.spend),                          sub: adFiltered.value.length+' campaigns',       color:'var(--slate)' },
  { label:'Impressions',  value: fmtNum(adTotals.value.impressions),                   sub: 'Avg CTR '+adTotals.value.ctr.toFixed(2)+'%', color:'var(--blue)' },
  { label:'Avg CTR',      value: adTotals.value.ctr.toFixed(2)+'%',                   sub: 'Click-through rate',                         color:ctrColor(adTotals.value.ctr) },
  { label:'ROAS',         value: adTotals.value.roas ? adTotals.value.roas.toFixed(2)+'x' : '—', sub:'Revenue '+fmtK(adTotals.value.revenue), color:'var(--green)' },
  { label:'CPA',          value: adTotals.value.cpa  ? fmtK(adTotals.value.cpa)  : '—', sub:'Cost per acquisition',                     color:'var(--amber)' },
  { label:'ROI',          value: adTotals.value.roi.toFixed(1)+'%',                   sub: adTotals.value.conversations+' DM convs',     color:roiColor(adTotals.value.roi) },
])

function platformMetrics(p, platform) {
  return [
    { label:'Spend',       value: fmtK(p.spend),       color:'var(--slate)' },
    { label:'Impressions', value: fmtNum(p.impressions),color:'var(--slate)' },
    { label:'CTR',         value: p.ctr.toFixed(2)+'%', color:ctrColor(p.ctr) },
    { label:'ROAS',        value: p.roas ? p.roas.toFixed(2)+'x' : '—', color:p.roas>=3?'var(--green)':p.roas>=1?'var(--amber)':'var(--slate-light)' },
  ]
}

const platformStats = computed(() => {
  const all = adFiltered.value
  const calc = (platform) => {
    const list = all.filter(c => c.platform === platform)
    const spend       = list.reduce((s,c)=>s+Number(c.spend||0),0)
    const impressions = list.reduce((s,c)=>s+Number(c.impressions||0),0)
    const clicks      = list.reduce((s,c)=>s+Number(c.clicks||0),0)
    const revenue     = list.reduce((s,c)=>s+Number(c.revenue||0),0)
    return {
      count:       list.length,
      spend,
      impressions,
      revenue,
      ctr:  impressions ? (clicks/impressions*100) : 0,
      roas: spend > 0   ? revenue / spend : 0,
    }
  }
  return {
    facebook:  calc('facebook'),
    instagram: calc('instagram'),
  }
})

const platformRecommendation = computed(() => {
  const fb = platformStats.value.facebook
  const ig = platformStats.value.instagram
  if (!fb.spend && !ig.spend) return 'No spend data available yet. Connect Meta accounts to see platform comparison.'
  if (!fb.spend) return 'All spend is on Instagram. Consider testing Facebook campaigns.'
  if (!ig.spend) return 'All spend is on Facebook. Consider testing Instagram campaigns for broader reach.'
  if (fb.roas > ig.roas * 1.2) return `Facebook is outperforming Instagram by ${((fb.roas/ig.roas-1)*100).toFixed(0)}% ROAS. Consider shifting more budget to Facebook.`
  if (ig.roas > fb.roas * 1.2) return `Instagram is outperforming Facebook by ${((ig.roas/fb.roas-1)*100).toFixed(0)}% ROAS. Consider shifting more budget to Instagram.`
  if (fb.ctr > ig.ctr) return `Facebook has a better CTR (${fb.ctr.toFixed(2)}% vs ${ig.ctr.toFixed(2)}%). Both platforms performing similarly — maintain current split.`
  return `Both platforms are performing similarly. Monitor for 2 more weeks before shifting budget.`
})

function clearAdFilters() { adFilterClient.value='';adFilterStatus.value='';adFilterPlatform.value='';adSearch.value='' }

const clientsByGoalStatus = computed(() => ({
  behind:   clients.value.filter(c=>c.goal_status==='behind'),
  on_track: clients.value.filter(c=>c.goal_status==='on_track'),
  ahead:    clients.value.filter(c=>c.goal_status==='ahead'),
  no_goal:  clients.value.filter(c=>!c.monthly_goal),
}))

const goalSummary = computed(() => [
  { icon:'⚠️', count: clientsByGoalStatus.value.behind.length,   label:'Behind Goal' },
  { icon:'✅', count: clientsByGoalStatus.value.on_track.length,  label:'On Track' },
  { icon:'🚀', count: clientsByGoalStatus.value.ahead.length,     label:'Ahead of Goal' },
  { icon:'📍', count: clientsByGoalStatus.value.no_goal.length,   label:'No Goal Set' },
])

const goalAlerts = computed(() =>
  clients.value.filter(c=>c.goal_status==='behind'||!c.monthly_goal)
    .map(c=>({...c, urgent: c.goal_status==='behind'}))
)

const pipelineAlerts = computed(() => {
  const alerts = []
  clients.value.forEach(c => {
    if ((c.open_deals||0) > 10)
      alerts.push({
        key:`pipe_${c.id}`, icon:'🔥', urgent:true, client:c.name,
        title:`${c.name} has ${c.open_deals} open deals`,
        sub:'Large pipeline — may need follow-up prioritisation',
        msg:`${c.name} has ${c.open_deals} deals in pipeline. Review and follow up on the oldest deals before they go cold.`,
      })
    const daysSinceSale = !c.last_sale || c.last_sale==='—' ? 999
      : c.last_sale==='Today' ? 0 : c.last_sale==='Yesterday' ? 1
      : parseInt(c.last_sale) || 5
    if (daysSinceSale >= 5 && c.monthly_goal)
      alerts.push({
        key:`sale_${c.id}`, icon:'📋', urgent:daysSinceSale>=7, client:c.name,
        title:`${c.name} — no sales in ${daysSinceSale}+ days`,
        sub:'Client may not be logging offline sales',
        msg:`${c.name} has a monthly goal but last sale was ${daysSinceSale}+ days ago. Remind them to log all sales to keep Revenue GPS accurate.`,
      })
  })
  return alerts
})

// Reset page on filter change
watch([adFilterClient,adFilterStatus,adFilterPlatform,adSearch],()=>{ adPage.value=1 })

function openClientByName(name) {
  const t = clients.value.find(c=>c.name===name)
  if (t) emit('open-client', t)
}
function openClientObj(c) { emit('open-client', c) }

async function dismiss(rec) {
  try {
    await api.post(`/recommendations/${rec.id}/dismiss/`)
    recs.value = recs.value.filter(r=>r.id!==rec.id)
  } catch(e) {}
}

async function loadRecs() {
  loadingRecs.value = true
  try {
    const r = await api.get('/recommendations/?is_dismissed=false')
    recs.value = r.data.results || r.data || []
  } catch(e) {}
  loadingRecs.value = false
}

async function loadAdIntelligence() {
  loadingAds.value = true
  try {
    // Run all three requests in parallel
    const [tenantsRes, campaignsRes, tokenRes] = await Promise.allSettled([
      api.get('/tenants/'),
      api.get('/meta/admin/campaigns/'),
      api.get('/meta/token-status/'),
    ])

    if (tenantsRes.status === 'fulfilled') {
      clients.value = tenantsRes.value.data.results || tenantsRes.value.data || []
    }
    if (campaignsRes.status === 'fulfilled') {
      allCampaigns.value = campaignsRes.value.data || []
    }
    if (tokenRes.status === 'fulfilled') {
      tokenAlerts.value = (tokenRes.value.data || []).filter(t => t.status !== 'ok')
    }
  } catch(e) {}
  loadingAds.value = false
  adsInitialLoaded.value = true
  loadingClients.value = false
}

async function loadData() {
  await loadRecs()
  // Load ad intelligence only on first load — campaigns are cached server-side
  if (allCampaigns.value.length === 0) {
    await loadAdIntelligence()
  }
}

useAutoRefresh(loadData, 60000)
// Refresh campaigns silently every 5 minutes in background
setInterval(() => { loadAdIntelligence() }, 300000)
</script>
