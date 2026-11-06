from pathlib import Path
import polars as pl

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_SILVER = PASTA_PROJETO / "data" / "silver"
CAMINHO_PASTA_GOLD = PASTA_PROJETO / "data" / "gold"
CAMINHO_LOCATIONS = PASTA_PROJETO / "config" / "locations.json"

def ler_dados_silver(
    caminho_silver: Path,
    nome_arquivo: str
) -> pl.DataFrame:
    caminho_arquivo = caminho_silver / nome_arquivo
    dataframe = pl.read_parquet(caminho_arquivo)
    return dataframe

def preparar_dim_capitais(
    caminho_locations: Path
) -> pl.DataFrame:
    dataframe_capitais = pl.read_json(caminho_locations)
    dataframe_capitais = dataframe_capitais.with_columns(
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
    return dataframe_capitais

def integrar_dados_horarios(
    df_forecast: pl.DataFrame,
    df_air_quality: pl.DataFrame,
    df_capitais: pl.DataFrame
) -> pl.DataFrame:
    df_air_quality = df_air_quality.drop("name", strict=False)
    df_forecast = df_forecast.drop("name", strict=False)

    radar_horario = df_forecast.join(
    other=df_air_quality,
    on=["uf","time"],
    how="full",
    coalesce=True
    )

    radar_horario = radar_horario.join(
    other=df_capitais,
    on=["uf"],
    how="left"
)

    return radar_horario

def converter_fuso_radar_horario(
    dataframe_resumo_horario: pl.DataFrame
) -> pl.DataFrame:
    df_particionado = dataframe_resumo_horario.partition_by("timezone",as_dict=True)
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
        pl.col("time_local").dt.date().alias("date"),
        pl.col("time_local").dt.time().alias("hora")
    )

    return radar_horario

def gerar_resumo_diario(
    df_resumo_horario: pl.DataFrame
) -> pl.DataFrame:
    radar_resumo_diario = df_resumo_horario.group_by(["uf","date"]).agg(
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

    return radar_resumo_diario

def gravar_parquet_gold(
    pasta_destino: Path,
    nome_arquivo: str,
    dataframe: pl.DataFrame
) -> None:
    pasta_destino.mkdir(parents=True, exist_ok=True)
    caminho_arquivo = pasta_destino / f"gold_{nome_arquivo}.parquet"
    dataframe.write_parquet(caminho_arquivo)

def silver_to_gold(
    pasta_silver: Path,
    pasta_gold: Path,
    caminho_locations: Path
) -> None:
    dataset_forecast = ler_dados_silver(caminho_silver=pasta_silver,nome_arquivo="silver_forecast.parquet")
    dataset_quality = ler_dados_silver(caminho_silver=pasta_silver,nome_arquivo="silver_air-quality.parquet")

    dataset_capitais = preparar_dim_capitais(caminho_locations=caminho_locations)

    resumo_horario = integrar_dados_horarios(
        df_forecast=dataset_forecast,
        df_air_quality=dataset_quality,
        df_capitais=dataset_capitais
    )

    resumo_horario = converter_fuso_radar_horario(dataframe_resumo_horario=resumo_horario)

    resumo_diario = gerar_resumo_diario(df_resumo_horario=resumo_horario)

    gravar_parquet_gold(
        pasta_destino=pasta_gold,
        nome_arquivo="radar_horario",
        dataframe=resumo_horario
    )

    gravar_parquet_gold(
            pasta_destino=pasta_gold,
            nome_arquivo="radar_diario",
            dataframe=resumo_diario
        )

    gravar_parquet_gold(
        pasta_destino=pasta_gold,
        nome_arquivo="dim_capitais",
        dataframe=dataset_capitais
    )

if __name__ == "__main__":
    silver_to_gold(
        pasta_silver=CAMINHO_PASTA_SILVER,
        pasta_gold=CAMINHO_PASTA_GOLD,
        caminho_locations=CAMINHO_LOCATIONS
    )
    

