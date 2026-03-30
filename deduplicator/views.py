import numpy as np
import faiss
import imagehash
from django.shortcuts import render
from .models import DocumentPage

def dashboard(request):
   
    pages = list(DocumentPage.objects.exclude(embedding_blob=None))
    
    if not pages:
        return render(request, 'deduplicator/dashboard.html', {'clusters': []})

    
    embeddings = [np.frombuffer(p.embedding_blob, dtype='float32') for p in pages]
    data_array = np.vstack(embeddings)
    faiss.normalize_L2(data_array) 
    
    dimension = data_array.shape[1]
    index = faiss.IndexFlatIP(dimension) 
    index.add(data_array)

    
    MAX_CANDIDATES = 50 
    SIMILARITY_THRESHOLD = 0.85  
    PHASH_THRESHOLD = 25         
    
    distances, indices = index.search(data_array, min(MAX_CANDIDATES, len(pages)))

    clusters = []
    processed_ids = set()

    for i in range(len(pages)):
        if pages[i].id in processed_ids:
            continue
            
        file_path = str(pages[i].page_image.name if pages[i].page_image else "")
        
        
        if "aug_" not in file_path:
            current_cluster = {
                'head': pages[i],
                'duplicates': [],
                'pdf_name': pages[i].original_pdf.name.split('/')[-1] if pages[i].original_pdf else "Source"
            }
            processed_ids.add(pages[i].id)
            
            
            for j in range(1, len(indices[i])): 
                idx = indices[i][j]
                if idx == -1: continue
                
                score = distances[i][j]
                match_page = pages[idx]
                
                
                if score > SIMILARITY_THRESHOLD and match_page.id not in processed_ids:
                    
                    
                    if pages[i].phash and match_page.phash:
                        h1 = imagehash.hex_to_hash(pages[i].phash)
                        h2 = imagehash.hex_to_hash(match_page.phash)
                        
                        if (h1 - h2) > PHASH_THRESHOLD:
                            continue 

                    current_cluster['duplicates'].append(match_page)
                    processed_ids.add(match_page.id)
            
            clusters.append(current_cluster)

    return render(request, 'deduplicator/dashboard.html', {'clusters': clusters})