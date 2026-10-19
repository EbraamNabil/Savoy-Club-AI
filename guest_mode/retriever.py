from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_policy_documents(
    documents: list,
    chunk_size: int = 800,
    chunk_overlap: int = 120
) -> list:
    """Split policy pages into chunks and preserve page metadata."""

    # Create a text splitter with overlap between adjacent chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # Store all generated chunks
    chunks = []

    # Process each loaded policy document
    for document in documents:
        # Read the source filename
        source = document["source"]

        # Use page-level text when the loader provides page metadata
        pages = document.get("pages")

        if pages:
            # Process each page separately to preserve accurate page numbers
            for page in pages:
                page_number = page["page"]
                page_text = page["text"].strip()

                # Skip pages that contain no extractable text
                if not page_text:
                    continue

                # Split the current page into smaller text segments
                text_parts = text_splitter.split_text(page_text)

                # Store each chunk with its original source and page number
                for index, text_part in enumerate(text_parts):
                    chunks.append({
                        "text": text_part,
                        "source": source,
                        "page": page_number,
                        "chunk_id": f"page_{page_number}_chunk_{index}"
                    })

        else:
            # Fall back to splitting the full text if page metadata is unavailable
            text_parts = text_splitter.split_text(document["text"])

            # Store chunks without inventing page numbers
            for index, text_part in enumerate(text_parts):
                chunks.append({
                    "text": text_part,
                    "source": source,
                    "page": None,
                    "chunk_id": f"chunk_{index}"
                })

    # Return all chunks with their metadata
    return chunks
