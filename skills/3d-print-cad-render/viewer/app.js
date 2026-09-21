import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { gunzipSync } from 'fflate';

const MODEL_ID = /^[a-z0-9][a-z0-9-]{0,63}$/;
function readEmbedded() {
  const dataElement = document.querySelector('#study-data');
  if (!dataElement) return null;
  const text = (dataElement.textContent || '').trim();
  dataElement.remove();
  if (!text || text === 'null' || text.includes('STUDY_DATA')) return null;
  try { return JSON.parse(text); } catch { return null; }
}
const embeddedStudy = readEmbedded();
let STUDY = null, catalogModels = [], currentModelId = '';
const $ = s => document.querySelector(s), plot = $('#plot');
const escapeHTML = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let current = 'part', view = 'solid', shell = 1, selected = [];
let hidden = new Set(), isolated = null, loadedConcept = null;
let renderer, controls, pending = 0, dirty = true, sectionDirty = true, needsFit = true, contextLost = false;
let frameCount = 0, loadCount = 0, disposedGeometries = 0;
const concept = () => STUDY.concepts.find(c => c.id === current);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#f7f4ec');
const assembly = new THREE.Group(); scene.add(assembly);
const camera = new THREE.OrthographicCamera(-200, 200, 250, -250, 0.1, 10000);
camera.up.set(0, 0, 1); camera.position.set(-650, -750, 570);
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8071, 2.4));
const light = new THREE.DirectionalLight(0xffffff, 2.5); light.position.set(-300, -450, 800); scene.add(light);
const fill = new THREE.DirectionalLight(0xffffff, 1); fill.position.set(400, 200, 150); scene.add(fill);
const axisHelper = new THREE.AxesHelper(55); scene.add(axisHelper);
const clipPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), 0);
const section = { enabled: false, axis: 'x', normal: [1, 0, 0], offset: 0, flip: false, helper: false };
const planeHelper = new THREE.Mesh(new THREE.PlaneGeometry(700, 700), new THREE.MeshBasicMaterial({ color: 0xc42b23, side: THREE.DoubleSide, transparent: true, opacity: 0.08, depthWrite: false }));
planeHelper.visible = false; scene.add(planeHelper);
const sectionLine = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xc42b23, depthTest: false, transparent: true, opacity: 0.95 }));
sectionLine.renderOrder = 100; scene.add(sectionLine);
const objects = new Map(), geometries = new Map(), edgeGeometries = new Map();
const measureLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xc42b23, depthTest: false, transparent: true }));
measureLine.renderOrder = 120; measureLine.visible = false; scene.add(measureLine);
const measurePts = [];
let measureOn = false, lastHit = null;
const raycaster = new THREE.Raycaster(), pointer = new THREE.Vector2();
let idleResolvers = [];

function presetVisible(r) {
  if (r.default_hidden) return false;
  if (view === 'electronics') return ['electronic', 'hardware'].includes(r.kind);
  if (view === 'installed' || view === 'exploded' || view === 'solid' || view === 'translucent') return r.kind !== 'reservation';
  return r.kind !== 'reservation';
}
function visible(r) {
  return !hidden.has(r.instance) && (isolated ? isolated.has(r.instance) : presetVisible(r));
}
function fail(message) {
  $('#error').style.display = 'block'; $('#error').textContent = message;
}
function requestDraw() {
  dirty = true;
  if (!pending && !contextLost && renderer) pending = requestAnimationFrame(draw);
}
function settle() { const resolve = idleResolvers; idleResolvers = []; resolve.forEach(r => r()); }

function loadPacked(key) {
  if (geometries.has(key)) return geometries.get(key);
  const packed = STUDY.geometry[key];
  const compressed = Uint8Array.from(atob(packed.data), c => c.charCodeAt(0));
  const raw = gunzipSync(compressed);
  const buffer = raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength);
  const g = new THREE.BufferGeometry();
  if (packed.kind === 'brep-edges') {
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buffer, 0, packed.pointCount * 3), 3));
  } else {
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buffer, 0, packed.vertexCount * 3), 3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(buffer, packed.vertexCount * 12, packed.indexCount), 1));
    g.computeVertexNormals();
  }
  g.computeBoundingBox(); g.computeBoundingSphere();
  geometries.set(key, g); return g;
}

function loadConcept() {
  for (const { mesh, edges } of objects.values()) {
    mesh.material.dispose();
    if (edges) edges.material.dispose();
  }
  for (const g of geometries.values()) { g.dispose(); disposedGeometries++; }
  objects.clear(); geometries.clear(); edgeGeometries.clear(); assembly.clear();
  renderer.renderLists.dispose();
  for (const row of concept().items) {
    const mesh = new THREE.Mesh(loadPacked(row.geometry), new THREE.MeshStandardMaterial({
      color: row.color, roughness: 0.8, metalness: row.kind === 'hardware' ? 0.2 : 0,
      side: THREE.DoubleSide, flatShading: true,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
    }));
    mesh.name = row.instance; mesh.userData.row = row; assembly.add(mesh);
    let edgeLine = null;
    if (row.cad_edges && STUDY.geometry[row.cad_edges]) {
      edgeLine = new THREE.LineSegments(loadPacked(row.cad_edges), new THREE.LineBasicMaterial({ color: 0x1c1b18, transparent: true, opacity: 0.85 }));
      assembly.add(edgeLine);
    }
    objects.set(row.instance, { mesh, row, edges: edgeLine });
  }
  loadedConcept = current; loadCount++; sectionDirty = true; needsFit = true;
}

function updateObjects() {
  const clipping = section.enabled ? [clipPlane] : [];
  for (const obj of objects.values()) {
    const { mesh, row } = obj, highlighted = selected.includes(row.instance);
    const opacity = highlighted ? 1 : row.kind === 'printed' ? shell : (row.opacity ?? 1);
    mesh.position.fromArray(view === 'exploded' ? row.explode_mm || [0, 0, 0] : [0, 0, 0]);
    mesh.visible = visible(row) && opacity > 0.001;
    const mat = mesh.material;
    const transparent = opacity < 0.999;
    if (mat.transparent !== transparent || !!mat.clippingPlanes?.length !== section.enabled) mat.needsUpdate = true;
    mat.color.set(highlighted ? '#c42b23' : row.color);
    mat.opacity = opacity; mat.transparent = transparent; mat.depthWrite = !transparent;
    mat.clippingPlanes = clipping;
    if (obj.edges) {
      obj.edges.position.copy(mesh.position);
      obj.edges.visible = mesh.visible && $('#edges').checked;
      obj.edges.material.clippingPlanes = clipping;
    }
  }
  axisHelper.visible = $('#axes').checked;
  $('#isolate').disabled = $('#hide-selection').disabled = $('#fit-selection').disabled = selected.length === 0;
}

function assemblyBounds(selectionOnly = false) {
  const box = new THREE.Box3();
  for (const { row, mesh } of objects.values()) {
    if (selectionOnly ? !selected.includes(row.instance) : !mesh.visible) continue;
    box.union(mesh.geometry.boundingBox.clone().translate(mesh.position));
  }
  if (box.isEmpty()) box.set(new THREE.Vector3(-50, -50, -50), new THREE.Vector3(50, 50, 50));
  return box;
}
function fit(selectionOnly = false) {
  const box = assemblyBounds(selectionOnly), center = box.getCenter(new THREE.Vector3());
  const dir = camera.position.clone().sub(controls.target).normalize();
  camera.position.copy(center).addScaledVector(dir, 1200); controls.target.copy(center); camera.lookAt(center); camera.updateMatrixWorld();
  const inverse = camera.matrixWorldInverse, bounds = new THREE.Box3();
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) bounds.expandByPoint(new THREE.Vector3(x, y, z).applyMatrix4(inverse));
  const size = bounds.getSize(new THREE.Vector3()), aspect = plot.clientWidth / plot.clientHeight;
  const height = Math.max(size.y, size.x / aspect, 10) * 1.15;
  camera.zoom = 1; camera.top = height / 2; camera.bottom = -height / 2; camera.left = -height * aspect / 2; camera.right = height * aspect / 2;
  camera.updateProjectionMatrix(); controls.update(); requestDraw();
}
function standardView(value) {
  const directions = { iso: [-1.3, -1.5, 0.83], front: [0, -1, 0], back: [0, 1, 0], left: [-1, 0, 0], right: [1, 0, 0], top: [0, 0, 1], bottom: [0, 0, -1] };
  const dir = new THREE.Vector3(...directions[value]);
  camera.up.set(0, 0, 1); if (value === 'top' || value === 'bottom') camera.up.set(0, 1, 0);
  camera.position.copy(controls.target).addScaledVector(dir, 1200); fit();
}
function setPlane() {
  const n = new THREE.Vector3(...section.normal).normalize();
  clipPlane.set(n.clone().multiplyScalar(section.flip ? -1 : 1), section.offset * (section.flip ? 1 : -1));
  planeHelper.position.copy(n).multiplyScalar(section.offset);
  planeHelper.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), n);
  planeHelper.visible = section.enabled && section.helper;
  sectionLine.visible = section.enabled;
  $('#section-summary').textContent = section.enabled ? `${section.axis.toUpperCase()} · ${section.offset.toFixed(1)} mm${section.flip ? ' · flipped' : ''}` : 'Off';
}
function updateSectionLines() {
  const lines = [], n = clipPlane.normal, constant = clipPlane.constant;
  for (const { mesh, row } of objects.values()) {
    if (!mesh.visible || !mesh.geometry.index) continue;
    const a = mesh.geometry.attributes.position.array, index = mesh.geometry.index.array;
    const p = [[0, 0, 0], [0, 0, 0], [0, 0, 0]], d = [0, 0, 0];
    for (let k = 0; k < index.length; k += 3) {
      for (let t = 0; t < 3; t++) { const j = index[k + t] * 3; p[t][0] = a[j] + mesh.position.x; p[t][1] = a[j + 1] + mesh.position.y; p[t][2] = a[j + 2] + mesh.position.z; d[t] = n.x * p[t][0] + n.y * p[t][1] + n.z * p[t][2] + constant; }
      if (d.every(v => v > 1e-6) || d.every(v => v < -1e-6) || d.every(v => Math.abs(v) < 1e-6)) continue;
      const hit = [];
      for (let t = 0; t < 3; t++) {
        const u = (t + 1) % 3;
        if (Math.abs(d[t]) < 1e-6) hit.push(p[t].slice());
        else if ((d[t] > 0) !== (d[u] > 0) && Math.abs(d[u]) >= 1e-6) {
          const f = d[t] / (d[t] - d[u]); hit.push(p[t].map((v, i) => v + f * (p[u][i] - v)));
        }
      }
      const unique = hit.filter((v, i) => hit.findIndex(w => v.every((x, j) => Math.abs(x - w[j]) < 1e-5)) === i);
      if (unique.length === 2) lines.push(...unique[0], ...unique[1]);
    }
  }
  sectionLine.geometry.dispose();
  sectionLine.geometry = new THREE.BufferGeometry();
  sectionLine.geometry.setAttribute('position', new THREE.Float32BufferAttribute(lines, 3));
  sectionLine.geometry.computeBoundingSphere();
}
function draw() {
  pending = 0;
  if (contextLost) { settle(); return; }
  try {
    if (loadedConcept !== current) loadConcept();
    if (dirty) { setPlane(); updateObjects(); dirty = false; }
    if (needsFit) { needsFit = false; fit(); }
    if (sectionDirty) { if (section.enabled) updateSectionLines(); sectionDirty = false; }
    renderer.render(scene, camera); frameCount++;
    $('#loading').hidden = true; window.studyReady = true;
    noteEnvelope();
    $('#scene-status').textContent = `${concept().name} · ${[...objects.values()].filter(o => o.mesh.visible).length} visible · CAD edges`;
    settle();
  } catch (e) { fail('The viewer could not render: ' + e.message); $('#loading').hidden = true; settle(); }
}
function markSceneChanged() { sectionDirty = true; requestDraw(); }
function selectParts(names) {
  selected = names;
  const rows = concept().items.filter(r => names.includes(r.instance));
  const hit = lastHit ? `<small>Hit ${lastHit.x.toFixed(2)}, ${lastHit.y.toFixed(2)}, ${lastHit.z.toFixed(2)} mm</small>` : '';
  $('#inspection').innerHTML = rows.map(r => `<b>${escapeHTML(r.instance)}</b><p>${escapeHTML(r.evidence || '')}</p><small>${(r.bbox_mm || []).map(x => Number(x).toFixed(1)).join(' × ')} mm · ${escapeHTML(r.status || 'cad')}</small>${hit}`).join('<hr>');
  parts(); markSceneChanged();
}
function noteEnvelope() {
  const node = document.querySelector('#metric-envelope');
  if (!node || !objects.size) return;
  const size = assemblyBounds().getSize(new THREE.Vector3());
  node.textContent = `${size.x.toFixed(1)} × ${size.y.toFixed(1)} × ${size.z.toFixed(1)} mm`;
}
function drawMeasure() {
  const el = $('#measure-readout');
  if (!el) return;
  if (measurePts.length === 2) {
    const d = measurePts[0].distanceTo(measurePts[1]);
    const dx = measurePts[1].x - measurePts[0].x, dy = measurePts[1].y - measurePts[0].y, dz = measurePts[1].z - measurePts[0].z;
    el.textContent = `${d.toFixed(2)} mm   Δ ${dx.toFixed(1)}, ${dy.toFixed(1)}, ${dz.toFixed(1)}`;
    measureLine.geometry.dispose();
    measureLine.geometry = new THREE.BufferGeometry().setFromPoints(measurePts);
    measureLine.visible = true;
  } else if (measurePts.length === 1) {
    el.textContent = 'First point. Click a second face.';
    measureLine.visible = false;
  } else {
    el.textContent = measureOn ? 'Click two faces.' : '';
    measureLine.visible = false;
  }
}
async function fetchModel(id) {
  if (!MODEL_ID.test(id)) throw new Error('bad model id');
  const res = await fetch('models/' + id + '.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('model ' + id + ' HTTP ' + res.status);
  return res.json();
}
function fillConcepts() {
  const nav = $('#concepts');
  nav.replaceChildren();
  if (!STUDY || STUDY.concepts.length < 2) { nav.hidden = true; return; }
  nav.hidden = false;
  STUDY.concepts.forEach(c => {
    const b = document.createElement('button'); b.dataset.concept = c.id; b.textContent = c.name;
    b.onclick = () => choose(c.id); nav.append(b);
  });
}
const openFolders = new Set();
let treeRestored = false;
function modelPath(m) {
  const raw = String(m.path || m.id).split('/').filter(Boolean);
  if (!raw.length || raw.some(seg => !MODEL_ID.test(seg))) return [m.id];
  return raw;
}
function treeIndex() {
  const root = { dirs: new Map(), files: [] };
  catalogModels.forEach(m => {
    const segs = modelPath(m);
    let node = root;
    for (let i = 0; i < segs.length - 1; i++) {
      if (!node.dirs.has(segs[i])) node.dirs.set(segs[i], { dirs: new Map(), files: [] });
      node = node.dirs.get(segs[i]);
    }
    node.files.push({ seg: segs[segs.length - 1], model: m });
  });
  return root;
}
function restoreTree() {
  if (treeRestored) return;
  treeRestored = true;
  try {
    const saved = JSON.parse(sessionStorage.getItem('rage-cad-tree-open') || 'null');
    if (Array.isArray(saved)) saved.forEach(key => { if (typeof key === 'string' && key.length < 240 && key.split('/').every(seg => MODEL_ID.test(seg))) openFolders.add(key); });
  } catch { /* private mode */ }
}
function rememberTree() {
  try { sessionStorage.setItem('rage-cad-tree-open', JSON.stringify([...openFolders])); } catch { /* ignore */ }
}
function ensureOpenFor(id) {
  const model = catalogModels.find(m => m.id === id);
  if (!model) return;
  const segs = modelPath(model);
  for (let i = 1; i < segs.length; i++) openFolders.add(segs.slice(0, i).join('/'));
}
function renderTreeNode(node, ul, prefix) {
  [...node.dirs.keys()].sort().forEach(name => {
    const path = [...prefix, name];
    const key = path.join('/');
    const open = openFolders.has(key);
    const li = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'dir';
    button.setAttribute('aria-expanded', open ? 'true' : 'false');
    button.textContent = (open ? '▾ ' : '▸ ') + name;
    button.onclick = () => {
      if (openFolders.has(key)) openFolders.delete(key); else openFolders.add(key);
      rememberTree();
      fillModelPicker(currentModelId);
    };
    li.append(button);
    if (open) {
      const child = document.createElement('ul');
      renderTreeNode(node.dirs.get(name), child, path);
      li.append(child);
    }
    ul.append(li);
  });
  [...node.files].sort((a, b) => a.seg.localeCompare(b.seg)).forEach(file => {
    const li = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'file'; button.dataset.model = file.model.id;
    if (file.model.id === currentModelId) button.setAttribute('aria-current', 'true');
    const label = document.createElement('span');
    label.textContent = file.seg;
    button.append(label);
    if (file.model.solids != null) {
      const count = document.createElement('span');
      count.className = 'count';
      count.textContent = String(file.model.solids);
      button.append(count);
    }
    button.onclick = () => loadModel(file.model.id);
    li.append(button);
    ul.append(li);
  });
}
function fillModelPicker(selectedId) {
  const tree = $('#model-tree');
  const wrap = $('#model-library');
  if (!tree) return;
  if (!catalogModels.length) { if (wrap) wrap.hidden = true; return; }
  if (wrap) wrap.hidden = false;
  restoreTree();
  ensureOpenFor(selectedId);
  tree.replaceChildren();
  const ul = document.createElement('ul');
  renderTreeNode(treeIndex(), ul, []);
  tree.append(ul);
  const current = catalogModels.find(m => m.id === selectedId);
  const label = $('#model-current');
  if (label) label.textContent = current ? (current.path || current.id) : '';
  const active = tree.querySelector('[aria-current="true"]');
  if (active) active.scrollIntoView({ block: 'nearest' });
}
async function loadModel(id) {
  if (!catalogModels.some(m => m.id === id)) return;
  $('#loading').hidden = false;
  $('#error').style.display = 'none';
  try { STUDY = await fetchModel(id); }
  catch (e) { fail(String(e.message || e)); $('#loading').hidden = true; return; }
  currentModelId = id;
  current = STUDY.concepts[0].id;
  view = STUDY.concepts[0].default_view || 'solid';
  shell = view === 'translucent' ? 0.2 : 1;
  selected = []; hidden.clear(); isolated = null; measurePts.length = 0; lastHit = null;
  $('#inspection').innerHTML = '';
  loadedConcept = null; needsFit = true; sectionDirty = true;
  const title = $('#page-title');
  if (title) title.textContent = STUDY.title || concept().name;
  document.title = STUDY.title || document.title;
  fillConcepts(); drawMeasure(); fillModelPicker(id); chrome(); requestDraw();
  return window.studyIdle();
}
function syncURL() {
  const url = new URL(location.href); url.searchParams.set('view', view); url.hash = current;
  if (currentModelId) url.searchParams.set('model', currentModelId); else url.searchParams.delete('model');
  if (section.enabled) {
    url.searchParams.set('cut', section.axis); url.searchParams.set('offset', section.offset.toFixed(1));
    url.searchParams.set('flip', section.flip ? '1' : '0');
    if (section.axis === 'custom') url.searchParams.set('normal', section.normal.join(',')); else url.searchParams.delete('normal');
  } else for (const key of ['cut', 'offset', 'flip', 'normal']) url.searchParams.delete(key);
  history.replaceState(null, '', url);
}
function choose(id) {
  if (!STUDY.concepts.some(c => c.id === id)) return;
  current = id; selected = []; hidden.clear(); isolated = null;
  view = concept().default_view || 'solid'; shell = view === 'translucent' ? 0.2 : 1;
  $('#inspection').innerHTML = ''; chrome(); sectionDirty = true; requestDraw();
  return window.studyIdle();
}
function chrome() {
  const c = concept();
  syncURL();
  $('#name').textContent = c.name;
  $('#priority').textContent = (c.release ? c.release + (c.priority ? ' · ' + c.priority : '') : (c.priority || ''));
  $('#service').textContent = c.service || '';
  document.querySelectorAll('#concepts button').forEach(b => b.setAttribute('aria-pressed', b.dataset.concept === current));
  document.querySelectorAll('#views button[data-view]').forEach(b => b.setAttribute('aria-pressed', b.dataset.view === view));
  $('#opacity').value = Math.round(shell * 100); $('#opacity-label').textContent = Math.round(shell * 100) + '%';
  $('#caption').textContent = view === 'exploded'
    ? 'Exploded inspection offsets solids along X; not a removal path.'
    : view === 'translucent'
      ? 'Printed shells use the opacity slider. CAD edges stay on the BREP.'
      : 'Drag to orbit · Right drag to pan · Scroll to zoom · Click a face to inspect. Edges are OCC BREP, not triangle creases.';
  const m = c.metrics || {};
  $('#metrics').innerHTML = [
    ['<span id="metric-envelope">—</span>', 'Assembly XYZ'],
    [String(m.solids ?? c.items.length), 'Solids'],
    [m.source || c.name, 'STEP'],
    [m.deflection_mm != null ? m.deflection_mm + ' mm' : 'OCC', 'Tessellation'],
  ].map(([a, b], i) => `<div class="metric"><strong>${i === 0 ? a : escapeHTML(String(a))}</strong>${escapeHTML(String(b))}</div>`).join('');
  noteEnvelope();
  parts();
}
function parts() {
  const q = $('#part-search').value.toLowerCase();
  $('#part-list').innerHTML = '';
  concept().items.filter(r => (r.instance + ' ' + (r.evidence || '')).toLowerCase().includes(q)).forEach(r => {
    const b = document.createElement('button'); b.className = 'part'; b.dataset.part = r.instance;
    b.setAttribute('aria-pressed', selected.includes(r.instance));
    b.innerHTML = escapeHTML(r.instance) + `<small>${escapeHTML(r.status)} · ${escapeHTML(r.kind)}</small>`;
    b.onclick = () => selectParts([r.instance]);
    $('#part-list').append(b);
  });
}
function sectionRange(center = false) {
  const n = new THREE.Vector3(...section.normal).normalize(), values = [];
  const box = assemblyBounds();
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) values.push(n.dot(new THREE.Vector3(x, y, z)));
  const min = Math.floor(Math.min(...values) - 1), max = Math.ceil(Math.max(...values) + 1);
  if (center) section.offset = Math.round((min + max) * 5) / 10;
  $('#section-offset').min = Math.min(min, section.offset); $('#section-offset').max = Math.max(max, section.offset);
  $('#section-offset').value = section.offset; $('#section-mm').value = section.offset;
}
function readSection() {
  const axis = $('#section-axis').value;
  const normal = axis === 'custom' ? ['x', 'y', 'z'].map(k => Number($('#normal-' + k).value)) : [axis === 'x' ? 1 : 0, axis === 'y' ? 1 : 0, axis === 'z' ? 1 : 0];
  if (!normal.every(Number.isFinite) || Math.hypot(...normal) < 1e-8) { fail('Enter a nonzero section normal.'); return; }
  $('#error').style.display = 'none'; section.axis = axis; section.normal = normal; section.enabled = $('#section-enabled').checked; section.flip = $('#section-flip').checked; section.helper = $('#plane-visible').checked;
  $('#custom-normal').hidden = axis !== 'custom'; sectionRange(); syncURL(); markSceneChanged();
}
function initUI() {
  fillConcepts();
  const views = concept().views || ['solid', 'translucent', 'exploded', 'installed'];
  views.forEach(v => {
    const b = document.createElement('button'); b.dataset.view = v; b.textContent = v.replace(/-/g, ' ');
    $('#views').append(b);
  });
  $('#views').addEventListener('click', e => {
    if (!e.target.dataset.view) return;
    view = e.target.dataset.view; shell = view === 'translucent' ? 0.2 : 1; selected = []; hidden.clear(); isolated = null; $('#inspection').innerHTML = ''; needsFit = true; chrome(); markSceneChanged();
  });
  $('#opacity').oninput = e => { shell = +e.target.value / 100; $('#opacity-label').textContent = e.target.value + '%'; markSceneChanged(); };
  $('#reset').onclick = () => { hidden.clear(); isolated = null; selectParts([]); $('#standard-view').value = 'iso'; standardView('iso'); chrome(); markSceneChanged(); };
  $('#standard-view').onchange = e => standardView(e.target.value);
  $('#fit-all').onclick = () => fit(); $('#fit-selection').onclick = () => fit(true);
  $('#edges').onchange = requestDraw; $('#axes').onchange = requestDraw;
  $('#clear-selection').onclick = () => selectParts([]); $('#part-search').oninput = parts;
  $('#isolate').onclick = () => { if (!selected.length) return; isolated = new Set(selected); hidden.clear(); needsFit = true; markSceneChanged(); };
  $('#hide-selection').onclick = () => { for (const name of selected) hidden.add(name); selectParts([]); markSceneChanged(); };
  $('#show-all').onclick = () => { hidden.clear(); isolated = null; view = 'translucent'; shell = 0.2; needsFit = true; chrome(); markSceneChanged(); };
  for (const id of ['section-enabled', 'section-axis', 'section-flip', 'plane-visible', 'normal-x', 'normal-y', 'normal-z']) $('#' + id).onchange = readSection;
  for (const id of ['section-offset', 'section-mm']) $('#' + id).oninput = e => {
    if (e.target.value === '' || !Number.isFinite(+e.target.value)) return;
    section.offset = +e.target.value; sectionRange(); syncURL(); markSceneChanged();
  };
  $('#section-center').onclick = () => { sectionRange(true); syncURL(); markSceneChanged(); };
  $('#section-align').onclick = () => {
    const dir = clipPlane.normal.clone().negate(); camera.up.set(0, 0, 1); if (Math.abs(dir.z) > 0.999) camera.up.set(0, 1, 0);
    camera.position.copy(controls.target).addScaledVector(dir, 1200); fit();
  };
  $('#save-image').onclick = () => {
    renderer.render(scene, camera);
    renderer.domElement.toBlob(blob => {
      if (!blob) return; const url = URL.createObjectURL(blob), a = document.createElement('a');
      a.href = url; a.download = `${currentModelId || current}-${section.enabled ? 'section' : view}.png`; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, 'image/png');
  };
  const measureBtn = $('#measure');
  if (measureBtn) measureBtn.onclick = () => {
    measureOn = !measureOn;
    measureBtn.setAttribute('aria-pressed', measureOn);
    if (!measureOn) measurePts.length = 0;
    drawMeasure(); requestDraw();
  };
  const copyBtn = $('#copy-link');
  if (copyBtn) copyBtn.onclick = () => navigator.clipboard.writeText(location.href).then(() => { copyBtn.textContent = 'Copied'; setTimeout(() => { copyBtn.textContent = 'Copy link'; }, 1200); });
  window.addEventListener('keydown', e => {
    if (e.target.matches('input, select, textarea')) return;
    const views = { '1': 'iso', '2': 'front', '3': 'right', '4': 'top', '5': 'back', '6': 'left', '7': 'bottom' };
    if (views[e.key]) { $('#standard-view').value = views[e.key]; standardView(views[e.key]); }
    else if (e.key === 'f') fit();
    else if (e.key === 'e') { $('#edges').checked = !$('#edges').checked; requestDraw(); }
    else if (e.key === 'm' && measureBtn) measureBtn.click();
  });
}
function initRenderer() {
  try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'low-power' }); }
  catch (e) {
    $('#loading').hidden = true;
    fail('Interactive inspection needs WebGL 2.');
    document.querySelectorAll('button,input,select').forEach(el => el.disabled = true); return false;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5)); renderer.localClippingEnabled = true;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  plot.prepend(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = false; controls.screenSpacePanning = true;
  controls.minZoom = 0.15; controls.maxZoom = 80; controls.addEventListener('change', () => { if (!pending && !contextLost) pending = requestAnimationFrame(draw); });
  renderer.domElement.addEventListener('webglcontextlost', e => { e.preventDefault(); contextLost = true; window.studyReady = false; cancelAnimationFrame(pending); pending = 0; settle(); fail('Graphics context interrupted.'); });
  renderer.domElement.addEventListener('webglcontextrestored', () => { contextLost = false; $('#error').style.display = 'none'; requestDraw(); });
  let down = null;
  renderer.domElement.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY, button: e.button }; });
  renderer.domElement.addEventListener('pointerup', e => {
    if (!down || down.button !== 0 || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set((e.clientX - rect.left) / rect.width * 2 - 1, -(e.clientY - rect.top) / rect.height * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects([...objects.values()].filter(o => o.mesh.visible).map(o => o.mesh), false);
    const hit = hits.find(h => !section.enabled || clipPlane.distanceToPoint(h.point) >= -1e-5);
    if (hit) {
      lastHit = hit.point.clone();
      if (measureOn) {
        measurePts.push(lastHit.clone());
        if (measurePts.length > 2) measurePts.shift();
        drawMeasure();
      }
      selectParts([hit.object.name]);
    }
  });
  new ResizeObserver(() => {
    const width = plot.clientWidth, height = plot.clientHeight; if (!width || !height) return;
    renderer.setSize(width, height, false); const half = (camera.top - camera.bottom) / 2;
    camera.left = -half * width / height; camera.right = half * width / height; camera.updateProjectionMatrix(); requestDraw();
  }).observe(plot);
  return true;
}
window.studyIdle = () => !pending ? Promise.resolve() : new Promise(r => idleResolvers.push(r));
window.studyState = () => ({ concept: current, view, shell, selected: [...selected], visible: concept().items.filter(visible).map(r => r.instance), section: { ...section }, hidden: [...hidden], isolated: isolated ? [...isolated] : null, cadEdges: true });
window.studyDiagnostics = () => ({
  renderer: 'Three.js ' + THREE.REVISION, loadedConcept, frameCount, loadCount, disposedGeometries, contextLost,
  gpuGeometries: renderer?.info.memory.geometries, cadEdgeKeys: concept().items.filter(r => r.cad_edges).length,
  sectionSegments: (sectionLine.geometry.attributes.position?.count || 0) / 2,
  model: currentModelId,
});
function applySearchState() {
  const params = new URLSearchParams(location.search);
  const hash = location.hash.slice(1);
  if (STUDY.concepts.some(c => c.id === hash)) current = hash;
  const requestedView = params.get('view');
  const allowed = concept().views || ['solid', 'translucent', 'exploded', 'installed'];
  if (allowed.includes(requestedView)) { view = requestedView; shell = view === 'translucent' ? 0.2 : 1; }
  if (['x', 'y', 'z', 'custom'].includes(params.get('cut'))) {
    section.enabled = true; section.axis = params.get('cut'); section.flip = params.get('flip') === '1';
    const value = Number(params.get('offset')); section.offset = Number.isFinite(value) ? value : 0;
    const normal = (params.get('normal') || '1,0,0').split(',').map(Number);
    section.normal = section.axis === 'custom' && normal.length === 3 && normal.every(Number.isFinite) && Math.hypot(...normal) > 1e-8 ? normal : section.axis === 'y' ? [0, 1, 0] : section.axis === 'z' ? [0, 0, 1] : [1, 0, 0];
  }
}
async function boot() {
  const params = new URLSearchParams(location.search);
  try {
    const res = await fetch('catalog.json', { cache: 'no-store' });
    if (res.ok) {
      const cat = await res.json();
      catalogModels = (cat.models || []).filter(m => m && MODEL_ID.test(m.id));
      if (MODEL_ID.test(cat.default || '') && catalogModels.some(m => m.id === cat.default)) currentModelId = cat.default;
    }
  } catch { catalogModels = []; }
  try {
    if (catalogModels.length) {
      const want = params.get('model');
      const id = catalogModels.some(m => m.id === want) ? want : (catalogModels.some(m => m.id === currentModelId) ? currentModelId : catalogModels[0].id);
      STUDY = await fetchModel(id);
      currentModelId = id;
      fillModelPicker(id);
    } else if (embeddedStudy && embeddedStudy.concepts && embeddedStudy.concepts.length) {
      STUDY = embeddedStudy;
      const library = $('#model-library');
      if (library) library.hidden = true;
    } else {
      fail('No CAD study loaded.');
      $('#loading').hidden = true;
      return;
    }
    current = STUDY.concepts[0].id;
    view = STUDY.concepts[0].default_view || 'solid';
    shell = view === 'translucent' ? 0.2 : 1;
    applySearchState();
    const title = $('#page-title');
    if (title && STUDY.title) title.textContent = STUDY.title;
    if (STUDY.title) document.title = STUDY.title;
    initUI(); chrome();
    $('#section-enabled').checked = section.enabled; $('#section-axis').value = section.axis; $('#section-flip').checked = section.flip; $('#custom-normal').hidden = section.axis !== 'custom';
    ['x', 'y', 'z'].forEach((k, i) => $('#normal-' + k).value = section.normal[i]);
    $('#section-tools').open = section.enabled;
    if (initRenderer()) requestDraw();
  } catch (e) {
    fail('The viewer could not start: ' + (e.message || e));
    $('#loading').hidden = true;
  }
}
boot();
