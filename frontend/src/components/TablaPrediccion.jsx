import React, { useState } from "react";
import { AlertTriangle, CheckCircle, AlertCircle, Download } from "lucide-react";

const TablaPrediccion = ({ data }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedRow, setExpandedRow] = useState(null);

  const filteredData = (data || []).filter((item) => {
    const matchesStatus = filterStatus === "all" || item.Estado === filterStatus;
    const matchesSearch = (item.Producto || String(item.CodArticulo || "")).toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const currentItems = filteredData.slice(indexOfLastItem - itemsPerPage, indexOfLastItem);
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);

  const getStatusIcon = (estado) =>
    estado === "OK" ? <CheckCircle className="text-green-500 w-4 h-4 mr-1" /> :
    estado === "Quiebre Potencial" ? <AlertTriangle className="text-amber-500 w-4 h-4 mr-1" /> :
    <AlertCircle className="text-red-500 w-4 h-4 mr-1" />;

  const getStatusColor = (estado) =>
    estado === "OK" ? "text-green-700 bg-green-100" :
    estado === "Quiebre Potencial" ? "text-amber-700 bg-amber-100" :
    "text-red-700 bg-red-100";

  const descargarCSV = () => {
    if (!filteredData.length) return;
    const headers = Object.keys(filteredData[0]);
    const csv = [
      headers.join(","),
      ...filteredData.map(row => headers.map(h => `"${row[h] ?? ""}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "predicciones.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h2 className="text-xl font-bold text-gray-800">📋 Resultados Detallados</h2>
        <div className="flex gap-2">
          <input
            type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar producto/SKU..." className="border border-gray-300 px-3 py-2 rounded-lg text-sm"
          />
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="border border-gray-300 px-3 py-2 rounded-lg text-sm">
            <option value="all">Todos</option>
            <option value="OK">OK</option>
            <option value="Quiebre Potencial">Quiebre Potencial</option>
            <option value="Sobre-stock">Sobre-stock</option>
          </select>
          <button onClick={descargarCSV} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center text-sm">
            <Download className="w-4 h-4 mr-1" /> Descargar CSV
          </button>
        </div>
      </div>

      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {["Producto/SKU", "Estado", "Stock Actual", "Recomendado", "Acción"].map((h) => (
              <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {currentItems.map((item, idx) => {
            const i = (currentPage - 1) * itemsPerPage + idx;
            const producto = item.Producto || item.CodArticulo || "N/A";
            return (
              <React.Fragment key={i}>
                <tr onClick={() => setExpandedRow(expandedRow === i ? null : i)} className="cursor-pointer hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{producto}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${getStatusColor(item.Estado)}`}>
                      {getStatusIcon(item.Estado)} {item.Estado}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">{Number(item.Stock_Actual ?? item.StockMes ?? 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">{Number(item.Stock_Recomendado ?? item.stock_objetivo ?? 0).toFixed(2)}</td>
                  <td className="px-6 py-4 text-sm">
                    {item.Estado === "Quiebre Potencial" ? (
                      <span className="text-red-600 font-semibold">Comprar urgente</span>
                    ) : item.Estado === "Sobre-stock" ? (
                      <span className="text-amber-600 font-semibold">Promocionar</span>
                    ) : <span className="text-green-600">Sin acción</span>}
                  </td>
                </tr>
                {expandedRow === i && (
                  <tr className="bg-gray-50">
                    <td colSpan={5} className="px-6 py-4 text-sm text-gray-700">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div><strong>Demanda Diaria:</strong> {item.Demanda_Diaria_Promedio ?? "-"}</div>
                        <div><strong>Días Cobertura:</strong> {item.Dias_Estimados ?? "-"}</div>
                        <div><strong>Diferencia:</strong> {item.Diferencia ?? "-"}</div>
                        <div><strong>% Desviación:</strong> {item.Porcentaje_Desviacion ?? "-"}%</div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex justify-center gap-1 w-max mx-auto px-2 mt-6">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(n => (
            <button key={n} onClick={() => setCurrentPage(n)}
              className={`px-3 py-1 rounded-lg text-sm min-w-[36px] ${n === currentPage ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800 hover:bg-gray-200"}`}>
              {n}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
export default TablaPrediccion;
