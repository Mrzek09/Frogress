from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, DateField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=25, message='Username must be between 3 and 25 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=1, max=140, message='Title must be between 1 and 140 characters')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    link = StringField('Link (URL)', validators=[Optional(), Length(max=500)])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], default='Medium')
    category_id = SelectField('Subject', coerce=int, validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()], format='%Y-%m-%d')
    
    # Recurring options
    is_recurring = BooleanField('Recurring Task')
    recurrence_pattern = SelectField('Repeat', choices=[
        ('', 'Select pattern'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[Optional()])
    recurrence_end = DateField('End Date', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Save Task')

class SubtaskForm(FlaskForm):
    title = StringField('Subtask', validators=[
        DataRequired(),
        Length(min=1, max=140)
    ])
    submit = SubmitField('Add Subtask')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=1, max=50)
    ])
    color = StringField('Color', validators=[Optional()])
    icon = StringField('Icon (emoji)', validators=[Optional()], default='📚')
    submit = SubmitField('Create Category')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    submit = SubmitField('Search')