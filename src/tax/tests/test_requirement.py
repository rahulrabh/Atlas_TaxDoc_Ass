from datetime import date

from django.db import IntegrityError
from django.test import TestCase

from tax.models import (
    Client,
    Employment,
    Person,
    Requirement,
    TaxCase,
)

class RequirementModelTests(TestCase):
    def create_tax_case(self, tax_year=2025):
        client = Client.objects.create(
            name="Rahul Kumar",
        )

        tax_case = TaxCase.objects.create(
            client=client,
            tax_year=tax_year,
            filing_status="SINGLE",
        )

        person = Person.objects.create(
            tax_case=tax_case,
            name="Rahul Kimar",
            role="TAXPAYER",
        )

        employment = Employment.objects.create(
            person=person,
            employer_name="Company A",
            start_date=date(2025, 1, 1),
        )

        return client, tax_case, person, employment

    def test_can_create_employment_requirement(self):
        _, tax_case, person, employment = self.create_tax_case()

        requirement = Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=employment,
            document_type="W2",
            tax_year=2025,
        )

        self.assertEqual(requirement.document_type, "W2")
        self.assertEqual(requirement.person, person)
        self.assertEqual(requirement.employment, employment)
        self.assertEqual(requirement.tax_year, 2025)

    def test_duplicate_employment_requirement_is_rejected(self):
        _, tax_case, person, employment = self.create_tax_case()

        Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=employment,
            document_type="W2",
            tax_year=2025,
        )

        with self.assertRaises(IntegrityError):
            Requirement.objects.create(
                tax_case=tax_case,
                person=person,
                employment=employment,
                document_type="W2",
                tax_year=2025,
            )

    def test_different_employments_can_have_separate_requirements(self):
        _, tax_case, person, employment_a = self.create_tax_case()

        employment_b = Employment.objects.create(
            person=person,
            employer_name="Company B",
            start_date=date(2025, 7, 1),
        )

        Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=employment_a,
            document_type="W2",
            tax_year=2025,
        )

        Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=employment_b,
            document_type="W2",
            tax_year=2025,
        )

        self.assertEqual(
            Requirement.objects.filter(
                person=person,
                document_type="W2",
            ).count(),
            2,
        )

    def test_can_create_person_level_requirement(self):
        _, tax_case, person, _ = self.create_tax_case()

        requirement = Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=None,
            document_type="GOVERNMENT_ID",
            tax_year=2025,
        )

        self.assertEqual(requirement.person, person)
        self.assertIsNone(requirement.employment)

    def test_duplicate_person_requirement_is_rejected(self):
        _, tax_case, person, _ = self.create_tax_case()

        Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=None,
            document_type="GOVERNMENT_ID",
            tax_year=2025,
        )

        with self.assertRaises(IntegrityError):
            Requirement.objects.create(
                tax_case=tax_case,
                person=person,
                employment=None,
                document_type="GOVERNMENT_ID",
                tax_year=2025,
            )

    def test_can_create_tax_case_level_requirement(self):
        _, tax_case, _, _ = self.create_tax_case()

        requirement = Requirement.objects.create(
            tax_case=tax_case,
            person=None,
            employment=None,
            document_type="FORM_1040",
            tax_year=2024,
        )

        self.assertIsNone(requirement.person)
        self.assertIsNone(requirement.employment)
        self.assertEqual(requirement.tax_year, 2024)

    def test_duplicate_tax_case_requirement_is_rejected(self):
        _, tax_case, _, _ = self.create_tax_case()

        Requirement.objects.create(
            tax_case=tax_case,
            person=None,
            employment=None,
            document_type="FORM_1040",
            tax_year=2024,
        )

        with self.assertRaises(IntegrityError):
            Requirement.objects.create(
                tax_case=tax_case,
                person=None,
                employment=None,
                document_type="FORM_1040",
                tax_year=2024,
            )

    def test_same_document_type_allowed_for_different_tax_years(self):
        _, tax_case, person, _ = self.create_tax_case()

        Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=None,
            document_type="GOVERNMENT_ID",
            tax_year=2025,
        )

        Requirement.objects.create(
            tax_case=tax_case,
            person=person,
            employment=None,
            document_type="GOVERNMENT_ID",
            tax_year=2026,
        )

        self.assertEqual(
            Requirement.objects.filter(
                person=person,
                document_type="GOVERNMENT_ID",
            ).count(),
            2,
        )