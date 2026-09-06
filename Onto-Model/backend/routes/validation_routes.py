from flask import Blueprint, request, jsonify
from services.validation_service import ValidationService

validation_bp = Blueprint('validation', __name__)
validation_service = ValidationService()

@validation_bp.route('/run', methods=['POST'])
def run_validation():
    """执行完整校验"""
    data = request.json
    workspace = data.get('workspace')
    
    if not workspace:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '工作区数据不能为空'
            }
        }), 400
    
    try:
        result = validation_service.validate_workspace(workspace)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_FAILED',
                'message': str(e)
            }
        }), 500
