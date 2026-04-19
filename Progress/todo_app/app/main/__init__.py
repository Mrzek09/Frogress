from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Task, Category, Subtask, Pomodoro
from app.forms import TaskForm, CategoryForm, SubtaskForm
from app.utils.analytics import get_user_stats
from datetime import datetime, timedelta
import json

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    # Get filter parameters
    filter_type = request.args.get('filter', 'all')
    category_id = request.args.get('category', type=int)
    priority = request.args.get('priority')
    search_query = request.args.get('q', '').strip()
    
    # Base query - only current user's tasks
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if filter_type == 'active':
        query = query.filter_by(is_completed=False)
    elif filter_type == 'completed':
        query = query.filter_by(is_completed=True)
    elif filter_type == 'today':
        today = datetime.utcnow().date()
        query = query.filter(Task.due_date >= datetime.combine(today, datetime.min.time()),
                            Task.due_date <= datetime.combine(today, datetime.max.time()))
    elif filter_type == 'overdue':
        query = query.filter(Task.due_date < datetime.utcnow(), Task.is_completed == False)
    
    # Category filter
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Priority filter
    if priority:
        query = query.filter_by(priority=priority)
    
    # Search
    if search_query:
        query = query.filter(Task.title.ilike(f'%{search_query}%') | Task.description.ilike(f'%{search_query}%'))
    
    # Order by priority and due date
    tasks = query.order_by(
        Task.is_completed.asc(),
        Task.priority.desc(),
        Task.due_date.asc().nullslast(),
        Task.created_at.desc()
    ).all()
    
    # Get categories for sidebar (alphabetical order)
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()
    
    # Get stats for dashboard
    stats = get_user_stats(current_user.id)
    
    return render_template('index.html', 
                         tasks=tasks, 
                         categories=categories,
                         stats=stats,
                         filter_type=filter_type)

@main.route('/category/create', methods=['POST'])
@login_required
def create_category():
    name = request.form.get('name')
    color = request.form.get('color', '#3b82f6')
    icon = '📚'  # Uniform icon for all subjects
    
    if not name:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'message': 'Category name is required'}), 400
        flash('Category name is required', 'danger')
        return redirect(url_for('main.index'))
    
    category = Category(
        name=name,
        color=color,
        icon=icon,
        user_id=current_user.id
    )
    db.session.add(category)
    db.session.commit()
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True, 'category': category.to_dict()})
    
    flash(f'Category "{name}" created!', 'success')
    return redirect(url_for('main.index'))

def get_subject_icon(name, fallback='📚'):
    """Auto-generate icon based on subject name"""
    name_lower = name.lower().strip()
    
    icon_map = {
        'math': '🔢', 'mathematics': '🔢', 'algebra': '📐', 'calculus': '∫', 'geometry': '📐', 'statistics': '📊',
        'science': '🔬', 'physics': '⚛️', 'chemistry': '🧪', 'biology': '🧬', 'astronomy': '🌟',
        'english': '📖', 'literature': '📚', 'reading': '📖', 'writing': '✍️', 'language': '🗣️', 'grammar': '📝',
        'history': '🏛️', 'social': '🌍', 'geography': '🗺️', 'economics': '💰', 'politics': '⚖️',
        'computer': '💻', 'programming': '💻', 'coding': '⌨️', 'cs': '💻', 'ict': '💻', 'informatics': '💻',
        'art': '🎨', 'design': '🎨', 'drawing': '✏️',
        'music': '🎵', 'song': '🎵', 'instrument': '🎸',
        'pe': '⚽', 'gym': '🏋️', 'sports': '⚽', 'physical': '⚽', 'health': '🏃',
        'spanish': '🇪🇸', 'french': '🇫🇷', 'german': '🇩🇪', 'chinese': '🇨🇳', 'japanese': '🇯🇵', 'korean': '🇰🇷', 'language': '🌐',
        'philosophy': '🤔', 'psychology': '🧠', 'law': '⚖️', 'religion': '✝️', 'ethics': '💭',
        'business': '💼', 'marketing': '📊', 'accounting': '🧾', 'finance': '💵', 'entrepreneurship': '🚀',
        'engineering': '⚙️', 'mechanical': '🔧', 'electrical': '⚡', 'civil': '🏗️',
        'medicine': '🏥', 'medical': '🏥', 'nursing': '👩‍⚕️', 'pharmacy': '💊',
        'law': '⚖️', 'legal': '⚖️',
        'video': '🎬', 'film': '🎬', 'media': '📺', 'photography': '📷',
        'robotics': '🤖', 'ai': '🤖', 'machine': '🤖',
    }
    
    for keyword, icon in icon_map.items():
        if keyword in name_lower:
            return icon
    
    return fallback

@main.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    form.category_id.choices = [(0, 'No Subject')] + \
        [(c.id, f'{c.icon} {c.name}') for c in Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()]
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            notes=form.notes.data,
            link=form.link.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            is_recurring=form.is_recurring.data,
            recurrence_pattern=form.recurrence_pattern.data if form.is_recurring.data else None,
            recurrence_end=form.recurrence_end.data if form.is_recurring.data else None,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('task_form.html', form=form, title='New Task')

@main.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('main.index'))
    
    form = TaskForm(obj=task)
    form.category_id.choices = [(0, 'No Subject')] + \
        [(c.id, f'{c.icon} {c.name}') for c in Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()]
    
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.notes = form.notes.data
        task.link = form.link.data
        task.priority = form.priority.data
        task.due_date = form.due_date.data
        task.category_id = form.category_id.data if form.category_id.data != 0 else None
        task.is_recurring = form.is_recurring.data
        task.recurrence_pattern = form.recurrence_pattern.data if form.is_recurring.data else None
        task.recurrence_end = form.recurrence_end.data if form.is_recurring.data else None
        task.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('task_form.html', form=form, title='Edit Task', task=task)

@main.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted!', 'success')
    return jsonify({'success': True})

@main.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def toggle_complete(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    task.is_completed = not task.is_completed
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Handle recurring tasks
    if task.is_completed and task.is_recurring and task.recurrence_pattern:
        create_next_recurring(task)
    
    return jsonify({
        'success': True, 
        'is_completed': task.is_completed,
        'completion_percentage': task.completion_percentage
    })

def create_next_recurring(task):
    """Create the next instance of a recurring task"""
    if not task.recurrence_pattern or task.recurrence_end:
        return
    
    if task.recurrence_pattern == 'daily':
        new_due = task.due_date + timedelta(days=1)
    elif task.recurrence_pattern == 'weekly':
        new_due = task.due_date + timedelta(weeks=1)
    elif task.recurrence_pattern == 'monthly':
        new_due = task.due_date + timedelta(days=30)
    else:
        return
    
    # Check if we've passed the recurrence end
    if task.recurrence_end and new_due > task.recurrence_end:
        return
    
    new_task = Task(
        title=task.title,
        description=task.description,
        notes=task.notes,
        priority=task.priority,
        due_date=new_due,
        is_recurring=True,
        recurrence_pattern=task.recurrence_pattern,
        recurrence_end=task.recurrence_end,
        category_id=task.category_id,
        user_id=task.user_id
    )
    db.session.add(new_task)
    db.session.commit()

# Subtask routes
@main.route('/task/<int:task_id>/subtask', methods=['POST'])
@login_required
def add_subtask(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    form = SubtaskForm()
    if form.validate_on_submit():
        subtask = Subtask(title=form.title.data, task_id=task_id)
        db.session.add(subtask)
        db.session.commit()
        return jsonify({
            'success': True, 
            'subtask': {'id': subtask.id, 'title': subtask.title, 'is_completed': False},
            'completion_percentage': task.completion_percentage
        })
    return jsonify({'success': False, 'errors': form.errors}), 400

@main.route('/subtask/<int:subtask_id>/toggle', methods=['POST'])
@login_required
def toggle_subtask(subtask_id):
    subtask = Subtask.query.get_or_404(subtask_id)
    task = Task.query.get(subtask.task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    subtask.is_completed = not subtask.is_completed
    db.session.commit()
    return jsonify({
        'success': True,
        'is_completed': subtask.is_completed,
        'completion_percentage': task.completion_percentage
    })

@main.route('/subtask/<int:subtask_id>/delete', methods=['POST'])
@login_required
def delete_subtask(subtask_id):
    subtask = Subtask.query.get_or_404(subtask_id)
    task = Task.query.get(subtask.task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    db.session.delete(subtask)
    db.session.commit()
    return jsonify({
        'success': True,
        'completion_percentage': task.completion_percentage
    })

# Category routes
@main.route('/category/new', methods=['POST'])
@login_required
def new_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            color=form.color.data,
            icon=form.icon.data,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created!', 'success')
    return redirect(url_for('main.index'))

@main.route('/category/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    name = request.form.get('name')
    color = request.form.get('color', '#3b82f6')
    icon = '📚'  # Uniform icon for all subjects
    
    if not name:
        return jsonify({'success': False, 'message': 'Category name is required'}), 400
    
    category.name = name
    category.color = color
    category.icon = icon
    db.session.commit()
    
    return jsonify({'success': True, 'category': category.to_dict()})

@main.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    # Remove category from tasks but don't delete tasks
    Task.query.filter_by(category_id=category_id).update({'category_id': None})
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted!', 'success')
    return jsonify({'success': True})

# Pomodoro routes
@main.route('/pomodoro/start/<int:task_id>', methods=['POST'])
@login_required
def start_pomodoro(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    # Create a pomodoro record (in real app, this would track start/end times)
    pomodoro = Pomodoro(
        duration=25,
        user_id=current_user.id,
        task_id=task_id
    )
    db.session.add(pomodoro)
    db.session.commit()
    
    return jsonify({'success': True, 'pomodoro_id': pomodoro.id})

@main.route('/pomodoro/complete/<int:pomodoro_id>', methods=['POST'])
@login_required
def complete_pomodoro(pomodoro_id):
    pomodoro = Pomodoro.query.get_or_404(pomodoro_id)
    if pomodoro.user_id != current_user.id:
        return jsonify({'success': False}), 403
    
    pomodoro.completed_at = datetime.utcnow()
    pomodoro.was_completed = True
    db.session.commit()
    
    return jsonify({'success': True})

# Analytics dashboard
@main.route('/analytics')
@login_required
def analytics():
    stats = get_user_stats(current_user.id)
    return render_template('analytics.html', stats=stats)

# Reorder tasks (for drag and drop)
@main.route('/task/reorder', methods=['POST'])
@login_required
def reorder_tasks():
    data = request.get_json()
    for item in data.get('tasks', []):
        task = Task.query.get(item['id'])
        if task and task.user_id == current_user.id:
            task.priority = item.get('priority', task.priority)
    db.session.commit()
    return jsonify({'success': True})