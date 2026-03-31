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
  .editor-panel { flex: 0 0 480px; }
  .preview-panel { flex: 1; min-width: 0; }
  textarea { width: 100%; height: 480px; font-family: "SF Mono", Monaco, Consolas, monospace;
             font-size: 13px; padding: 12px; border: 1px solid #ccc; border-radius: 6px;
             resize: vertical; background: #fff; tab-size: 2; }
  textarea:focus { outline: none; border-color: #4a90d9; box-shadow: 0 0 0 2px rgba(74,144,217,0.2); }
  .buttons { margin-top: 12px; display: flex; gap: 10px; }
  button { padding: 10px 20px; border: none; border-radius: 6px; font-size: 14px;
           cursor: pointer; font-weight: 500; }
  .btn-preview { background: #4a90d9; color: #fff; }
  .btn-preview:hover { background: #357abd; }
  .btn-download { background: #2ecc71; color: #fff; }
  .btn-download:hover { background: #27ae60; }
  .btn-download:disabled { background: #95a5a6; cursor: not-allowed; }
  .error { color: #e74c3c; margin-top: 10px; font-size: 13px; white-space: pre-wrap; }
  .info { color: #666; margin-top: 10px; font-size: 13px; }
  .preview-box { background: #fff; border: 1px solid #ccc; border-radius: 6px;
                 padding: 16px; min-height: 200px; overflow: auto; }
  .preview-box svg { width: 100%; height: auto; }
  .preview-placeholder { color: #aaa; text-align: center; padding: 80px 0; }
  .spinner { display: none; }
  .spinner.active { display: inline-block; }
  footer { margin-top: 30px; padding-top: 16px; border-top: 1px solid #ddd;
           color: #999; font-size: 12px; text-align: center; }
  footer a { color: #999; text-decoration: none; }
  footer a:hover { color: #666; }
  footer svg { vertical-align: middle; margin-right: 4px; }
  @media (max-width: 900px) { .layout { flex-direction: column; } .editor-panel { flex: none; } }
</style>
</head>
<body>
<div class="container">
  <h1>Parking Lot Stone Pattern Generator</h1>
  <p class="subtitle">Define color proportions per lot, preview the pattern, download as DXF.</p>

  <div class="layout">
    <div class="editor-panel">
      <textarea id="config" spellcheck="false">{{ default_config }}</textarea>
      <div class="buttons">
        <button class="btn-preview" onclick="preview()">
          <span class="spinner" id="spinner">&#9881; </span>Preview
        </button>
        <button class="btn-download" id="downloadBtn" onclick="download()" disabled title="Run Preview first to enable download">
          <span class="spinner" id="dxfSpinner" title="Generating DXF file, please wait…">&#9881; </span>Download DXF
        </button>
      </div>
      <div id="error" class="error"></div>
      <div id="info" class="info"></div>
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

async function preview() {
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
    infoEl.textContent = data.info;
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

// Allow Tab key in textarea
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
