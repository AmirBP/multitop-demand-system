"""
Servicio mejorado de validación de datos para HU002
Implementa validaciones robustas antes del procesamiento
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Columnas requeridas según especificación
REQUIRED_COLUMNS = [
    "Fechaventa", "CodArticulo", "Temporada", "PrecioVenta",
    "CantidadVendida", "StockMes", "TiempoReposicionDias",
    "Promocion", "DiaFestivo", "EsDomingo", "TiendaCerrada"
]

# Columnas numéricas y sus rangos esperados
NUMERIC_COLUMNS_RANGES = {
    "PrecioVenta": (0, 100000),  # S/ 0 - S/ 100,000
    "CantidadVendida": (0, 10000),  # 0 - 10,000 unidades
    "StockMes": (0, 50000),  # 0 - 50,000 unidades
    "TiempoReposicionDias": (1, 365),  # 1 día - 1 año
}

# Columnas binarias (0 o 1)
BINARY_COLUMNS = ["Promocion", "DiaFestivo", "EsDomingo", "TiendaCerrada"]

# Temporadas válidas
VALID_TEMPORADAS = ["Verano", "Otoño", "Invierno", "Primavera", "Todo el año"]


class ValidationError:
    """Representa un error de validación"""
    def __init__(self, type: str, column: str = None, message: str = "", 
                 severity: str = "error", rows: List[int] = None):
        self.type = type
        self.column = column
        self.message = message
        self.severity = severity  # 'error', 'warning', 'info'
        self.rows = rows or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "column": self.column,
            "message": self.message,
            "severity": self.severity,
            "affected_rows": len(self.rows),
            "sample_rows": self.rows[:5] if self.rows else []
        }


class DataFrameValidator:
    """Validador robusto de DataFrames"""
    
    def __init__(self, df: pd.DataFrame, strict_mode: bool = True):
        self.df = df
        self.strict_mode = strict_mode
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []
    
    def validate_all(self) -> tuple[List[Dict], bool]:
        """
        Ejecuta todas las validaciones
        Returns:
            (errores, es_valido)
        """
        logger.info(f"Iniciando validación de DataFrame con {len(self.df)} filas")
        
        # Validaciones estructurales
        self._validate_required_columns()
        self._validate_empty_dataframe()
        
        if self.has_errors():
            return self.get_all_issues(), False
        
        # Validaciones de contenido
        self._validate_date_column()
        self._validate_numeric_columns()
        self._validate_binary_columns()
        self._validate_categorical_columns()
        self._validate_duplicates()
        self._validate_temporal_consistency()
        self._validate_business_rules()
        
        # Análisis de calidad (warnings)
        self._check_data_quality()
        
        has_blocking_errors = len(self.errors) > 0
        
        if has_blocking_errors:
            logger.error(f"Validación fallida: {len(self.errors)} errores encontrados")
        else:
            logger.info(f"Validación exitosa. Warnings: {len(self.warnings)}")
        
        return self.get_all_issues(), not has_blocking_errors
    
    def has_errors(self) -> bool:
        """Retorna True si hay errores bloqueantes"""
        return len(self.errors) > 0
    
    def get_all_issues(self) -> List[Dict]:
        """Retorna todos los problemas encontrados"""
        all_issues = []
        all_issues.extend([e.to_dict() for e in self.errors])
        all_issues.extend([w.to_dict() for w in self.warnings])
        all_issues.extend([i.to_dict() for i in self.info])
        return all_issues
    
    def _add_error(self, type: str, message: str, column: str = None, rows: List[int] = None):
        """Agrega un error bloqueante"""
        self.errors.append(ValidationError(type, column, message, "error", rows))
    
    def _add_warning(self, type: str, message: str, column: str = None, rows: List[int] = None):
        """Agrega una advertencia no bloqueante"""
        self.warnings.append(ValidationError(type, column, message, "warning", rows))
    
    def _add_info(self, type: str, message: str, column: str = None):
        """Agrega información no crítica"""
        self.info.append(ValidationError(type, column, message, "info"))
    
    def _validate_required_columns(self):
        """Valida que existan todas las columnas requeridas"""
        missing = [col for col in REQUIRED_COLUMNS if col not in self.df.columns]
        if missing:
            self._add_error(
                "missing_columns",
                f"Faltan columnas requeridas: {', '.join(missing)}",
                column=None
            )
        
        # Columnas extra (info)
        extra = [col for col in self.df.columns if col not in REQUIRED_COLUMNS]
        if extra:
            self._add_info(
                "extra_columns",
                f"Columnas adicionales encontradas (serán ignoradas): {', '.join(extra)}"
            )
    
    def _validate_empty_dataframe(self):
        """Valida que el DataFrame no esté vacío"""
        if len(self.df) == 0:
            self._add_error("empty_dataframe", "El archivo no contiene datos")
        elif len(self.df) < 30:
            self._add_warning(
                "insufficient_data",
                f"Solo {len(self.df)} filas. Se recomienda al menos 30 para predicciones confiables"
            )
    
    def _validate_date_column(self):
        """Valida la columna de fecha"""
        if "Fechaventa" not in self.df.columns:
            return
        
        # Intentar parsear fechas
        try:
            dates = pd.to_datetime(self.df["Fechaventa"], errors="coerce", dayfirst=True)
            invalid_rows = dates.isna()
            
            if invalid_rows.any():
                invalid_count = invalid_rows.sum()
                invalid_indices = self.df[invalid_rows].index.tolist()
                self._add_error(
                    "invalid_dates",
                    f"{invalid_count} fechas inválidas encontradas",
                    column="Fechaventa",
                    rows=invalid_indices
                )
            else:
                # Validar rango de fechas
                min_date = dates.min()
                max_date = dates.max()
                today = pd.Timestamp.now()
                
                if max_date > today:
                    future_rows = self.df[dates > today].index.tolist()
                    self._add_error(
                        "future_dates",
                        f"Fechas futuras encontradas (última: {max_date.strftime('%Y-%m-%d')})",
                        column="Fechaventa",
                        rows=future_rows
                    )
                
                if min_date < pd.Timestamp("2020-01-01"):
                    self._add_warning(
                        "very_old_dates",
                        f"Fechas muy antiguas encontradas (primera: {min_date.strftime('%Y-%m-%d')})",
                        column="Fechaventa"
                    )
                
                # Info sobre rango
                self._add_info(
                    "date_range",
                    f"Rango de fechas: {min_date.strftime('%Y-%m-%d')} a {max_date.strftime('%Y-%m-%d')}"
                )
        
        except Exception as e:
            self._add_error(
                "date_parsing_error",
                f"Error al procesar fechas: {str(e)}",
                column="Fechaventa"
            )
    
    def _validate_numeric_columns(self):
        """Valida columnas numéricas y sus rangos"""
        for col, (min_val, max_val) in NUMERIC_COLUMNS_RANGES.items():
            if col not in self.df.columns:
                continue
            
            # Convertir a numérico
            numeric_series = pd.to_numeric(self.df[col], errors="coerce")
            
            # Valores no numéricos
            non_numeric = numeric_series.isna() & self.df[col].notna()
            if non_numeric.any():
                invalid_rows = self.df[non_numeric].index.tolist()
                self._add_error(
                    "non_numeric_values",
                    f"{non_numeric.sum()} valores no numéricos en columna {col}",
                    column=col,
                    rows=invalid_rows
                )
            
            # Valores negativos
            negative = numeric_series < 0
            if negative.any():
                negative_rows = self.df[negative].index.tolist()
                self._add_error(
                    "negative_values",
                    f"{negative.sum()} valores negativos en columna {col}",
                    column=col,
                    rows=negative_rows
                )
            
            # Valores fuera de rango
            out_of_range = (numeric_series < min_val) | (numeric_series > max_val)
            out_of_range = out_of_range & numeric_series.notna()
            if out_of_range.any():
                oor_rows = self.df[out_of_range].index.tolist()
                self._add_warning(
                    "out_of_range",
                    f"{out_of_range.sum()} valores fuera del rango esperado [{min_val}, {max_val}] en {col}",
                    column=col,
                    rows=oor_rows
                )
            
            # Valores faltantes
            missing = numeric_series.isna()
            if missing.any():
                missing_rows = self.df[missing].index.tolist()
                self._add_error(
                    "missing_values",
                    f"{missing.sum()} valores faltantes en columna {col}",
                    column=col,
                    rows=missing_rows
                )
    
    def _validate_binary_columns(self):
        """Valida columnas binarias (0 o 1)"""
        for col in BINARY_COLUMNS:
            if col not in self.df.columns:
                continue
            
            numeric_series = pd.to_numeric(self.df[col], errors="coerce")
            valid_values = numeric_series.isin([0, 1])
            
            invalid = ~valid_values & numeric_series.notna()
            if invalid.any():
                invalid_rows = self.df[invalid].index.tolist()
                self._add_error(
                    "invalid_binary_values",
                    f"{invalid.sum()} valores inválidos en {col} (debe ser 0 o 1)",
                    column=col,
                    rows=invalid_rows
                )
    
    def _validate_categorical_columns(self):
        """Valida columnas categóricas"""
        # Validar Temporada
        if "Temporada" in self.df.columns:
            invalid_seasons = ~self.df["Temporada"].isin(VALID_TEMPORADAS)
            if invalid_seasons.any():
                invalid_rows = self.df[invalid_seasons].index.tolist()
                unique_invalid = self.df[invalid_seasons]["Temporada"].unique().tolist()
                self._add_warning(
                    "invalid_temporada",
                    f"Temporadas no estándar encontradas: {unique_invalid}",
                    column="Temporada",
                    rows=invalid_rows
                )
        
        # Validar CodArticulo
        if "CodArticulo" in self.df.columns:
            empty_skus = self.df["CodArticulo"].isna() | (self.df["CodArticulo"] == "")
            if empty_skus.any():
                empty_rows = self.df[empty_skus].index.tolist()
                self._add_error(
                    "empty_sku",
                    f"{empty_skus.sum()} SKUs vacíos",
                    column="CodArticulo",
                    rows=empty_rows
                )
    
    def _validate_duplicates(self):
        """Valida duplicados problemáticos"""
        if "Fechaventa" not in self.df.columns or "CodArticulo" not in self.df.columns:
            return
        
        # Duplicados exactos (misma fecha + SKU)
        duplicates = self.df.duplicated(subset=["Fechaventa", "CodArticulo"], keep=False)
        if duplicates.any():
            dup_rows = self.df[duplicates].index.tolist()
            self._add_warning(
                "duplicate_records",
                f"{duplicates.sum()} registros duplicados (misma fecha + SKU)",
                rows=dup_rows
            )
    
    def _validate_temporal_consistency(self):
        """Valida consistencia temporal"""
        if "Fechaventa" not in self.df.columns or "CodArticulo" not in self.df.columns:
            return
        
        try:
            dates = pd.to_datetime(self.df["Fechaventa"], errors="coerce", dayfirst=True)
            
            # Verificar gaps temporales por SKU
            for sku in self.df["CodArticulo"].unique()[:10]:  # Muestra de 10 SKUs
                sku_data = self.df[self.df["CodArticulo"] == sku].copy()
                sku_data["Fechaventa_parsed"] = dates[sku_data.index]
                sku_data = sku_data.sort_values("Fechaventa_parsed")
                
                if len(sku_data) > 1:
                    date_diffs = sku_data["Fechaventa_parsed"].diff()
                    large_gaps = date_diffs > pd.Timedelta(days=60)
                    
                    if large_gaps.any():
                        self._add_info(
                            "temporal_gaps",
                            f"Gaps temporales >60 días detectados en SKU {sku}"
                        )
        except Exception as e:
            logger.warning(f"Error en validación temporal: {e}")
    
    def _validate_business_rules(self):
        """Valida reglas de negocio"""
        # Ventas sin stock
        if all(col in self.df.columns for col in ["CantidadVendida", "StockMes"]):
            ventas_numeric = pd.to_numeric(self.df["CantidadVendida"], errors="coerce")
            stock_numeric = pd.to_numeric(self.df["StockMes"], errors="coerce")
            
            ventas_sin_stock = (ventas_numeric > 0) & (stock_numeric == 0)
            if ventas_sin_stock.any():
                rows = self.df[ventas_sin_stock].index.tolist()
                self._add_warning(
                    "sales_without_stock",
                    f"{ventas_sin_stock.sum()} ventas registradas con stock en 0",
                    rows=rows
                )
        
        # Stock excesivo con ventas bajas
        if all(col in self.df.columns for col in ["CantidadVendida", "StockMes"]):
            ventas_numeric = pd.to_numeric(self.df["CantidadVendida"], errors="coerce")
            stock_numeric = pd.to_numeric(self.df["StockMes"], errors="coerce")
            
            ratio = stock_numeric / (ventas_numeric + 1)
            excesivo = ratio > 100
            if excesivo.any():
                rows = self.df[excesivo].index.tolist()
                self._add_warning(
                    "excessive_stock",
                    f"{excesivo.sum()} casos de stock excesivo (>100x ventas)",
                    rows=rows
                )
    
    def _check_data_quality(self):
        """Análisis de calidad general de datos"""
        # Porcentaje de datos faltantes
        missing_percent = (self.df.isna().sum() / len(self.df) * 100).to_dict()
        high_missing = {k: v for k, v in missing_percent.items() if v > 5}
        
        if high_missing:
            msg = ", ".join([f"{k}: {v:.1f}%" for k, v in high_missing.items()])
            self._add_warning(
                "high_missing_rate",
                f"Columnas con >5% datos faltantes: {msg}"
            )
        
        # Distribución de datos
        if "CodArticulo" in self.df.columns:
            sku_counts = self.df["CodArticulo"].value_counts()
            skus_con_pocos_datos = (sku_counts < 10).sum()
            
            if skus_con_pocos_datos > 0:
                self._add_info(
                    "low_data_skus",
                    f"{skus_con_pocos_datos} SKUs con menos de 10 registros"
                )


def validate_dataframe(df: pd.DataFrame, strict_mode: bool = True) -> tuple[List[Dict], bool]:
    """
    Función principal de validación
    
    Args:
        df: DataFrame a validar
        strict_mode: Si True, rechaza archivos con errores
    
    Returns:
        (lista_de_problemas, es_valido)
    """
    validator = DataFrameValidator(df, strict_mode=strict_mode)
    return validator.validate_all()


def validate_dataframe_legacy(df: pd.DataFrame) -> list[dict]:
    """
    Versión legacy para compatibilidad con código existente
    Retorna solo errores críticos
    """
    issues, is_valid = validate_dataframe(df, strict_mode=True)
    # Filtrar solo errores
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    return errors