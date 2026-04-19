from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app import db
from app.models import Task, Category, Pomodoro
from datetime import datetime, timedelta

api = Blueprint('api', __name__)

# Helper to check ownership
def get_user_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        return task
    return None

# ==================== TASKS ====================

@api.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get all tasks for current user with optional filters"""
    filter_type = request.args.get('filter', 'all')
    category_id = request.args.get('category', type=int)
    priority = request.args.get('priority')
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if filter_type == 'active':
        query = query.filter_by(is_completed=False)
    elif filter_type == 'completed':
        query = query.filter_by(is_completed=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if priority:
        query = query.filter_by(priority=priority)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks]
    })

@api.route('/tasks', methods=['POST'])
@login_required
def create_task():
    """Create a new task"""
    data = request.get_json()
    
    task = Task(
        title=data.get('title'),
        description=data.get('description'),
        notes=data.get('notes'),
        priority=data.get('priority', 'Medium'),
        due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
        category_id=data.get('category_id'),
        user_id=current_user.id
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'task': task.to_dict()}), 201

@api.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get a specific task"""
    task = get_user_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({'task': task.to_dict()})

@api.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update a task"""
    task = get_user_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'notes' in data:
        task.notes = data['notes']
    if 'priority' in data:
        task.priority = data['priority']
    if 'due_date' in data:
        task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'category_id' in data:
        task.category_id = data['category_id']
    if 'is_completed' in data:
        task.is_completed = data['is_completed']
    
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'task': task.to_dict()})

@api.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    task = get_user_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'message': 'Task deleted'})

@api.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Toggle task completion status"""
    task = get_user_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task.is_completed = not task.is_completed
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'task': task.to_dict()})

# ==================== SUBTASKS ====================

@api.route('/tasks/<int:task_id>/subtasks', methods=['GET'])
@login_required
def get_subtasks(task_id):
    """Get all subtasks for a task"""
    task = get_user_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    subtasks = task.subtasks.all()
    return jsonify({'subtasks': [s.to_dict() for s in subtasks]})

@api.route('/tasks/<int:task_id>/subtasks', methods=['POST'])
@login_required
def create_subtask(task_id):
    """Create a subtask"""
    task = get_user_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    from app.models import Subtask
    subtask = Subtask(title=data['title'], task_id=task_id)
    db.session.add(subtask)
    db.session.commit()
    
    return jsonify({'subtask': subtask.to_dict()}), 201

@api.route('/subtasks/<int:subtask_id>', methods=['PUT'])
@login_required
def update_subtask(subtask_id):
    """Update a subtask"""
    from app.models import Subtask
    subtask = Subtask.query.get(subtask_id)
    if not subtask:
        return jsonify({'error': 'Subtask not found'}), 404
    
    task = Task.query.get(subtask.task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if 'title' in data:
        subtask.title = data['title']
    if 'is_completed' in data:
        subtask.is_completed = data['is_completed']
    
    db.session.commit()
    return jsonify({'subtask': subtask.to_dict()})

@api.route('/subtasks/<int:subtask_id>', methods=['DELETE'])
@login_required
def delete_subtask(subtask_id):
    """Delete a subtask"""
    from app.models import Subtask
    subtask = Subtask.query.get(subtask_id)
    if not subtask:
        return jsonify({'error': 'Subtask not found'}), 404
    
    task = Task.query.get(subtask.task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(subtask)
    db.session.commit()
    return jsonify({'message': 'Subtask deleted'})

# ==================== CATEGORIES ====================

@api.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get all categories for current user"""
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify({'categories': [c.to_dict() for c in categories]})

@api.route('/categories', methods=['POST'])
@login_required
def create_category():
    """Create a new category"""
    data = request.get_json()
    
    category = Category(
        name=data['name'],
        color=data.get('color', '#3498db'),
        icon=data.get('icon', '📚'),
        user_id=current_user.id
    )
    db.session.add(category)
    db.session.commit()
    
    return jsonify({'category': category.to_dict()}), 201

@api.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """Update a category"""
    category = Category.query.get(category_id)
    if not category or category.user_id != current_user.id:
        return jsonify({'error': 'Category not found'}), 404
    
    data = request.get_json()
    if 'name' in data:
        category.name = data['name']
    if 'color' in data:
        category.color = data['color']
    if 'icon' in data:
        category.icon = data['icon']
    
    db.session.commit()
    return jsonify({'category': category.to_dict()})

@api.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.get(category_id)
    if not category or category.user_id != current_user.id:
        return jsonify({'error': 'Category not found'}), 404
    
    # Remove category from tasks
    Task.query.filter_by(category_id=category_id).update({'category_id': None})
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Category deleted'})

# ==================== ANALYTICS ====================

@api.route('/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Get analytics data for the current user"""
    from app.utils.analytics import get_user_stats
    stats = get_user_stats(current_user.id)
    return jsonify(stats)

@api.route('/pomodoros', methods=['GET'])
@login_required
def get_pomodoros():
    """Get pomodoro history"""
    days = request.args.get('days', 7, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    pomodoros = Pomodoro.query.filter(
        Pomodoro.user_id == current_user.id,
        Pomodoro.completed_at >= start_date
    ).all()
    
    return jsonify({
        'pomodoros': [p.to_dict() for p in pomodoros],
        'total': len(pomodoros),
        'total_minutes': sum(p.duration for p in pomodoros)
    })

@api.route('/pomodoros', methods=['POST'])
@login_required
def create_pomodoro():
    """Log a completed pomodoro"""
    data = request.get_json()
    
    pomodoro = Pomodoro(
        duration=data.get('duration', 25),
        user_id=current_user.id,
        task_id=data.get('task_id'),
        was_completed=data.get('was_completed', True)
    )
    db.session.add(pomodoro)
    db.session.commit()
    
    return jsonify({'pomodoro': pomodoro.to_dict()}), 201