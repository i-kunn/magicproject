"""
WSGI config for magic project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magic.settings")

application = get_wsgi_application()
import os
import sys

# プロジェクトのパスを追加
path = '/home/kohei/magicproject'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'magicproject.settings'

# 仮想環境のパスを設定
activate_this = '/home/kohei/.virtualenvs/djangoenv/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import os
import sys

# この部分をプロジェクトのパスに置き換えます
path = '/home/yourusername/magicproject'
if path not in sys.path:
    sys.path.append(path)

# この部分をプロジェクトの設定ファイルに置き換えます
os.environ['DJANGO_SETTINGS_MODULE'] = 'magic.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
