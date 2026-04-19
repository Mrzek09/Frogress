# Utility functions for the app

def format_date(date):
    """Format a date for display"""
    if not date:
        return ''
    return date.strftime('%Y-%m-%d')

def format_datetime(dt):
    """Format a datetime for display"""
    if not dt:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M')

def time_ago(dt):
    """Return a human-readable time ago string"""
    if not dt:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        return f'{diff.days // 365} year(s) ago'
    elif diff.days > 30:
        return f'{diff.days // 30} month(s) ago'
    elif diff.days > 0:
        return f'{diff.days} day(s) ago'
    elif diff.seconds > 3600:
        return f'{diff.seconds // 3600} hour(s) ago'
    elif diff.seconds > 60:
        return f'{diff.seconds // 60} minute(s) ago'
    else:
        return 'Just now'

def is_overdue(due_date):
    """Check if a due date has passed"""
    if not due_date:
        return False
    return due_date < datetime.utcnow()

def get_priority_class(priority):
    """Get CSS class for priority"""
    classes = {
        'Low': 'priority-low',
        'Medium': 'priority-medium',
        'High': 'priority-high'
    }
    return classes.get(priority, 'priority-medium')

from datetime import datetime