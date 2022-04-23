import boto3


def test_create_and_upload_to_bucket():
    session = boto3.Session(aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")
    s3 = session.resource('s3', endpoint_url='http://localstack:4566')
    s3.create_bucket(Bucket='testbucket')
    response = s3.Object('testbucket', 'test.txt').put(Body='Hello World!')
    print(response)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
    bucket = s3.Bucket('testbucket')
    files = []
    for file in bucket.objects.all():
        files.append(file)
    assert len(files) == 1
    assert files[0].key == 'test.txt'
    file = s3.Object('testbucket', 'test.txt')
    content = file.get()['Body'].read().decode('utf-8')
    assert content == 'Hello World!'
    assert file.delete()['ResponseMetadata']['HTTPStatusCode'] == 204
    assert bucket.delete()['ResponseMetadata']['HTTPStatusCode'] == 204
