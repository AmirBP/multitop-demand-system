import { IDataSource } from "./DataSource";
import { parseCSV } from "../utils/csvParse";

const DEMO_TARGET = {
  mae: 31.8, mape: 13.8, wape: 14.4, smape: 15.1,
  bias: -0.8, precision: 85.6, zero_rate: 33.4, wape_naive: 22.0, mejora_pp: 7.6,
};

const ESTADOS = ["OK","Quiebre Potencial","Sobre-stock"];

function mulberry32(a){return function(){let t=a+=0x6d2b79f5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}

function genDemo(n=120, seed=42){
  const rand = mulberry32(seed);
  const tiendas = ["Lima-Centro","Gamarra","San Juan"];
  const categorias = ["Sintéticos","Espumas","Lonas"];
  const campañas = ["Regular","Campaña Invierno","Liquidación"];
  const arr = Array.from({length:n}).map((_,i)=>{
    const tienda = tiendas[(rand()*tiendas.length)|0];
    const categoria = categorias[(rand()*categorias.length)|0];
    const campaña = campañas[(rand()*campañas.length)|0];
    const base = 30 + Math.floor(rand()*150);
    const boost = campaña==="Liquidación"?1.15: campaña==="Campaña Invierno"?1.08:1;
    const pred = Math.round(base*boost);
    const stock = Math.round(pred*(0.6 + rand()*1.2));
    const diff = (stock - Math.round(pred*0.95));
    const estado = stock < pred*0.7 ? "Quiebre Potencial" : stock > pred*1.3 ? "Sobre-stock" : "OK";
    return {
      CodArticulo:`SKU-${1000+i}`,
      Estado:estado,
      StockMes:stock,
      stock_objetivo: Math.round(pred*0.95),
      d_media: Math.max(1, Math.round(pred/30)),
      dias_cobertura: Math.max(1, Math.round(stock / Math.max(1, pred/30))),
      porcentaje_sobrestock: Math.max(0, stock - pred) / Math.max(1, pred),
      tienda, categoria, campaña,
      _diff: diff,
    };
  });
  const summary = arr.reduce((acc,r)=>{ acc[r.Estado]=(acc[r.Estado]||0)+1; return acc; },{OK:0,"Quiebre Potencial":0,"Sobre-stock":0});
  return { predictions: arr, summary };
}

function adaptFromParsed(rows){
  // intenta mapear cabeceras típicas; si faltan, crea valores razonables
  return rows.slice(0,500).map((r,i)=>{
    const sku = r.sku || r.SKU || r.cod || r.CodArticulo || `SKU-${i+1}`;
    const stock = Number(r.stock || r.StockMes || r.stock_actual || 60);
    const objetivo = Number(r.stock_objetivo || r.Stock_Recomendado || 80);
    const diff = (stock - objetivo);
    const estado = stock < objetivo*0.7 ? "Quiebre Potencial" : stock > objetivo*1.3 ? "Sobre-stock" : "OK";
    return {
      CodArticulo: sku,
      Estado: estado,
      StockMes: stock,
      stock_objetivo: objetivo,
      d_media: Number(r.demanda || r.Demanda || 3),
      dias_cobertura: Number(r.dias || r.Dias || Math.max(1, Math.round(stock / Math.max(1, Number(r.demanda || 3))))),
      porcentaje_sobrestock: objetivo ? Math.max(0, stock - objetivo) / objetivo : 0,
    };
  });
}

export class MockDataSource extends IDataSource {
  async cargarCSV(file){
    const text = await file.text();
    const rows = parseCSV(text);
    const adapted = adaptFromParsed(rows);
    const summary = adapted.reduce((a,r)=>{a[r.Estado]=(a[r.Estado]||0)+1; return a;},{OK:0,"Quiebre Potencial":0,"Sobre-stock":0});
    return { job_id:"demo-csv", summary, rawPredictions: adapted };
  }
  async cargarMuestra(){
    const { predictions, summary } = genDemo();
    return { job_id:"demo", summary, rawPredictions: predictions };
  }
  async obtenerMetrics(){
    const raw = localStorage.getItem("last_train_metrics");
    return raw ? JSON.parse(raw) : DEMO_TARGET;
  }

  // Soporte Dashboard
  async getSummary(){ const {summary} = genDemo(120,99); return { estados: summary }; }
  async getHistory(){ 
    // tres ejecuciones ficticias
    const now = Date.now();
    return [
      { job_id:"demo-001", created_at: new Date(now-86400000*2).toISOString() },
      { job_id:"demo-002", created_at: new Date(now-86400000).toISOString() },
      { job_id:"demo-003", created_at: new Date(now).toISOString() },
    ];
  }
  async getDetail(jobId){ const { predictions } = genDemo(90, jobId.length*13); return { job_id:jobId, generated_at:new Date().toISOString(), predictions }; }
  async validar(){ return { mae: 31.2, mape: 14.8, match_count: 842 }; }
}
