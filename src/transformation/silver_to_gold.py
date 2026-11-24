
from pathlib import Path
import polars as pl


PASTA_PROJETO = Path(__file__).resolve().parents[2]

CAMINHO_PASTA_SILVER = PASTA_PROJETO / "data" / "silver"
CAMINHO_PASTA_GOLD = PASTA_PROJETO / "data" / "gold"
CAMINHO_LOCATIONS = PASTA_PROJETO / "config" / "locations.json"


# ============================================================
# LEITURA DOS DADOS
# ============================================================

def ler_dados_silver(
    caminho_silver: Path,
    nome_arquivo: str
) -> pl.DataFrame:

    caminho_arquivo = caminho_silver / nome_arquivo

    dataframe = pl.read_parquet(caminho_arquivo)

    return dataframe


# ============================================================
# DIMENSÃO DE CAPITAIS
# ============================================================

def preparar_dim_capitais(
    caminho_locations: Path
) -> pl.DataFrame:

    dataframe_capitais = pl.read_json(caminho_locations)

    dataframe_capitais = dataframe_capitais.with_columns(
        pl.when(pl.col("uf").is_in(["RJ", "SP", "ES", "MG"]))
        .then(pl.lit("Sudeste"))

        .when(pl.col("uf").is_in([
            "BA", "SE", "AL", "PE", "PB",
            "RN", "CE", "MA", "PI"
        ]))
        .then(pl.lit("Nordeste"))

        .when(pl.col("uf").is_in([
            "AM", "AP", "RR", "RO", "AC", "PA", "TO"
        ]))
        .then(pl.lit("Norte"))

        .when(pl.col("uf").is_in(["MS", "MT", "GO", "DF"]))
        .then(pl.lit("Centro-Oeste"))

        .when(pl.col("uf").is_in(["PR", "SC", "RS"]))
        .then(pl.lit("Sul"))

        .otherwise(None)
        .alias("regiao")
    )

    return dataframe_capitais


# ============================================================
# INTEGRAÇÃO DOS DADOS HORÁRIOS
# ============================================================

def integrar_dados_horarios(
    df_forecast: pl.DataFrame,
    df_air_quality: pl.DataFrame,
    df_capitais: pl.DataFrame
) -> pl.DataFrame:

    df_air_quality = df_air_quality.drop(
        "name",
        strict=False
    )

    df_forecast = df_forecast.drop(
        "name",
        strict=False
    )

    radar_horario = df_forecast.join(
        other=df_air_quality,
        on=["uf", "time"],
        how="full",
        coalesce=True
    )

    radar_horario = radar_horario.join(
        other=df_capitais,
        on=["uf"],
        how="left"
    )

    return radar_horario


# ============================================================
# CONVERSÃO DE FUSO HORÁRIO
# ============================================================

def converter_fuso_radar_horario(
    dataframe_resumo_horario: pl.DataFrame
) -> pl.DataFrame:

    df_particionado = dataframe_resumo_horario.partition_by(
        "timezone",
        as_dict=True
    )

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

    radar_horario = radar_horario.sort(["uf", "time"])

    radar_horario = radar_horario.with_columns(
        pl.col("time_local").dt.date().alias("date"),
        pl.col("time_local").dt.time().alias("hora")
    )

    return radar_horario


# ============================================================
# MÉDIA MÓVEL DE 8 HORAS DO OZÔNIO
# ============================================================

def calcular_media_movel_ozonio(
    df_resumo_horario: pl.DataFrame
) -> pl.DataFrame:

    df_resumo_horario = df_resumo_horario.sort(
        ["uf", "time_local"]
    )

    # Verifica se cada registro está separado do anterior
    # por exatamente uma hora.
    df_resumo_horario = df_resumo_horario.with_columns(
        (
            pl.col("time_local").diff().over("uf")
            == pl.duration(hours=1)
        )
        .cast(pl.Int8)
        .alias("intervalo_horario_valido")
    )

    # Calcula a média das últimas oito observações.
    df_resumo_horario = df_resumo_horario.with_columns(
        pl.col("ozone")
        .rolling_mean(
            window_size=8,
            min_samples=8
        )
        .over("uf")
        .alias("media_movel_8h_ozonio"),

        # Verifica se as oito observações formam
        # um intervalo de sete horas consecutivas.
        pl.col("intervalo_horario_valido")
        .rolling_sum(
            window_size=7,
            min_samples=7
        )
        .over("uf")
        .alias("intervalos_consecutivos")
    )

    # Descarta janelas com intervalos irregulares.
    df_resumo_horario = df_resumo_horario.with_columns(
        pl.when(
            pl.col("intervalos_consecutivos") == 7
        )
        .then(pl.col("media_movel_8h_ozonio"))
        .otherwise(None)
        .alias("media_movel_8h_ozonio")
    )

    return df_resumo_horario


# ============================================================
# RESUMO DIÁRIO
# ============================================================

def gerar_resumo_diario(
    df_resumo_horario: pl.DataFrame
) -> pl.DataFrame:

    radar_resumo_diario = df_resumo_horario.group_by(
        ["uf", "date"]
    ).agg(

        # Identificação geográfica
        pl.col("capital").first().alias("capital"),
        pl.col("regiao").first().alias("regiao"),

        # Meteorologia
        pl.col("temperature_2m")
        .min()
        .alias("min_temperatura"),

        pl.col("temperature_2m")
        .max()
        .alias("max_temperatura"),

        pl.col("temperature_2m")
        .mean()
        .alias("media_temperatura"),

        pl.col("precipitation")
        .sum()
        .alias("soma_precipitacao"),

        pl.col("precipitation")
        .max()
        .alias("max_precipitacao"),

        (pl.col("precipitation") > 0)
        .sum()
        .alias("horas_com_chuva"),

        pl.col("precipitation_probability")
        .max()
        .alias("max_prob_chuva"),

        pl.col("relative_humidity_2m")
        .mean()
        .alias("media_umidade"),

        pl.col("relative_humidity_2m")
        .min()
        .alias("min_umidade"),

        pl.col("relative_humidity_2m")
        .max()
        .alias("max_umidade"),

        # PM2.5
        pl.col("pm2_5")
        .max()
        .alias("max_pm2_5"),

        pl.col("pm2_5")
        .mean()
        .alias("media_pm2_5"),

        pl.col("pm2_5")
        .count()
        .alias("horas_com_pm2_5"),

        # PM10
        pl.col("pm10")
        .max()
        .alias("max_pm10"),

        pl.col("pm10")
        .mean()
        .alias("media_pm10"),

        pl.col("pm10")
        .count()
        .alias("horas_com_pm10"),

        # Ozônio
        pl.col("ozone")
        .max()
        .alias("max_ozonio"),

        pl.col("ozone")
        .mean()
        .alias("media_ozonio"),

        pl.col("ozone")
        .count()
        .alias("horas_com_ozonio"),

        # Máxima média móvel de 8 horas
        pl.col("media_movel_8h_ozonio")
        .max()
        .alias("max_media_movel_8h_ozonio"),

        # Cobertura temporal
        pl.len().alias("horas_observadas")

    ).sort(["uf", "date"])

    return radar_resumo_diario


# ============================================================
# ALERTAS INDICATIVOS DE QUALIDADE DO AR
# ============================================================

def gerar_alertas_qualidade_ar(
    df_resumo_diario: pl.DataFrame
) -> pl.DataFrame:

    # Referências PI-2 da Resolução CONAMA 506/2024.
    LIMITE_PM2_5 = 50
    LIMITE_PM10 = 100
    LIMITE_OZONIO = 130

    df_alertas = df_resumo_diario.select(
        "uf",
        "capital",
        "regiao",
        "date",
        "media_pm2_5",
        "media_pm10",
        "max_media_movel_8h_ozonio",
        "horas_com_pm2_5",
        "horas_com_pm10",
        "horas_com_ozonio"
    )

    # Classificação do PM2.5
    df_alertas = df_alertas.with_columns(

        pl.when(pl.col("media_pm2_5").is_null())
        .then(pl.lit("Sem dados"))

        .when(pl.col("media_pm2_5") > LIMITE_PM2_5)
        .then(pl.lit("Acima do PI-2"))

        .otherwise(pl.lit("Dentro do PI-2"))
        .alias("status_pm2_5"),

        # Classificação do PM10
        pl.when(pl.col("media_pm10").is_null())
        .then(pl.lit("Sem dados"))

        .when(pl.col("media_pm10") > LIMITE_PM10)
        .then(pl.lit("Acima do PI-2"))

        .otherwise(pl.lit("Dentro do PI-2"))
        .alias("status_pm10"),

        # Classificação do ozônio
        pl.when(
            pl.col("max_media_movel_8h_ozonio").is_null()
        )
        .then(pl.lit("Sem dados"))

        .when(
            pl.col("max_media_movel_8h_ozonio") > LIMITE_OZONIO
        )
        .then(pl.lit("Acima do PI-2"))

        .otherwise(pl.lit("Dentro do PI-2"))
        .alias("status_ozonio")
    )

    # Classificação geral:
    # considera o pior status entre os três poluentes.
    df_alertas = df_alertas.with_columns(

        pl.when(
            pl.any_horizontal([
                pl.col("status_pm2_5") == "Acima do PI-2",
                pl.col("status_pm10") == "Acima do PI-2",
                pl.col("status_ozonio") == "Acima do PI-2"
            ])
        )
        .then(pl.lit("Acima do PI-2"))

        .when(
            pl.all_horizontal([
                pl.col("status_pm2_5") == "Sem dados",
                pl.col("status_pm10") == "Sem dados",
                pl.col("status_ozonio") == "Sem dados"
            ])
        )
        .then(pl.lit("Sem dados"))

        .when(
            pl.any_horizontal([
                pl.col("status_pm2_5") == "Sem dados",
                pl.col("status_pm10") == "Sem dados",
                pl.col("status_ozonio") == "Sem dados"
            ])
        )
        .then(pl.lit("Dados incompletos"))

        .otherwise(pl.lit("Dentro do PI-2"))
        .alias("status_geral")
    )

    return df_alertas


# ============================================================
# GRAVAÇÃO DOS ARQUIVOS GOLD
# ============================================================

def gravar_parquet_gold(
    pasta_destino: Path,
    nome_arquivo: str,
    dataframe: pl.DataFrame
) -> None:

    pasta_destino.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho_arquivo = pasta_destino / f"gold_{nome_arquivo}.parquet"

    dataframe.write_parquet(caminho_arquivo)


# ============================================================
# ORQUESTRAÇÃO SILVER TO GOLD
# ============================================================

def silver_to_gold(
    pasta_silver: Path,
    pasta_gold: Path,
    caminho_locations: Path
) -> None:

    # 1. Leitura dos dados Silver
    dataset_forecast = ler_dados_silver(
        caminho_silver=pasta_silver,
        nome_arquivo="silver_forecast.parquet"
    )

    dataset_quality = ler_dados_silver(
        caminho_silver=pasta_silver,
        nome_arquivo="silver_air-quality.parquet"
    )

    # 2. Preparação da dimensão de capitais
    dataset_capitais = preparar_dim_capitais(
        caminho_locations=caminho_locations
    )

    # 3. Integração dos dados
    resumo_horario = integrar_dados_horarios(
        df_forecast=dataset_forecast,
        df_air_quality=dataset_quality,
        df_capitais=dataset_capitais
    )

    # 4. Conversão dos fusos horários
    resumo_horario = converter_fuso_radar_horario(
        dataframe_resumo_horario=resumo_horario
    )

    # 5. Cálculo da média móvel de ozônio
    resumo_horario = calcular_media_movel_ozonio(
        df_resumo_horario=resumo_horario
    )

    # 6. Geração do resumo diário
    resumo_diario = gerar_resumo_diario(
        df_resumo_horario=resumo_horario
    )

    # 7. Geração dos alertas
    alertas_qualidade_ar = gerar_alertas_qualidade_ar(
        df_resumo_diario=resumo_diario
    )

    # 8. Gravação dos arquivos Gold

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

    gravar_parquet_gold(
        pasta_destino=pasta_gold,
        nome_arquivo="alertas_qualidade_ar",
        dataframe=alertas_qualidade_ar
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    silver_to_gold(
        pasta_silver=CAMINHO_PASTA_SILVER,
        pasta_gold=CAMINHO_PASTA_GOLD,
        caminho_locations=CAMINHO_LOCATIONS
    )
