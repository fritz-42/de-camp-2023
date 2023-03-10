
from path import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta

@task( retries = 1, cache_key_fn = task_input_hash, cache_expiration = timedelta(days = 1) )
def fetch( dataset_url: str ) -> pd.DataFrame:
    """Read data from WEB into pandas DataFrame"""

    df = pd.read_csv( dataset_url )
    return df

@task( log_prints = True )
def clean( df = pd.DataFrame ) -> pd.DataFrame:
    """Fix data format issues"""
    # df['tpep_pickup_datetime']  = pd.to_datetime( df['tpep_pickup_datetime'] )
    # df['tpep_dropoff_datetime'] = pd.to_datetime( df['tpep_dropoff_datetime'] )

    print( df.head(2) )
    print( f"columns: {df.dtypes}" )
    print( f"rows: {len(df)}" )
    return df

@task( log_prints = True )
def write_local( df: pd.DataFrame, color: str, dataset_file: str ) -> Path:
    """Write DataFrame out locally as parquet file"""
    path = Path( f"/tmp/data/{color}/{dataset_file}.parquet" )
    print( f"write data to path: {path}" )
    df.to_parquet( path, compression = 'gzip' )
    return path

@task()
def write_gcs( path: Path ) -> None:
    """ Upload local parquet file to GCS"""

    # make sure: GCS Bucket is configured as described in:
    # week-02/google_cloud_storage/HOWTO_PREFECT_GOOGLE_CLOUDE_STORAGE
    gcp_cloud_storage_bucket_block = GcsBucket.load( "de-camp" )

    gcp_cloud_storage_bucket_block.upload_from_path( from_path = path,
                                                     to_path = path )
    return

@flow()
def etl_web_to_gcs( year: int, month: int, color: str ) -> None:
    """The main ETL function"""
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url  = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"

    df = fetch( dataset_url )
    df_clean = clean( df )
    path = write_local( df_clean, color, dataset_file )
    write_gcs( path )

@flow()
def etl_parent_flow( months: list[int] = [1, 2], year: int = 2021, color: str = "yellow" ):

    for month in months:
        # call subflow
        etl_web_to_gcs( year, month, color )

if __name__ == '__main__':
    color = "green"
    months = [11]
    year = 2020

    etl_parent_flow( months, year, color )
