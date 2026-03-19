from django.contrib import admin
from django.contrib.auth.models import Group, User
from .models import DocumentPage
from django.utils.html import format_html
from .utils import process_pdf_full, create_synthetic_copies

admin.site.site_header = "AI Document Intelligence Portal"
admin.site.site_title = "Deduplication Engine"
admin.site.index_title = "Document Management Dashboard"

try:
    admin.site.unregister(Group)
    admin.site.unregister(User)
except:
    pass

@admin.register(DocumentPage)
class DocumentPageAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'display_filename', 'page_number', 'image_preview')
    list_filter = ('original_pdf',)
    
    fields = ('original_pdf',) 

    
    actions = ['manual_augment_action']

    def display_filename(self, obj):
       
        return obj.original_pdf.name.split('/')[-1] if obj.original_pdf else "N/A"
    display_filename.short_description = 'Source PDF'

    def image_preview(self, obj):
        
        if obj.page_image:
            return format_html('<img src="{}" width="60" style="border: 1px solid #ddd; border-radius: 4px;"/>', obj.page_image.url)
        return "⏳ Processing..."
    image_preview.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
       
        super().save_model(request, obj, form, change)
        
        if not change and obj.original_pdf:
            try:
                
                process_pdf_full(obj)
                self.message_user(request, "PDF processed successfully: Pages extracted and augmented.")
            except Exception as e:
                self.message_user(request, f"Error: {e}", level='ERROR')

    @admin.action(description="Generate Extra Synthetic Copies")
    def manual_augment_action(self, request, queryset):
        """Manual trigger agar dashboard testing ke liye aur data chahiye"""
        for obj in queryset:
            create_synthetic_copies(obj, count=3)
        self.message_user(request, "Extra copies generated for selected pages.")