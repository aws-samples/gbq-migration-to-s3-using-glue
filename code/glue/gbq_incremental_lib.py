from awsglue.transforms import *
from datetime import datetime, timedelta
import logging
import boto3
import json

def obtain_job_connection(gc, jn):
    """For parm Glue Job Name, return the name of the first Job Connection associated with it"""
    get_job_response = gc.get_job(JobName=jn)

    connection = get_job_response['Job']['Connections']['Connections'][0]       # Take the first Job Connection.
    return connection

def get_secrets(secret_name: str) -> str:
    """ Fetches the secrets for the Secret Manager - JSON Credential for the Service Account

    Args:
        secret_name (str): The name of the Secrets in Secrets Manager
    Raises:
        err: error if the secrets cannot be found
    Returns:
        bool: Returns the secrets
    """
    try:
        sc_client = boto3.client('secretsmanager')
        secret_response = sc_client.get_secret_value(
            SecretId= secret_name
        )
        secret_json = secret_response['SecretString']
        secret = json.loads(secret_json)
        return secret
    except Exception as e:
        logging.info('Exception occurred "%s"',str(e))
        raise e

def parse_tables_parm(bucket: str, key:str) -> list:
    """For parm job parameter, fetch the JSON File from the S3 Bucket
    Args:
        bucket (str): The S3 Bucket where the JSON File can be found
        key (str): The Key of the JSON File
    Raises:
        err: error if the file cannot be found
    Returns:
        list: Returns the content of config file into list
    """
    try:
        s3_client = boto3.client("s3")
        content_object = s3_client.get_object(Bucket=bucket, Key=key)
        json_content = json.loads(content_object['Body'].read())
    except Exception as e:
        logging.info('Exception occurred "%s"',str(e))
        raise e
    tl = list(json_content)
    logging.info(tl)
    return tl

def fetch_duration(table_map):
    try:
        """ This function looks at the input parameter and fetches the starting_date and ending_date from the parameter"
        Args:
            table_map (str): JSON Object having the parameters
        Raises:
            err: error if the JSON Object cannot be read
        Returns:
            str: Returns the starting date and ending date
        """

        days_behind_start = table_map['days_behind_start'] if 'days_behind_start' in table_map else None

        days_behind_end = table_map['days_behind_end'] if 'days_behind_end' in table_map else None

        starting_date = table_map['starting_date'] if 'starting_date' in table_map else None

        ending_date = table_map['ending_date'] if 'ending_date' in table_map else None
    
        constant_time_format = "%Y-%m-%d"

        if days_behind_start != None and days_behind_end != None:
            starting_date = (datetime.today() - timedelta(days=days_behind_start)).strftime(constant_time_format)
            ending_date =  (datetime.today() - timedelta(days=days_behind_end)).strftime(constant_time_format)

        elif days_behind_start != None:
            days_behind_end = days_behind_start
            starting_date = (datetime.today() - timedelta(days=days_behind_start)).strftime(constant_time_format)
            ending_date =  (datetime.today() - timedelta(days=days_behind_end)).strftime(constant_time_format)

        elif ending_date == None:
            raise ValueError('Please provide a value for days_behind_start or ending_date')

        elif starting_date == None:
            starting_date = ending_date

        return starting_date, ending_date
        
    except Exception as e:
        logging.info('Exception occurred "%s"',str(e))
        raise e

