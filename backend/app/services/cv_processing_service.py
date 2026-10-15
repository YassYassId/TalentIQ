import pymupdf


MAX_CV_SIZE = 5 * 1024 * 1024  # 5 MB


class InvalidCVError(Exception):
    pass


class CVProcessingService:

    def extract_text(self, file_content: bytes) -> str:

        if not file_content:
            raise InvalidCVError("The uploaded file is empty")

        if len(file_content) > MAX_CV_SIZE:
            raise InvalidCVError("CV exceeds the 5 MB size limit")

        if not file_content.startswith(b"%PDF-"):
            raise InvalidCVError("Only PDF documents are supported")

        try:
            with pymupdf.open(
                stream=file_content,
                filetype="pdf",
            ) as document:

                if document.page_count == 0:
                    raise InvalidCVError(
                        "The PDF contains no pages"
                    )

                extracted_pages = [
                    page.get_text(sort=True)
                    for page in document
                ]

        except InvalidCVError:
            raise
        except (pymupdf.FileDataError, ValueError) as exc:
            raise InvalidCVError(
                "The uploaded PDF is invalid or corrupted"
            ) from exc

        text = "\n\n".join(extracted_pages).strip()

        if not text:
            raise InvalidCVError(
                "No extractable text found. "
                "Scanned PDFs are not supported yet."
            )

        return text