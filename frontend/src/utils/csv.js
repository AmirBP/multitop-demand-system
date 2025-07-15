// src/utils/csv.js
export function generarCSV(data, encabezados) {
  return [
    encabezados.join(","),
    ...data.map((row) =>
      encabezados.map((key) => `"${row[key] ?? ""}"`).join(",")
    ),
  ].join("\n");
}
