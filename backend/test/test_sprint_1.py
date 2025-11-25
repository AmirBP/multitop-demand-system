"""
Pruebas Unitarias - Sprint 1
Sistema de Predicción de Demanda - Multitop SAC
Basado en la estructura real del proyecto
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================================
# PRUEBAS DE VALIDACIÓN (HU002)
# ============================================================================


class TestValidacionEstructura:
    """Pruebas para app/services/validation_service.py"""

    def test_validar_columnas_requeridas(self):
        """
        Verifica que validate_dataframe detecte columnas faltantes
        """
        from app.services.validation_service import validate_dataframe, REQUIRED

        # Arrange - DataFrame con columnas faltantes
        df_invalido = pd.DataFrame({
            "Fechaventa": ["2024-01-15"],
            "CodArticulo": ["ME000008556"],
            # Faltan las demás columnas requeridas
        })

        # Act
        errores = validate_dataframe(df_invalido)

        # Assert
        assert len(errores) > 0, "Debe detectar columnas faltantes"
        assert errores[0]["type"] == "missing_columns"

        # Verificar que detecta exactamente las columnas faltantes
        columnas_faltantes = errores[0]["columns"]
        esperadas = [col for col in REQUIRED if col not in df_invalido.columns]
        assert set(columnas_faltantes) == set(esperadas)

    def test_dataframe_valido_sin_errores(self):
        """
        Verifica que un DataFrame válido no genere errores
        """
        from app.services.validation_service import validate_dataframe, REQUIRED

        # Arrange - DataFrame completo
        df_valido = pd.DataFrame({col: [1] for col in REQUIRED})
        df_valido["Fechaventa"] = ["2024-01-15"]
        df_valido["CodArticulo"] = ["ME000008556"]

        # Act
        errores = validate_dataframe(df_valido)

        # Assert
        assert len(errores) == 0, "No debe haber errores con DataFrame válido"


# ============================================================================
# PRUEBAS DE ETL Y LIMPIEZA (HU008)
# ============================================================================


class TestLimpiezaDatos:
    """Pruebas para app/services/etl_service.py"""

    def test_limpiar_sin_filtros(self):
        """
        Verifica que limpiar_df funcione sin filtros
        """
        from app.services.etl_service import limpiar_df

        # Arrange
        df = pd.DataFrame({
            "CodArticulo": ["ME001", "ME002", "ME003"],
            "tienda": ["Lima Centro", "Lima Norte", "Lima Centro"],
            "CantidadVendida": [100, 120, 110],
        })

        # Act
        resultado = limpiar_df(df, filtros=None)

        # Assert
        assert len(resultado) == 3, "Debe retornar todos los registros"
        assert list(resultado.columns) == list(df.columns)

    def test_limpiar_con_filtro_tienda(self):
        """
        Verifica que limpiar_df filtre correctamente por tienda (HU007)
        """
        from app.services.etl_service import limpiar_df

        # Arrange
        df = pd.DataFrame({
            "CodArticulo": ["ME001", "ME002", "ME003"],
            "tienda": ["Lima Centro", "Lima Norte", "Lima Centro"],
            "CantidadVendida": [100, 120, 110],
        })
        filtros = {"tienda": "Lima Centro"}

        # Act
        resultado = limpiar_df(df, filtros=filtros)

        # Assert
        assert len(resultado) == 2, "Debe filtrar solo 2 registros de Lima Centro"
        assert all(resultado["tienda"] == "Lima Centro")

    def test_filtros_multiples(self):
        """
        Verifica que se puedan aplicar múltiples filtros simultáneamente
        """
        from app.services.etl_service import limpiar_df

        # Arrange
        df = pd.DataFrame({
            "CodArticulo": ["ME001", "ME002", "ME003", "ME004"],
            "tienda": ["Lima Centro", "Lima Norte", "Lima Centro", "Lima Centro"],
            "categoria": ["Telas", "Espumas", "Telas", "Sintéticos"],
        })
        filtros = {"tienda": "Lima Centro", "categoria": "Telas"}

        # Act
        resultado = limpiar_df(df, filtros=filtros)

        # Assert
        assert len(resultado) == 2, "Debe filtrar por tienda Y categoría"
        assert all(resultado["tienda"] == "Lima Centro")
        assert all(resultado["categoria"] == "Telas")


# ============================================================================
# PRUEBAS DEL MODELO (HU003, HU009)
# ============================================================================


class TestModeloPredictivo:
    """Pruebas para ml/model_prediction.py"""

    @pytest.mark.requires_model
    def test_procesar_prediccion_genera_columnas_esperadas(self):
        """
        Verifica que procesar_prediccion_global genere las columnas esperadas
        """
        from ml.model_prediction import procesar_prediccion_global

        if not Path("outputs/modelo_xgb_sku_global.joblib").exists():
            pytest.skip("Modelo no entrenado aún")

        # Arrange - Datos mínimos válidos
        df = pd.DataFrame({
            "Fechaventa": pd.date_range("2024-01-01", periods=40),
            "CodArticulo": ["ME000008556"] * 40,
            "Temporada": ["Verano"] * 40,
            "PrecioVenta": [45.5] * 40,
            "CantidadVendida": np.random.randint(100, 150, 40),
            "StockMes": [5000] * 40,
            "TiempoReposicionDias": [60] * 40,
            "Promocion": [0] * 40,
            "DiaFestivo": [0] * 40,
            "EsDomingo": [0] * 40,
            "TiendaCerrada": [0] * 40,
        })

        # Act
        resultado = procesar_prediccion_global(df)

        # Assert
        columnas_esperadas = [
            "CodArticulo", "d_media", "d_sigma", "StockMes", "horizon",
            "seguridad", "stock_objetivo", "dias_cobertura",
            "porcentaje_sobrestock", "indice_riesgo_quiebre",
            "Estado", "Accion",
        ]
        assert all(col in resultado.columns for col in columnas_esperadas)

    @pytest.mark.requires_model
    def test_clasificacion_estados(self):
        """
        Verifica que el modelo clasifique correctamente los estados de stock
        """
        from ml.model_prediction import procesar_prediccion_global

        if not Path("outputs/modelo_xgb_sku_global.joblib").exists():
            pytest.skip("Modelo no entrenado")

        # Arrange
        df = pd.DataFrame({
            "Fechaventa": pd.date_range("2024-01-01", periods=40),
            "CodArticulo": ["ME000008556"] * 40,
            "Temporada": ["Verano"] * 40,
            "PrecioVenta": [45.5] * 40,
            "CantidadVendida": np.random.randint(100, 150, 40),
            "StockMes": [5000] * 40,
            "TiempoReposicionDias": [60] * 40,
            "Promocion": [0] * 40,
            "DiaFestivo": [0] * 40,
            "EsDomingo": [0] * 40,
            "TiendaCerrada": [0] * 40,
        })

        # Act
        resultado = procesar_prediccion_global(df)

        # Assert
        estados_validos = ["OK", "Quiebre Potencial", "Sobre-stock"]
        assert resultado["Estado"].iloc[0] in estados_validos


# (el resto de clases de pruebas: TestServicioPrediction, TestPredictionsRepo,
#  TestAPIEndpoints, TestMetricasValidacion…) pueden quedarse tal cual,
# solo sin el bloque `if __name__ == "__main__": ...`
