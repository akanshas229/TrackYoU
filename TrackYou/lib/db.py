import os

class Databases:
    
    def postgres(self):
        database_url = os.getenv('DATABASE_URL')
        parts = database_url.split('postgres://')[1]
        auth = parts.split('@')[0].split(':')
        hostDetails = parts.split('@')[1].split(':')
        hostname = hostDetails[0]
        portDb = hostDetails[1].split('/')
        data = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': portDb[1],
            'HOST': hostname,
            'PORT': portDb[0],
            'USER': auth[0],
            'PASSWORD': auth[1],
        }
        return data