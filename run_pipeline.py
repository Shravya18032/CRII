import os

print("Step 1: Generate Grid")
os.system("python preprocessing/generate_grid.py")

print("Step 2: NDVI")
os.system("python preprocessing/extract_ndvi.py")

print("Step 3: LST")
os.system("python preprocessing/extract_lst.py")

print("Step 4: Urban")
os.system("python preprocessing/extract_urban.py")

print("Step 5: Flood")
os.system("python preprocessing/extract_flood.py")

print("Step 6: CRII")
os.system("python crii_engine/compute_crii.py")

print("Step 7: Extract Images")
os.system("python preprocessing/extract_images.py")

print("Step 8: CLIP")
os.system("python models/clip_scoring.py")

print("Step 9: Hybrid CRII")
os.system("python crii_engine/hybrid_crii.py")

print("Step 10: Visualization")
os.system("python visualization/plot_map.py")

print("Pipeline completed 🚀")