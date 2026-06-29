"""Package configuration for the Module 6 GradCafe microservice application."""

from setuptools import find_packages, setup

setup(
    name="gradcafe-microservices",
    version="1.0.0",
    description="Dockerized GradCafe Flask, RabbitMQ, worker, and PostgreSQL application",
    author="Jonah Thomas",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "beautifulsoup4",
        "flask",
        "lxml",
        "pika",
        "psycopg[binary]",
        "python-dotenv",
    ],
)