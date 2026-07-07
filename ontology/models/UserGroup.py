from django.db import models


class UserGroup(models.Model):
    id = models.TextField(primary_key=True, db_column="id")
    immediate_member_count = models.BigIntegerField(
        null=True, db_column="immediate_member_count"
    )
    name = models.TextField(null=True, db_column="name")
    user_count = models.BigIntegerField(null=True, db_column="user_count")
