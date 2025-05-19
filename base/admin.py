from django.contrib import admin
from django.utils.html import format_html
from .models import GMOProduct, ChatMessage, EducationalResource, VerificationRequest
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# Jazzmin Configuration
admin.site.site_header = "AgriVerify Admin"
admin.site.site_title = "AgriVerify Administration"
admin.site.index_title = "Welcome to AgriVerify Admin Portal"


# Model Resources for Import/Export
class GMOProductResource(resources.ModelResource):
    class Meta:
        model = GMOProduct
        fields = ('id', 'name', 'company', 'crop_type', 'season', 'verification_status', 'certification_id')
        export_order = fields

class EducationalResourceResource(resources.ModelResource):
    class Meta:
        model = EducationalResource
        fields = ('id', 'title', 'resource_type', 'source', 'duration')
        export_order = fields



@admin.register(GMOProduct)
class GMOProductAdmin(ImportExportModelAdmin):
    resource_class = GMOProductResource
    list_display = ('name', 'company', 'crop_type', 'season', 'verification_status', 'image_preview', 'created_at')
    list_filter = ('verification_status', 'crop_type', 'season', 'created_at')
    search_fields = ('name', 'company', 'certification_id')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')  # Make these fields read-only
    list_per_page = 25
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company', 'description')
        }),
        ('Product Details', {
            'fields': ('crop_type', 'season', 'image', 'image_preview')
        }),
        ('Verification Information', {
            'fields': ('verification_status', 'certification_id', 'certification_date', 'certification_authority', 'qr_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'

from .models import Webinar

@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = ('title', 'scheduled_time', 'is_active')
    list_filter = ('is_active', 'scheduled_time')
    search_fields = ('title', 'description')
    date_hierarchy = 'scheduled_time'
from django.contrib import admin
from django.utils.html import format_html
from .models import ChatMessage, GMOKnowledgeBase

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'truncated_message', 'truncated_response', 'feedback_indicator', 'created_at')
    list_filter = ('user', 'is_helpful', 'created_at')
    search_fields = ('message', 'response', 'user__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('user', 'created_at')
        }),
        ('Message Content', {
            'fields': ('message', 'response')
        }),
        ('Feedback & Analysis', {
            'fields': ('is_helpful', 'context'),
            'classes': ('collapse',)
        }),
    )
    
    def truncated_message(self, obj):
        return obj.message[:75] + '...' if len(obj.message) > 75 else obj.message
    truncated_message.short_description = 'Message'
    
    def truncated_response(self, obj):
        return obj.response[:75] + '...' if obj.response and len(obj.response) > 75 else obj.response
    truncated_response.short_description = 'Response'
    
    def feedback_indicator(self, obj):
        if obj.is_helpful is None:
            return format_html('<span style="color: gray;">━</span> No feedback')
        elif obj.is_helpful:
            return format_html('<span style="color: green;">↑</span> Helpful')
        return format_html('<span style="color: red;">↓</span> Not helpful')
    feedback_indicator.short_description = 'Feedback'

@admin.register(GMOKnowledgeBase)
class GMOKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('topic', 'question_count', 'confidence_score', 'confidence_bar', 'last_updated')  # Added confidence_score here
    list_filter = ('topic',)
    search_fields = ('question_patterns', 'answer', 'references')
    list_editable = ('confidence_score',)  # Now this field exists in list_display
    list_per_page = 20
    actions = ['update_confidence', 'export_as_json']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('topic', 'confidence_score')
        }),
        ('Content', {
            'fields': ('question_patterns', 'answer', 'references')
        }),
    )
    
    def question_count(self, obj):
        return len(obj.question_patterns.split('\n'))
    question_count.short_description = 'Questions'
    
    def confidence_bar(self, obj):
        percent = int(obj.confidence_score * 100)
        color = 'green' if percent > 70 else 'orange' if percent > 40 else 'red'
        return format_html(
            '<div style="background: lightgray; width: 100px; height: 20px; position: relative;">'
            '<div style="background: {color}; width: {percent}%; height: 100%;"></div>'
            '<div style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; color: black;">{percent}%</div>'
            '</div>',
            color=color, percent=percent
        )
    confidence_bar.short_description = 'Confidence'
    
    def update_confidence(self, request, queryset):
        updated = queryset.update(confidence_score=1.0)
        self.message_user(request, f"Reset confidence for {updated} knowledge items")
    update_confidence.short_description = "Reset confidence to 100%"
    
    def export_as_json(self, request, queryset):
        import json
        from django.http import HttpResponse
        data = []
        for item in queryset:
            data.append({
                'topic': item.topic,
                'questions': item.question_patterns.split('\n'),
                'answer': item.answer,
                'confidence': item.confidence_score
            })
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename=gmo_knowledge_export.json'
        return response
    export_as_json.short_description = "Export selected as JSON"

    
# Optional: Custom admin site header
admin.site.site_header = "GMO Agricultural Assistant Administration"
admin.site.site_title = "GMO Knowledge Base"
admin.site.index_title = "Welcome to GMO Agricultural Assistant Admin"

    
@admin.register(EducationalResource)
class EducationalResourceAdmin(ImportExportModelAdmin):
    resource_class = EducationalResourceResource
    list_display = ('title', 'resource_type', 'source', 'duration', 'thumbnail_preview', 'created_at')
    list_filter = ('resource_type', 'source', 'created_at')
    search_fields = ('title', 'description', 'source')
    readonly_fields = ('thumbnail_preview',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail'

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_name', 'verification_method', 'is_verified', 'created_at')
    list_filter = ('verification_method', 'is_verified', 'created_at')
    search_fields = ('user__username', 'product__name', 'verification_code')
    readonly_fields = ('created_at', 'verification_result_formatted')
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else "-"
    product_name.short_description = 'Product'
    
    def verification_result_formatted(self, obj):
        if obj.verification_result:
            return format_html("<pre>{}</pre>", json.dumps(obj.verification_result, indent=2))
        return "-"
    verification_result_formatted.short_description = 'Verification Result'