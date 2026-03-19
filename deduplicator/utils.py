import fitz, io, torch, imagehash
import numpy as np
import imgaug.augmenters as iaa
from PIL import Image
from django.core.files.base import ContentFile
from .models import DocumentPage
from transformers import SiglipVisionModel, SiglipImageProcessor


device = "cuda" if torch.cuda.is_available() else "cpu"
model = SiglipVisionModel.from_pretrained("google/siglip-base-patch16-224").to(device)
processor = SiglipImageProcessor.from_pretrained("google/siglip-base-patch16-224")

aug_seq = iaa.Sequential([
    iaa.Affine(rotate=(-10, 10)), 
    iaa.AdditiveGaussianNoise(scale=(0, 0.05*255)), 
    iaa.GaussianBlur(sigma=(0, 0.5)) 
])

def get_embedding(pil_img):
    """Image ko mathematical vector mein badalta hai"""
    inputs = processor(images=pil_img, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.pooler_output.cpu().numpy().flatten().astype('float32')

def create_synthetic_copies(instance, count=5):
    """Original page se fake duplicates banata hai stress testing ke liye"""
    pil_img = Image.open(instance.page_image.path).convert('RGB')
    img_np = np.array(pil_img)

    for i in range(count):
        aug_img_np = aug_seq(image=img_np)
        aug_pil = Image.fromarray(aug_img_np)
        emb = get_embedding(aug_pil)

       
        buf = io.BytesIO()
        aug_pil.save(buf, format='PNG')
        
        
        copy_page = DocumentPage.objects.create(
            original_pdf=instance.original_pdf,
            page_number=instance.page_number,
            embedding_blob=emb.tobytes(),
            phash=str(imagehash.phash(aug_pil))
        )
       
        filename = f"aug_p{instance.page_number}_id{instance.id}_{i}.png"
        copy_page.page_image.save(filename, ContentFile(buf.getvalue()), save=True)

def process_pdf_full(instance):
    
    doc = fitz.open(instance.original_pdf.path)
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        
        emb = get_embedding(pil_img)
        
        
        orig_page = DocumentPage.objects.create(
            original_pdf=instance.original_pdf,
            page_number=i+1,
            embedding_blob=emb.tobytes(),
            phash=str(imagehash.phash(pil_img))
        )
        filename = f"orig_p{i+1}_id{instance.id}.png"
        orig_page.page_image.save(filename, ContentFile(img_data), save=True)
        
        
        create_synthetic_copies(orig_page)