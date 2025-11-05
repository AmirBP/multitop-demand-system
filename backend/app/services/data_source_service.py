"""
Servicio de Carga de Datos desde CSV o Base de Datos
"""
import pandas as pd
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataSourceService:
    """Servicio para cargar datos desde diferentes fuentes"""
    
    @staticmethod
    def load_from_csv(file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """Carga datos desde CSV"""
        logger.info(f"📁 Cargando desde CSV: {file_path}")
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            metadata = {
                "source_type": "CSV",
                "source_name": Path(file_path).name,
                "loaded_at": datetime.utcnow().isoformat(),
                "total_rows": len(df),
                "columns": list(df.columns)
            }
            
            logger.info(f"✅ CSV cargado: {len(df)} filas")
            return df, metadata
        
        except Exception as e:
            logger.error(f"❌ Error cargando CSV: {e}")
            raise
    
    @staticmethod
    def load_from_database(
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        tienda: Optional[str] = None,
        categoria: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Carga datos desde BD de MultiTop
        
        NOTA: Requiere configurar MULTITOP_DATABASE_URL en .env
        """
        from app.database import get_multitop_source_db
        
        logger.info("🏢 Cargando desde BD de MultiTop...")
        
        db = get_multitop_source_db()
        if db is None:
            raise ValueError(
                "MULTITOP_DATABASE_URL no configurada. "
                "Configure en .env para habilitar carga desde BD."
            )
        
        # Query ajustable según esquema real de MultiTop
        query = """
            SELECT 
                v.FechaVenta as Fechaventa,
                a.CodigoArticulo as CodArticulo,
                a.Temporada,
                v.PrecioUnitario as PrecioVenta,
                v.Cantidad as CantidadVendida,
                s.StockActual as StockMes,
                p.TiempoReposicion as TiempoReposicionDias,
                CASE WHEN pr.IdPromocion IS NOT NULL THEN 1 ELSE 0 END as Promocion,
                CASE WHEN f.EsFestivo = 1 THEN 1 ELSE 0 END as DiaFestivo,
                CASE WHEN DATEPART(WEEKDAY, v.FechaVenta) = 1 THEN 1 ELSE 0 END as EsDomingo,
                CASE WHEN h.HorarioCerrado = 1 THEN 1 ELSE 0 END as TiendaCerrada
            FROM Ventas v
            INNER JOIN Articulos a ON v.IdArticulo = a.IdArticulo
            LEFT JOIN Stock s ON a.IdArticulo = s.IdArticulo
            LEFT JOIN Proveedores p ON a.IdProveedor = p.IdProveedor
            LEFT JOIN Promociones pr ON v.IdVenta = pr.IdVenta
            LEFT JOIN Festivos f ON CAST(v.FechaVenta AS DATE) = f.Fecha
            LEFT JOIN Horarios h ON v.IdTienda = h.IdTienda
            WHERE 1=1
        """
        
        params = []
        if fecha_desde:
            query += " AND v.FechaVenta >= ?"
            params.append(fecha_desde)
        if fecha_hasta:
            query += " AND v.FechaVenta <= ?"
            params.append(fecha_hasta)
        if tienda:
            query += " AND v.IdTienda = ?"
            params.append(tienda)
        if categoria:
            query += " AND a.Categoria = ?"
            params.append(categoria)
        
        query += " ORDER BY v.FechaVenta DESC"
        
        try:
            results = db.execute_query(query, tuple(params) if params else None)
            df = pd.DataFrame(results)
            
            metadata = {
                "source_type": "DATABASE",
                "source_name": "MultitopDB",
                "loaded_at": datetime.utcnow().isoformat(),
                "total_rows": len(df),
                "filters": {
                    "fecha_desde": fecha_desde,
                    "fecha_hasta": fecha_hasta,
                    "tienda": tienda,
                    "categoria": categoria
                }
            }
            
            logger.info(f"✅ BD cargada: {len(df)} filas")
            return df, metadata
        
        except Exception as e:
            logger.error(f"❌ Error cargando desde BD: {e}")
            raise
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> pd.DataFrame:
        """Valida y prepara datos"""
        required_cols = [
            "Fechaventa", "CodArticulo", "Temporada", "PrecioVenta",
            "CantidadVendida", "StockMes", "TiempoReposicionDias",
            "Promocion", "DiaFestivo", "EsDomingo", "TiendaCerrada"
        ]
        
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Columnas faltantes: {missing}")
        
        # Limpiar tipos
        df["Fechaventa"] = pd.to_datetime(df["Fechaventa"], errors="coerce")
        df["CodArticulo"] = df["CodArticulo"].astype(str)
        df["PrecioVenta"] = pd.to_numeric(df["PrecioVenta"], errors="coerce")
        df["CantidadVendida"] = pd.to_numeric(df["CantidadVendida"], errors="coerce")
        df["StockMes"] = pd.to_numeric(df["StockMes"], errors="coerce")
        
        # Eliminar nulos críticos
        df = df.dropna(subset=["Fechaventa", "CodArticulo", "CantidadVendida"])
        
        logger.info(f"✅ Datos validados: {len(df)} filas")
        return df