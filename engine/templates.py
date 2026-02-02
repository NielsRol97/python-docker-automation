def docker_compose_yml(project_name: str) -> str:
    return """
services:
  app:
    build:
      context: .
      dockerfile: docker/php/Dockerfile
    working_dir: /var/www/html
    volumes:
      - ./:/var/www/html
    depends_on:
      - mysql
    networks:
      - laravel

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./:/var/www/html
      - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - app
    networks:
      - laravel

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: laravel
      MYSQL_USER: laravel
      MYSQL_PASSWORD: secret
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - laravel

  phpmyadmin:
    image: phpmyadmin:5
    environment:
      PMA_HOST: mysql
      PMA_PORT: 3306
      PMA_USER: laravel
      PMA_PASSWORD: secret
    ports:
      - "8080:80"
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - laravel

  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "8025:8025"
      - "1025:1025"
    networks:
      - laravel

volumes:
  mysql-data:

networks:
  laravel:
    driver: bridge
"""





def nginx_default_conf() -> str:
    return r"""server {
  listen 80;
  server_name localhost;
  root /var/www/html/public;

  index index.php index.html;

  location / {
    try_files $uri $uri/ /index.php?$query_string;
  }

  location ~ \.php$ {
    include fastcgi_params;
    fastcgi_pass app:9000;
    fastcgi_index index.php;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    fastcgi_param PATH_INFO $fastcgi_path_info;
  }

  location ~ /\. {
    deny all;
  }
}
"""


def php_dockerfile() -> str:
    # Minimal but sane PHP-FPM image for Laravel
    return r"""FROM php:8.3-fpm-alpine

# System deps
RUN apk add --no-cache \
    bash \
    curl \
    git \
    unzip \
    libzip-dev \
    icu-dev \
    oniguruma-dev \
    zlib-dev \
    linux-headers \
    $PHPIZE_DEPS

# PHP extensions commonly needed by Laravel
RUN docker-php-ext-install \
    pdo_mysql \
    mbstring \
    intl \
    zip \
    opcache

# Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# PHP overrides
COPY docker/php/zz-overrides.ini /usr/local/etc/php/conf.d/zz-overrides.ini

WORKDIR /var/www/html

# Optional: keep container running even if no command is provided (php-fpm default)
CMD ["php-fpm"]
"""


def php_ini_overrides() -> str:
    return r"""memory_limit=512M
upload_max_filesize=64M
post_max_size=64M
max_execution_time=120

opcache.enable=1
opcache.enable_cli=1
opcache.validate_timestamps=1
opcache.revalidate_freq=0
"""
