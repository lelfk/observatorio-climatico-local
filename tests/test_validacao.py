"""Testes com dados sintéticos, nunca misturados com resultados meteorológicos."""
import unittest
from datetime import date, timedelta
from coleta import configuracao
from banco import transformar_validar

def amostra():
    cfg = configuracao()
    dias = [(date.fromisoformat(cfg["inicio"]) + timedelta(days=i)).isoformat() for i in range(30)]
    return {
        "timezone": cfg["timezone"],
        "daily_units": {"temperature_2m_min": "°C", "temperature_2m_max": "°C", "precipitation_sum": "mm"},
        "daily": {
            "time": dias, "temperature_2m_min": [18.0]*30,
            "temperature_2m_max": [26.0]*30, "precipitation_sum": [0.0]*30
        }
    }, cfg

class TestQualidade(unittest.TestCase):
    def test_serie_30_dias(self):
        payload,cfg=amostra()
        df,qual=transformar_validar(payload,cfg)
        self.assertEqual(len(df),30)
        self.assertEqual(qual["datas_duplicadas"],0)
    def test_duplicada(self):
        payload,cfg=amostra()
        payload["daily"]["time"][5]=payload["daily"]["time"][4]
        with self.assertRaises(ValueError): transformar_validar(payload,cfg)
    def test_chuva_negativa(self):
        payload,cfg=amostra()
        payload["daily"]["precipitation_sum"][2]=-1
        with self.assertRaises(ValueError): transformar_validar(payload,cfg)
    def test_minima_acima_maxima(self):
        payload,cfg=amostra()
        payload["daily"]["temperature_2m_min"][0]=30
        with self.assertRaises(ValueError): transformar_validar(payload,cfg)
    def test_nulo_preservado(self):
        payload,cfg=amostra()
        payload["daily"]["precipitation_sum"][3]=None
        df,qual=transformar_validar(payload,cfg)
        self.assertTrue(df["precipitacao_mm"].isna().iloc[3])
        self.assertEqual(qual["nulos"]["precipitacao_mm"],1)

if __name__ == "__main__":
    unittest.main()
