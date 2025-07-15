import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  FileText,
  Download,
  BarChart3,
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

const DashboardGeneral = () => {
  const [resultados, setResultados] = useState(null);

  useEffect(() => {
    const datosGuardados = localStorage.getItem("predicciones");
    if (datosGuardados) {
      setResultados(JSON.parse(datosGuardados));
    }
  }, []);

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

  const topCriticos = resultados
    ? [...resultados.predictions]
        .filter((p) => p.Estado !== "OK")
        .sort((a, b) => Math.abs(b.Diferencia) - Math.abs(a.Diferencia))
        .slice(0, 5)
    : [];

  const descargarResumen = () => {
    if (!resultados?.predictions?.length) return;

    const csv = [
      "Producto,Estado,Diferencia,Stock_Actual,Stock_Recomendado",
      ...resultados.predictions.map((row) =>
        [
          row.Producto,
          row.Estado,
          row.Diferencia,
          row.Stock_Actual,
          row.Stock_Recomendado,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resumen_dashboard.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-5xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">
          📊 Dashboard General de Stock
        </h1>

        {!resultados ? (
          <div className="text-center text-gray-600 text-lg">
            No hay datos disponibles. Ve a la sección de predicción primero.
          </div>
        ) : (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(resultados.summary).map(([estado, count]) => (
                <div
                  key={estado}
                  className="bg-white p-6 rounded-xl shadow flex justify-between items-center"
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

            {/* Gráfico */}
            <div className="bg-white p-6 rounded-xl shadow">
              <h2 className="text-lg font-semibold mb-4">
                📈 Distribución de Estados
              </h2>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={datosGrafico}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="estado" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count">
                      {datosGrafico.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Productos Críticos */}
            <div className="bg-white p-6 rounded-xl shadow">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">
                  📌 Top 5 Productos Críticos
                </h2>
                <button
                  onClick={descargarResumen}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Descargar CSV</span>
                </button>
              </div>
              <ul className="list-disc ml-6 space-y-1 text-sm text-gray-700">
                {topCriticos.map((p, i) => (
                  <li key={i}>
                    <strong>{p.Producto}</strong> — {p.Estado} — Diferencia:{" "}
                    {p.Diferencia}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DashboardGeneral;
