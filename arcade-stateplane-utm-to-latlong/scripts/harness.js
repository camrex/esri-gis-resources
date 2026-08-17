// Execute the ACTUAL Arcade script text under Node, with Arcade built-ins mapped
// to JavaScript. No re-implementation of the maths -- the file is loaded verbatim
// apart from the one-line output-mode assignment.
const fs = require('fs');

function round(v, n) {                       // Arcade rounds half away from zero
  if (n === undefined) n = 0;
  if (!isFinite(v)) return v;
  const p = Math.pow(10, n);
  const x = v * p;
  const r = x < 0 ? -Math.round(-x) : Math.round(x);
  return r / p;
}

function fmtNum(v, fmt) {                    // enough of "#.######" for BOTH mode
  if (fmt === undefined) return String(v);
  const dec = (fmt.split('.')[1] || '').length;
  let s = round(v, dec).toFixed(dec);
  if (s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, '');
  return s;
}

const BUILTINS = {
  PI: Math.PI,
  Sqrt: Math.sqrt, Pow: Math.pow, Exp: Math.exp, Log: Math.log, Abs: Math.abs,
  Sin: Math.sin, Cos: Math.cos, Tan: Math.tan,
  Asin: Math.asin, Acos: Math.acos, Atan: Math.atan,
  Atan2: (y, x) => Math.atan2(y, x),
  Floor: Math.floor, Ceil: Math.ceil,
  Max: (...a) => Math.max(...(Array.isArray(a[0]) ? a[0] : a)),
  Min: (...a) => Math.min(...(Array.isArray(a[0]) ? a[0] : a)),
  Round: round,
  IsNan: (v) => typeof v === 'number' && isNaN(v),
  IIf: (c, a, b) => (c ? a : b),
  Text: (v, f) => (typeof v === 'number' ? fmtNum(v, f) : String(v)),
  HasKey: (d, k) => d !== null && d !== undefined && Object.prototype.hasOwnProperty.call(d, String(k)),
  Dictionary: (...a) => { const o = {}; for (let i = 0; i < a.length; i += 2) o[String(a[i])] = a[i + 1]; return o; },
  Geometry: (f) => (f && f.geometry !== undefined ? f.geometry : null),
  IsEmpty: (v) => v === null || v === undefined || v === '' ||
                  (Array.isArray(v) && v.length === 0),
  Count: (v) => (v && v.length !== undefined ? v.length : 0),
  Number: (v) => Number(v),
  Console: () => {},
  Includes: (a, v) => Array.isArray(a) && a.indexOf(v) >= 0,
  Push: (a, v) => { a.push(v); return a.length; },
  Centroid: (g) => g,   // mock geometries are points
};

const NAMES = Object.keys(BUILTINS);
const VALUES = NAMES.map(n => BUILTINS[n]);

function compile(path, mode) {
  let src = fs.readFileSync(path, 'utf8');
  const re = /var\s+(MD|OUT_MODE)\s*=\s*"[A-Z]+"\s*;/;
  const hits = src.match(new RegExp(re.source, 'g')) || [];
  if (hits.length !== 1) throw new Error('expected 1 mode assignment, found ' + hits.length);
  src = src.replace(re, (m, v) => 'var ' + v + ' = ' + JSON.stringify(mode) + ';');
  // eslint-disable-next-line no-new-func
  return new Function(...NAMES, '$feature', '"use strict";\n' + src);
}

module.exports = { compile, BUILTINS, round, fmtNum };

if (require.main === module) {
  const [, , scriptPath, mode, pointsPath, outPath] = process.argv;
  const fn = compile(scriptPath, mode);
  const pts = JSON.parse(fs.readFileSync(pointsPath, 'utf8'));
  const out = new Array(pts.length);
  let errors = 0;
  for (let i = 0; i < pts.length; i++) {
    const [wkid, x, y] = pts[i];
    const feat = { geometry: { X: x, Y: y, spatialReference: { wkid: wkid } } };
    try {
      out[i] = fn(...VALUES, feat);
    } catch (e) {
      out[i] = { __throw: String(e && e.message || e) };
      errors++;
    }
  }
  fs.writeFileSync(outPath, JSON.stringify(out));
  console.error('evaluated ' + pts.length + ' points, ' + errors + ' runtime errors -> ' + outPath);
}
