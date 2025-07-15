import React, { useState } from "react";
import axios from "axios";
import TablaPrediccion from "../components/TablaPrediccion";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

const EntrenamientoModelo = () => {
  const [archivo, setArchivo] = useState(null);
  const [mae, setMae] = useState(null);
  const [plotData, setPlotData] = useState([]);
  const [importancia, setImportancia] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!archivo) return;
    const formData = new FormData();
    formData.append("file", archivo);

    try {
      setLoading(true);
      const res = await axios.post(
        "http://localhost:8000/api/train-model",
        formData
      );
      setMae(res.data.mae);
      setPlotData(res.data.plot_data || []);
      setImportancia(res.data.importancia);
      setAlertas(res.data.alerta);
    } catch (error) {
      console.error("Error al entrenar modelo:", error);
    } finally {
      setLoading(false);
    }
  };

  const alertasAdaptadas = alertas.map((a) => ({
    Producto: a.CodArticulo || "N/A",
    Estado: a.Estado,
    Stock_Actual: a.StockMes ?? a.Stock_Actual ?? 0,
    Stock_Recomendado: a.stock_objetivo ?? a.Stock_Recomendado ?? 0,
    Tipo: "SKU",
    Ventas_Totales: 0,
    Demanda_Diaria_Promedio: 0,
    Dias_Estimados: 0,
    Diferencia: 0,
    Porcentaje_Desviacion: 0,
  }));

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        🧠 Entrenamiento del Modelo
      </h1>

      <div className="mb-4">
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setArchivo(e.target.files[0])}
        />
        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-4 py-2 rounded ml-2"
        >
          Entrenar
        </button>
      </div>

      {loading && <p>Entrenando modelo...</p>}

      {mae !== null && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800">
            📉 MAE del Modelo
          </h2>
          <p className="text-3xl font-bold text-blue-700">{mae}</p>
        </div>
      )}

      {plotData.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            📈 Comparación de Demanda Real vs. Predicha
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={plotData}>
              <XAxis dataKey="Fechaventa" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="real" fill="#10b981" name="Real" />
              <Bar dataKey="predicho" fill="#3b82f6" name="Predicho" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {importancia.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            📊 Importancia de Variables
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={importancia.slice(0, 10)}>
              <XAxis dataKey="feature" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="gain" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {alertas.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mt-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            📋 Alertas Generadas
          </h2>
          <button
            onClick={() => {
              const csv = [
                "CodArticulo,Estado,StockMes,StockObjetivo",
                ...alertas.map(
                  (row) =>
                    `${row.CodArticulo || row.Producto},${row.Estado},${
                      row.StockMes || row.Stock_Actual
                    },${row.stock_objetivo || row.Stock_Recomendado}`
                ),
              ].join("\n");

              const blob = new Blob([csv], { type: "text/csv" });
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "alertas_stock_entrenamiento.csv";
              a.click();
              window.URL.revokeObjectURL(url);
            }}
            className="bg-green-600 text-white px-4 py-2 rounded mt-2"
          >
            📥 Descargar Alertas CSV
          </button>

          <TablaPrediccion data={alertasAdaptadas} />
        </div>
      )}
    </div>
  );
};

export default EntrenamientoModelo;
