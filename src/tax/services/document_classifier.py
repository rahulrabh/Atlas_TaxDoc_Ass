from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from tax.models import (
    DocumentClassificationStatus,
    RequirementDocumentType,
)


@dataclass
class ClassificationResult:
    document_type: Optional[str]
    tax_year: Optional[int]
    person_id: Optional[UUID]
    employment_id: Optional[UUID]
    confidence: Decimal
    status: str


class DocumentClassifier:

    def classify(self, document):
        """
        Deterministic classifier used for the take-home demo.

        A production implementation could replace this class with
        OCR + LLM/document-classification infrastructure without
        changing the processing pipeline.
        """

        file_name = document.file_name.lower()

        # Unreadable / unknown document
        if "unreadable" in file_name or "unknown" in file_name:
            return ClassificationResult(
                document_type=RequirementDocumentType.UNKNOWN,
                tax_year=None,
                person_id=None,
                employment_id=None,
                confidence=Decimal("0.2000"),
                status=DocumentClassificationStatus.REVIEW_REQUIRED,
            )

        # 1040
        if "1040" in file_name:
            tax_year = self._extract_year(file_name)

            return ClassificationResult(
                document_type=RequirementDocumentType.FORM_1040,
                tax_year=tax_year,
                person_id=None,
                employment_id=None,
                confidence=Decimal("0.9500"),
                status=DocumentClassificationStatus.CLASSIFIED,
            )

        # Government ID
        if "government_id" in file_name:
            person = self._find_person(
                document,
                file_name,
            )

            if person is None:
                return self._review_result()

            return ClassificationResult(
                document_type=RequirementDocumentType.GOVERNMENT_ID,
                tax_year=document.tax_case.tax_year,
                person_id=person.id,
                employment_id=None,
                confidence=Decimal("0.9500"),
                status=DocumentClassificationStatus.CLASSIFIED,
            )

        # W-2
        if "w2" in file_name:
            person = self._find_person(
                document,
                file_name,
            )

            employment = self._find_employment(
                document,
                file_name,
            )

            if person is None or employment is None:
                return self._review_result()

            return ClassificationResult(
                document_type=RequirementDocumentType.W2,
                tax_year=self._extract_year(file_name),
                person_id=person.id,
                employment_id=employment.id,
                confidence=Decimal("0.9500"),
                status=DocumentClassificationStatus.CLASSIFIED,
            )

        return self._review_result()

    def _find_person(self, document, file_name):
        people = document.tax_case.people.all()

        for person in people:
            normalized_name = person.name.lower().replace(
                " ",
                "_",
            )

            if normalized_name in file_name:
                return person

        return None

    def _find_employment(self, document, file_name):
        employments = []

        for person in document.tax_case.people.all():
            employments.extend(
                person.employments.all()
            )

        for employment in employments:
            normalized_name = (
                employment.employer_name
                .lower()
                .replace(" ", "_")
            )

            if normalized_name in file_name:
                return employment

        return None

    def _extract_year(self, file_name):
        import re

        match = re.search(
            r"(20\d{2})",
            file_name,
        )

        if match:
            return int(match.group(1))

        return None

    def _review_result(self):
        return ClassificationResult(
            document_type=RequirementDocumentType.UNKNOWN,
            tax_year=None,
            person_id=None,
            employment_id=None,
            confidence=Decimal("0.2000"),
            status=DocumentClassificationStatus.REVIEW_REQUIRED,
        )