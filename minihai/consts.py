import uuid

ENVIRONMENT_NAME = "Minihai Environment"
ENVIRONMENT_SLUG = "minihai-environment"
PROJECT_NAME = "minihai-project"

PROJECT_ID = uuid.UUID(fields=[0, 0, 0, 0x42, 42, 0])
ENVIRONMENT_ID = uuid.UUID(fields=[0, 0, 0, 42, 0x42, 0])

USER_ID = 42

LIMITED_USER_DATA = {
    "id": USER_ID,
    "username": "minihai-user",
}

EXPANDED_USER_DATA = {
    **LIMITED_USER_DATA,
    "email": "minihai-user@example.com",
    "first_name": "Minihai",
    "last_name": "User",
}

PROJECT_DATA = {
    "id": PROJECT_ID,
    "name": PROJECT_NAME,
    "description": "",
    "owner": LIMITED_USER_DATA,
    "ctime": "2001-05-11T12:42:42.000000Z",
    "mtime": "2001-05-11T12:42:42.000000Z",
    "url": f"/api/v0/projects/{PROJECT_ID}/",
    "urls": {},
    "execution_count": 0,
    "running_execution_count": 0,
    "queued_execution_count": 0,
    "enabled_endpoint_count": 0,
    "last_execution_ctime": None,
}

ENVIRONMENT_DATA = {
    "allow_personal_usage": True,
    "can_admin": False,
    "description": "",
    "enabled": True,
    "gpu_spec": "",
    "has_gpu": False,
    "id": ENVIRONMENT_ID,
    "name": ENVIRONMENT_NAME,
    "owner": EXPANDED_USER_DATA,
    "per_hour_price_usd": "0.00000",
    "per_user_queue_quota": 0,
    "provider": None,
    "slug": ENVIRONMENT_SLUG,
    "unfinished_job_count": 0,
    "url": f"/api/v0/environments/{ENVIRONMENT_ID}/",
}
