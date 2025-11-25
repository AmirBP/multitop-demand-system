// Parser simple y robusto (comillas, comas, saltos)
export function parseCSV(text) {
  const rows = [];
  let i = 0, field = "", row = [], inQuotes = false;

  const pushField = () => { row.push(field); field = ""; };
  const pushRow = () => { rows.push(row); row = []; };

  while (i < text.length) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 2; continue; }
        inQuotes = false; i++; continue;
      }
      field += c; i++; continue;
    } else {
      if (c === '"') { inQuotes = true; i++; continue; }
      if (c === ',') { pushField(); i++; continue; }
      if (c === '\r') { i++; continue; }
      if (c === '\n') { pushField(); pushRow(); i++; continue; }
      field += c; i++; continue;
    }
  }
  pushField(); pushRow();
  // cabeza + cuerpo
  const header = rows.shift()?.map(h => h.trim()) || [];
  return rows.filter(r => r.length && r.some(x => x?.length)).map(r => {
    const o = {};
    header.forEach((h, idx) => o[h] = (r[idx] ?? "").trim());
    return o;
  });
}
