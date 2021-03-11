FROM nginx
RUN mkdir /dist_django
# # Add the Nginx configuration file
# ADD ./nginx/nginx.conf /etc/nginx/nginx.conf
# Copy over static assets from the client application
COPY ./dist_gui /usr/share/nginx/html
COPY docker/nginx/start.sh /start.sh
RUN chmod +x /start.sh
