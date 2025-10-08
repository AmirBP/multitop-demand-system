import React, { useState } from "react";
import { FileText, Download, AlertCircle, AlertTriangle, CheckCircle } from "lucide-react";
import TablaPrediccion from "../components/TablaPrediccion";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { api, API_URL } from "../utils/api";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

const PrediccionProductos = () => {
  const [archivo, setArchivo] = useState(null);
  const [resultados, setResultados] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const adaptarPredicciones = (arr) =>
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

  const enviarArchivo = async () => {
    if (!archivo) return;
    const formData = new FormData();
    formData.append("file", archivo);

    try {
      setLoading(true); setError(null);
      const { data } = await api.post("/api/predictions/run", formData, { headers: { "Content-Type": "multipart/form-data" }});
      const adapted = adaptarPredicciones(data.predictions || []);
      const payload = { job_id: data.job_id, summary: data.summary, predictions: adapted };
      setResultados(payload);
      localStorage.setItem("last_job_id", data.job_id);
      localStorage.setItem("predicciones", JSON.stringify(payload));
    } catch (err) {
      setError(err?.response?.data?.detail || "Error al procesar la predicción.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportarDesdeAPI = () => {
    const jobId = localStorage.getItem("last_job_id");
    if (!jobId) return;
    window.open(`${API_URL}/api/predictions/export?job_id=${jobId}`, "_blank");
  };

  const datosGrafico = resultados
    ? Object.entries(resultados.summary).map(([estado, count]) => ({
        estado,
        count,
        color: estado === "OK" ? "#10b981" : estado === "Quiebre Potencial" ? "#f59e0b" : "#ef4444",
      }))
    : [];

  const iconoEstado = (estado) =>
    estado === "OK" ? <CheckCircle className="text-green-600 w-5 h-5" /> :
    estado === "Quiebre Potencial" ? <AlertTriangle className="text-amber-500 w-5 h-5" /> :
    <AlertCircle className="text-red-500 w-5 h-5" />;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">📈 Predicción de Productos</h1>

        <div className="bg-white p-6 rounded-xl shadow mb-8">
          <div className="flex flex-wrap items-center gap-3">
            <label className="cursor-pointer bg-blue-600 text-white px-5 py-3 rounded-lg flex items-center gap-2 hover:bg-blue-700">
              <FileText className="w-5 h-5" /><span>Seleccionar CSV</span>
              <input type="file" accept=".csv" onChange={(e)=>setArchivo(e.target.files[0])} className="hidden" />
            </label>
            <button disabled={!archivo || loading} onClick={enviarArchivo} className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50">
              {loading ? "Procesando..." : "Generar Predicción"}
            </button>
            {archivo && <span className="text-sm text-slate-600">Archivo: {archivo.name}</span>}
            {loading && <Loader text="Calculando demandas y generando alertas..." />}
          </div>
          {error && <p className="mt-3 text-red-600 font-medium">{error}</p>}
        </div>

        {!resultados ? (
          <EmptyState
            title="Aún no hay predicciones"
            subtitle="Carga un CSV para ver el resumen, gráficos y el detalle por SKU."
          />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              {Object.entries(resultados.summary).map(([estado, count]) => (
                <div key={estado} className="bg-white p-5 rounded-xl shadow flex justify-between items-center">
                  <div>
                    <p className="text-sm text-gray-600">{estado}</p>
                    <p className="text-3xl font-bold">{count}</p>
                  </div>
                  <div className="bg-gray-100 p-3 rounded-full">{iconoEstado(estado)}</div>
                </div>
              ))}
            </div>

            <div className="bg-white p-6 rounded-xl shadow mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">📊 Distribución por Estado</h2>
                <button onClick={exportarDesdeAPI} className="bg-slate-700 text-white px-4 py-2 rounded-lg hover:bg-slate-800">
                  Exportar CSV desde API
                </button>
              </div>
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

            <TablaPrediccion data={resultados.predictions} />
          </>
        )}
      </div>
    </div>
  );
};
export default PrediccionProductos;