-- maior temperatura registrada
SELECT data, temperatura_max_c AS maior_temperatura_c
FROM clima_diario
WHERE temperatura_max_c = (SELECT MAX(temperatura_max_c) FROM clima_diario)
ORDER BY data;

-- total de chuva e dias chuvosos
SELECT ROUND(SUM(precipitacao_mm), 1) AS precipitacao_total_mm,
       COUNT(*) FILTER (WHERE precipitacao_mm > 0) AS dias_com_chuva,
       COUNT(precipitacao_mm) AS dias_com_dado,
       MAX(precipitacao_mm) AS maior_precipitacao_diaria_mm
FROM clima_diario;

-- media simples diaria e amplitude
SELECT ROUND(AVG((temperatura_min_c + temperatura_max_c)/2), 1) AS temperatura_media_aproximada_c,
       COUNT(*) FILTER (WHERE temperatura_min_c IS NOT NULL AND temperatura_max_c IS NOT NULL) AS dias_validos,
       ROUND(AVG(temperatura_max_c - temperatura_min_c), 1) AS amplitude_termica_media_c
FROM clima_diario;
