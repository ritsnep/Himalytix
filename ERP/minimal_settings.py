SECRET_KEY = 'test'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'tenancy',
    'accounting',
    'usermanagement',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'