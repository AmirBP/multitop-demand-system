import React, { useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { Brain, FileUp } from "lucide-react";
import TablaPrediccion from "../components/TablaPrediccion";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import { api } from "../utils/api";

const EntrenamientoModelo = () => {
  const [archivo, setArchivo] = useState(null);
  const [mae, setMae] = useState(null);
  const [plotData, setPlotData] = useState([]);
  const [importancia, setImportancia] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async () => {
    if (!archivo) return;
    const formData = new FormData();
    formData.append("file", archivo);

    try {
      setLoading(true); setError(null);
      const { data } = await api.post("/api/model/train", formData, { headers: {"Content-Type":"multipart/form-data"}});
      setMae(data.mae);
      setPlotData(data.plot_data || []);
      setImportancia(data.importancia || []);
      setAlertas(data.alerta || []);
      // guardar para que el profe vea outputs también en predicción
      localStorage.setItem("last_train_mae", String(data.mae));
    } catch (e) {
      setError("No se pudo entrenar el modelo. Revisa el CSV.");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const alertasAdaptadas = alertas.map((a) => ({
    Producto: a.CodArticulo || "N/A",
    Estado: a.Estado,
    Stock_Actual: a.StockMes ?? 0,
    Stock_Recomendado: a.stock_objetivo ?? 0,
    Demanda_Diaria_Promedio: 0,
    Dias_Estimados: 0,
    Diferencia: ((a.StockMes ?? 0) - (a.stock_objetivo ?? 0)).toFixed(2),
    Porcentaje_Desviacion: ((a.porcentaje_sobrestock ?? 0) * 100).toFixed(2),
  }));

  return (
    <div className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="text-pink-600" />
        <h1 className="text-2xl font-bold text-gray-900">Entrenamiento del Modelo</h1>
      </div>

      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-700">
            <FileUp className="w-4 h-4" /><span>Seleccionar CSV</span>
            <input type="file" accept=".csv" onChange={(e)=>setArchivo(e.target.files[0])} className="hidden" />
          </label>
          <button onClick={handleUpload} disabled={!archivo || loading}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50">
            {loading ? "Entrenando..." : "Entrenar"}
          </button>
          {archivo && <span className="text-sm text-slate-600">Archivo: {archivo.name}</span>}
          {loading && <Loader text="Entrenando modelo y generando artefactos..." />}
          {error && <span className="text-red-600 font-medium">{error}</span>}
        </div>
      </div>

      {mae === null ? (
        <EmptyState
          title="Aún no has entrenado el modelo"
          subtitle="Sube un CSV con histórico de ventas para iniciar el entrenamiento."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-white rounded-xl shadow p-6">
              <p className="text-sm text-slate-600">MAE del modelo</p>
              <p className="text-4xl font-bold text-blue-700">{mae}</p>
              <p className="text-xs text-slate-500 mt-1">Guardado en outputs/modelo_xgb_sku_global.joblib</p>
            </div>
            <div className="bg-white rounded-xl shadow p-6 md:col-span-2">
              <p className="font-semibold text-slate-800 mb-2">📈 Real vs Predicho (agregado)</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={plotData}>
                  <XAxis dataKey="Fechaventa" /><YAxis /><Tooltip />
                  <Bar dataKey="real" fill="#10b981" name="Real" />
                  <Bar dataKey="predicho" fill="#3b82f6" name="Predicho" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {importancia.length > 0 && (
            <div className="bg-white rounded-xl shadow p-6 mb-6">
              <p className="font-semibold text-slate-800 mb-2">📊 Top 10 Importancia de Variables</p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={importancia.slice(0, 10)}>
                  <XAxis dataKey="feature" /><YAxis /><Tooltip />
                  <Bar dataKey="gain" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {alertas.length > 0 && (
            <div className="bg-white rounded-xl shadow p-6">
              <p className="font-semibold text-slate-800 mb-4">🔔 Alertas derivadas del entrenamiento</p>
              <TablaPrediccion data={alertasAdaptadas} />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EntrenamientoModelo;