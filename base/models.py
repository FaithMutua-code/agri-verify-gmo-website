from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

from django.db import models
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class GMOProduct(models.Model):
    VERIFICATION_STATUS = [
        ('verified', 'Verified'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    ]
    
    CROP_TYPES = [
        ('corn', 'Corn'),
        ('soybeans', 'Soybeans'),
        ('cotton', 'Cotton'),
        ('canola', 'Canola'),
        ('rice', 'Rice'),
        ('wheat', 'Wheat'),
        ('sugarbeet', 'Sugarbeet'),
        ('alfalfa', 'Alfalfa'),
        ('potato', 'Potato'),
        ('tomato', 'Tomato'),
    ]
    
    SEASONS = [
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
        ('winter', 'Winter'),
    ]
    
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    description = models.TextField()
    crop_type = models.CharField(max_length=20, choices=CROP_TYPES)
    season = models.CharField(max_length=20, choices=SEASONS)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    certification_id = models.CharField(max_length=50, blank=True)
    certification_date = models.DateField(null=True, blank=True)
    certification_authority = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    qr_data = models.TextField(blank=True)  # Optional: Store the raw QR data

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.qr_code:  # Generate QR code if it doesn't exist
            self.generate_qr_code()
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        """Generate QR code using the product's basic information"""
        qr_data = f"""
        GMO Product Information:
        Name: {self.name}
        Company: {self.company}
        Crop Type: {self.get_crop_type_display()}
        Status: {self.get_verification_status_display()}
        Certification: {self.certification_id or 'None'}
        Certified By: {self.certification_authority or 'N/A'}
        """
        
        # Clean up the data
        qr_data = "\n".join([line.strip() for line in qr_data.split("\n") if line.strip()])
        self.qr_data = qr_data  # Store the raw data if needed
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Generate filename using product name and ID
        filename = f'qr_{self.name.lower().replace(" ", "_")}_{self.id or "new"}.png'
        
        # Save QR code image
        self.qr_code.save(
            filename,
            ContentFile(buffer.getvalue()),
            save=False
        )



class Webinar(models.Model):
    title = models.CharField(max_length=200, help_text="Name of the webinar")
    description = models.TextField(blank=True, null=True)
    zoom_registration_url = models.URLField(help_text="Zoom registration link")
    scheduled_time = models.DateTimeField(help_text="When the webinar starts")
    is_active = models.BooleanField(default=True, help_text="Is registration open?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time']  # Newest first

    def __str__(self):
        return f"{self.title} ({self.scheduled_time})"




class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    message = models.TextField(null=True)
    response = models.TextField(null=True)
    context = models.JSONField(default=dict)  # Store conversation context
    is_helpful = models.BooleanField(null=True)  # User feedback
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class GMOKnowledgeBase(models.Model):
    TOPIC_CHOICES = [
        ('science', 'GMO Science'),
        ('regulations', 'Regulations'),
        ('crops', 'Specific Crops'),
        ('verification', 'Product Verification'),
        ('myths', 'Myths & Facts'),
    ]
    
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES)
    question_patterns = models.TextField(help_text="One per line, common question patterns")
    answer = models.TextField()
    references = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    confidence_score = models.FloatField(default=1.0)
    
    def __str__(self):
        return f"{self.get_topic_display()}: {self.question_patterns[:50]}"

class EducationalResource(models.Model):
    RESOURCE_TYPES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('document', 'Document'),
    ]
    
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    description = models.TextField()
    url = models.URLField()
    thumbnail = models.ImageField(upload_to='resources/', null=True, blank=True)
    duration = models.CharField(max_length=20, blank=True)  # For videos
    source = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title

class VerificationRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(GMOProduct, on_delete=models.CASCADE, null=True, blank=True)
    verification_code = models.CharField(max_length=100)
    verification_method = models.CharField(max_length=20, choices=[
        ('qr', 'QR Code'),
        ('manual', 'Manual Entry'),
        ('image', 'Image Upload'),
    ])
    is_verified = models.BooleanField(default=False)
    verification_result = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Verification for {self.product.name if self.product else 'Unknown Product'}"