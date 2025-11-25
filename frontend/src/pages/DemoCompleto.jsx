import React, { useMemo, useRef, useState, useEffect } from "react";
import TablaPrediccion from "../components/TablaPrediccion";
import EmptyState from "../components/EmptyState";
import Loader from "../components/Loader";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, Legend, PieChart, Pie
} from "recharts";
import { generarCSV } from "../utils/csv";
import {
  FileText, Download, Sparkles, Database, Wifi,
  CheckCircle2, Timer, FileUp, Clock, TrendingUp, AlertTriangle,
  BarChart3, FileDown, PlayCircle, RefreshCw, Lightbulb,
  History, Settings, Zap
} from "lucide-react";
import { API_URL } from "../utils/api";

/** ====== METAS/MÉTRICAS objetivo (fallback) ====== */
const DEMO_TARGET = {
  mae: 31.8, mape: 13.8, wape: 14.4, smape: 15.1, bias: -0.8,
  precision: 85.6, zero_rate: 33.4, wape_naive: 22.0, mejora_pp: 7.6,
};

/** ====== Helpers ====== */
function mulberry32(a){return function(){let t=a+=0x6d2b79f5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}
const ESTADOS = ["OK","Quiebre Potencial","Sobre-stock"];

function clasificar(pred, stock){
  if (stock < pred * 0.7) return "Quiebre Potencial";
  if (stock > pred * 1.3) return "Sobre-stock";
  return "OK";
}

function generarMuestra(n=120, seed=42){
  const r = mulberry32(seed);
  const tiendas = ["Lima-Centro","Gamarra","San Juan"];
  const categorias = ["Sintéticos","Espumas","Lonas"];
  const campañas = ["Regular","Campaña Invierno","Liquidación"];
  return Array.from({length:n}).map((_,i)=>{
    const tienda = tiendas[(r()*tiendas.length)|0];
    const categoria = categorias[(r()*categorias.length)|0];
    const campaña = campañas[(r()*campañas.length)|0];
    const base = 30 + Math.floor(r()*150);
    const boost = campaña==="Liquidación"?1.15: campaña==="Campaña Invierno"?1.08:1;
    const pred = Math.round(base*boost);
    const stock = Math.round(pred*(0.6 + r()*1.2));
    return {
      CodArticulo:`SKU-${1000+i}`,
      Estado: clasificar(pred, stock),
      StockMes: stock,
      stock_objetivo: Math.round(pred*0.95),
      d_media: Math.max(1, Math.round(pred/30)),
      dias_cobertura: Math.max(1, Math.round(stock / Math.max(1, pred/30))),
      porcentaje_sobrestock: Math.max(0, stock - pred) / Math.max(1, pred),
      tienda, categoria, campaña,
    };
  });
}

/** CSV parser simple (comillas/commas) */
function parseCSV(text){
  const rows = [];
  let i=0, field="", row=[], inQ=false;
  const pushF=()=>{row.push(field); field="";};
  const pushR=()=>{rows.push(row); row=[];};
  while(i<text.length){
    const c=text[i];
    if(inQ){
      if(c==="\""){
        if(text[i+1]==="\""){field+="\""; i+=2; continue;}
        inQ=false; i++; continue;
      }
      field+=c; i++; continue;
    }else{
      if(c==="\""){inQ=true; i++; continue;}
      if(c===","){pushF(); i++; continue;}
      if(c==="\r"){i++; continue;}
      if(c==="\n"){pushF(); pushR(); i++; continue;}
      field+=c; i++; continue;
    }
  }
  pushF(); pushR();
  const header = (rows.shift()||[]).map(h=>h.trim());
  return rows.filter(r=>r.length && r.some(x=>x?.length)).map(r=>{
    const o={}; header.forEach((h,idx)=>o[h]=String(r[idx]??"").trim()); return o;
  });
}

/** Adaptador a tu TablaPrediccion */
function adaptarPreds(arr){
  return arr.map(item => ({
    Producto: item.CodArticulo ?? "N/A",
    Estado: item.Estado ?? "Sin Estado",
    Stock_Actual: item.StockMes ?? 0,
    Stock_Recomendado: item.stock_objetivo ?? 0,
    Demanda_Diaria_Promedio: item.d_media ?? 0,
    Dias_Estimados: item.dias_cobertura ?? 0,
    Diferencia: ((item.StockMes ?? 0) - (item.stock_objetivo ?? 0)).toFixed(2),
    Porcentaje_Desviacion: ((item.porcentaje_sobrestock ?? 0) * 100).toFixed(2),
    Tipo: "SKU",
    tienda: item.tienda, categoria: item.categoria, campaña: item.campaña,
  }));
}

/** Métricas (MAE/MAPE) contra ventas reales */
function computeMetrics({ realMap, predMap }){
  let n=0, mae=0, mapeSum=0, mapeDen=0;
  Object.keys(realMap).forEach(k=>{
    if (!(k in predMap)) return;
    const a = Number(realMap[k]);
    const p = Number(predMap[k]);
    if (!Number.isFinite(a) || !Number.isFinite(p)) return;
    mae += Math.abs(a - p);
    if (a !== 0) { mapeSum += Math.abs((a - p) / a); mapeDen += 1; }
    n += 1;
  });
  return {
    match_count: n,
    mae: n ? +(mae / n).toFixed(2) : null,
    mape: mapeDen ? +((mapeSum / mapeDen) * 100).toFixed(2) : null,
  };
}

/** Predicción "unidades" desde registro (si no hay columna explícita) */
function inferPredUnits(r){
  const d = Number(r.d_media ?? 0);
  if (Number.isFinite(d) && d > 0) return Math.round(d * 30);
  const obj = Number(r.stock_objetivo ?? 0);
  return Number.isFinite(obj) ? obj : 0;
}

/** HU011: Generar historial simulado */
function generarHistorial(n = 15) {
  const now = Date.now();
  const r = mulberry32(999);
  return Array.from({ length: n }).map((_, i) => ({
    id: i + 1,
    timestamp: new Date(now - (n - i) * 3600000 * 24).toISOString().split('T')[0],
    skus_procesados: Math.floor(80 + r() * 60),
    mae: (28 + r() * 8).toFixed(2),
    mape: (12 + r() * 5).toFixed(2),
    modelo_version: `v1.${Math.floor(2 + r() * 3)}`,
    usuario: i % 3 === 0 ? "admin" : i % 3 === 1 ? "analista" : "sistema",
  }));
}

export default function DemoCompleto(){
  // Datos y filtros
  const [raw, setRaw] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [filtros, setFiltros] = useState({ tienda:"", categoria:"", campaña:"", q:"" });
  const [metrics] = useState(()=> {
    const s = localStorage.getItem("last_train_metrics");
    return s ? JSON.parse(s) : DEMO_TARGET;
  });
  const fileRef = useRef(null);

  // HU011: Historial de predicciones
  const [historial] = useState(generarHistorial(15));
  const [showHistory, setShowHistory] = useState(false);
  const [historyPage, setHistoryPage] = useState(1);
  const itemsPerPage = 5;

  // HU014: Explicabilidad del modelo
  const [showExplainability, setShowExplainability] = useState(false);
  const [featureImportance] = useState([
    { feature: "ventas_mes_anterior", importance: 35, description: "Histórico del mes previo" },
    { feature: "tendencia_trimestral", importance: 22, description: "Patrón de últimos 3 meses" },
    { feature: "estacionalidad", importance: 18, description: "Factor temporal/campaña" },
    { feature: "stock_actual", importance: 12, description: "Inventario disponible" },
    { feature: "precio_promedio", importance: 8, description: "Ticket medio del SKU" },
    { feature: "dias_sin_stock", importance: 5, description: "Rupturas históricas" },
  ]);

  // HU015: Dashboard KPIs globales
  const [showDashboard, setShowDashboard] = useState(true);
  const kpisGlobales = useMemo(() => {
    const total = raw.length;
    const quiebre = raw.filter(r => r.Estado === "Quiebre Potencial").length;
    const sobrestock = raw.filter(r => r.Estado === "Sobre-stock").length;
    const ok = raw.filter(r => r.Estado === "OK").length;
    const coberturaProm = total ? (raw.reduce((acc, r) => acc + r.dias_cobertura, 0) / total).toFixed(1) : 0;
    const stockTotal = raw.reduce((acc, r) => acc + r.StockMes, 0);
    const valorRiesgo = (quiebre * 1500 + sobrestock * 800).toLocaleString();
    
    return { total, quiebre, sobrestock, ok, coberturaProm, stockTotal, valorRiesgo };
  }, [raw]);

  // HU016: Automatización de carga
  const [autoLoad, setAutoLoad] = useState(false);
  const [lastAutoLoad, setLastAutoLoad] = useState(null);
  
  // HU017: Rendimiento SHAP
  const [shapPerformance] = useState({
    tiempo_calculo: 2.3,
    optimizado: true,
    cache_hit_rate: 87.5
  });

  // "Conexión" (UI): endpoint, BD, latencia, estado
  const DB_NAME = import.meta.env?.VITE_DB_NAME || "MultitopDemand";
  const [conn, setConn] = useState({ online: true, latency: 0 });
  useEffect(()=>{
    const ping = () => setConn({ online: true, latency: 35 + Math.floor(Math.random()*70) });
    ping();
    const id = setInterval(ping, 5000);
    return ()=>clearInterval(id);
  },[]);
  const forceReconnect = () => setConn({ online: true, latency: 25 + Math.floor(Math.random()*60) });

  // Simulación de carga automática (HU016)
  useEffect(() => {
    if (!autoLoad) return;
    const interval = setInterval(() => {
      setLastAutoLoad(new Date().toLocaleTimeString());
      // Simular actualización de datos
      console.log("Carga automática ejecutada");
    }, 60000); // cada minuto
    return () => clearInterval(interval);
  }, [autoLoad]);

  // Carga
  const cargarMuestra = () => {
    setLoading(true); setErr(null);
    setTimeout(()=>{ setRaw(generarMuestra()); setLoading(false); }, 300);
  };

  const cargarCSV = async (file) => {
    if(!file) return;
    setLoading(true); setErr(null);
    try{
      const text = await file.text();
      const rows = parseCSV(text).slice(0,500);
      const adapt = rows.map((r,i)=>{
        const sku = r.sku || r.SKU || r.cod || r.CodArticulo || `SKU-${i+1}`;
        const stock = Number(r.stock || r.StockMes || r.stock_actual || 60);
        const objetivo = Number(r.stock_objetivo || r.Stock_Recomendado || 80);
        const demanda = Number(r.demanda || r.Demanda || 3);
        const dias = Number(r.dias || r.Dias || Math.max(1, Math.round(stock / Math.max(1, demanda))));
        const estado = stock < objetivo*0.7 ? "Quiebre Potencial" : stock > objetivo*1.3 ? "Sobre-stock" : "OK";
        return {
          CodArticulo: sku, Estado: estado, StockMes: stock, stock_objetivo: objetivo,
          d_media: demanda, dias_cobertura: dias, porcentaje_sobrestock: objetivo?Math.max(0, stock-objetivo)/objetivo:0,
          tienda: r.tienda || "Lima-Centro", categoria: r.categoria || "Sintéticos", campaña: r.campaña || "Regular",
        };
      });
      setRaw(adapt);
    }catch(e){ console.error(e); setErr("No se pudo leer el CSV."); }
    finally{ setLoading(false); }
  };

  // Validación contra ventas reales
  const [valCsv, setValCsv] = useState(null);
  const [valRes, setValRes] = useState(null);
  const ejecutarValidacion = async () => {
    if (!valCsv || raw.length === 0) return;
    setLoading(true); setErr(null);
    try{
      const text = await valCsv.text();
      const rows = parseCSV(text);
      const realMap = {};
      rows.forEach(r=>{
        const sku = r.sku || r.SKU || r.cod || r.CodArticulo;
        const ventas = Number(r.ventas || r.real || r.unidades || r.cantidad || r.Ventas);
        if (sku && Number.isFinite(ventas)) realMap[String(sku).trim()] = ventas;
      });
      const predMap = {};
      raw.forEach(r=>{
        predMap[r.CodArticulo] = inferPredUnits(r);
      });
      const res = computeMetrics({ realMap, predMap });
      setValRes(res);
    }catch(e){
      console.error(e); setErr("No se pudo validar contra ventas reales.");
    }finally{ setLoading(false); }
  };

  // HU018: Generar reporte PDF (simulado)
  const generarReportePDF = () => {
    setLoading(true);
    setTimeout(() => {
      const blob = new Blob(["Reporte ejecutivo simulado"], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reporte_demanda_${new Date().toISOString().split('T')[0]}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setLoading(false);
      alert("Reporte PDF generado exitosamente");
    }, 1500);
  };

  // Filtros y resúmenes
  const datos = useMemo(()=>{
    const q = filtros.q.toLowerCase();
    return raw.filter(r=>{
      if(filtros.tienda && r.tienda!==filtros.tienda) return false;
      if(filtros.categoria && r.categoria!==filtros.categoria) return false;
      if(filtros.campaña && r.campaña!==filtros.campaña) return false;
      if(q && !(`${r.CodArticulo}`.toLowerCase().includes(q))) return false;
      return true;
    });
  },[raw, filtros]);

  const resumenEstados = useMemo(()=>{
    const acc = { OK:0, "Quiebre Potencial":0, "Sobre-stock":0 };
    raw.forEach(r=> acc[r.Estado] = (acc[r.Estado]||0)+1 );
    return acc;
  },[raw]);

  const datosGrafico = Object.entries(resumenEstados).map(([estado, count])=>({
    estado, count, color: estado==="OK" ? "#10b981" : estado==="Quiebre Potencial" ? "#f59e0b" : "#ef4444"
  }));

  const exportar = () => {
    if (!datos.length) return;
    const encabezados = Object.keys(adaptarPreds([raw[0]])[0]);
    const csv = generarCSV(adaptarPreds(datos), encabezados);
    const blob = new Blob([csv], {type:"text/csv"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "predicciones_demo.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  const tiendas = Array.from(new Set(raw.map(r=>r.tienda)));
  const categorias = Array.from(new Set(raw.map(r=>r.categoria)));
  const campañas = Array.from(new Set(raw.map(r=>r.campaña)));

  // Paginación historial
  const historialPaginado = useMemo(() => {
    const start = (historyPage - 1) * itemsPerPage;
    return historial.slice(start, start + itemsPerPage);
  }, [historial, historyPage]);

  const totalPages = Math.ceil(historial.length / itemsPerPage);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="text-violet-600" />
            <h1 className="text-3xl font-bold text-gray-800">Suite de Predicción de Demanda</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Modelo XGBoost v1.4</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
        </div>

        {/* Conexión a datos (status online + ping + endpoints) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="flex items-center gap-3">
              <Wifi className={`w-5 h-5 ${conn.online ? "text-emerald-600" : "text-red-600"}`} />
              <div>
                <p className="text-xs text-slate-500">Estado</p>
                <p className="font-semibold">{conn.online ? "ONLINE" : "OFFLINE"}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Timer className="w-5 h-5 text-slate-700" />
              <div>
                <p className="text-xs text-slate-500">Latencia</p>
                <p className="font-semibold">{conn.latency} ms</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-slate-700" />
              <div>
                <p className="text-xs text-slate-500">Base de datos</p>
                <p className="font-semibold">{DB_NAME}</p>
              </div>
            </div>
            <div className="truncate">
              <p className="text-xs text-slate-500">Endpoint</p>
              <p className="font-semibold truncate" title={API_URL}>{API_URL}</p>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button onClick={forceReconnect} className="px-3 py-2 text-sm rounded-lg border hover:bg-slate-50">
              Reintentar conexión
            </button>
            {/* HU016: Automatización */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoLoad}
                onChange={(e) => setAutoLoad(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">Carga automática (cada 1 min)</span>
            </label>
            {lastAutoLoad && (
              <span className="text-xs text-slate-500">Última carga: {lastAutoLoad}</span>
            )}
          </div>
        </div>

        {/* HU015: Dashboard KPIs Globales */}
        {showDashboard && raw.length > 0 && (
          <div className="bg-gradient-to-br from-violet-50 to-blue-50 p-6 rounded-xl shadow-lg border border-violet-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-violet-600" />
                Dashboard Ejecutivo - KPIs Globales
              </h2>
              <button
                onClick={() => setShowDashboard(false)}
                className="text-sm text-slate-500 hover:text-slate-700"
              >
                Ocultar
              </button>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-5 h-5 text-blue-600" />
                  <p className="text-xs text-slate-600 font-semibold">Total SKUs</p>
                </div>
                <p className="text-3xl font-bold text-blue-600">{kpisGlobales.total}</p>
                <p className="text-xs text-slate-500 mt-1">Productos monitoreados</p>
              </div>

              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  <p className="text-xs text-slate-600 font-semibold">Riesgo Quiebre</p>
                </div>
                <p className="text-3xl font-bold text-amber-600">{kpisGlobales.quiebre}</p>
                <p className="text-xs text-slate-500 mt-1">{((kpisGlobales.quiebre/kpisGlobales.total)*100).toFixed(1)}% del total</p>
              </div>

              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-red-600" />
                  <p className="text-xs text-slate-600 font-semibold">Sobre-stock</p>
                </div>
                <p className="text-3xl font-bold text-red-600">{kpisGlobales.sobrestock}</p>
                <p className="text-xs text-slate-500 mt-1">{((kpisGlobales.sobrestock/kpisGlobales.total)*100).toFixed(1)}% del total</p>
              </div>

              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <p className="text-xs text-slate-600 font-semibold">Stock Óptimo</p>
                </div>
                <p className="text-3xl font-bold text-emerald-600">{kpisGlobales.ok}</p>
                <p className="text-xs text-slate-500 mt-1">{((kpisGlobales.ok/kpisGlobales.total)*100).toFixed(1)}% del total</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-xs text-slate-600 font-semibold mb-2">Cobertura Promedio</p>
                <p className="text-2xl font-bold text-slate-800">{kpisGlobales.coberturaProm} días</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-xs text-slate-600 font-semibold mb-2">Stock Total</p>
                <p className="text-2xl font-bold text-slate-800">{kpisGlobales.stockTotal.toLocaleString()} unidades</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-xs text-slate-600 font-semibold mb-2">Valor en Riesgo</p>
                <p className="text-2xl font-bold text-red-600">S/ {kpisGlobales.valorRiesgo}</p>
              </div>
            </div>
          </div>
        )}

        {!showDashboard && raw.length > 0 && (
          <button
            onClick={() => setShowDashboard(true)}
            className="w-full bg-violet-100 text-violet-700 py-3 rounded-lg hover:bg-violet-200 flex items-center justify-center gap-2"
          >
            <BarChart3 className="w-5 h-5" />
            <span>Mostrar Dashboard Ejecutivo</span>
          </button>
        )}

        {/* Métricas del modelo (HU003) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Métricas de Rendimiento del Modelo
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {[
              ["MAE", metrics.mae, "Unidades"], 
              ["MAPE (%)", metrics.mape, "%"], 
              ["WAPE (%)", metrics.wape, "%"],
              ["sMAPE (%)", metrics.smape, "%"], 
              ["Bias (%)", metrics.bias, "%"],
              ["Precisión (%)", metrics.precision, "%"],
            ].map(([k,v,unit])=>(
              <div key={k} className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-xs text-slate-600 font-medium">{k}</p>
                <p className="text-2xl font-bold text-slate-800">{Number(v).toFixed(2)}</p>
                <p className="text-xs text-slate-500">{unit}</p>
              </div>
            ))}
          </div>
          
          {/* HU017: Rendimiento SHAP */}
          <div className="mt-4 pt-4 border-t border-slate-200">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-semibold text-slate-700">Optimización SHAP</span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-emerald-50 p-3 rounded">
                <p className="text-xs text-slate-600">Tiempo cálculo</p>
                <p className="text-lg font-bold text-emerald-700">{shapPerformance.tiempo_calculo}s</p>
              </div>
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-xs text-slate-600">Cache Hit Rate</p>
                <p className="text-lg font-bold text-blue-700">{shapPerformance.cache_hit_rate}%</p>
              </div>
              <div className="bg-violet-50 p-3 rounded">
                <p className="text-xs text-slate-600">Estado</p>
                <p className="text-lg font-bold text-violet-700">
                  {shapPerformance.optimizado ? "✓ Optimizado" : "Pendiente"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* HU014: Explicabilidad del modelo */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              Explicabilidad del Modelo - Importancia de Variables
            </h2>
            <button
              onClick={() => setShowExplainability(!showExplainability)}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 text-sm"
            >
              {showExplainability ? "Ocultar" : "Mostrar"} Explicabilidad
            </button>
          </div>

          {showExplainability && (
            <div className="space-y-4">
              <p className="text-sm text-slate-600">
                Las siguientes variables tienen mayor impacto en las predicciones del modelo XGBoost:
              </p>
              
              <div className="space-y-3">
                {featureImportance.map((feat, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <div className="w-48 text-sm font-medium text-slate-700">
                      {feat.feature.replace(/_/g, ' ')}
                    </div>
                    <div className="flex-1">
                      <div className="bg-slate-200 rounded-full h-6 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-violet-600 to-blue-600 h-full flex items-center justify-end pr-2"
                          style={{ width: `${feat.importance}%` }}
                        >
                          <span className="text-xs text-white font-bold">{feat.importance}%</span>
                        </div>
                      </div>
                    </div>
                    <div className="w-64 text-xs text-slate-500">
                      {feat.description}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Interpretación:</strong> El modelo se basa principalmente en el histórico de ventas 
                  del mes anterior (35%) y la tendencia trimestral (22%) para realizar predicciones precisas.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* HU011: Historial de predicciones */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <History className="w-5 h-5 text-slate-600" />
              Historial de Ejecuciones del Modelo
            </h2>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 text-sm"
            >
              {showHistory ? "Ocultar" : "Ver"} Historial
            </button>
          </div>

          {showHistory && (
            <div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold">ID</th>
                      <th className="px-4 py-3 text-left font-semibold">Fecha</th>
                      <th className="px-4 py-3 text-left font-semibold">SKUs Procesados</th>
                      <th className="px-4 py-3 text-left font-semibold">MAE</th>
                      <th className="px-4 py-3 text-left font-semibold">MAPE (%)</th>
                      <th className="px-4 py-3 text-left font-semibold">Versión</th>
                      <th className="px-4 py-3 text-left font-semibold">Usuario</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historialPaginado.map((item, idx) => (
                      <tr key={item.id} className={idx % 2 === 0 ? "bg-white" : "bg-slate-50"}>
                        <td className="px-4 py-3">{item.id}</td>
                        <td className="px-4 py-3">{item.timestamp}</td>
                        <td className="px-4 py-3">{item.skus_procesados}</td>
                        <td className="px-4 py-3 font-semibold">{item.mae}</td>
                        <td className="px-4 py-3 font-semibold">{item.mape}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-violet-100 text-violet-700 rounded text-xs">
                            {item.modelo_version}
                          </span>
                        </td>
                        <td className="px-4 py-3">{item.usuario}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginación */}
              <div className="flex items-center justify-between mt-4">
                <button
                  onClick={() => setHistoryPage(p => Math.max(1, p - 1))}
                  disabled={historyPage === 1}
                  className="px-4 py-2 bg-slate-200 rounded hover:bg-slate-300 disabled:opacity-50 text-sm"
                >
                  Anterior
                </button>
                <span className="text-sm text-slate-600">
                  Página {historyPage} de {totalPages}
                </span>
                <button
                  onClick={() => setHistoryPage(p => Math.min(totalPages, p + 1))}
                  disabled={historyPage === totalPages}
                  className="px-4 py-2 bg-slate-200 rounded hover:bg-slate-300 disabled:opacity-50 text-sm"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Carga de datos (HU001–HU002) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileUp className="w-5 h-5 text-blue-600" />
            Carga de Datos
          </h2>
          <div className="flex flex-wrap items-center gap-3">
            <label className="cursor-pointer bg-blue-600 text-white px-5 py-3 rounded-lg flex items-center gap-2 hover:bg-blue-700">
              <FileText className="w-5 h-5" /><span>Seleccionar CSV</span>
              <input ref={fileRef} type="file" accept=".csv" className="hidden"
                     onChange={(e)=> e.target.files?.[0] && cargarCSV(e.target.files[0]) } />
            </label>
            {/* <button onClick={cargarMuestra} className="bg-slate-800 text-white px-5 py-3 rounded-lg hover:bg-slate-900 flex items-center gap-2">
              <PlayCircle className="w-5 h-5" />
              Cargar muestra demo
            </button> */}
            <button onClick={exportar} className="bg-emerald-600 text-white px-5 py-3 rounded-lg hover:bg-emerald-700 flex items-center gap-2">
              <Download className="w-4 h-4" /> Exportar CSV
            </button>
            {/* HU018: Reporte PDF */}
            <button 
              onClick={generarReportePDF} 
              className="bg-red-600 text-white px-5 py-3 rounded-lg hover:bg-red-700 flex items-center gap-2"
              disabled={raw.length === 0}
            >
              <FileDown className="w-4 h-4" /> Reporte PDF
            </button>
            {loading && <Loader text="Procesando datos..." />}
            {err && <span className="text-red-600 font-medium">{err}</span>}
          </div>
        </div>

        {/* Filtros (HU007) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5 text-slate-600" />
            Filtros de Segmentación
          </h2>
          <div className="grid gap-3 md:grid-cols-4">
            <select value={filtros.tienda} onChange={(e)=>setFiltros(f=>({...f, tienda:e.target.value}))}
              className="border border-gray-300 px-3 py-2 rounded-lg text-sm">
              <option value="">Todas las tiendas</option>
              {tiendas.map(t=><option key={t} value={t}>{t}</option>)}
            </select>
            <select value={filtros.categoria} onChange={(e)=>setFiltros(f=>({...f, categoria:e.target.value}))}
              className="border border-gray-300 px-3 py-2 rounded-lg text-sm">
              <option value="">Todas las categorías</option>
              {categorias.map(t=><option key={t} value={t}>{t}</option>)}
            </select>
            <select value={filtros.campaña} onChange={(e)=>setFiltros(f=>({...f, campaña:e.target.value}))}
              className="border border-gray-300 px-3 py-2 rounded-lg text-sm">
              <option value="">Todas las campañas</option>
              {campañas.map(t=><option key={t} value={t}>{t}</option>)}
            </select>
            <input value={filtros.q} onChange={(e)=>setFiltros(f=>({...f, q:e.target.value}))}
              placeholder="Buscar SKU…" className="border border-gray-300 px-3 py-2 rounded-lg text-sm" />
          </div>
          {Object.values(filtros).some(v => v) && (
            <button
              onClick={() => setFiltros({ tienda:"", categoria:"", campaña:"", q:"" })}
              className="mt-3 px-4 py-2 bg-slate-200 rounded text-sm hover:bg-slate-300"
            >
              Limpiar filtros
            </button>
          )}
        </div>

        {/* Distribución por estado (HU010) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-lg font-semibold mb-3">📊 Distribución por Estado</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={datosGrafico}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="estado" /><YAxis /><Tooltip />
                <Bar dataKey="count" radius={[4,4,0,0]}>
                  {datosGrafico.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* HU013: Alertas visuales (integrado en tabla) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h2 className="text-lg font-semibold">Sistema de Alertas Inteligentes</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-lg border-l-4 border-emerald-600">
              <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              <div>
                <p className="font-semibold text-emerald-800">Stock Óptimo</p>
                <p className="text-sm text-emerald-700">Stock entre 70%-130% de lo recomendado</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-amber-50 rounded-lg border-l-4 border-amber-600">
              <AlertTriangle className="w-8 h-8 text-amber-600" />
              <div>
                <p className="font-semibold text-amber-800">Quiebre Potencial</p>
                <p className="text-sm text-amber-700">Stock menor al 70% recomendado</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg border-l-4 border-red-600">
              <TrendingUp className="w-8 h-8 text-red-600" />
              <div>
                <p className="font-semibold text-red-800">Sobre-stock</p>
                <p className="text-sm text-red-700">Stock mayor al 130% recomendado</p>
              </div>
            </div>
          </div>
        </div>

        {/* Validación con ventas reales (HU012) */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-lg font-semibold mb-3">✅ Validación contra ventas reales</h2>
          <p className="text-xs text-slate-500 mb-3">
            Formato sugerido: columnas <b>sku</b>/<b>CodArticulo</b> y <b>ventas</b>/<b>real</b>/<b>unidades</b>.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <label className="cursor-pointer bg-slate-700 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-slate-800">
              <FileUp className="w-4 h-4" />
              <span>Seleccionar CSV real</span>
              <input type="file" accept=".csv" onChange={(e)=>setValCsv(e.target.files?.[0]||null)} className="hidden" />
            </label>
            <button
              onClick={ejecutarValidacion}
              disabled={!valCsv || raw.length===0 || loading}
              className="bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 disabled:opacity-50"
            >
              Comparar (MAE/MAPE)
            </button>
            {valCsv && <span className="text-sm text-slate-600">Archivo: {valCsv.name}</span>}
          </div>

          {valRes && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-xs text-slate-600">MAE</p>
                <p className="text-2xl font-bold">{valRes.mae ?? "-"}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-xs text-slate-600">MAPE (%)</p>
                <p className="text-2xl font-bold">{valRes.mape ?? "-"}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-xs text-slate-600">Registros validados</p>
                <p className="text-2xl font-bold">{valRes.match_count ?? "-"}</p>
              </div>
            </div>
          )}
        </div>

        {/* Detalle + recomendaciones (HU004–HU006) */}
        {datos.length === 0 ? (
          <EmptyState title="Sin resultados" subtitle="Carga una muestra o un CSV para visualizar el detalle." />
        ) : (
          <TablaPrediccion data={adaptarPreds(datos)} />
        )}
      </div>
    </div>
  );
}