
"""Package configuration for the Module 5 GradCafe application."""



from setuptools import find_packages, setup





setup(

    name="gradcafe-analysis",

    version="1.0.0",

    description="Secure GradCafe data collection and Flask analysis application",

    author="Jonah Thomas",

    packages=find_packages(),

    python_requires=">=3.10",

    install_requires=[

        "beautifulsoup4",

        "flask",

        "lxml",

        "psycopg[binary]",

        "python-dotenv",

    ],

)

