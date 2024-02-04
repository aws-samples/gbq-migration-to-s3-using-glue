# Google Big Query Glue Code
* This pattern uses a AWS Glue Spark Job to incrementally transfer data from multiple tables in an Google Big Query Server to an Amazon Simple Storage Service (Amazon S3) bucket.
* The list of tables to be transferred is provided to the AWS Glue job as a json file
* Database credentials are stored in AWS Secrets Manager.

![](../../media/architecture.png)

### How is Data Organized into Google Cloud?

In Google BigQuery, data is organized into tables within datasets. A dataset is a grouping of related tables, similar to a schema in a relational database. Each table contains rows and columns, similar to a spreadsheet. 

BigQuery supports structured data in the form of SQL tables as well as semi-structured data such as JSON, Avro, ORC, Parquet and more. Tables can be either loaded with data or created as the result of a query, and can be either single-row or multi-row.

Each dataset is associated with a project.   Projects form the basis for creating, enabling, and using all Google Cloud services.

### How is Data migrated to AWS?

AWS Glue is a fully managed extract, transform, and load (ETL) service that makes it easy to prepare and load your data for analytics.  AWS Glue Connectors makes it easy for you to transfer data from SaaS applications and custom data sources to your data lake in Amazon S3. With just a few clicks, you can search and select connectors from the AWS Marketplace and begin your data preparation workflow in minutes.  There is a Google Big Query Connector available in the AWS Marketplace.  Follow this blog to learn more.

### Wildcard Tables:

In Google BigQuery, a wildcard table is a virtual table that represents multiple existing tables. It uses the wildcard character "*" in the table name to match multiple tables. Wildcard tables allow you to query multiple tables as if they were a single table, making it easier to consolidate data from multiple sources. The syntax for a wildcard table is [dataset_name].[table_name_prefix]*. To use a wildcard table in a query, you need to provide a date or timestamp range in the WHERE clause to specify which tables should be included in the query.

### Limitations of the GBQ Connector:

The connector is really helpful when you know which tables to extract.  However, there are limitation when you want to migrate a wildcard table.

In such cases, we need an GBQ Client which would run queries on the datasets to extract tables.  You can specify conditions to the query to extract only specific types of tables.  

In this pattern we will use this query:
```
    dataset_id = f"{parent_project}.{dataset}"

    table_name_pattern = f'{table_map["table_name"]}\\_%'
                
    # Construct the parameterized query
    gbq_query = """
                SELECT table_name 
                FROM `{dataset_id}.INFORMATION_SCHEMA.TABLES` 
                WHERE table_name LIKE @table_name_pattern;
                """

```

This query will basically extract all the table under a dataset which fulfills the applied conditions.

### JSON File Structure:
* is_wildcard_table: True or False – describe if a table is a wildcard
* table_name (Required): The name of the Google Biqtable to be transferred to the S3 Bucket
* starting_date  (Optional): Starting date from where you want to transfer the data
* ending_date  (Optional): Combine it with `starting_date` to get the duration
* days_behind_start (Optional): Number of days you want to go behind to start transferring data
* days_behind_end(Optional): Combine it with `days_behind_start` to get the duration

Either `days_behind_start` is required or `ending_date`

e.g. Lets say if days_behind_start was 3 and days_behind_end was 1 it will load data from 6th Nov to 8th Nov assuming today's date is 9th Nov

Examples can be found under ```glue/config``` folder

