import React, { useEffect, useMemo, useState } from "react";
import { CheckCircle, AlertTriangle, AlertCircle, Download, FileUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import TablaPrediccion from "../components/TablaPrediccion";
import { api, getJson } from "../utils/api";
import { fileToBase64 } from "../utils/files";

const ESTADOS = ["OK", "Quiebre Potencial", "Sobre-stock"];

const icono = (estado) =>
  estado === "OK" ? <CheckCircle className="text-green-600 w-5 h-5" /> :
  estado === "Quiebre Potencial" ? <AlertTriangle className="text-amber-500 w-5 h-5" /> :
  <AlertCircle className="text-red-500 w-5 h-5" />;

const adaptarPreds = (arr=[]) =>
  arr.map((item) => ({
    Producto: item.CodArticulo ?? "N/A",
    Estado: item.Estado ?? "Sin Estado",
    Stock_Actual: item.StockMes ?? 0,
    Stock_Recomendado: item.stock_objetivo ?? 0,
    Demanda_Diaria_Promedio: item.d_media ?? 0,
    Dias_Estimados: item.dias_cobertura ?? 0,
    Diferencia: ((item.StockMes ?? 0) - (item.stock_objetivo ?? 0)).toFixed(2),
    Porcentaje_Desviacion: ((item.porcentaje_sobrestock ?? 0) * 100).toFixed(2),
    Tipo: "SKU",
  }));

export default function DashboardGeneral() {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [jobId, setJobId] = useState(localStorage.getItem("last_job_id") || "");
  const [jobDetail, setJobDetail] = useState(null);
  const [estadoActivo, setEstadoActivo] = useState("Todos");
  const [csvReal, setCsvReal] = useState(null);
  const [valMetrics, setValMetrics] = useState(null); // mae/mape de validación
  const ultimoMae = localStorage.getItem("last_train_mae");

  // Carga inicial: resumen y listado de jobs
  useEffect(() => {
    (async () => {
      const sum = await getJson("/api/predictions/summary");
      setSummary(sum);
      const jobs = await getJson("/api/predictions/history");
      setHistory(jobs);
      if (!jobId && jobs?.length) setJobId(jobs[0].job_id);
    })().catch(console.error);
  }, []);

  // Cargar detalle del job seleccionado
  useEffect(() => {
    if (!jobId) return;
    (async () => {
      const det = await getJson(`/api/predictions/${jobId}`);
      setJobDetail(det);
      setValMetrics(null); // resetea métricas al cambiar de job
    })().catch(console.error);
  }, [jobId]);

  // Datos para gráfico de barras (resumen global)
  const datosGrafico = summary
    ? Object.entries(summary.estados || {}).map(([estado, count]) => ({
        estado,
        count,
        color: estado === "OK" ? "#10b981" : estado === "Quiebre Potencial" ? "#f59e0b" : "#ef4444",
      }))
    : [];

  // Filtro por estado en el detalle del job
  const predsAdaptadas = useMemo(() => {
    const base = adaptarPreds(jobDetail?.predictions || []);
    if (estadoActivo === "Todos") return base;
    return base.filter((p) => p.Estado === estadoActivo);
  }, [jobDetail, estadoActivo]);

  const descargarResumenJob = () => {
    if (!jobDetail?.predictions?.length) return;
    const csv = [
      "CodArticulo,Estado,Stock,StockObjetivo,Diferencia",
      ...jobDetail.predictions.map(r => [
        r.CodArticulo, r.Estado, r.StockMes ?? 0, r.stock_objetivo ?? 0, (Number(r.StockMes ?? 0) - Number(r.stock_objetivo ?? 0)).toFixed(2)
      ].join(","))
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `resumen_${jobDetail.job_id}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  const validarConVentasReales = async () => {
    if (!csvReal || !jobId) return;
    const ventasB64 = await fileToBase64(csvReal);
    const { data } = await api.post("/api/validation/compare-real", {
      job_id: jobId,
      ventas_real_csv_base64: ventasB64,
      nivel: "SKU",
    });
    // asume { mae, mape, coincidencias, ... }
    setValMetrics(data);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">📊 Dashboard General</h1>

        {/* KPIs + Salud del modelo */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {summary && Object.entries(summary.estados).map(([estado, count]) => (
            <div key={estado} className="bg-white p-6 rounded-xl shadow flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">{estado}</p>
                <p className="text-3xl font-bold">{count}</p>
              </div>
              <div className="bg-gray-100 p-3 rounded-full">{icono(estado)}</div>
            </div>
          ))}
          <div className="bg-white p-6 rounded-xl shadow">
            <p className="text-sm text-gray-600">MAE último entrenamiento</p>
            <p className="text-3xl font-bold text-blue-700">{ultimoMae ?? "-"}</p>
            <p className="text-xs text-slate-500 mt-1">Fuente: /api/model/train</p>
          </div>
        </div>

        {/* Gráfico global */}
        {summary && (
          <div className="bg-white p-6 rounded-xl shadow">
            <h2 className="text-lg font-semibold mb-4">📈 Distribución de Estados</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={datosGrafico}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="estado" /><YAxis /><Tooltip />
                  <Bar dataKey="count">
                    {datosGrafico.map((e,i) => <Cell key={i} fill={e.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Historico + selector de job */}
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
            <div>
              <h2 className="text-lg font-semibold">📌 Job seleccionado</h2>
              <p className="text-xs text-slate-500">
                Cambia de ejecución para navegar por el histórico.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={jobId}
                onChange={(e) => setJobId(e.target.value)}
                className="border border-gray-300 px-3 py-2 rounded-lg text-sm"
              >
                {history.map((j) => (
                  <option key={j.job_id} value={j.job_id}>
                    {new Date(j.created_at).toLocaleString()} — {j.job_id}
                  </option>
                ))}
              </select>
              <button onClick={descargarResumenJob} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center gap-2">
                <Download className="w-4 h-4" /> Descargar CSV
              </button>
            </div>
          </div>

          {jobDetail && (
            <>
              <p className="text-sm text-slate-500 mb-3">
                Generado: {new Date(jobDetail.generated_at).toLocaleString()}
              </p>

              {/* Filtros por estado */}
              <div className="flex gap-2 mb-4">
                {["Todos", ...ESTADOS].map((e) => (
                  <button
                    key={e}
                    onClick={() => setEstadoActivo(e)}
                    className={`px-3 py-1 rounded-full text-sm border ${
                      estadoActivo === e ? "bg-slate-900 text-white" : "bg-white text-slate-700"
                    }`}
                  >
                    {e}
                  </button>
                ))}
              </div>

              {/* Tabla reutilizando el componente general */}
              <TablaPrediccion data={predsAdaptadas} />
            </>
          )}
        </div>

        {/* Validación HU012 */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h2 className="text-lg font-semibold mb-3">✅ Validar contra ventas reales (HU012)</h2>
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <label className="cursor-pointer bg-slate-700 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-slate-800">
              <FileUp className="w-4 h-4" />
              <span>Seleccionar CSV real</span>
              <input type="file" accept=".csv" onChange={(e)=>setCsvReal(e.target.files[0])} className="hidden" />
            </label>
            <button
              onClick={validarConVentasReales}
              disabled={!csvReal || !jobId}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              Comparar (MAE/MAPE)
            </button>
            {csvReal && <span className="text-sm text-slate-600">Archivo: {csvReal.name}</span>}
          </div>
          {valMetrics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-600">MAE</p>
                <p className="text-2xl font-bold">{valMetrics.mae ?? "-"}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-600">MAPE (%)</p>
                <p className="text-2xl font-bold">{valMetrics.mape ?? "-"}</p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-600">Registros validados</p>
                <p className="text-2xl font-bold">{valMetrics.match_count ?? "-"}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
