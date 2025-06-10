import React, { useState } from "react";
import TablaPrediccion from "../components/TablaPrediccion";
import {
  Upload,
  Download,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Package,
  FileText,
} from "lucide-react";
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

const MultiTopDemandPredictor = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });
  const [filterStatus, setFilterStatus] = useState("all");

  const handleFileUpload = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === "text/csv") {
      setFile(selectedFile);
      setError(null);
    } else {
      setError("Por favor selecciona un archivo CSV válido");
    }
  };

  const processFile = async () => {
    if (!file) {
      setError("Por favor selecciona un archivo CSV");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null); // Limpiar resultados anteriores

    try {
      console.log("Iniciando procesamiento del archivo:", file.name);

      const formData = new FormData();
      formData.append("file", file);

      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
      console.log("API URL:", API_URL);

      const response = await fetch(`${API_URL}/api/prediction`, {
        method: "POST",
        body: formData,
      });

      console.log("RESPONSE STATUS:", response.status);
      console.log("RESPONSE HEADERS:", response.headers);

      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage =
            errorData.detail || errorData.message || `Error ${response.status}`;
        } catch {
          const errorText = await response.text();
          errorMessage =
            errorText || `Error ${response.status}: ${response.statusText}`;
        }
        console.error("BACKEND ERROR:", errorMessage);
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("API DATA:", data);

      // Validación más robusta
      if (!data) {
        throw new Error("Respuesta vacía del servidor");
      }

      if (!data.predictions || !Array.isArray(data.predictions)) {
        throw new Error("Formato de predicciones inválido");
      }

      if (!data.summary || typeof data.summary !== "object") {
        throw new Error("Formato de resumen inválido");
      }

      if (data.predictions.length === 0) {
        throw new Error(
          "No se generaron predicciones. Verifica el formato de tu archivo CSV."
        );
      }

      console.log(`Predicciones recibidas: ${data.predictions.length}`);
      console.log("Resumen:", data.summary);

      setResults(data);
    } catch (err) {
      console.error("FRONTEND ERROR:", err);
      setError(`Error al procesar el archivo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadResults = () => {
    if (!results) return;

    const csvContent = [
      "Producto,Tipo,Ventas_Totales,Demanda_Diaria_Promedio,Stock_Actual,Stock_Recomendado,Dias_Estimados,Diferencia,Porcentaje_Desviacion,Estado",
      ...results.predictions.map(
        (row) =>
          `${row.Producto},${row.Tipo},${row["Ventas_Totales"]},${row["Demanda_Diaria_Promedio"]},${row["Stock_Actual"]},${row["Stock_Recomendado"]},${row["Dias_Estimados"]},${row["Diferencia"]},${row["Porcentaje_Desviacion"]},${row.Estado}`
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "alerta_stock_global.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "OK":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "Quiebre Potencial":
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case "Sobre-stock":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "OK":
        return "bg-green-100 text-green-800";
      case "Quiebre Potencial":
        return "bg-amber-100 text-amber-800";
      case "Sobre-stock":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const sortedData = results
    ? [...results.predictions].sort((a, b) => {
        if (!sortConfig.key) return 0;

        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
        return 0;
      })
    : [];

  const [searchQuery, setSearchQuery] = useState("");

  const searchFilteredData = sortedData.filter((item) => {
    const matchesStatus =
      filterStatus === "all" || item.Estado === filterStatus;
    const matchesQuery =
      typeof item.Producto === "string" &&
      item.Producto.toLowerCase().includes(searchQuery.trim().toLowerCase());
    return matchesStatus && matchesQuery;
  });

  const chartData = results
    ? Object.entries(results.summary).map(([status, count]) => ({
        status,
        count,
        color:
          status === "OK"
            ? "#10b981"
            : status === "Quiebre Potencial"
            ? "#f59e0b"
            : "#ef4444",
      }))
    : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MultiTop</h1>
                <p className="text-sm text-gray-600">
                  Sistema de Predicción de Demanda
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Versión MVP</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Upload className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Cargar Datos de Ventas
            </h2>
            <p className="text-gray-600 mb-6">
              Sube tu archivo CSV con los datos históricos de ventas
            </p>

            <div className="flex flex-col items-center space-y-4">
              <label className="relative cursor-pointer bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2">
                <FileText className="w-5 h-5" />
                <span>Seleccionar Archivo CSV</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>

              {file && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">{file.name}</span>
                </div>
              )}

              <button
                onClick={processFile}
                disabled={!file || loading}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-3 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Procesando...</span>
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-5 h-5" />
                    <span>Generar Predicciones</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        {results && (
          <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(results.summary).map(([status, count]) => (
                <div key={status} className="bg-white rounded-xl shadow-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        {status}
                      </p>
                      <p className="text-3xl font-bold text-gray-900">
                        {count}
                      </p>
                    </div>
                    <div className="p-3 rounded-full bg-gray-50">
                      {getStatusIcon(status)}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Chart */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  <span role="img" aria-label="graph">
                    📊
                  </span>
                  Distribución por Estado
                </h3>
                <Package className="w-6 h-6 text-gray-400" />
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="status" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Data Table */}
            <TablaPrediccion data={searchFilteredData} />
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiTopDemandPredictor;
