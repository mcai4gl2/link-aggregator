# Link Aggregator

There are a lot of web links I read but either didn't get time to finish or found interesting and want to check later. I usually save them in Chrome tabs or paste them to Notion, Notepad++ or emails. They however tend to get lost over time. 

Link Aggregator is trying to solve this problem by saving these links to github pages organized by dates. An email address is setup to receive the links of interest. The aggregator then fetch the title of the link and save to github repo.

More implementation details:
- Receving email account is setup in Amazon aws with SES
- Email content is saved to S3 bucket when recveived
- Link Aggregator program runs periodically and reads from S3 bucket for all emails
- Link Aggregator updates github via HTTP API

#### Local Development Setup

Development environment can be setup using docker with the following steps:
- Start the dev environment with `docker-compose up -d`
- SSH to dev image to develop with `docker-compose exec dev /bin/bash`. Code shall be mounted to `/work`

Before development, updating `docker-compose.override.yml` to have linux user's id and group id.

To run tests, run `docker-compose --profile test up --exit-code-from test`. The code uses `localstack` and `mock-server` for S3 integration testing and github API integration testing respectively.

#### Running Aggregator

To run the aggregator, the following environment variables need to be set:
| Environment Variable   | Purpose                                        |
|------------------------|------------------------------------------------|
| AWS_ACCESS_KEY_ID      | s3 access key id                               |
| AWS_SECRET_ACCESS_KEY  | s3 secret access key                           |
| AWS_DEFAULT_REGION     | s3 region. Default to us-east-1 if not set     |
| AWS_BUCKET_NAME        | s3 bucket name                                 |
| FROM_WHITE_LIST        | comma separate list for permitted email sender |
| GITHUB_AUTH_TOKEN      | github auth token for updating github pages    |
