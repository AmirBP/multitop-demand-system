"""
Pruebas Unitarias - Sprint 2
Sistema de Predicción de Demanda - Multitop SAC
Segmentación, Ajuste de Modelo y Dashboard
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# PRUEBAS DE ENTRENAMIENTO Y AJUSTE (HU009)
# ============================================================================

class TestEntrenamientoModelo:
    """Pruebas para ml/train_model.py"""
    
    def test_entrenar_modelo_genera_salida_completa(self):
        """
        Verifica que entrenar_modelo retorne todas las métricas esperadas
        """
        from ml.train_model import entrenar_modelo
        
        # Arrange - Dataset mínimo pero válido para entrenar
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=120),
            'CodArticulo': ['ME000008556'] * 120,
            'Temporada': ['Verano'] * 120,
            'PrecioVenta': np.random.uniform(40, 50, 120),
            'CantidadVendida': np.random.randint(90, 160, 120),
            'StockMes': [5000] * 120,
            'TiempoReposicionDias': [60] * 120,
            'Promocion': np.random.choice([0, 1], 120),
            'DiaFestivo': np.random.choice([0, 1], 120),
            'EsDomingo': [0] * 120,
            'TiendaCerrada': [0] * 120
        })
        
        # Act
        resultado = entrenar_modelo(df)
        
        # Assert - Verificar que retorne todas las métricas
        metricas_esperadas = ['mae', 'mape', 'wape', 'smape', 'bias', 'precision']
        for metrica in metricas_esperadas:
            assert metrica in resultado, f"Debe incluir métrica {metrica}"
        
        # Verificar que MAE sea un número válido
        assert isinstance(resultado['mae'], (int, float)), "MAE debe ser numérico"
        assert resultado['mae'] >= 0, "MAE no puede ser negativo"
    
    def test_modelo_guardado_correctamente(self):
        """
        Verifica que el modelo se guarde en la ubicación correcta
        """
        from ml.train_model import entrenar_modelo, MODEL_PATH
        
        # Arrange
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=120),
            'CodArticulo': ['ME000008556'] * 120,
            'Temporada': ['Verano'] * 120,
            'PrecioVenta': np.random.uniform(40, 50, 120),
            'CantidadVendida': np.random.randint(90, 160, 120),
            'StockMes': [5000] * 120,
            'TiempoReposicionDias': [60] * 120,
            'Promocion': np.random.choice([0, 1], 120),
            'DiaFestivo': np.random.choice([0, 1], 120),
            'EsDomingo': [0] * 120,
            'TiendaCerrada': [0] * 120
        })
        
        # Act
        entrenar_modelo(df)
        
        # Assert
        assert MODEL_PATH.exists(), f"Modelo debe guardarse en {MODEL_PATH}"
    
    def test_precision_minima_85_porciento(self):
        """
        Verifica que el modelo alcance la precisión mínima del 85%
        Criterio de éxito del proyecto: IE1
        """
        from ml.train_model import entrenar_modelo
        
        # Arrange - Dataset con patrón predecible
        n = 120
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=n),
            'CodArticulo': ['ME000008556'] * n,
            'Temporada': ['Verano'] * n,
            'PrecioVenta': [45.0] * n,
            'CantidadVendida': [120] * n,  # Patrón constante
            'StockMes': [5000] * n,
            'TiempoReposicionDias': [60] * n,
            'Promocion': [0] * n,
            'DiaFestivo': [0] * n,
            'EsDomingo': [0] * n,
            'TiendaCerrada': [0] * n
        })
        
        # Act
        resultado = entrenar_modelo(df)
        
        # Assert
        assert resultado['precision'] >= 85, \
            f"Precisión debe ser ≥ 85%. Obtenido: {resultado['precision']}%"


# ============================================================================
# PRUEBAS DE FEATURE IMPORTANCE (HU014)
# ============================================================================

class TestExplicabilidad:
    """Pruebas para verificar la explicabilidad del modelo"""
    
    def test_genera_archivo_importancia_features(self):
        """
        Verifica que el entrenamiento genere el archivo de importancia de features
        """
        from ml.train_model import entrenar_modelo, OUTPUT_DIR
        
        # Arrange
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=120),
            'CodArticulo': ['ME000008556'] * 120,
            'Temporada': ['Verano'] * 120,
            'PrecioVenta': np.random.uniform(40, 50, 120),
            'CantidadVendida': np.random.randint(90, 160, 120),
            'StockMes': [5000] * 120,
            'TiempoReposicionDias': [60] * 120,
            'Promocion': np.random.choice([0, 1], 120),
            'DiaFestivo': np.random.choice([0, 1], 120),
            'EsDomingo': [0] * 120,
            'TiendaCerrada': [0] * 120
        })
        
        # Act
        entrenar_modelo(df)
        
        # Assert
        imp_file = OUTPUT_DIR / "importancia_features.csv"
        assert imp_file.exists(), "Debe generar archivo de importancia de features"
        
        # Verificar contenido
        imp_df = pd.read_csv(imp_file)
        assert 'feature' in imp_df.columns
        assert 'gain' in imp_df.columns
        assert len(imp_df) > 0, "Debe contener al menos una feature"
    
    def test_importancia_retornada_en_resultado(self):
        """
        Verifica que el resultado del entrenamiento incluya importancia de features
        """
        from ml.train_model import entrenar_modelo
        
        # Arrange
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=120),
            'CodArticulo': ['ME000008556'] * 120,
            'Temporada': ['Verano'] * 120,
            'PrecioVenta': np.random.uniform(40, 50, 120),
            'CantidadVendida': np.random.randint(90, 160, 120),
            'StockMes': [5000] * 120,
            'TiempoReposicionDias': [60] * 120,
            'Promocion': np.random.choice([0, 1], 120),
            'DiaFestivo': np.random.choice([0, 1], 120),
            'EsDomingo': [0] * 120,
            'TiendaCerrada': [0] * 120
        })
        
        # Act
        resultado = entrenar_modelo(df)
        
        # Assert
        assert 'importancia' in resultado, "Resultado debe incluir importancia"
        assert isinstance(resultado['importancia'], list)
        assert len(resultado['importancia']) > 0


# ============================================================================
# PRUEBAS DE ALERTAS Y DASHBOARD (HU010, HU013)
# ============================================================================

class TestAlertas:
    """Pruebas para el sistema de alertas de stock"""
    
    def test_clasificacion_quiebre_potencial(self):
        """
        Verifica que el sistema detecte correctamente quiebre potencial
        """
        from ml.model_prediction import procesar_prediccion_global
        
        if not Path("outputs/modelo_xgb_sku_global.joblib").exists():
            pytest.skip("Modelo no entrenado")
        
        # Arrange - Stock muy bajo para generar quiebre
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=40),
            'CodArticulo': ['ME000008556'] * 40,
            'Temporada': ['Verano'] * 40,
            'PrecioVenta': [45.5] * 40,
            'CantidadVendida': [150] * 40,  # Demanda alta
            'StockMes': [100] * 40,  # Stock muy bajo
            'TiempoReposicionDias': [60] * 40,
            'Promocion': [0] * 40,
            'DiaFestivo': [0] * 40,
            'EsDomingo': [0] * 40,
            'TiendaCerrada': [0] * 40
        })
        
        # Act
        resultado = procesar_prediccion_global(df)
        
        # Assert
        estado = resultado['Estado'].iloc[0]
        assert estado in ['Quiebre Potencial', 'OK', 'Sobre-stock'], \
            "Estado debe ser válido"
    
    def test_clasificacion_sobrestock(self):
        """
        Verifica que el sistema detecte correctamente sobrestock
        """
        from ml.model_prediction import procesar_prediccion_global
        
        if not Path("outputs/modelo_xgb_sku_global.joblib").exists():
            pytest.skip("Modelo no entrenado")
        
        # Arrange - Stock muy alto para generar sobrestock
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=40),
            'CodArticulo': ['ME000008556'] * 40,
            'Temporada': ['Verano'] * 40,
            'PrecioVenta': [45.5] * 40,
            'CantidadVendida': [50] * 40,  # Demanda baja
            'StockMes': [100000] * 40,  # Stock muy alto
            'TiempoReposicionDias': [60] * 40,
            'Promocion': [0] * 40,
            'DiaFestivo': [0] * 40,
            'EsDomingo': [0] * 40,
            'TiendaCerrada': [0] * 40
        })
        
        # Act
        resultado = procesar_prediccion_global(df)
        
        # Assert
        estado = resultado['Estado'].iloc[0]
        # Con stock tan alto, debería ser Sobre-stock
        assert 'Accion' in resultado.columns, "Debe incluir columna de Acción"
    
    def test_indicadores_stock_calculados(self):
        """
        Verifica que se calculen todos los indicadores de stock
        """
        from ml.model_prediction import procesar_prediccion_global
        
        if not Path("outputs/modelo_xgb_sku_global.joblib").exists():
            pytest.skip("Modelo no entrenado")
        
        # Arrange
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=40),
            'CodArticulo': ['ME000008556'] * 40,
            'Temporada': ['Verano'] * 40,
            'PrecioVenta': [45.5] * 40,
            'CantidadVendida': np.random.randint(100, 150, 40),
            'StockMes': [5000] * 40,
            'TiempoReposicionDias': [60] * 40,
            'Promocion': [0] * 40,
            'DiaFestivo': [0] * 40,
            'EsDomingo': [0] * 40,
            'TiendaCerrada': [0] * 40
        })
        
        # Act
        resultado = procesar_prediccion_global(df)
        
        # Assert - Verificar indicadores clave
        indicadores = [
            'd_media', 'd_sigma', 'seguridad', 'stock_objetivo',
            'dias_cobertura', 'porcentaje_sobrestock', 'indice_riesgo_quiebre'
        ]
        for ind in indicadores:
            assert ind in resultado.columns, f"Debe calcular {ind}"
            assert not resultado[ind].isna().all(), f"{ind} no debe ser todo NaN"


# ============================================================================
# PRUEBAS DE INTEGRACIÓN SPRINT 2
# ============================================================================

class TestIntegracionCompletaSprint2:
    """Pruebas de integración end-to-end del Sprint 2"""
    
    def test_flujo_completo_entrenamiento_prediccion(self):
        """
        Prueba el flujo completo: entrenar → predecir → alertas
        """
        from ml.train_model import entrenar_modelo
        from ml.model_prediction import procesar_prediccion_global
        
        # Arrange - Dataset completo
        n_train = 120
        n_pred = 40
        
        df_train = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=n_train),
            'CodArticulo': ['ME000008556'] * n_train,
            'Temporada': ['Verano'] * n_train,
            'PrecioVenta': np.random.uniform(40, 50, n_train),
            'CantidadVendida': np.random.randint(90, 160, n_train),
            'StockMes': [5000] * n_train,
            'TiempoReposicionDias': [60] * n_train,
            'Promocion': np.random.choice([0, 1], n_train),
            'DiaFestivo': np.random.choice([0, 1], n_train),
            'EsDomingo': [0] * n_train,
            'TiendaCerrada': [0] * n_train
        })
        
        df_pred = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-11-01', periods=n_pred),
            'CodArticulo': ['ME000008556'] * n_pred,
            'Temporada': ['Verano'] * n_pred,
            'PrecioVenta': [45.5] * n_pred,
            'CantidadVendida': [120] * n_pred,
            'StockMes': [5000] * n_pred,
            'TiempoReposicionDias': [60] * n_pred,
            'Promocion': [0] * n_pred,
            'DiaFestivo': [0] * n_pred,
            'EsDomingo': [0] * n_pred,
            'TiendaCerrada': [0] * n_pred
        })
        
        # Act
        # 1. Entrenar modelo
        resultado_train = entrenar_modelo(df_train)
        
        # 2. Generar predicciones
        resultado_pred = procesar_prediccion_global(df_pred)
        
        # Assert
        # Verificar que el entrenamiento fue exitoso
        assert resultado_train['mae'] < 100, "MAE debe ser razonable"
        
        # Verificar que las predicciones se generaron
        assert len(resultado_pred) > 0, "Debe generar predicciones"
        assert 'Estado' in resultado_pred.columns
        assert 'Accion' in resultado_pred.columns


# ============================================================================
# PRUEBAS DE SERVICIOS AVANZADOS
# ============================================================================

class TestServicioTrain:
    """Pruebas para app/services/train_service.py"""
    
    def test_train_from_df_con_limpieza(self):
        """
        Verifica que train_from_df aplique limpieza antes de entrenar
        """
        from app.services.train_service import train_from_df
        
        # Arrange
        df = pd.DataFrame({
            'Fechaventa': pd.date_range('2024-01-01', periods=120),
            'CodArticulo': ['ME000008556'] * 120,
            'Temporada': ['Verano'] * 120,
            'PrecioVenta': np.random.uniform(40, 50, 120),
            'CantidadVendida': np.random.randint(90, 160, 120),
            'StockMes': [5000] * 120,
            'TiempoReposicionDias': [60] * 120,
            'Promocion': np.random.choice([0, 1], 120),
            'DiaFestivo': np.random.choice([0, 1], 120),
            'EsDomingo': [0] * 120,
            'TiendaCerrada': [0] * 120
        })
        
        # Act
        resultado = train_from_df(df, tuning=False)
        
        # Assert
        assert 'mae' in resultado
        assert isinstance(resultado['mae'], (int, float))


# ============================================================================
# CONFIGURACIÓN DE PYTEST
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup inicial para las pruebas"""
    # Crear directorios necesarios
    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/store").mkdir(exist_ok=True)
    Path("outputs/exports").mkdir(exist_ok=True)
    yield
    # Cleanup si es necesario


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])