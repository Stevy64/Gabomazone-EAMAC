# GabomaZone
My multivendor app just like LeBonCoin

# Create venv
virtualenv venv-gabomazone
source venv-gabomazone/bin/activate (Linux)
source venv-gabomazone/Script/activate (Windows)

# Install Requirements
pip install -r requirements.txt

# Small fixes to do
1) Replace 'ugettext' by 'gettext' library
2) Replace 'force_text' by 'force_str'
3) Make sure django and pillow libs versions are compatible

# Launch server (in virtualenv)
python3 manage.py runserver 8001

# Docker
1) Create a Dockerfile with minimal packages based from official Python image
2) run cmd > ' docker build -t gabomazone-app . ' ## docker build -t <containername> . -f <mycustomdockerfile>.Dockerfile
3) run cmd > ' docker run -it --rm --name my-running-gabomazone-app my-gabomazone-app '


# Netlify : Deploy Static Django Site using Distill and CacheKiller
https://pypi.org/project/django-distill/

# PythonAnyWhere Deployment
1) Deployment steps : https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/
2) Collect Static files : https://help.pythonanywhere.com/pages/DjangoStaticFiles


