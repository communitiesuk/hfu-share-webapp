#!/bin/bash

BUCKET_NAME=${FILE_DOWNLOAD_S3_BUCKET_NAME:-hfu-webapp-attachments-local}
REGION=${AWS_REGION:-eu-west-2}

awslocal s3api \
create-bucket --bucket "$BUCKET_NAME" \
--create-bucket-configuration LocationConstraint="$REGION" \
--region "$REGION"

# Create temporary files with content
echo "UK Parental Consent Form" > /tmp/uk_parental_consent.txt
echo "Ukraine Parental Consent Form" > /tmp/ukraine_parental_consent.txt
echo "Interaction attachment" > /tmp/interaction_attachment.txt
echo "Comment attachment" > /tmp/comment_attachment.txt

# Upload the files to the S3 bucket
awslocal s3 cp /tmp/uk_parental_consent.txt s3://"$BUCKET_NAME"/uams/uk-form-id/uk_parental_consent.txt
awslocal s3 cp /tmp/ukraine_parental_consent.txt s3://"$BUCKET_NAME"/uams/ukr-form-id/ukraine_parental_consent.txt
awslocal s3 cp /tmp/interaction_attachment.txt s3://"$BUCKET_NAME"/interactions/interaction-file-id/file.txt
awslocal s3 cp /tmp/comment_attachment.txt s3://"$BUCKET_NAME"/comments/comment_attachment.txt

# Clean up temporary files
rm /tmp/uk_parental_consent.txt /tmp/ukraine_parental_consent.txt /tmp/interaction_attachment.txt /tmp/comment_attachment.txt
