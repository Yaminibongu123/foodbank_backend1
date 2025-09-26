from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import get_config
from database import db
from auth import init_auth
from routes import api
import logging
import os
import mysql.connector

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api') 

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    cfg = get_config()
    app.config.from_object(cfg)
    
    # Database configuration test
    db_config = {
        'host': app.config['MYSQL_HOST'],
        'user': app.config['MYSQL_USER'],
        'password': app.config['MYSQL_PASSWORD'],
        'database': app.config['MYSQL_DB'],
        'port': app.config['MYSQL_PORT']
    }
    
    # Test database connection
    try:
        connection = mysql.connector.connect(**db_config)
        print("✅ Database connected successfully")
        connection.close()
    except mysql.connector.Error as err:
        print(f"❌ Error connecting to MySQL: {err}")
        return None
    
    # Initialize extensions
    CORS(app, supports_credentials=True)
    init_auth(app)
    
    # Initialize database
    with app.app_context():
        db.initialize_database()
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    # Serve static files - FIXED VERSION
    @app.route('/')
    def serve_frontend():
        return send_from_directory('../frontend', 'login.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        # If it's an API request that doesn't exist, return 404
        if path.startswith('api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        
        # Serve frontend files
        frontend_path = '../frontend'
        full_path = os.path.join(frontend_path, path)
        
        # Check if the file exists
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(frontend_path, path)
        
        # If it's a directory or doesn't have extension, try adding .html
        if not os.path.splitext(path)[1]:  # No file extension
            html_path = path + '.html'
            html_full_path = os.path.join(frontend_path, html_path)
            if os.path.exists(html_full_path):
                return send_from_directory(frontend_path, html_path)
        
        # For SPA (Single Page Application) routing, serve index.html
        # This allows frontend routing to work
        index_path = os.path.join(frontend_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_path, 'index.html')
        
        # Fallback to login page
        return send_from_directory(frontend_path, 'login.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("Starting Food Bank Application...")
    
    # Set environment variables
    os.environ['MYSQL_USER'] = 'foodbank_user'
    os.environ['MYSQL_PASSWORD'] = 'password123'
    os.environ['MYSQL_DB'] = 'foodbank_db'
    os.environ['MYSQL_HOST'] = 'localhost'
    os.environ['MYSQL_PORT'] = '3306'
    os.environ['SECRET_KEY'] = 'your-secret-key-here'
    os.environ['FLASK_ENV'] = 'development'
    
    app = create_app()
    
    if app is None:
        print("❌ Failed to start application")
        exit(1)
    
    print("Database initialized successfully")
    print("Server running on http://localhost:5090")
    
    app.run(debug=True, host='0.0.0.0', port=5090)