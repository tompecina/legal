import os
import sys

sys.path.append('/var/www/django/legal')

__file__ = "/var/www/django/legal/venv-legal/bin/activate"

old_os_path = os.environ['PATH']
os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + \
                     os.pathsep + \
                     old_os_path
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys.platform == 'win32':
    site_packages = os.path.join(base, 'Lib', 'site-packages')
else:
    site_packages = os.path.join(
        base,
        'lib',
        'python{0.major:d}.{0.minor:d}'.format(sys.version_info),
        'site-packages')
prev_sys_path = list(sys.path)
import site
site.addsitedir(site_packages)
sys.real_prefix = sys.prefix
sys.prefix = base
# Move the added items to the front of the path:
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

os.environ['DJANGO_SETTINGS_MODULE'] = 'common.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
