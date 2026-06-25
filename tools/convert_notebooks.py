import os
import glob
import subprocess
import tempfile
import sys

def main():
    # Set paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    notebooks_dir = os.path.join(repo_root, "notebooks")
    output_pdf = os.path.join(notebooks_dir, "combined_handbook.pdf")
    
    # 1. Find all .ipynb files in the notebooks directory
    pattern = os.path.join(notebooks_dir, "*.ipynb")
    notebook_files = glob.glob(pattern)
    
    # 2. Filter and sort book chapters
    book_notebooks = []
    for f in notebook_files:
        basename = os.path.basename(f)
        if basename.startswith("Untitled") or basename.startswith("06.00-Figure-Code"):
            continue
        if basename.startswith("."):
            continue
        book_notebooks.append(f)
        
    book_notebooks.sort()
    
    if not book_notebooks:
        print("No notebooks found.")
        sys.exit(1)
        
    print(f"Found {len(book_notebooks)} notebooks to convert.")
    
    # 3. Create a temporary directory for individual PDF files
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_paths = []
        
        for idx, notebook_path in enumerate(book_notebooks, 1):
            basename = os.path.basename(notebook_path)
            name_without_ext = os.path.splitext(basename)[0]
            print(f"[{idx}/{len(book_notebooks)}] Converting {basename}...")
            
            # Convert to HTML in the same directory (so relative resource paths resolve correctly)
            html_cmd = [
                "jupyter", "nbconvert",
                "--to", "html",
                notebook_path
            ]
            
            try:
                subprocess.run(html_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                print(f"WARNING: Error converting {basename} to HTML. Skipping.")
                print(e.stderr.decode('utf-8', errors='ignore'))
                continue
                
            html_file = os.path.join(notebooks_dir, f"{name_without_ext}.html")
            pdf_file = os.path.join(tmpdir, f"{name_without_ext}.pdf")
            
            # Convert HTML to PDF using weasyprint with custom stylesheet
            weasy_css = os.path.join(script_dir, "weasyprint.css")
            weasy_cmd = ["weasyprint", "-s", weasy_css, html_file, pdf_file]
            try:
                subprocess.run(weasy_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pdf_paths.append(pdf_file)
            except subprocess.CalledProcessError as e:
                print(f"WARNING: Error converting HTML of {basename} to PDF. Skipping.")
                print(e.stderr.decode('utf-8', errors='ignore'))
            finally:
                # Always remove the temporary HTML file
                if os.path.exists(html_file):
                    os.remove(html_file)
                
        # 4. Merge all PDFs using pdfunite
        print("Merging all PDFs into a single file...")
        merge_cmd = ["pdfunite"] + pdf_paths + [output_pdf]
        try:
            subprocess.run(merge_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"\nSuccess! Combined PDF saved to:\n{output_pdf}")
        except subprocess.CalledProcessError as e:
            print("Error merging PDFs with pdfunite:")
            print(e.stderr.decode('utf-8', errors='ignore'))
            sys.exit(1)

if __name__ == "__main__":
    main()
