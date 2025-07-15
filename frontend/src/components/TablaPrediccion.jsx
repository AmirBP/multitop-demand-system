import React, { useState } from "react";
import { generarCSV } from "../utils/csv";
import {
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  Download,
} from "lucide-react";

const TablaPrediccion = ({ data }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedRow, setExpandedRow] = useState(null);

  const filteredData = data.filter((item) => {
    const matchesStatus =
      filterStatus === "all" || item.Estado === filterStatus;
    const matchesSearch = (item.Producto || "")
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredData.slice(indexOfFirstItem, indexOfLastItem);

  const totalPages = Math.ceil(filteredData.length / itemsPerPage);

  const handleDownload = () => {
    const encabezados = [
      "Producto",
      "Tipo",
      "Ventas_Totales",
      "Demanda_Diaria_Promedio",
      "Stock_Actual",
      "Stock_Recomendado",
      "Dias_Estimados",
      "Diferencia",
      "Porcentaje_Desviacion",
      "Estado",
    ];

    const csvContent = generarCSV(data, encabezados);

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "alerta_stock_global.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getStatusIcon = (estado) => {
    switch (estado) {
      case "OK":
        return <CheckCircle className="text-green-500 w-4 h-4 mr-1" />;
      case "Quiebre Potencial":
        return <AlertTriangle className="text-amber-500 w-4 h-4 mr-1" />;
      case "Sobre-stock":
        return <AlertCircle className="text-red-500 w-4 h-4 mr-1" />;
      default:
        return null;
    }
  };

  const getStatusColor = (estado) => {
    switch (estado) {
      case "OK":
        return "text-green-700 bg-green-100";
      case "Quiebre Potencial":
        return "text-amber-700 bg-amber-100";
      case "Sobre-stock":
        return "text-red-700 bg-red-100";
      default:
        return "text-gray-700 bg-gray-100";
    }
  };

  const toggleExpand = (index) => {
    setExpandedRow(expandedRow === index ? null : index);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <span role="img" aria-label="graph">
          📋
        </span>
        Resumen de Predicción de Stock
      </h2>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar producto..."
            className="border border-gray-300 px-3 py-2 rounded-lg text-sm"
          />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-300 px-3 py-2 rounded-lg text-sm"
          >
            <option value="all">Todos los estados</option>
            <option value="OK">OK</option>
            <option value="Quiebre Potencial">Quiebre Potencial</option>
            <option value="Sobre-stock">Sobre-stock</option>
          </select>
        </div>
        <button
          onClick={handleDownload}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center text-sm"
        >
          <Download className="w-4 h-4 mr-1" /> Descargar CSV
        </button>
      </div>

      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Producto
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Estado
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Stock Actual
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Recomendado
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Acción
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {currentItems.map((item, index) => {
            const globalIndex = indexOfFirstItem + index;
            return (
              <React.Fragment key={index}>
                <tr
                  onClick={() => toggleExpand(globalIndex)}
                  className="cursor-pointer hover:bg-gray-50"
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {item.Producto}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                        item.Estado
                      )}`}
                    >
                      {getStatusIcon(item.Estado)}
                      {item.Estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {Number(item.Stock_Actual).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {Number(item.Stock_Recomendado).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {item.Estado === "Quiebre Potencial" && (
                      <span className="text-red-600 font-semibold">
                        Comprar urgente
                      </span>
                    )}
                    {item.Estado === "Sobre-stock" && (
                      <span className="text-yellow-600 font-semibold">
                        Promocionar
                      </span>
                    )}
                    {item.Estado === "OK" && (
                      <span className="text-green-600">Sin acción</span>
                    )}
                  </td>
                </tr>
                {expandedRow === globalIndex && (
                  <tr className="bg-gray-50">
                    <td colSpan={5} className="px-6 py-4 text-sm text-gray-700">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <strong>Demanda Diaria:</strong>{" "}
                          {item.Demanda_Diaria_Promedio}
                        </div>
                        <div>
                          <strong>Ventas Totales:</strong> {item.Ventas_Totales}
                        </div>
                        <div>
                          <strong>Días Estimados:</strong> {item.Dias_Estimados}
                        </div>
                        <div>
                          <strong>Desviación:</strong>{" "}
                          {item.Porcentaje_Desviacion}%
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>

      <div className="overflow-x-auto max-w-full mt-6">
        <div className="flex justify-center gap-1 w-max mx-auto px-2">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((number) => (
            <button
              key={number}
              onClick={() => setCurrentPage(number)}
              className={`px-3 py-1 rounded-lg text-sm min-w-[36px] ${
                number === currentPage
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-800 hover:bg-gray-200"
              }`}
            >
              {number}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TablaPrediccion;
