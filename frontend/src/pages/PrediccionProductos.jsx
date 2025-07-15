import React, { useState } from "react";
import {
  Upload,
  FileText,
  Download,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import TablaPrediccion from "../components/TablaPrediccion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const PrediccionProductos = () => {
  const [archivo, setArchivo] = useState(null);
  const [resultados, setResultados] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setArchivo(e.target.files[0]);
    setError(null);
  };

  const adaptarPredicciones = (data) =>
  data.map((item) => ({
    Producto: item.CodArticulo ?? "N/A",
    Estado: item.Estado ?? "Sin Estado",
    Stock_Actual: item.StockMes ?? 0,
    Stock_Recomendado: item.stock_objetivo ?? 0,
    Ventas_Totales: 0,
    Demanda_Diaria_Promedio: item.d_media ?? 0,
    Dias_Estimados: item.dias_cobertura ?? 0,
    Diferencia: ((item.StockMes ?? 0) - (item.stock_objetivo ?? 0)).toFixed(2),
    Porcentaje_Desviacion: ((item.porcentaje_sobrestock ?? 0) * 100).toFixed(2),
    Tipo: "SKU",
  }));

  const enviarArchivo = async () => {
    if (!archivo) return;
    setLoading(true);
    setResultados(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", archivo);

    try {
      const res = await fetch("http://localhost:8000/api/prediction", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Error en la predicción.");

      const data = await res.json();
      setResultados({
        summary: data.summary,
        predictions: adaptarPredicciones(data.predictions),
      });

      localStorage.setItem("predicciones", JSON.stringify(data));

    } catch (err) {
      setError("Error al procesar la predicción.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const descargarCSV = () => {
    if (!resultados?.predictions?.length) return;

    const csv = [
      Object.keys(resultados.predictions[0]).join(","),
      ...resultados.predictions.map((row) => Object.values(row).join(",")),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "predicciones.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const iconoEstado = (estado) => {
    switch (estado) {
      case "OK":
        return <CheckCircle className="text-green-600 w-5 h-5" />;
      case "Quiebre Potencial":
        return <AlertTriangle className="text-amber-500 w-5 h-5" />;
      case "Sobre-stock":
        return <AlertCircle className="text-red-500 w-5 h-5" />;
      default:
        return null;
    }
  };

  const datosGrafico = resultados
    ? Object.entries(resultados.summary).map(([estado, count]) => ({
        estado,
        count,
        color:
          estado === "OK"
            ? "#10b981"
            : estado === "Quiebre Potencial"
            ? "#f59e0b"
            : "#ef4444",
      }))
    : [];

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">
          📈 Predicción de Productos
        </h1>

        {/* Carga de archivo */}
        <div className="bg-white p-6 rounded-xl shadow mb-8">
          <div className="flex flex-col items-center space-y-4">
            <label className="cursor-pointer bg-blue-600 text-white px-5 py-3 rounded-lg flex items-center space-x-2 hover:bg-blue-700">
              <FileText className="w-5 h-5" />
              <span>Seleccionar CSV</span>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
            {archivo && (
              <div className="text-sm text-green-700 font-medium">
                Archivo: {archivo.name}
              </div>
            )}
            <button
              disabled={!archivo || loading}
              onClick={enviarArchivo}
              className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? "Procesando..." : "Generar Predicción"}
            </button>
          </div>
          {error && (
            <p className="mt-4 text-red-600 font-medium text-center">{error}</p>
          )}
        </div>

        {/* Resultados */}
        {resultados && (
          <div className="space-y-8">
            {/* Tarjetas resumen */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(resultados.summary).map(([estado, count]) => (
                <div
                  key={estado}
                  className="bg-white p-5 rounded-xl shadow flex justify-between items-center"
                >
                  <div>
                    <p className="text-sm text-gray-600">{estado}</p>
                    <p className="text-3xl font-bold">{count}</p>
                  </div>
                  <div className="bg-gray-100 p-3 rounded-full">
                    {iconoEstado(estado)}
                  </div>
                </div>
              ))}
            </div>

            {/* Gráfico de barras */}
            <div className="bg-white p-6 rounded-xl shadow">
              <h2 className="text-lg font-semibold mb-4">
                📊 Distribución por Estado
              </h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={datosGrafico}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="estado" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {datosGrafico.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Tabla de predicciones */}
            <div className="bg-white p-6 rounded-xl shadow">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">
                  📋 Resultados Detallados
                </h2>
                <button
                  onClick={descargarCSV}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 hover:bg-blue-700"
                >
                  <Download className="w-4 h-4" />
                  <span>Descargar CSV</span>
                </button>
              </div>
              <TablaPrediccion data={resultados.predictions} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PrediccionProductos;
