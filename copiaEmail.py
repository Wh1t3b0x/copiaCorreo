import json
import boto3
import re
from monday import MondayClient
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "Monday_API"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see

        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

        raise e

    # Decrypts secret using the associated KMS key.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    return json.loads(get_secret_value_response["SecretString"])

#se asigna la key y los ids necesarios
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
monday_api_key = get_secret()["monday_api"]
mon = MondayClient(monday_api_key)
board_id = "3549157032"
column_id = "conectar_tableros60"


def syncchallenge(event: dict):
    try:
        event_body = json.loads(event["body"])
        challenge = {"challenge": event_body["challenge"]}
        return challenge
    except Exception as e:
        return


def lambda_handler(event, context):
    if challenge := syncchallenge(event):
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "body": json.dumps(challenge),
            "headers": {"content-type": "application/json"},
        }

    evento = json.loads(event["body"])["event"]
    #se toma el id del pulso y el texto en el encargado
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    pulso_id = evento["pulseId"]
    boardId = evento["boardId"]
    columnas = mon.items.fetch_items_by_id(pulso_id)["data"]["items"][0]["column_values"]

    encargado = None
    for columna in columnas:
        if columna["id"] == column_id:
            encargado = columna["text"]

    #se asignan las busquedas de los correos a variables
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    updatesBoardAdministrativo = mon.updates.fetch_updates_for_item(boardId, pulso_id)["data"]["boards"][0]["items"][0]["updates"]

    html = mon.items.fetch_items_by_column_value(board_id, "name", encargado)["data"]["items_by_column_values"][0]["updates"][0]["body"]

    #se modifican los textos para poder comparar solo su contenido
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    bandera = False
    for update in updatesBoardAdministrativo:
        texto1_modificado = re.sub(r"/resources/\d+/", "/resources/ID/", update["body"])
        texto1_modificado = re.sub(r'data-asset_id="\d+"', 'data-asset_id="ID"', texto1_modificado)
        texto2_modificado = re.sub(r"/resources/\d+/", "/resources/ID/", html)
        texto2_modificado = re.sub(r'data-asset_id="\d+"', 'data-asset_id="ID"', texto2_modificado)
        if texto1_modificado == texto2_modificado:
            bandera = True
            break
    
    #si el texto no existia dentro de updatesBoardAdministrativo se crea una copia
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    if not bandera:
        mon.updates.create_update(pulso_id, html)

    exit()