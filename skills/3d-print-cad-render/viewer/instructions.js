/**
 * Lego-style step planner for the CAD inspector.
 * Order is centroid z, then y, then x, then name.
 * Must match skills/3d-print-lego-instructions/scripts/plan_steps.py.
 */
export const ORDER_RULE = 'centroid z, then y, then x, then name';
export const Z_BAND_MM = 2;
export const DEFAULT_COLOR = '#c4b49a';
export const NOTE = `Assembly order is ${ORDER_RULE}. Not an LDraw model. Not print approval.`;

export function tenth(value) {
  return Math.floor(Number(value) * 10 + 0.5);
}

export function fingerprint(row) {
  const box = row.bbox_mm || [0, 0, 0];
  const color = row.color || DEFAULT_COLOR;
  return [tenth(box[0]), tenth(box[1]), tenth(box[2]), row.vertexCount || 0, color].join('|');
}

export function planInstructionSteps(rows, zBandMm = Z_BAND_MM) {
  if (!rows.length) return [];
  const sorted = rows.slice().sort((a, b) => {
    const c = a.centroid, d = b.centroid;
    const an = String(a.id), bn = String(b.id);
    return c[2] - d[2] || c[1] - d[1] || c[0] - d[0] || (an < bn ? -1 : an > bn ? 1 : 0);
  });
  const steps = [];
  let i = 0;
  while (i < sorted.length) {
    const anchor = sorted[i];
    const group = [anchor];
    let j = i + 1;
    while (j < sorted.length) {
      const nxt = sorted[j];
      if (nxt.fingerprint !== anchor.fingerprint) break;
      if (Math.abs(nxt.centroid[2] - anchor.centroid[2]) > zBandMm) break;
      group.push(nxt);
      j += 1;
    }
    const qty = group.length;
    const first = group[0].id;
    steps.push({
      number: steps.length + 1,
      new_ids: group.map(row => row.id),
      placed_ids: sorted.slice(0, j).map(row => row.id),
      quantity: qty,
      label: qty === 1 ? first : `${first} ×${qty}`,
    });
    i = j;
  }
  return steps;
}
