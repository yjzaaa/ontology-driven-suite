from flask import Blueprint, request, jsonify
from services.workspace_service import WorkspaceService

workspace_bp = Blueprint('workspace', __name__)
workspace_service = WorkspaceService()

@workspace_bp.route('/scan', methods=['POST'])
def scan_workspaces():
    """扫描候选工作区目录"""
    data = request.json or {}
    root = data.get('root')
    max_depth = int(data.get('maxDepth', 4))

    try:
        candidates = workspace_service.scan_workspaces(root, max_depth)
        return jsonify({
            'success': True,
            'data': candidates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'WORKSPACE_SCAN_FAILED',
                'message': str(e)
            }
        }), 500


@workspace_bp.route('/open', methods=['POST'])
def open_workspace():
    """打开工作区"""
    data = request.json
    directory = data.get('directory')
    
    if not directory:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '目录路径不能为空'
            }
        }), 400
    
    try:
        workspace = workspace_service.open_workspace(directory)
        return jsonify({
            'success': True,
            'data': workspace
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'WORKSPACE_OPEN_FAILED',
                'message': str(e)
            }
        }), 500

@workspace_bp.route('/save', methods=['POST'])
def save_workspace():
    """保存工作区"""
    data = request.json
    workspace = data.get('workspace')
    options = data.get('options', {})
    
    if not workspace:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '工作区数据不能为空'
            }
        }), 400
    
    try:
        result = workspace_service.save_workspace(
            workspace,
            validate_before_save=options.get('validateBeforeSave', True)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'WORKSPACE_SAVE_FAILED',
                'message': str(e)
            }
        }), 500

@workspace_bp.route('/current', methods=['GET'])
def get_current_workspace():
    """获取当前工作区"""
    if workspace_service.current_workspace:
        return jsonify({
            'success': True,
            'data': workspace_service.current_workspace
        })
    else:
        return jsonify({
            'success': False,
            'error': {
                'code': 'NO_WORKSPACE',
                'message': '当前没有打开的工作区'
            }
        }), 404
