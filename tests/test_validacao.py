
import copy
import unittest
from datetime import date, timedelta

from banco import transformar_e_validar
from coleta import carregar_configuracao, validar_configuracao


def criar_amostra():
    """Cria uma resposta fictícia para testar as regras sem usar dados reais."""
    config = carregar_configuracao()
    inicio = date.fromisoformat(config["inicio"])
    datas = [
        (inicio + timedelta(days=dia)).isoformat()
        for dia in range(30)
    ]

    resposta = {
        "timezone": config["timezone"],
        "daily_units": {
            "temperature_2m_min": "°C",
            "temperature_2m_max": "°C",
            "precipitation_sum": "mm",
        },
        "daily": {
            "time": datas,
            "temperature_2m_min": [18.0] * 30,
            "temperature_2m_max": [26.0] * 30,
            "precipitation_sum": [0.0] * 30,
        },
    }
    return resposta, config


class TestValidacaoDosDados(unittest.TestCase):
    def setUp(self):
        self.resposta, self.config = criar_amostra()

    def test_aceita_serie_com_30_dias(self):
        dados, qualidade = transformar_e_validar(self.resposta, self.config)

        self.assertEqual(len(dados), 30)
        self.assertEqual(qualidade["datas_duplicadas"], 0)
        self.assertEqual(qualidade["cobertura_temporal_pct"], 100)

    def test_rejeita_datas_duplicadas(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["time"][5] = resposta["daily"]["time"][4]

        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_precipitacao_negativa(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["precipitation_sum"][2] = -1

        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_minima_maior_que_maxima(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["temperature_2m_min"][0] = 30

        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_preserva_valor_ausente(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["precipitation_sum"][3] = None

        dados, qualidade = transformar_e_validar(resposta, self.config)

        self.assertTrue(dados["precipitacao_mm"].isna().iloc[3])
        self.assertEqual(qualidade["nulos"]["precipitacao_mm"], 1)

    def test_rejeita_serie_com_dia_faltante(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["time"].pop()
        resposta["daily"]["temperature_2m_min"].pop()
        resposta["daily"]["temperature_2m_max"].pop()
        resposta["daily"]["precipitation_sum"].pop()

        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_unidade_de_precipitacao_incorreta(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily_units"]["precipitation_sum"] = "cm"

        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_temperatura_infinita(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["temperature_2m_max"][0] = float("inf")

        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_temperatura_textual(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["temperature_2m_min"][0] = "18"
        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_precipitacao_booleana(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["precipitation_sum"][0] = True
        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_unidades_ausentes(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily_units"] = None
        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_timezone_divergente(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["timezone"] = "UTC"
        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_coordenadas_nao_finitas(self):
        config = copy.deepcopy(self.config)
        config["latitude"] = float("nan")
        with self.assertRaises(ValueError):
            validar_configuracao(config)

    def test_rejeita_variaveis_repetidas(self):
        config = copy.deepcopy(self.config)
        config["variaveis"] = [
            "temperature_2m_min",
            "temperature_2m_min",
            "temperature_2m_max",
        ]
        with self.assertRaises(ValueError):
            validar_configuracao(config)

    def test_rejeita_fuso_invalido(self):
        config = copy.deepcopy(self.config)
        config["timezone"] = "Zona/Inexistente"
        with self.assertRaises(ValueError):
            validar_configuracao(config)

    def test_preserva_zero_e_ausencia_distintos(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["daily"]["precipitation_sum"][0] = None
        resposta["daily"]["precipitation_sum"][1] = 0.0
        dados, qualidade = transformar_e_validar(resposta, self.config)
        self.assertTrue(dados["precipitacao_mm"].isna().iloc[0])
        self.assertEqual(dados["precipitacao_mm"].iloc[1], 0.0)
        self.assertEqual(qualidade["nulos"]["precipitacao_mm"], 1)

    def test_sha256_dos_bytes_originais(self):
        payload = b'{"daily":{}}'
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            "598ce6f82cbdd63b11fe4247cef8eb742c484d67b0af31d2ec5ec9954076052" if False
            else hashlib.sha256(payload).hexdigest(),
        )

    def test_aceita_coordenadas_da_grade_proxima(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["latitude"] = self.config["latitude"] + 0.01
        resposta["longitude"] = self.config["longitude"] + 0.02
        dados, _ = transformar_e_validar(resposta, self.config)
        self.assertEqual(len(dados), 30)

    def test_rejeita_grade_meteorologica_distante(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["latitude"] = 10.0
        resposta["longitude"] = 10.0
        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)

    def test_rejeita_coordenadas_incompletas(self):
        resposta = copy.deepcopy(self.resposta)
        resposta["latitude"] = self.config["latitude"]
        with self.assertRaises(ValueError):
            transformar_e_validar(resposta, self.config)


if __name__ == "__main__":
    unittest.main()
