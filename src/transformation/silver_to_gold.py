from pathlib import Path
import polars as pl

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_SILVER_FORECAST = PASTA_PROJETO / "data/silver/silver_forecast.parquet"
CAMINHO_SILVER_QUALITY = PASTA_PROJETO / "data/silver/silver_air-quality.parquet"
CAMINHO_PASTA_GOLD = PASTA_PROJETO / "data/gold"
CAMINHO_PASTA_GOLD.mkdir(parents=True,exist_ok=True)

dataset_forecast = pl.read_parquet(CAMINHO_SILVER_FORECAST)
dataset_quality = pl.read_parquet(CAMINHO_SILVER_QUALITY)
dataset_capitais = pl.read_json(PASTA_PROJETO / "config/locations.json")
dataset_capitais = dataset_capitais.with_columns(
    pl.when(pl.col("uf").is_in(["RJ", "SP", "ES", "MG"]))
    .then(pl.lit("Sudeste"))
    .when(pl.col("uf").is_in(["BA", "SE", "AL", "PE", "PB", "RN", "CE", "MA", "PI"]))
    .then(pl.lit("Nordeste"))
    .when(pl.col("uf").is_in(["AM", "AP", "RR", "RO", "AC", "PA", "TO"]))
    .then(pl.lit("Norte"))
    .when(pl.col("uf").is_in(["MS", "MT", "GO", "DF"]))
    .then(pl.lit("Centro-Oeste"))
    .when(pl.col("uf").is_in(["PR", "SC", "RS"]))
    .then(pl.lit("Sul"))
    .otherwise(None)
    .alias("regiao")
)

dataset_quality = dataset_quality.drop("name")
dataset_forecast = dataset_forecast.drop("name")
radar_horario = dataset_forecast.join(
    other=dataset_quality,
    on=["uf","time"],
    how="full",
    coalesce=True
)

radar_horario = radar_horario.join(
    other=dataset_capitais,
    on=["uf"],
    how="left"
)

df_particionado = radar_horario.partition_by("timezone",as_dict=True)

tabelas_convertidas = []
for chave, pedaco in df_particionado.items():
    fuso = chave[0]
    tabela = pedaco.with_columns(
        pl.col("time")
        .dt.convert_time_zone(fuso)
        .dt.replace_time_zone(None)
        .alias("time_local")
    )
    tabelas_convertidas.append(tabela)

radar_horario = pl.concat(tabelas_convertidas)
radar_horario = radar_horario.sort(["uf","time"])
radar_horario = radar_horario.with_columns(
    pl.col("time_local")
    .dt.date()
    .alias("date")
)

radar_resumo_diario = radar_horario.group_by(["uf","date"]).agg(
    pl.col("temperature_2m").min().alias("min_temperatura"),
    pl.col("temperature_2m").max().alias("max_temperatura"),
    pl.col("temperature_2m").mean().alias("media_temperatura"),
    pl.col("precipitation").sum().alias("soma_precipitacao"),
    pl.col("precipitation").max().alias("max_precipitacao"),
    (pl.col("precipitation") > 0).sum().alias("horas_com_chuva"),
    pl.col("precipitation_probability").max().alias("max_prob_chuva"),
    pl.col("relative_humidity_2m").mean().alias("media_umidade"),
    pl.col("relative_humidity_2m").min().alias("min_umidade"),
    pl.col("relative_humidity_2m").max().alias("max_umidade"),
    pl.col("pm2_5").max().alias("max_pm2_5"),
    pl.col("pm2_5").mean().alias("media_pm2_5"),
    pl.col("pm2_5").count().alias("horas_com_pm2_5"),
    pl.col("pm10").max().alias("max_pm10"),
    pl.col("pm10").mean().alias("media_pm10"),
    pl.col("pm10").count().alias("horas_com_pm10"),
    pl.col("ozone").max().alias("max_ozonio"),
    pl.col("ozone").mean().alias("media_ozonio"),
    pl.col("ozone").count().alias("horas_com_ozonio"),
    pl.len().alias("horas_observadas")
).sort(["uf","date"])


dataset_capitais.write_parquet(CAMINHO_PASTA_GOLD / "gold_dim_capitais.parquet")
radar_horario.write_parquet(CAMINHO_PASTA_GOLD / "gold_radar_horario.parquet")
radar_resumo_diario.write_parquet(CAMINHO_PASTA_GOLD / "gold_radar_resumo_diario.parquet")



