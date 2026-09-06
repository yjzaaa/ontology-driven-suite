from flask import Blueprint, request, jsonify
from services.reference_service import ReferenceService

reference_bp = Blueprint('reference', __name__)
reference_service = ReferenceService()

@reference_bp.route('/find', methods=['POST'])
def find_references():
    """查找引用关系"""
    data = request.json
    node_type = data.get('nodeType')
    node_id = data.get('nodeId')
    
    if not node_type or not node_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '节点类型和ID不能为空'
            }
        }), 400
    
    try:
        references = reference_service.find_references(node_type, node_id)
        return jsonify({
            'success': True,
            'data': references
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FIND_REFERENCES_FAILED',
                'message': str(e)
            }
        }), 500

@reference_bp.route('/delete-impact', methods=['POST'])
def analyze_delete_impact():
    """分析删除影响"""
    data = request.json
    node_type = data.get('nodeType')
    node_id = data.get('nodeId')
    
    if not node_type or not node_id:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '节点类型和ID不能为空'
            }
        }), 400
    
    try:
        impact = reference_service.analyze_delete_impact(node_type, node_id)
        return jsonify({
            'success': True,
            'data': impact
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ANALYZE_IMPACT_FAILED',
                'message': str(e)
            }
        }), 500
