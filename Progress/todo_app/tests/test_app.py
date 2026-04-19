import pytest
from app import create_app, db
from app.models import User, Task, Category

@pytest.fixture
def app():
    """Create and configure a test instance of the app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Test CLI runner for the app."""
    return app.test_cli_runner()

class TestAuth:
    """Test authentication routes."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/auth/login')
        assert response.status_code == 200
    
    def test_register_page_loads(self, client):
        """Test that register page loads successfully."""
        response = client.get('/auth/register')
        assert response.status_code == 200
    
    def test_register_user(self, client):
        """Test user registration."""
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_user(self, app, client):
        """Test user login."""
        # First create a user
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Then try to login
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_logout(self, app, client):
        """Test user logout."""
        # First login
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200

class TestTask:
    """Test task functionality."""
    
    @pytest.fixture
    def authenticated_client(self, app, client):
        """Create an authenticated test client."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        return client
    
    def test_index_requires_login(self, client):
        """Test that index page requires authentication."""
        response = client.get('/')
        # Should redirect to login
        assert response.status_code in [302, 401]
    
    def test_create_task(self, authenticated_client):
        """Test creating a new task."""
        response = authenticated_client.post('/task/new', data={
            'title': 'Test Task',
            'description': 'Test Description',
            'priority': 'Medium'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_task_list(self, authenticated_client):
        """Test that task list loads."""
        response = authenticated_client.get('/')
        assert response.status_code == 200

class TestModels:
    """Test database models."""
    
    def test_user_password_hashing(self, app):
        """Test that password hashing works."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            assert user.password_hash is not None
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_task_creation(self, app):
        """Test creating a task."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            task = Task(
                title='Test Task',
                description='Test Description',
                priority='High',
                user_id=user.id
            )
            db.session.add(task)
            db.session.commit()
            
            assert task.id is not None
            assert task.title == 'Test Task'
            assert task.priority == 'High'
    
    def test_category_creation(self, app):
        """Test creating a category."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            category = Category(
                name='Math',
                color='#3498db',
                icon='📐',
                user_id=user.id
            )
            db.session.add(category)
            db.session.commit()
            
            assert category.id is not None
            assert category.name == 'Math'

class TestAPI:
    """Test API endpoints."""
    
    @pytest.fixture
    def authenticated_client(self, app, client):
        """Create an authenticated test client."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        return client
    
    def test_get_tasks_api(self, authenticated_client):
        """Test getting tasks via API."""
        response = authenticated_client.get('/api/tasks')
        assert response.status_code == 200
        assert 'tasks' in response.json
    
    def test_create_task_api(self, authenticated_client):
        """Test creating a task via API."""
        response = authenticated_client.post('/api/tasks', json={
            'title': 'API Task',
            'priority': 'High'
        })
        assert response.status_code == 201
        assert response.json['task']['title'] == 'API Task'
    
    def test_get_categories_api(self, authenticated_client):
        """Test getting categories via API."""
        response = authenticated_client.get('/api/categories')
        assert response.status_code == 200
        assert 'categories' in response.json