// Lesson: the browser requests source-tagged JSON; Python gathers and labels signals.
const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const safeHref = value => { try { const url = new URL(value); return url.protocol === 'https:' ? url.href : '#'; } catch { return '#'; } };
const timeLabel = value => { const date = new Date(value); return Number.isNaN(date.valueOf()) ? '' : new Intl.DateTimeFormat('en-GB',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/London'}).format(date); };
const cash = (value, currency) => { try { return new Intl.NumberFormat('en-GB',{style:'currency',currency,maximumFractionDigits:value<1?5:2}).format(value); } catch { return Number(value).toLocaleString('en-GB'); } };
const guideDate = document.querySelector('.hero-bottom span:last-child b');
if (guideDate) guideDate.textContent = new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric'}).format(new Date()).toUpperCase();
const mechanics = document.createElement('div');
mechanics.className = 'mechanics';
mechanics.innerHTML = '<article><span>01 / APPROACH</span><h3>Investing vs trading</h3><p>Investing usually means owning assets over a longer horizon. Trading usually means acting on shorter-term price changes. Both can lose money; frequent trading can add costs and tax complexity.</p></article><article><span>02 / ORDERS</span><h3>Market vs limit</h3><p>A market order prioritises execution, not a particular price. A limit order sets a price boundary but may never fill. Thin markets can add slippage—the gap between an expected and actual execution price.</p></article><article><span>03 / AMPLIFIERS</span><h3>Leverage & shorting</h3><p>Borrowing to trade can magnify losses and trigger forced liquidation. Short positions can lose more than the initial cash committed. Beginners should first understand the mechanics and risks before considering either.</p></article>';
const mechanicsStyle = document.createElement('style');
mechanicsStyle.textContent = '.mechanics{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid #d5dbd0;border-bottom:1px solid #d5dbd0;margin-top:20px}.mechanics article{padding:15px 18px 16px 0}.mechanics article+article{border-left:1px solid #d5dbd0;padding-left:18px}.mechanics article>span{font:8px "DM Mono",monospace;letter-spacing:.8px;color:#9b7958}.mechanics h3{font:500 16px "Playfair Display",serif;margin:8px 0 5px}.mechanics p{font:10px/1.7 "DM Sans",sans-serif;color:#748074;margin:0}@media(max-width:650px){.mechanics{grid-template-columns:1fr}.mechanics article{padding:14px 0}.mechanics article+article{border-left:0;border-top:1px solid #d5dbd0;padding-left:0}}';
mechanicsStyle.textContent += '.asset-group-title{padding:13px 0 7px;border-bottom:1px solid #526458;color:#d1b98c;font:8px "DM Mono",monospace;letter-spacing:1px}.range-lesson b:before{content:"VOLATILITY CUE / ";font:8px "DM Mono",monospace;color:#b9c89f;letter-spacing:.6px}';
document.head.append(mechanicsStyle);
document.querySelector('.markets-section .small-source')?.insertAdjacentElement('beforebegin',mechanics);
const lessonCount = document.querySelector('.hero-bottom span:first-child');
if (lessonCount) lessonCount.textContent = 'LESSONS 01—07';

function renderScout(data) {
  $('#scout-updated').textContent = data.assets.length
    ? 'SCAN UPDATED ' + timeLabel(data.updated_at).toUpperCase() + (data.errors.length ? ' · SOME SOURCES UNAVAILABLE' : '')
    : 'LIVE SCAN UNAVAILABLE · SEE DATA SOURCES BELOW';
  $('#scout-universe').textContent = data.universe_note || '';
  if (!data.assets.length) {
    $('#scout-list').innerHTML = '<div class="empty-row">The market-data providers did not respond. The scan will retry tomorrow or when you refresh. This app does not substitute stale or invented prices.</div>';
    if (data.errors.length) showToast(data.errors.join(' '));
    return;
  }
  const row = (asset,index) => {
    const value = Number(asset.change);
    const riskClass = asset.risk_label.startsWith('High') ? 'high' : asset.risk_label.startsWith('Elevated') ? 'elevated' : '';
    return '<a class="asset-row" href="'+safeHref(asset.source_url)+'" target="_blank" rel="noreferrer">'
      + '<span class="asset-rank">'+String(index+1).padStart(2,'0')+'</span>'
      + '<span class="asset-id"><b>'+escapeHtml(asset.name)+' · '+escapeHtml(asset.symbol)+'</b><small>'+escapeHtml(asset.kind)+' · '+cash(asset.price,asset.currency)+'</small></span>'
      + '<span class="asset-kind">'+escapeHtml(asset.change_window)+' trend</span>'
      + '<span class="asset-move '+(value<0?'negative':'')+'">'+(value>0?'+':'')+value.toFixed(2)+'%</span>'
      + '<span class="asset-range">'+escapeHtml(asset.observed_range.toFixed(2))+'% range · '+escapeHtml(asset.range_window)+'</span>'
      + '<span class="risk-chip '+riskClass+'">'+escapeHtml(asset.risk_label)+'</span></a>';
  };
  $('#scout-list').innerHTML = ['Crypto','Stock'].map(kind => {
    const group = data.assets.filter(asset => asset.kind === kind).slice(0,6);
    if (!group.length) return '';
    return '<div class="asset-group-title">'+(kind === 'Crypto' ? 'CRYPTO · TOP RECENT MOVERS' : 'STOCKS · WATCHLIST MOVERS')+'</div>'+group.map(row).join('');
  }).join('');
  if (data.errors.length) showToast(data.errors.join(' '));
}

async function loadScout(refresh=false) {
  const button = $('#refresh-scout');
  button.disabled = true;
  try {
    const response = await fetch('/api/scout'+(refresh?'?refresh=true':''));
    const data = await response.json();
    if (!response.ok) throw new Error('Market scan unavailable.');
    renderScout(data);
  } catch (error) {
    $('#scout-updated').textContent = 'LIVE SCAN UNAVAILABLE';
    $('#scout-list').innerHTML = '<div class="empty-row">Could not reach the market-data service. Try again later or use the research links above.</div>';
  } finally { button.disabled = false; }
}

function renderNews(data) {
  $('#news-status').textContent = data.available
    ? data.message + ' Updated ' + timeLabel(data.updated_at) + (data.sources.length ? ' · Sources: '+data.sources.join(', ') : '')
    : data.message;
  if (!data.stories.length) {
    $('#news-list').innerHTML = '<div class="empty-row">The feed service is unavailable right now. Use these publisher pages for current coverage.</div>';
    return;
  }
  $('#news-list').innerHTML = data.stories.map(story => '<article class="news-item">'
    + '<span class="news-type">'+escapeHtml(story.kind)+'</span>'
    + '<a href="'+safeHref(story.link)+'" target="_blank" rel="noreferrer">'+escapeHtml(story.title)+' ↗</a>'
    + '<span class="news-source">'+escapeHtml(story.source)+(story.published?' · '+escapeHtml(story.published):'')+'</span>'
    + '</article>').join('');
}

async function loadNews(refresh=false) {
  const button = $('#refresh-news');
  button.disabled = true;
  try {
    const response = await fetch('/api/news'+(refresh?'?refresh=true':''));
    const data = await response.json();
    if (!response.ok) throw new Error('News feed unavailable.');
    renderNews(data);
  } catch {
    $('#news-status').textContent = 'Could not connect to publisher feeds. Use the direct publisher links below.';
    $('#news-list').innerHTML = '<div class="empty-row">Live headlines are unavailable right now. The publisher links below open current coverage.</div>';
  } finally { button.disabled = false; }
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4200);
}

$('#refresh-scout').addEventListener('click', () => loadScout(true));
$('#refresh-news').addEventListener('click', () => loadNews(true));
loadScout();
loadNews();
// Refresh current headlines hourly while the guide remains open.
setInterval(() => loadNews(), 60*60*1000);
