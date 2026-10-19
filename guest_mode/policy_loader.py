from pathlib import Path
from pypdf import PdfReader


def load_txt(file_path: Path) -> dict:
    """Load a text file and return its content and source metadata."""

    # Read the text file using UTF-8 encoding
    text = file_path.read_text(encoding="utf-8")

    # Return the extracted text and its source information
    return {
        "source": file_path.name,
        "text": text
    }


def load_pdf(file_path: Path) -> dict:
    """Extract text from a PDF file and return its source metadata."""

    # Open the PDF document
    reader = PdfReader(str(file_path))

    # Extract text from every page and keep page boundaries
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        # Extract the text from the current page
        page_text = page.extract_text() or ""

        # Store the page number alongside its text
        pages.append({
            "page": page_number,
            "text": page_text
        })

    # Combine page text while preserving the page information
    full_text = "\n".join(
        f"[Page {page['page']}]\n{page['text']}"
        for page in pages
    )

    # Return the extracted text and source metadata
    return {
        "source": file_path.name,
        "text": full_text,
        "pages": pages
    }


def load_policy_file(file_path: Path) -> dict:
    """Load a supported policy file based on its extension."""

    # Normalize the file extension to lowercase
    extension = file_path.suffix.lower()

    # Route PDF files to the PDF loader
    if extension == ".pdf":
        return load_pdf(file_path)

    # Route plain text files to the text loader
    if extension == ".txt":
        return load_txt(file_path)

    # Reject unsupported file types with a clear error
    raise ValueError(
        f"Unsupported policy file type: {extension}"
    )


def load_all_policies(policy_dir: Path) -> list:
    """Load all supported policy files from a directory."""

    # Define the supported policy file extensions
    supported_extensions = {".pdf", ".txt"}

    # Find supported files in the directory
    policy_files = sorted(
        file_path
        for file_path in policy_dir.iterdir()
        if file_path.is_file()
        and file_path.suffix.lower() in supported_extensions
    )

    # Load every supported file
    documents = [
        load_policy_file(file_path)
        for file_path in policy_files
    ]

    # Return the list of extracted policy documents
    return documents
