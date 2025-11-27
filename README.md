# GabomaZone
My multivendor app just like LeBonCoin and Amazon

# Lancer le projet
Lancer le fichier 'launcher.sh'
Assurez vous que le fichier est exécutable

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

# Remove an app (module) from the project
1) Revert all migrations for the app : python manage.py migrate <app_name> zero
2) Remove app : INSTALLED_apps, urls.py
3) Deploy : python manage.py makemigrations // python manage.py migrate
4) Delete the app folder

# Loading image (TO BE REMOVED)
/home/stevy64/Developpement/DjangoDev/Gabomazone-EAMAC/gabomazone-app/static/assets/imgs/theme/loading.gif
