
import os.path
from path import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta

@task( retries = 1, cache_key_fn = task_input_hash, cache_expiration = timedelta(days = 1) )
def fetch( dataset_url: str ) -> pd.DataFrame:
    """Read data from WEB into pandas DataFrame"""

    print( f"fetch file from: {dataset_url}" )

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
def write_local( df: pd.DataFrame, dataset_file: str ) -> Path:
    """Write DataFrame out locally as parquet file"""
    path = Path( f"/tmp/{dataset_file}" )
    print( f"write data to path: {path}" )
    df.to_csv( path, compression = 'gzip' )
    return path

@task()
def write_gcs( path: Path ) -> None:
    """ Upload local parquet file to GCS"""

    # make sure: GCS Bucket is configured as described in:
    # week-02/google_cloud_storage/HOWTO_PREFECT_GOOGLE_CLOUDE_STORAGE
    gcp_cloud_storage_bucket_block = GcsBucket.load( "de-camp" )

    gcp_cloud_storage_bucket_block.upload_from_path( from_path = path,
                                                     to_path = os.path.basename(path) )
    return

@flow()
def etl_web_to_gcs( year: int, month: int ) -> None:
    """The main ETL function"""
    dataset_file = f"fhv_tripdata_{year}-{month:02}.csv.gz"
    dataset_url  = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/fhv/{dataset_file}"

    print( f"dataset url: {dataset_url}" )

    df = fetch( dataset_url )
    df_clean = clean( df )
    path = write_local( df_clean, dataset_file )
    write_gcs( path )

@flow()
def etl_parent_flow( months: list[int] = [1], year: int = 2019 ):

    for month in months:
        etl_web_to_gcs( year, month )

if __name__ == '__main__':
    months = list(range(1, 13))
    year = 2019

    print( f"downloading data for: year: {year} months: {months}" )

    etl_parent_flow( months, year )
