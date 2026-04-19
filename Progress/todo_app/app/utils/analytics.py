from app import db
from app.models import Task, Category, Pomodoro, Subtask
from datetime import datetime, timedelta
from sqlalchemy import func

def get_user_stats(user_id):
    """Get comprehensive statistics for a user"""
    
    # Basic task counts
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    completed_tasks = Task.query.filter_by(user_id=user_id, is_completed=True).count()
    active_tasks = Task.query.filter_by(user_id=user_id, is_completed=False).count()
    overdue_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.is_completed == False,
        Task.due_date < datetime.utcnow()
    ).count()
    
    # Completion rate
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
    
    # Tasks by priority
    priority_counts = db.session.query(
        Task.priority,
        func.count(Task.id)
    ).filter(Task.user_id == user_id).group_by(Task.priority).all()
    
    # Tasks by category
    category_counts = db.session.query(
        Category.name,
        Category.color,
        func.count(Task.id)
    ).join(Task).filter(
        Task.user_id == user_id,
        Task.category_id == Category.id
    ).group_by(Category.id).all()
    
    # Tasks created this week
    week_start = datetime.utcnow() - timedelta(days=7)
    tasks_this_week = Task.query.filter(
        Task.user_id == user_id,
        Task.created_at >= week_start
    ).count()
    
    # Completed this week
    completed_this_week = Task.query.filter(
        Task.user_id == user_id,
        Task.is_completed == True,
        Task.updated_at >= week_start
    ).count()
    
    # Pomodoro stats
    pomodoros_today = Pomodoro.query.filter(
        Pomodoro.user_id == user_id,
        func.date(Pomodoro.completed_at) == func.date(datetime.utcnow())
    ).count()
    
    pomodoros_week = Pomodoro.query.filter(
        Pomodoro.user_id == user_id,
        Pomodoro.completed_at >= week_start
    ).count()
    
    total_pomodoro_minutes = db.session.query(
        func.sum(Pomodoro.duration)
    ).filter(Pomodoro.user_id == user_id).scalar() or 0
    
    # Daily task completion for the last 7 days
    daily_completion = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        
        completed = Task.query.filter(
            Task.user_id == user_id,
            Task.is_completed == True,
            Task.updated_at >= day_start,
            Task.updated_at <= day_end
        ).count()
        
        created = Task.query.filter(
            Task.user_id == user_id,
            Task.created_at >= day_start,
            Task.created_at <= day_end
        ).count()
        
        daily_completion.append({
            'date': day.strftime('%Y-%m-%d'),
            'day_name': day.strftime('%a'),
            'completed': completed,
            'created': created
        })
    
    # Current streak (consecutive days with completed tasks)
    streak = calculate_streak(user_id)
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'active_tasks': active_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate,
        'priority_counts': {p: c for p, c in priority_counts},
        'category_counts': [{'name': n, 'color': c, 'count': ct} for n, c, ct in category_counts],
        'tasks_this_week': tasks_this_week,
        'completed_this_week': completed_this_week,
        'pomodoros_today': pomodoros_today,
        'pomodoros_week': pomodoros_week,
        'total_pomodoro_minutes': total_pomodoro_minutes,
        'daily_completion': daily_completion,
        'streak': streak
    }

def calculate_streak(user_id):
    """Calculate consecutive days with completed tasks"""
    streak = 0
    current_date = datetime.utcnow().date()
    
    while True:
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = datetime.combine(current_date, datetime.max.time())
        
        completed = Task.query.filter(
            Task.user_id == user_id,
            Task.is_completed == True,
            Task.updated_at >= day_start,
            Task.updated_at <= day_end
        ).count()
        
        if completed > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            # Check if we're at today - if no tasks completed today yet, still count the streak
            if current_date == datetime.utcnow().date():
                current_date -= timedelta(days=1)
                continue
            break
        
        # Limit to 365 days to prevent infinite loop
        if streak >= 365:
            break
    
    return streak