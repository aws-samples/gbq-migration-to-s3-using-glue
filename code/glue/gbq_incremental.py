import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from datetime import datetime, date, timedelta
import logging
from gbq_incremental_lib import get_secrets, parse_tables_parm, obtain_job_connection, fetch_duration
from google.cloud import bigquery
import boto3

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

now = datetime.now()
now_date = now.strftime("%Y%m%d%H%M%S")
now_time = now.strftime("%H%M%S")


def main():
    try:
        args = getResolvedOptions(sys.argv, ['JOB_NAME',
                                     'region_name',
                                     's3_path',
                                     'parent_project',
                                     'tables_file',
                                     'dataset',
                                     'secret_name',
                                     's3_bucket'
                                     ])

        JOB_NAME=args['JOB_NAME']
        job.init(JOB_NAME, args)


        dataset = args['dataset']
        region_name = args['region_name']
        s3_path = args['s3_path']
        parent_project = args['parent_project']
        tables_file = args['tables_file']
        secret_name = args['secret_name']
        s3_bucket = args['s3_bucket']


        logging.info('JOB_NAME: ' + JOB_NAME)
        logging.info('dataset: ' + dataset)
        logging.info('region_name: ' + region_name)
        logging.info('s3_path: ' + s3_path)


        secret = get_secrets(secret_name)

        glue_client = boto3.client('glue')

        # Creating the Google Big Query Client
        gbq_client = bigquery.Client.from_service_account_info(secret)

        # Fetching the time when the data was loaded

        logging.getLogger().setLevel(logging.INFO)
        
        
        # Converting the tables parameter into a list
        table_list = parse_tables_parm(s3_bucket, tables_file)

        # Obtain the Glue Connection Details
        connection = obtain_job_connection(glue_client,JOB_NAME)
    
        # Finding the table map in the list
        for table_map in table_list:
            
            # Fetching the start date and end date for from where the data needs to be transferred
            starting_date, ending_date = fetch_duration(table_map)
            
            start_date_split = starting_date.split('-')    
            start_date = date(int(start_date_split[0]), int(start_date_split[1]), int(start_date_split[2]))
            end_date_split = ending_date.split('-')
            end_date = date(int(end_date_split[0]), int(end_date_split[1]), int(end_date_split[2]))

            is_wildcard_table = table_map['is_wildcard_table'] if 'is_wildcard_table' in table_map else "false"

            """If a table is a wildcard table it means that it will have multiple tables..
            
            For e.g: p_table_* can be p_table_0000000,p_table_0000001 ...etc

            So the function run an SQL Query on GBQ and find tables like p_table_
            """
            
            if is_wildcard_table == "true":
                logging.info("Found is_wildcard_table true, checking available tables with name like '%s'\n",table_map["table_name"])

                gbq_query = r"SELECT table_name FROM `{0}`.{1}.INFORMATION_SCHEMA.TABLES WHERE table_name like '{2}\\_%';".format(parent_project, dataset, table_map["table_name"])
                
                query_job = gbq_client.query(gbq_query)
                
                results = query_job.result()
                
                logging.info("Number of tables found like '%s' is '%s'\n", table_map["table_name"], str(results.total_rows))

                table_whole = (f'{(table_map["table_name"])}_').lower()
                
                landing_path = s3_path + '/test/' + table_whole + '/datetime=' + now_date
                
                for row in results:

                    logging.info("Found Table '%s'\n",row.table_name)
                    table_name = row.table_name
                    
                    start_date = date(int(start_date_split[0]), int(start_date_split[1]), int(start_date_split[2]))
   
                    loop_through_dates(start_date,end_date,is_wildcard_table,parent_project,dataset,table_name,connection,landing_path)
            
            else:
                """If the table is not partitioned it means that the table will have date at the end.
                
                For e.g: table_1_20221021, table_1_20221022 etc.
            
                So it will just loop through the dates from start date to end date and attach the date at the end
                """
                #Looping through the tables from the start date to the end date
                table_name = table_map["table_name"]

                landing_path = s3_path + '/test/' + table_name.lower() + '/datetime='
                loop_through_dates(start_date,end_date,is_wildcard_table,parent_project,dataset,table_name,connection,landing_path)

            
        job.commit()
        logging.info("Job Committed")
    except Exception as err:
        logging.info('Exception occurred "%s"',str(err))
        raise err


def loop_through_dates(start_date,end_date,is_wildcard_table,parent_project,dataset,table_name,connection,landing_path):

    try:
        # Loop through single days
        delta = timedelta(days=1)
        logging.info(table_name)
        logging.info(landing_path)

        logging.info("Looping through the dates")
        
        
        while start_date <= end_date:
            
            if is_wildcard_table  == "true":
                """ 
                If is_wildcard_table it will filter the queries by the column DATE(_PARTITIONTIME)

                This would act like a WHERE STATEMENT

                e.g. SELECT * FROM p_table_0000000 where DATE(_PARTITIONTIME) = <DATE>
                
                """
                filter_queries = f'(DATE(_PARTITIONTIME) = "{start_date.strftime("%Y-%m-%d")}")'
                
                final_table = table_name
                
                final_landing_path = landing_path

                logging.info("Filter is '%s'\n", filter_queries)
            
            else:
                """ 
                If its not_partitioned it will attach a date to the ending of the table_name

                e.g. SELECT * FROM table_1_20221021
                
                """

                loading_date = start_date.strftime("%Y%m%d")
                loading_time = loading_date + now_time
                final_table = table_name + "_" + loading_date
                final_landing_path = landing_path + loading_time
                
            
            table_to_copy = dataset + "." + final_table

            logging.info("Loading data of DATE(_PARTITIONTIME) '%s' of table '%s'\n", start_date, table_to_copy)

            GoogleBigQueryTableToCopy = None
        
            if is_wildcard_table  == "true":
                GoogleBigQueryTableToCopy = (
                glueContext.create_dynamic_frame.from_options(
                connection_type="marketplace.spark",
                connection_options={
                    "table": table_to_copy,
                    "parentProject": parent_project,
                    "connectionName": connection,
                    "filter": filter_queries
                },
                ))
            else:
                GoogleBigQueryTableToCopy = (
                    glueContext.create_dynamic_frame.from_options(
                    connection_type="marketplace.spark",
                    connection_options={
                    "table": table_to_copy,
                    "parentProject": parent_project,
                    "connectionName": connection
                    }
                ))


            logging.info("The schema of table '%s' is '%s' ", table_to_copy, str(GoogleBigQueryTableToCopy.schema()))
            logging.info("The count of table '%s' is '%s' ", table_to_copy, str(GoogleBigQueryTableToCopy.count()))
            logging.info("The landing path is '%s'", final_landing_path)

            if(GoogleBigQueryTableToCopy.count()==0):
                raise ValueError("The following dataset.table was found empty", table_to_copy)


            if(GoogleBigQueryTableToCopy.count()!=0):
                datasink = glueContext.write_dynamic_frame.from_options(
                frame=GoogleBigQueryTableToCopy,
                connection_type="s3",
                format="glueparquet",
                connection_options={"path": final_landing_path},
                format_options={"compression": "snappy"},
                )


            start_date += delta
    
    except Exception as err:
        logging.info('Exception occurred "%s"',str(err))
        raise err


if __name__ == "__main__":
    main()

