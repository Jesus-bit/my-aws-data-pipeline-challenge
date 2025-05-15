import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when, regexp_extract, udf
from pyspark.sql.types import IntegerType, FloatType, StringType
import boto3
from datetime import datetime

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 1. Encontrar el archivo más reciente en el bucket raw/
s3 = boto3.client('s3')
bucket_name = 'my-data-challenge-swapi'  # Reemplaza con tu nombre de bucket

response = s3.list_objects_v2(Bucket=bucket_name, Prefix='raw/')
if 'Contents' not in response:
    raise Exception("No hay archivos en el directorio raw/")

# Ordenar por fecha de modificación y obtener el más reciente
latest_file = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]['Key']
input_path = f"s3://{bucket_name}/{latest_file}"

# 2. Leer el archivo JSON
datasource = glueContext.create_dynamic_frame.from_options(
    format_options={"multiline": True},
    connection_type="s3",
    format="json",
    connection_options={
        "paths": [input_path],
        "recurse": True
    },
    transformation_ctx="datasource"
)

# Convertir a DataFrame de Spark para facilitar las transformaciones
df = datasource.toDF()

# 3. Seleccionar solo las columnas necesarias
selected_columns = ["name", "height", "mass", "hair_color", "skin_color", "eye_color", "birth_year", "gender"]
df = df.select(selected_columns)

# 4. Transformaciones

# Función para extraer el año BBY y convertirlo
def extract_birth_year(birth_year):
    if birth_year is None or birth_year == "unknown" or birth_year == "n/a":
        return None
    try:
        # Extraer el número antes de BBY
        num = float(birth_year.replace("BBY", "").strip())
        return int(2000 - num)
    except:
        return None

# Registrar la función como UDF
extract_birth_year_udf = udf(extract_birth_year, IntegerType())

# Aplicar transformaciones
df = df.withColumn(
    "normalized_birth_year",
    extract_birth_year_udf(col("birth_year"))
)

# Convertir mass a numérico y crear mass_lb (1 kg = 2.20462 lbs)
df = df.withColumn(
    "mass_kg",
    when(
        (col("mass").rlike("^\\d+$")) & (col("mass") != "unknown") & (col("mass") != "n/a"),
        col("mass").cast(FloatType())
    ).otherwise(None)
)

df = df.withColumn(
    "mass_lb",
    when(col("mass_kg").isNotNull(), col("mass_kg") * 2.20462).otherwise(None)
)

# Crear gender_id (M, F, N)
df = df.withColumn(
    "gender_id",
    when(col("gender").isin("male", "m"), "M")
    .when(col("gender").isin("female", "f"), "F")
    .otherwise("N")
)

# 5. Filtrar masas > 1000kg
df = df.filter((col("mass_kg").isNull()) | (col("mass_kg") <= 1000))

# 6. Eliminar filas con 3+ campos vacíos/n/a/unknown
def count_null_fields(row):
    null_count = 0
    for field in selected_columns:
        val = row[field]
        if val is None or val in ["unknown", "n/a", ""]:
            null_count += 1
    return null_count < 3

# Filtrar las filas
df = df.rdd.filter(count_null_fields).toDF()

# 7. Seleccionar columnas finales y ordenar
final_columns = [
    "name", "height", "mass_kg", "mass_lb", "hair_color", 
    "skin_color", "eye_color", "birth_year", "normalized_birth_year", 
    "gender", "gender_id"
]

df = df.select(final_columns)

# 8. Guardar como CSV en processed/
output_path = f"s3://{bucket_name}/processed/people_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

df.write.mode("overwrite").format("csv").option("header", "true").save(output_path)

job.commit()
