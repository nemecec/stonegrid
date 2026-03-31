"""Flask web app for the parking lot stone pattern generator."""

import io
import os

from flask import Flask, request, jsonify, send_file, render_template_string
import parking_generator as gen

app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Parking Lot Stone Pattern Generator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f5f5f5; color: #333; }
  .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
  h1 { margin-bottom: 4px; font-size: 1.5rem; }
  .subtitle { color: #666; margin-bottom: 20px; font-size: 0.9rem; }
  .layout { display: flex; gap: 20px; }
  .editor-panel { flex: 0 0 520px; }
  .preview-panel { flex: 1; min-width: 0; }

  /* Tabs */
  .tabs { display: flex; border-bottom: 2px solid #ddd; margin-bottom: 12px; }
  .tab { padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: 500;
         color: #888; border-bottom: 2px solid transparent; margin-bottom: -2px; }
  .tab:hover { color: #555; }
  .tab.active { color: #4a90d9; border-bottom-color: #4a90d9; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* Visual editor */
  .ve-section { margin-bottom: 16px; }
  .ve-section h3 { font-size: 13px; font-weight: 600; color: #555; margin-bottom: 8px;
                   text-transform: uppercase; letter-spacing: 0.5px; }
  .ve-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .ve-field { display: flex; flex-direction: column; gap: 2px; }
  .ve-field label { font-size: 11px; color: #888; }
  .ve-field input[type="number"] { width: 100%; padding: 6px 8px; border: 1px solid #ccc;
         border-radius: 4px; font-size: 13px; }
  .ve-field input[type="number"]:focus { outline: none; border-color: #4a90d9;
         box-shadow: 0 0 0 2px rgba(74,144,217,0.2); }

  /* Color list */
  .color-list { display: flex; flex-direction: column; gap: 8px; }
  .color-item { display: flex; align-items: center; gap: 8px; padding: 8px;
                background: #fff; border: 1px solid #ddd; border-radius: 6px; }
  .color-swatch { width: 32px; height: 32px; border-radius: 4px; border: 1px solid #ccc;
                  cursor: pointer; flex-shrink: 0; }
  .color-swatch input[type="color"] { opacity: 0; width: 100%; height: 100%; cursor: pointer; }
  .color-item .color-name { flex: 1; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px;
                            font-size: 13px; }
  .color-item .color-name:focus { outline: none; border-color: #4a90d9; }
  .color-meta { font-size: 11px; color: #999; flex-shrink: 0; }
  .btn-sm { padding: 4px 10px; font-size: 12px; border: none; border-radius: 4px;
            cursor: pointer; }
  .btn-add { background: #4a90d9; color: #fff; margin-top: 4px; }
  .btn-add:hover { background: #357abd; }
  .btn-remove { background: #e74c3c; color: #fff; }
  .btn-remove:hover { background: #c0392b; }

  /* Lot list */
  .lot-item { padding: 10px; background: #fff; border: 1px solid #ddd; border-radius: 6px;
              margin-bottom: 8px; }
  .lot-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .lot-header span { font-weight: 600; font-size: 13px; }
  .lot-toggle { display: flex; gap: 4px; align-items: center; font-size: 12px; color: #666; }
  .lot-toggle input { cursor: pointer; }
  .lot-proportions { display: flex; flex-direction: column; gap: 6px; }
  .lot-gradient-label { font-size: 11px; color: #888; font-weight: 600; margin-top: 4px; }
  .prop-row { display: flex; align-items: center; gap: 6px; }
  .prop-swatch { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #ccc; flex-shrink: 0; }
  .prop-name { font-size: 12px; flex: 1; }
  .prop-row input[type="range"] { flex: 2; cursor: pointer; }
  .prop-row .prop-val { width: 48px; text-align: right; font-size: 12px; font-family: monospace;
                        padding: 2px 4px; border: 1px solid #ddd; border-radius: 3px;
                        -moz-appearance: textfield; }
  .prop-row .prop-val::-webkit-inner-spin-button,
  .prop-row .prop-val::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
  .prop-row .prop-val:focus { outline: none; border-color: #4a90d9; }
  .prop-pct { font-size: 11px; color: #999; margin-left: 1px; }

  /* JSON editor */
  textarea { width: 100%; height: 480px; font-family: "SF Mono", Monaco, Consolas, monospace;
             font-size: 13px; padding: 12px; border: 1px solid #ccc; border-radius: 6px;
             resize: vertical; background: #fff; tab-size: 2; }
  textarea:focus { outline: none; border-color: #4a90d9; box-shadow: 0 0 0 2px rgba(74,144,217,0.2); }

  /* Buttons & feedback */
  .buttons { margin-top: 12px; display: flex; gap: 10px; flex-wrap: wrap; }
  button { padding: 10px 20px; border: none; border-radius: 6px; font-size: 14px;
           cursor: pointer; font-weight: 500; }
  .btn-preview { background: #4a90d9; color: #fff; }
  .btn-preview:hover { background: #357abd; }
  .btn-download { background: #2ecc71; color: #fff; }
  .btn-download:hover { background: #27ae60; }
  .btn-share { background: #8e44ad; color: #fff; }
  .btn-share:hover { background: #7d3c98; }
  .btn-download:disabled, .btn-share:disabled { background: #95a5a6; cursor: not-allowed; }
  .share-bar { display: none; margin-top: 10px; gap: 6px; align-items: center; }
  .share-bar.active { display: flex; }
  .share-bar input { flex: 1; font-family: "SF Mono", Monaco, Consolas, monospace; font-size: 12px;
                     padding: 6px 8px; border: 1px solid #ccc; border-radius: 4px; background: #fff; }
  .share-bar input:focus { outline: none; border-color: #8e44ad; box-shadow: 0 0 0 2px rgba(142,68,173,0.2); }
  .btn-copy { padding: 6px 12px; font-size: 12px; background: #8e44ad; color: #fff;
              border: none; border-radius: 4px; cursor: pointer; white-space: nowrap; }
  .btn-copy:hover { background: #7d3c98; }
  .error { color: #e74c3c; margin-top: 10px; font-size: 13px; white-space: pre-wrap; }
  .info { color: #666; margin-top: 10px; font-size: 13px; }
  .preview-box { background: #fff; border: 1px solid #ccc; border-radius: 6px;
                 padding: 16px; min-height: 200px; overflow: auto; }
  .preview-box svg { width: 100%; height: auto; }
  .preview-placeholder { color: #aaa; text-align: center; padding: 80px 0; }
  .spinner { display: none; }
  .spinner.active { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; color: #666; }
  .spin-icon { display: inline-block; width: 16px; height: 16px; border: 2px solid #ccc;
               border-top-color: #4a90d9; border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  footer { margin-top: 30px; padding-top: 16px; border-top: 1px solid #ddd;
           color: #999; font-size: 12px; text-align: center; }
  footer a { color: #999; text-decoration: none; }
  footer a:hover { color: #666; }
  footer svg { vertical-align: middle; margin-right: 4px; }
  .ve-scroll { max-height: 520px; overflow-y: auto; padding-right: 4px; }
  @media (max-width: 900px) { .layout { flex-direction: column; } .editor-panel { flex: none; } }
</style>
</head>
<body>
<div class="container">
  <h1>Parking Lot Stone Pattern Generator</h1>
  <p class="subtitle">Define color proportions per lot, preview the pattern, download as DXF.</p>

  <div class="layout">
    <div class="editor-panel">
      <div class="tabs">
        <div class="tab active" onclick="switchTab('visual')">Visual Editor</div>
        <div class="tab" onclick="switchTab('json')">JSON</div>
      </div>

      <div id="tab-visual" class="tab-content active">
        <div class="ve-scroll">
          <div class="ve-section">
            <h3>Dimensions</h3>
            <div class="ve-grid">
              <div class="ve-field">
                <label>Triangle side (mm)</label>
                <input type="number" id="ve-triangle_side" min="10" step="10">
              </div>
              <div class="ve-field">
                <label>Random seed</label>
                <input type="number" id="ve-seed" min="0" step="1">
              </div>
              <div class="ve-field">
                <label>Space width (mm)</label>
                <input type="number" id="ve-space_width" min="100" step="100">
              </div>
              <div class="ve-field">
                <label>Space height (mm)</label>
                <input type="number" id="ve-space_height" min="100" step="100">
              </div>
            </div>
          </div>

          <div class="ve-section">
            <h3>Colors</h3>
            <div class="color-list" id="ve-colors"></div>
            <button class="btn-sm btn-add" onclick="addColor()">+ Add color</button>
          </div>

          <div class="ve-section">
            <h3>Lots</h3>
            <div id="ve-lots"></div>
            <button class="btn-sm btn-add" onclick="addLot()">+ Add lot</button>
          </div>
        </div>
      </div>

      <div id="tab-json" class="tab-content">
        <textarea id="config" spellcheck="false">{{ default_config }}</textarea>
      </div>

      <div class="buttons">
        <button class="btn-preview" onclick="preview()">Preview</button>
        <button class="btn-download" id="downloadBtn" onclick="download()" disabled title="Run Preview first to enable download">Download DXF</button>
        <button class="btn-share" id="shareBtn" onclick="share()" disabled title="Run Preview first to get a shareable link">Share Link</button>
        <span class="spinner" id="spinner"><span class="spin-icon"></span> Generating preview…</span>
        <span class="spinner" id="dxfSpinner"><span class="spin-icon"></span> Generating DXF…</span>
      </div>
      <div id="error" class="error"></div>
      <div id="info" class="info"></div>
      <div class="share-bar" id="shareBar">
        <input type="text" id="shareUrl" readonly>
        <button class="btn-copy" onclick="copyShareUrl()">Copy</button>
      </div>
    </div>
    <div class="preview-panel">
      <div class="preview-box" id="previewBox">
        <div class="preview-placeholder">Click "Preview" to generate the pattern</div>
      </div>
    </div>
  </div>
  <footer>
    <a href="https://github.com/nemecec/stonegrid">
      <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      Source code available on GitHub
    </a>
  </footer>
</div>
<script>
let currentConfig = null;

// --- Tab switching ---
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  if (tab === 'visual') {
    document.querySelectorAll('.tab')[0].classList.add('active');
    document.getElementById('tab-visual').classList.add('active');
    jsonToVisual();
  } else {
    document.querySelectorAll('.tab')[1].classList.add('active');
    document.getElementById('tab-json').classList.add('active');
    visualToJson();
  }
}

// --- Visual editor: read/write config ---
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(c => c.toString(16).padStart(2, '0')).join('');
}

function hexToRgb(hex) {
  const m = hex.match(/^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [128, 128, 128];
}

function getConfigFromJson() {
  try { return JSON.parse(document.getElementById('config').value); }
  catch { return null; }
}

function jsonToVisual() {
  const cfg = getConfigFromJson();
  if (!cfg) return;
  document.getElementById('ve-triangle_side').value = cfg.triangle_side || 200;
  document.getElementById('ve-space_width').value = cfg.space_width || 2700;
  document.getElementById('ve-space_height').value = cfg.space_height || 5000;
  document.getElementById('ve-seed').value = cfg.seed || 42;
  renderColors(cfg.colors || {});
  renderLots(cfg.lots || [], cfg.colors || {});
}

function visualToJson() {
  const cfg = buildConfigFromVisual();
  document.getElementById('config').value = JSON.stringify(cfg, null, 2);
}

function buildConfigFromVisual() {
  const cfg = {
    triangle_side: parseInt(document.getElementById('ve-triangle_side').value, 10) || 200,
    space_width: parseInt(document.getElementById('ve-space_width').value, 10) || 2700,
    space_height: parseInt(document.getElementById('ve-space_height').value, 10) || 5000,
    seed: (() => { const v = parseInt(document.getElementById('ve-seed').value, 10); return isNaN(v) ? 42 : v; })(),
    colors: {},
    lots: []
  };

  // Colors
  document.querySelectorAll('.color-item').forEach(el => {
    const name = el.querySelector('.color-name').value.trim();
    if (!name) return;
    const hex = el.querySelector('input[type="color"]').value;
    const rgb = hexToRgb(hex);
    const layer = el.dataset.layer || 'STONE_' + name.toUpperCase();
    const aci = Number(el.dataset.aci) || 7;
    cfg.colors[name] = { rgb, layer, aci };
  });

  // Lots
  document.querySelectorAll('.lot-item').forEach(el => {
    const isGradient = el.querySelector('.lot-toggle input').checked;
    if (isGradient) {
      const bottom = {};
      const top = {};
      el.querySelectorAll('.prop-row[data-section="bottom"]').forEach(row => {
        bottom[row.dataset.color] = Number(row.querySelector('input[type="range"]').value);
      });
      el.querySelectorAll('.prop-row[data-section="top"]').forEach(row => {
        top[row.dataset.color] = Number(row.querySelector('input[type="range"]').value);
      });
      cfg.lots.push({ bottom, top });
    } else {
      const props = {};
      el.querySelectorAll('.prop-row[data-section="flat"]').forEach(row => {
        props[row.dataset.color] = Number(row.querySelector('input[type="range"]').value);
      });
      cfg.lots.push(props);
    }
  });

  return cfg;
}

// --- Render color list ---
function renderColors(colors) {
  const container = document.getElementById('ve-colors');
  container.innerHTML = '';
  for (const [name, info] of Object.entries(colors)) {
    const rgb = info.rgb || [128, 128, 128];
    const hex = rgbToHex(...rgb);
    const el = document.createElement('div');
    el.className = 'color-item';
    el.dataset.layer = info.layer || '';
    el.dataset.aci = info.aci || 7;
    el.innerHTML =
      '<div class="color-swatch" style="background:' + hex + '">' +
        '<input type="color" value="' + hex + '" onchange="this.parentElement.style.background=this.value">' +
      '</div>' +
      '<input class="color-name" type="text" value="' + name + '">' +
      '<span class="color-meta">RGB ' + rgb.join(', ') + '</span>' +
      '<button class="btn-sm btn-remove" onclick="this.closest(\'.color-item\').remove()">&#x2715;</button>';
    // Update meta on color change
    el.querySelector('input[type="color"]').addEventListener('input', function() {
      const [r, g, b] = hexToRgb(this.value);
      el.querySelector('.color-meta').textContent = 'RGB ' + r + ', ' + g + ', ' + b;
    });
    container.appendChild(el);
  }
}

function addColor() {
  const container = document.getElementById('ve-colors');
  const idx = container.children.length + 1;
  const name = 'color' + idx;
  const hex = '#808080';
  const el = document.createElement('div');
  el.className = 'color-item';
  el.dataset.layer = 'STONE_' + name.toUpperCase();
  el.dataset.aci = '7';
  el.innerHTML =
    '<div class="color-swatch" style="background:' + hex + '">' +
      '<input type="color" value="' + hex + '" onchange="this.parentElement.style.background=this.value">' +
    '</div>' +
    '<input class="color-name" type="text" value="' + name + '">' +
    '<span class="color-meta">RGB 128, 128, 128</span>' +
    '<button class="btn-sm btn-remove" onclick="this.closest(\'.color-item\').remove()">&#x2715;</button>';
  el.querySelector('input[type="color"]').addEventListener('input', function() {
    const [r, g, b] = hexToRgb(this.value);
    el.querySelector('.color-meta').textContent = 'RGB ' + r + ', ' + g + ', ' + b;
  });
  container.appendChild(el);
}

// --- Render lot list ---
function getCurrentColors() {
  const colors = {};
  document.querySelectorAll('.color-item').forEach(el => {
    const name = el.querySelector('.color-name').value.trim();
    if (!name) return;
    const hex = el.querySelector('input[type="color"]').value;
    colors[name] = { rgb: hexToRgb(hex) };
  });
  return colors;
}

function makePropRows(colorMap, values, section) {
  let html = '';
  for (const [name, info] of Object.entries(colorMap)) {
    const rgb = info.rgb || [128, 128, 128];
    const hex = rgbToHex(...rgb);
    const val = values[name] || 0;
    html +=
      '<div class="prop-row" data-color="' + name + '" data-section="' + section + '">' +
        '<div class="prop-swatch" style="background:' + hex + '"></div>' +
        '<span class="prop-name">' + name + '</span>' +
        '<input type="range" min="0" max="100" value="' + val + '" ' +
          'oninput="syncPropFromSlider(this)">' +
        '<input type="number" class="prop-val" min="0" max="100" value="' + val + '" ' +
          'oninput="syncPropFromInput(this)"><span class="prop-pct">%</span>' +
      '</div>';
  }
  return html;
}

function renderLots(lots, colors) {
  const container = document.getElementById('ve-lots');
  container.innerHTML = '';
  lots.forEach((lot, i) => {
    const isGrad = lot.bottom !== undefined && lot.top !== undefined;
    addLotElement(container, i, isGrad, lot, colors);
  });
}

function addLotElement(container, index, isGradient, lot, colors) {
  const el = document.createElement('div');
  el.className = 'lot-item';

  const bottomVals = isGradient ? (lot.bottom || {}) : (lot || {});
  const topVals = isGradient ? (lot.top || {}) : (lot || {});

  let propsHtml = '';
  if (isGradient) {
    propsHtml =
      '<div class="lot-gradient-label">Bottom edge</div>' +
      makePropRows(colors, bottomVals, 'bottom') +
      '<div class="lot-gradient-label">Top edge</div>' +
      makePropRows(colors, topVals, 'top');
  } else {
    propsHtml = makePropRows(colors, bottomVals, 'flat');
  }

  el.innerHTML =
    '<div class="lot-header">' +
      '<span>Lot ' + (index + 1) + '</span>' +
      '<div style="display:flex;gap:8px;align-items:center">' +
        '<label class="lot-toggle"><input type="checkbox"' + (isGradient ? ' checked' : '') +
          ' onchange="toggleLotGradient(this)"> Gradient</label>' +
        '<button class="btn-sm btn-remove" onclick="this.closest(\'.lot-item\').remove();renumberLots()">&#x2715;</button>' +
      '</div>' +
    '</div>' +
    '<div class="lot-proportions">' + propsHtml + '</div>';

  container.appendChild(el);
}

function toggleLotGradient(checkbox) {
  const lotEl = checkbox.closest('.lot-item');
  const colors = getCurrentColors();
  const isGrad = checkbox.checked;

  // Collect current values
  const currentVals = {};
  lotEl.querySelectorAll('.prop-row').forEach(row => {
    currentVals[row.dataset.color] = Number(row.querySelector('input[type="range"]').value);
  });

  const propsDiv = lotEl.querySelector('.lot-proportions');
  if (isGrad) {
    propsDiv.innerHTML =
      '<div class="lot-gradient-label">Bottom edge</div>' +
      makePropRows(colors, currentVals, 'bottom') +
      '<div class="lot-gradient-label">Top edge</div>' +
      makePropRows(colors, currentVals, 'top');
  } else {
    propsDiv.innerHTML = makePropRows(colors, currentVals, 'flat');
  }
}

function addLot() {
  const container = document.getElementById('ve-lots');
  const colors = getCurrentColors();
  const index = container.children.length;
  const defaultVals = {};
  const keys = Object.keys(colors);
  if (keys.length > 0) {
    defaultVals[keys[0]] = 100;
    for (let i = 1; i < keys.length; i++) defaultVals[keys[i]] = 0;
  }
  addLotElement(container, index, false, defaultVals, colors);
}

function syncPropFromSlider(slider) {
  slider.parentElement.querySelector('.prop-val').value = slider.value;
}

function syncPropFromInput(input) {
  let v = parseInt(input.value, 10);
  if (isNaN(v)) v = 0;
  if (v < 0) v = 0;
  if (v > 100) v = 100;
  input.parentElement.querySelector('input[type="range"]').value = v;
}

function renumberLots() {
  document.querySelectorAll('.lot-item').forEach((el, i) => {
    el.querySelector('.lot-header span').textContent = 'Lot ' + (i + 1);
  });
}

// --- URL hash encoding ---
async function compress(str) {
  const bytes = new TextEncoder().encode(str);
  const cs = new CompressionStream('deflate-raw');
  const writer = cs.writable.getWriter();
  writer.write(bytes);
  writer.close();
  return await new Response(cs.readable).arrayBuffer();
}

async function decompress(buf) {
  const ds = new DecompressionStream('deflate-raw');
  const writer = ds.writable.getWriter();
  writer.write(buf);
  writer.close();
  const decompressed = await new Response(ds.readable).arrayBuffer();
  return new TextDecoder().decode(decompressed);
}

function toBase64Url(buf) {
  let binary = '';
  const bytes = new Uint8Array(buf);
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function fromBase64Url(str) {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  const pad = (4 - str.length % 4) % 4;
  str += '='.repeat(pad);
  const binary = atob(str);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

async function encodeConfig(json) {
  return toBase64Url(await compress(json));
}

async function decodeConfig(hash) {
  return await decompress(fromBase64Url(hash));
}

async function updateHash(json) {
  const encoded = await encodeConfig(json);
  history.replaceState(null, '', '#' + encoded);
}

// --- Share ---
async function share() {
  if (!currentConfig) return;
  syncToJson();
  const json = document.getElementById('config').value;
  await updateHash(json);
  const url = location.href;
  const urlInput = document.getElementById('shareUrl');
  const bar = document.getElementById('shareBar');
  urlInput.value = url;
  bar.classList.add('active');
  urlInput.select();
  try {
    await navigator.clipboard.writeText(url);
    flashCopyButton('Copied!');
  } catch (e) { }
}

function copyShareUrl() {
  const urlInput = document.getElementById('shareUrl');
  urlInput.select();
  navigator.clipboard.writeText(urlInput.value).then(() => {
    flashCopyButton('Copied!');
  });
}

function flashCopyButton(msg) {
  const btn = document.querySelector('.btn-copy');
  const orig = btn.textContent;
  btn.textContent = msg;
  setTimeout(() => btn.textContent = orig, 2000);
}

// --- Sync helper: ensure JSON textarea is up to date ---
function syncToJson() {
  if (document.getElementById('tab-visual').classList.contains('active')) {
    visualToJson();
  }
}

// --- Preview & Download ---
async function preview() {
  syncToJson();
  const errEl = document.getElementById('error');
  const infoEl = document.getElementById('info');
  const spinner = document.getElementById('spinner');
  const box = document.getElementById('previewBox');
  errEl.textContent = '';
  infoEl.textContent = '';

  let cfg;
  try {
    cfg = JSON.parse(document.getElementById('config').value);
  } catch (e) {
    errEl.textContent = 'Invalid JSON: ' + e.message;
    return;
  }

  spinner.classList.add('active');
  try {
    const resp = await fetch('/api/preview', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(cfg)
    });
    const data = await resp.json();
    if (data.error) {
      errEl.textContent = data.error;
      return;
    }
    box.innerHTML = data.svg;
    currentConfig = cfg;
    const dlBtn = document.getElementById('downloadBtn');
    dlBtn.disabled = false;
    dlBtn.title = '';
    const shareBtn = document.getElementById('shareBtn');
    shareBtn.disabled = false;
    shareBtn.title = '';
    infoEl.textContent = data.info;
    updateHash(document.getElementById('config').value);
  } catch (e) {
    errEl.textContent = 'Request failed: ' + e.message;
  } finally {
    spinner.classList.remove('active');
  }
}

async function download() {
  if (!currentConfig) return;
  const errEl = document.getElementById('error');
  const btn = document.getElementById('downloadBtn');
  const dxfSpinner = document.getElementById('dxfSpinner');
  errEl.textContent = '';

  btn.disabled = true;
  btn.title = 'Generating DXF file, please wait…';
  dxfSpinner.classList.add('active');

  try {
    const resp = await fetch('/api/dxf', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(currentConfig)
    });
    if (!resp.ok) {
      const data = await resp.json();
      errEl.textContent = data.error || 'Download failed';
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'parking_lot.dxf';
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    errEl.textContent = 'Download failed: ' + e.message;
  } finally {
    dxfSpinner.classList.remove('active');
    btn.disabled = false;
    btn.title = '';
  }
}

// --- Init ---
(async function() {
  // Load from URL hash if present
  const hash = location.hash.slice(1);
  if (hash) {
    try {
      const json = await decodeConfig(hash);
      JSON.parse(json); // validate
      document.getElementById('config').value = json;
    } catch (e) {
      document.getElementById('error').textContent = 'Failed to load config from URL: ' + e.message;
    }
  }
  // Populate visual editor from JSON
  jsonToVisual();
})();

// Allow Tab key in JSON textarea
document.getElementById('config').addEventListener('keydown', function(e) {
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = this.selectionStart, end = this.selectionEnd;
    this.value = this.value.substring(0, s) + '  ' + this.value.substring(end);
    this.selectionStart = this.selectionEnd = s + 2;
  }
});
</script>
</body>
</html>"""


def _process_config(cfg):
    """Parse and validate config, return (settings, errors)."""
    settings = gen.parse_config(cfg)
    errors = gen.validate_config(settings)
    return settings, errors


@app.route('/')
def index():
    config_path = 'parking_config.json' if os.path.exists('parking_config.json') else 'parking_config.sample.json'
    with open(config_path) as f:
        default_config = f.read()
    return render_template_string(HTML, default_config=default_config)


@app.route('/api/preview', methods=['POST'])
def api_preview():
    cfg = request.get_json()
    if not cfg:
        return jsonify(error='No JSON provided'), 400

    settings, errors = _process_config(cfg)
    if errors:
        return jsonify(error='\n'.join(errors))

    triangles, boundaries, num_spaces = gen.generate(settings)
    svg = gen.render_svg(settings, triangles, boundaries, num_spaces)

    # Strip XML declaration for inline embedding
    svg_inline = svg.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '')

    return jsonify(
        svg=svg_inline,
        info=f'{len(triangles)} triangles across {num_spaces} lots'
    )


@app.route('/api/dxf', methods=['POST'])
def api_dxf():
    cfg = request.get_json()
    if not cfg:
        return jsonify(error='No JSON provided'), 400

    settings, errors = _process_config(cfg)
    if errors:
        return jsonify(error='\n'.join(errors)), 400

    triangles, boundaries, num_spaces = gen.generate(settings)
    dxf_bytes = gen.render_dxf_bytes(settings, triangles, boundaries, num_spaces)

    return send_file(
        io.BytesIO(dxf_bytes),
        mimetype='application/dxf',
        as_attachment=True,
        download_name='parking_lot.dxf'
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
