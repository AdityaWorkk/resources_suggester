from flask import Flask, render_template
from flask_cors import CORS
from app.core.config import settings
from app.v1.endpoints.routes import v1_api

def create_app():
    app = Flask(__name__, 
                static_folder='app/v1/static', 
                template_folder='app/v1/static/templates')
    
    # Enable CORS for frontend-backend communication
    CORS(app)

    # Register the V1 Blueprint
    # This makes all routes in routes.py available at /api/v1/...
    app.register_blueprint(v1_api, url_prefix='/api/v1')

    # Basic route to serve the main HTML page
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/admin')
    def admin_page():
        return render_template('admin.html')
    
    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    return app

app = create_app()

if __name__ == "__main__":
    # Updated port to 8000
    app.run(host='0.0.0.0', port=8000, debug=True)
