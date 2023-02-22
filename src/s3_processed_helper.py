from src.s3_helper import s3_upload_and_local_log
import boto3
import os

def s3_list_buckets():
    s3=boto3.client('s3')
    response=s3.list_buckets()['Buckets']
    return [bucket['Name'] for bucket in response]

def s3_list_prefix_csv_buckets():
    full_list = s3_list_buckets()
    if full_list == []:
        raise ValueError("ERROR: No buckets found")
    for bucket in full_list:
        if "nc-de-databakers-csv-store-" in bucket:
            return bucket
    raise ValueError("ERROR: Prefix not found in any bucket")

def s3_list_prefix_parquet_buckets():
    full_list = s3_list_buckets()
    if full_list == []:
        raise ValueError("ERROR: No buckets found")
    for bucket in full_list:
        if "nc-de-databakers-parquet-store-" in bucket:
            return bucket
    raise ValueError("ERROR: Prefix not found in any bucket")

def s3_csv_processed_setup_success():
    s3=boto3.client('s3')
    bucket = s3_list_prefix_csv_buckets()
    objects = s3.list_objects(Bucket=bucket)['Contents']
    for object in objects:
        if object['Key'] == 'processed_csv_key/setup_success_csv_processed.txt':
            return True
    else:
        raise ValueError("ERROR: Terraform deployment unsuccessful")


def s3_upload_pqt_files_to_csv_processed_key():
    s3=boto3.resource('s3')
    if s3_csv_processed_setup_success():
        pqt_files = os.listdir('pqt_tmp')
        for file in pqt_files:
            s3.Bucket(s3_list_prefix_csv_buckets()).upload_file(f'./pqt_tmp/{file}', f'processed_csv_key/{file}')
    else:
        raise ValueError("ERROR: Terraform deployment unsuccessful")

def s3_upload_pqt_files_to_pqt_input_key():
    s3=boto3.resource('s3')
    if s3_pqt_input_setup_success():
        pqt_files = os.listdir('pqt_tmp')
        for file in pqt_files:
            s3.Bucket(s3_list_prefix_parquet_buckets()).upload_file(f'./pqt_tmp/{file}', f'input_parquet_key/{file}')
    else:
        raise ValueError("ERROR: Terraform deployment unsuccessful")

def s3_upload_pqt_and_delete_csv_files_from_input_key():
    s3_upload_pqt_files_to_csv_processed_key()
    s3=boto3.resource('s3')
    bucket_name = s3_list_prefix_csv_buckets()
    bucket = s3.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix='input_csv_key/'):
        if obj.key.endswith('.csv'):
            obj.delete()

def s3_upload_pqt_and_delete_pqt_files_from_processed_key():
    s3_upload_pqt_files_to_pqt_input_key()
    s3=boto3.resource('s3')
    bucket_name = s3_list_prefix_csv_buckets()
    bucket = s3.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix='processed_csv_key/'):
        if obj.key.endswith('.parquet'):
            obj.delete()

def s3_pqt_input_setup_success():
    s3=boto3.client('s3')
    bucket = s3_list_prefix_parquet_buckets()
    objects = s3.list_objects(Bucket=bucket)['Contents']
    for object in objects:
        if object['Key'] == 'input_parquet_key/setup_success_parquet_input.txt':
            return True
    else:
        raise ValueError("ERROR: Terraform deployment unsuccessful")

def create_pqt_completed_txt_file():
    s3_upload_pqt_and_delete_csv_files_from_input_key()
    if not os.path.exists("pqt_run_number.txt"):
        with open("pqt_run_number.txt", "w") as rn_f:
            rn_f.write("0")
    with open("pqt_run_number.txt", "r+") as rn_f:
        run_num = int(rn_f.read()) + 1
        rn_f.seek(0)
        rn_f.write(str(run_num))
    with open(f"pqt_export_completed.txt", "a+") as f:
        f.write(f'run {run_num}\n')

def s3_pqt_upload_and_log():
    create_pqt_completed_txt_file()
    s3=boto3.resource('s3')
    s3.Bucket(s3_list_prefix_csv_buckets()).upload_file('./pqt_export_completed.txt', 'processed_csv_key/pqt_export_completed.txt')

# def s3_move_pqt_to_parquet_bucket_input_key_and_delete_parquet_from_csv_bucket_processed_key():
#     s3_upload_pqt_and_delete_csv_files_from_input_key()
#     s3=boto3.resource('s3')
#     bucket_name=s3_list_prefix_csv_buckets()