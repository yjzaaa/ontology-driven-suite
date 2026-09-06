from flask import Flask
from flask_cors import CORS
from routes.workspace_routes import workspace_bp
from routes.validation_routes import validation_bp
from routes.reference_routes import reference_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(workspace_bp, url_prefix='/api/workspace')
app.register_blueprint(validation_bp, url_prefix='/api/validation')
app.register_blueprint(reference_bp, url_prefix='/api/references')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
