from app import create_app

# Create the Flask application using application factory.
app = create_app()

if __name__ == '__main__':
    # Run local development server on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)