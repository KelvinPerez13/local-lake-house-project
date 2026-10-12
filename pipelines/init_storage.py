from botocore.exceptions import ClientError
from pipelines.common import s3, bucket

def main():
    client = s3()
    try:
        client.head_bucket(Bucket=bucket())
    except ClientError as exc:
        if exc.response['Error']['Code'] not in ('404', 'NoSuchBucket'):
            raise
        client.create_bucket(Bucket=bucket())
    print('Bucket pronto:', bucket())

if __name__ == '__main__':
    main()
