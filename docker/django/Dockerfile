FROM nixos/nix
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY default.nix /code/
COPY Pipfile /code/
COPY Pipfile.lock /code/
RUN nix-env -i -f default.nix
RUN pipenv install
COPY . /code/
COPY docker/django/start.sh /start-django.sh
COPY docker/django/start-prod.sh /start-prod-django.sh
RUN chmod +x /start-django.sh
RUN chmod +x /start-prod-django.sh
