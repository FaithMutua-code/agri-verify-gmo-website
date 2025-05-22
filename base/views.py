from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import GMOProduct, ChatMessage, EducationalResource, VerificationRequest
import json
from django.contrib.auth import login, logout, authenticate
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import Http404
from .models import Webinar
from django.views.decorators.csrf import csrf_exempt
import openai
from django.views.generic import DetailView
import requests  




@login_required
def dashboard(request):
    # Get latest chat messages (last 10)
    chat_messages = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:10]  
    
    # Get video resources - first one is featured, next 3 are related
    video_resources = EducationalResource.objects.filter(
        resource_type='video'
    ).exclude(video_file='').order_by('-created_at')  # Exclude empty video files
    
    featured_video = video_resources.first() if video_resources.exists() else None
    related_videos = video_resources[1:4] if video_resources.count() > 1 else []
    
    # Get other educational resources (non-video)
    other_resources = EducationalResource.objects.exclude(
        resource_type='video'
    ).order_by('-created_at')[:4]
    
    # Get verified products
    verified_products = GMOProduct.objects.filter(verification_status='verified').order_by('-created_at')[:3]
    
    # Get all products for directory (paginated)
    all_products = GMOProduct.objects.all().order_by('-created_at')
    paginator = Paginator(all_products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'chat_messages': chat_messages,
        'featured_video': featured_video,
        'educational_resources': list(related_videos) + list(other_resources),
        'verified_products': verified_products,
        'page_obj': page_obj,
    }
    return render(request, 'dashboard.html', context)




import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import ChatMessage

def get_grok_response(user_message, context):   
    """
    Get a response from Grok's API (JSON-safe format).
    """
    try:
        # Prepare messages for the API
        messages = [
            {"role": "system", "content": "You are an expert on GMOs. Provide accurate, science-based answers about genetically modified organisms, agricultural biotechnology, and related regulations."},
        ]
        
        if context.get('last_topic'):
            messages.append({"role": "assistant", "content": f"Previously discussing: {context['last_topic']}"})
        
        messages.append({"role": "user", "content": user_message})

        # Call Grok API (replace with actual Grok API endpoint and credentials)
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",  # Verify actual Grok API endpoint
            headers={
                "Authorization": "Bearer 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",  # Replace with your Grok API key
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # Or whatever model name Grok uses
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
                "top_p": 0.9,
            },
            timeout=15  # Slightly longer timeout for Grok
        )
        
        # Handle potential API errors
        response.raise_for_status()
        response_data = response.json()

        # Safely extract the answer (adjust based on Grok's actual response format)
        answer = response_data.get("choices", [{}])[0].get("message", {}).get("content", "No answer found.")

        # Update context (ensure all values are JSON-serializable)
        new_context = {
            "last_topic": str(user_message[:50]),  # Truncate to avoid issues
            "conversation_id": response_data.get("conversation_id", "")  # If Grok provides conversation tracking
        }

        return {
            "answer": str(answer),  # Force string conversion
            "context": new_context,  # Dict with serializable values
            "confidence": float(0.9)  # Confidence score
        }

    except requests.exceptions.RequestException as e:
        return {
            "answer": f"API Connection Error: {str(e)}",
            "context": {},
            "confidence": 0.1
        }
    except Exception as e:
        return {
            "answer": f"Processing Error: {str(e)}",
            "context": {},
            "confidence": 0.1
        }

@csrf_exempt
@login_required
def chat_api(request):
    """
    Handle AJAX chat requests with Grok AI integration.
    """
    if request.method == 'POST':
        try:
            # Parse input data
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            context = data.get("context", {})

            if not user_message:
                return JsonResponse({"error": "Empty message"}, status=400)

            # Get Grok's response
            result = get_grok_response(user_message, context)

            # Save to database
            chat_msg = ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=result["answer"],
                context=json.dumps(result["context"]),
                is_helpful=None  # Initialize feedback as neutral
            )

            # Return response
            return JsonResponse({
                "response": result["answer"],
                "context": result["context"],
                "message_id": chat_msg.id,
                "suggestions": get_related_suggestions(user_message)
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_related_suggestions(user_message):
    """
    Generate context-aware suggestions based on user message.
    """
    suggestions = [
        "GMO regulations in my country",
        "How to verify GMO products",
        "Benefits of GMO crops",
        "Safety of genetically modified foods"
    ]
    
    # Add more context-aware suggestions based on message content
    if "seed" in user_message.lower():
        suggestions.append("How to identify authentic seeds")
    if "corn" in user_message.lower():
        suggestions.append("GMO corn varieties")
    if "regulation" in user_message.lower():
        suggestions.append("Latest GMO regulations")
    
    return suggestions[:4]  # Return max 4 suggestions

@login_required
def chat_view(request):
    """Render the agriculture chat template"""
    recent_messages = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'dashboard.html', {
        'recent_messages': recent_messages,
        'topics': ["GMO Science", "GMO Regulations", "GMO Crops", "GMO Verification"]
    })

@csrf_exempt
@login_required
def feedback_api(request):
    """Handle user feedback on responses"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            is_helpful = data.get('is_helpful')
            
            if message_id is None or is_helpful is None:
                return JsonResponse({'error': 'Missing parameters'}, status=400)
            
            message = ChatMessage.objects.get(id=message_id, user=request.user)
            message.is_helpful = is_helpful
            message.save()
            
            return JsonResponse({'status': 'success'})
        except ChatMessage.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)



@login_required
def verify_product(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_data', '')
            
            # Parse the QR data to extract the product ID or certification ID
            # This depends on how you structure your QR data
            product_id = None
            for line in qr_data.split('\n'):
                if line.startswith('Certification:'):
                    cert_id = line.split(': ')[1].strip()
                    if cert_id != 'None':
                        product = get_object_or_404(GMOProduct, certification_id=cert_id)
                        break
            
            if not product_id:
                # Alternative parsing if certification ID not found
                for line in qr_data.split('\n'):
                    if line.startswith('Name:'):
                        product_name = line.split(': ')[1].strip()
                        product = get_object_or_404(GMOProduct, name=product_name)
                        break
            
            response_data = {
                'status': 'success',
                'product': {
                    'name': product.name,
                    'company': product.company,
                    'crop_type': product.get_crop_type_display(),
                    'verification_status': product.get_verification_status_display(),
                    'certification_id': product.certification_id,
                    'certification_authority': product.certification_authority,
                    'certification_date': product.certification_date.strftime('%Y-%m-%d') if product.certification_date else None,
                    'image_url': product.image.url if product.image else None,
                }
            }
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def filter_products(request):
    crop_type = request.GET.get('crop_type', '')
    season = request.GET.get('season', '')
    region = request.GET.get('region', '')
    status = request.GET.get('status', '')
    
    products = GMOProduct.objects.all()
    
    if crop_type:
        products = products.filter(crop_type=crop_type)
    if season:
        products = products.filter(season=season)
    if status:
        products = products.filter(verification_status=status)
    
    # Note: Region filtering would require a region field in the model
    
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'product_list_partial.html', {
        'page_obj': page_obj
    })



# Login View
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")  
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username:
            messages.error(request, "Username is required.")
            return redirect("register")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login_view")

    return render(request, "register.html")



def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login_view')


def webinar_redirect(request):
    try:
        # Get the latest active webinar
        webinar = Webinar.objects.filter(
            is_active=True,
            scheduled_time__gte=timezone.now()  # Only future webinars
        ).latest('scheduled_time')
        return redirect(webinar.zoom_registration_url)
    
    except Webinar.DoesNotExist:
        # Fallback URL if no webinars exist
        return redirect('https://zoom.us/webinars')  # Or a custom "no webinars" page




class ProductDetailView(DetailView):
    model = GMOProduct
    template_name = 'product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = GMOProduct.objects.filter(
            crop_type=self.object.crop_type
        ).exclude(id=self.object.id)[:3]
        return context



@csrf_exempt  # Only for development - use proper CSRF protection in production
def verify_product(request, product_id):
    try:
        product = GMOProduct.objects.get(id=product_id)
        
        # In a real app, you might have more complex verification logic
        is_verified = product.verification_status == 'verified'
        certification_valid = bool(product.certification_id)
        
        return JsonResponse({
            'success': True,
            'verified': is_verified,
            'certification_valid': certification_valid,
            'status': product.get_verification_status_display(),
            'product': {
                'name': product.name,
                'company': product.company,
                'certification_id': product.certification_id,
            }
        })
    except GMOProduct.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)





def quiz(request):
    return render(request, 'quiz.html')