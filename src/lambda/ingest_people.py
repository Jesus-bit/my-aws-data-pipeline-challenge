import json
import boto3
import urllib3
from datetime import datetime
import os

# Inicializamos el cliente de S3
s3 = boto3.client('s3')
http = urllib3.PoolManager()

# Puedes definir el nombre de bucket aquí o usar una variable de entorno
BUCKET_NAME = os.environ.get("BUCKET_NAME")  # <-- cámbialo si es necesario

def lambda_handler(event, context):
    url = "https://swapi.info/api/people"

    try:
        # Llamamos a la API
        response = http.request('GET', url)

        if response.status != 200:
            raise Exception(f"Error al obtener datos: código {response.status}")
        
        data = json.loads(response.data.decode('utf-8'))

        # Generamos el timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        filename = f"raw/people-{timestamp}.json"

        # Guardamos en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Datos guardados exitosamente",
                "filename": filename
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
