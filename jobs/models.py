from django.db import models
from django.conf import settings

# Predefined skills list
PREDEFINED_SKILLS = [
    # Programming Languages
    'Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust', 'Swift',
    'TypeScript', 'Kotlin', 'Scala', 'R', 'MATLAB', 'SQL', 'HTML/CSS',
    
    # Frameworks & Libraries
    'React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring Boot', 'Node.js', 
    'Express.js', 'Laravel', 'Rails', 'ASP.NET', 'jQuery', 'Bootstrap',
    
    # Databases
    'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'MS SQL Server',
    'Firebase', 'DynamoDB', 'Elasticsearch',
    
    # Cloud & DevOps
    'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 
    'Linux', 'CI/CD', 'Terraform', 'Ansible',
    
    # Data Science & Analytics
    'Machine Learning', 'Data Analysis', 'Pandas', 'NumPy', 'TensorFlow', 'PyTorch',
    'Scikit-learn', 'Tableau', 'Power BI', 'Excel', 'Statistics',
    
    # Design & Marketing
    'UI/UX Design', 'Figma', 'Adobe Creative Suite', 'Photoshop', 'Illustrator',
    'Digital Marketing', 'SEO', 'Content Marketing', 'Social Media Marketing',
    
    # Business & Soft Skills
    'Project Management', 'Agile/Scrum', 'Leadership', 'Communication', 
    'Problem Solving', 'Team Collaboration', 'Customer Service', 'Sales',
    'Public Speaking', 'Time Management',
    
    # Other Technical
    'REST APIs', 'GraphQL', 'Microservices', 'Mobile Development', 'iOS Development',
    'Android Development', 'Game Development', 'Blockchain', 'Cybersecurity',
    'Network Administration', 'Quality Assurance', 'Testing'
]

# Will try to make it nicer and more flexible in terms of salary filtering
PAY_TYPE_CHOICES = [
    ('annual', 'Annual'),
    ('hourly', 'Hourly'),
    ('monthly', 'Monthly'),
]
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True)  # Optional categorization
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Job(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default='Remote')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)   # Leave lat and long in for Google Maps API in future
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pay_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_max = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_type = models.CharField(max_length=20, choices=PAY_TYPE_CHOICES, default='annual')
    description = models.TextField()
    image = models.ImageField(upload_to='job_images/', blank=True, null=True)  # allow optional images
    required_skills = models.ManyToManyField(Skill, blank=True, related_name='jobs_requiring')
    preferred_skills = models.ManyToManyField(Skill, blank=True, related_name='jobs_preferring')
    
    def __str__(self):
        return str(self.id) + " - " + self.name + " | " + self.company
