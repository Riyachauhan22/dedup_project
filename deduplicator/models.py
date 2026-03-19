from django.db import models

class DocumentPage(models.Model):
    
    original_pdf = models.FileField(upload_to='pdfs/')
    
   
    page_image = models.ImageField(upload_to='extracted_pages/', null=True, blank=True)
    
    page_number = models.IntegerField(default=0)
   
    phash = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    
    embedding_blob = models.BinaryField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Page {self.page_number} - {self.original_pdf.name}"