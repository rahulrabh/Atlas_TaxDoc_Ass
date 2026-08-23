from datetime import date

from django.test import TestCase

from tax.models import (
    Client,
    Employment,
    Person,
    Requirement,
    RequirementDocumentType,
    TaxCase,
)

from tax.services.requirement_generator import generate_requirements

class RequirementGeneratorTests(TestCase):

    def setUp(self):
        """
        Baseline scenario:

        Tax year: 2025

        Rahul:
            - Company A
            - Company B

        Priya:
            - Company C
        """

        self.client_obj = Client.objects.create(
            name="Acme Corp Client",
        )

        self.tax_case = TaxCase.objects.create(
            client=self.client_obj,
            tax_year=2025,
            filing_status=TaxCase.FilingStatus.MARRIED_JOINTLY,
        )

        self.rahul = Person.objects.create(
            tax_case=self.tax_case,
            name="Rahul",
            role=Person.Role.TAXPAYER,
        )

        self.priya = Person.objects.create(
            tax_case=self.tax_case,
            name="Priya",
            role=Person.Role.SPOUSE,
        )

        self.rahul_company_a = Employment.objects.create(
            person=self.rahul,
            employer_name="Company A",
            start_date=date(2024, 1, 1),
        )

        self.rahul_company_b = Employment.objects.create(
            person=self.rahul,
            employer_name="Company B",
            start_date=date(2024, 1, 1),
        )

        self.priya_company_c = Employment.objects.create(
            person=self.priya,
            employer_name="Company C",
            start_date=date(2024, 1, 1),
        )

    # Test 1

    def test_generates_correct_requirements(self):
        """
        2025 tax case should generate:

        - 1 previous-year Form 1040
        - 2 government IDs
        - 3 W-2s

        Total = 6 requirements.
        """

        requirements = generate_requirements(self.tax_case)

        self.assertEqual(len(requirements), 6)

        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
            ).count(),
            6,
        )

        # Form 1040
        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
                document_type=RequirementDocumentType.FORM_1040,
                tax_year=2024,
                person=None,
                employment=None,
            ).count(),
            1,
        )

        # Government IDs
        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
                document_type=RequirementDocumentType.GOVERNMENT_ID,
                tax_year=2025,
            ).count(),
            2,
        )

        # W-2s
        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
                document_type=RequirementDocumentType.W2,
                tax_year=2025,
            ).count(),
            3,
        )

    # Test 2

    def test_w2_requirements_are_linked_to_correct_people_and_employments(self):
        """
        Each W-2 must belong to the correct person and employment.
        """

        generate_requirements(self.tax_case)

        rahul_w2s = Requirement.objects.filter(
            tax_case=self.tax_case,
            person=self.rahul,
            document_type=RequirementDocumentType.W2,
        )

        priya_w2s = Requirement.objects.filter(
            tax_case=self.tax_case,
            person=self.priya,
            document_type=RequirementDocumentType.W2,
        )

        self.assertEqual(rahul_w2s.count(), 2)
        self.assertEqual(priya_w2s.count(), 1)

        rahul_employments = set(
            rahul_w2s.values_list(
                "employment_id",
                flat=True,
            )
        )

        self.assertEqual(
            rahul_employments,
            {
                self.rahul_company_a.id,
                self.rahul_company_b.id,
            },
        )

        self.assertEqual(
            priya_w2s.first().employment_id,
            self.priya_company_c.id,
        )

    # Test 3

    def test_running_generator_twice_is_idempotent(self):
        """
        Running the generator repeatedly must not create duplicates.
        """

        first_run = generate_requirements(self.tax_case)
        second_run = generate_requirements(self.tax_case)

        self.assertEqual(len(first_run), 6)
        self.assertEqual(len(second_run), 6)

        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
            ).count(),
            6,
        )

        first_ids = {requirement.id for requirement in first_run}
        second_ids = {requirement.id for requirement in second_run}

        self.assertEqual(first_ids, second_ids)

    # Test 4

    def test_new_employment_creates_only_new_w2_requirement(self):
        """
        If Rahul gets another job after the initial generation,
        running the generator again should create only the new W-2.
        """

        initial_requirements = generate_requirements(
            self.tax_case
        )

        initial_ids = {
            requirement.id
            for requirement in initial_requirements
        }

        self.assertEqual(len(initial_ids), 6)

        # New employment
        rahul_company_d = Employment.objects.create(
            person=self.rahul,
            employer_name="Company D",
            start_date=date(2025, 7, 1),
        )

        updated_requirements = generate_requirements(
            self.tax_case
        )

        self.assertEqual(len(updated_requirements), 7)

        current_ids = {
            requirement.id
            for requirement in updated_requirements
        }

        # All old requirements still exist
        self.assertTrue(
            initial_ids.issubset(current_ids)
        )

        # New W-2 exists
        new_w2 = Requirement.objects.get(
            tax_case=self.tax_case,
            person=self.rahul,
            employment=rahul_company_d,
            document_type=RequirementDocumentType.W2,
            tax_year=2025,
        )

        self.assertIsNotNone(new_w2)

        # Exactly 3 W-2s now belong to Rahul
        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
                person=self.rahul,
                document_type=RequirementDocumentType.W2,
            ).count(),
            3,
        )

    # Test 5

    def test_new_person_creates_only_that_persons_requirements(self):
        """
        Adding a new person should create:

        - Government ID
        - One W-2 per employment

        Existing requirements must remain.
        """

        initial_requirements = generate_requirements(
            self.tax_case
        )

        initial_ids = {
            requirement.id
            for requirement in initial_requirements
        }

        # New person
        gaurav = Person.objects.create(
            tax_case=self.tax_case,
            name="Gaurav",
            role=Person.Role.DEPENDENT,
        )

        gaurav_employment = Employment.objects.create(
            person=gaurav,
            employer_name="Company D",
            start_date=date(2025, 1, 1),
        )

        updated_requirements = generate_requirements(
            self.tax_case
        )

        # Original 6 + Government ID + W-2
        self.assertEqual(
            len(updated_requirements),
            8,
        )

        current_ids = {
            requirement.id
            for requirement in updated_requirements
        }

        self.assertTrue(
            initial_ids.issubset(current_ids)
        )

        # Government ID
        self.assertTrue(
            Requirement.objects.filter(
                tax_case=self.tax_case,
                person=gaurav,
                employment=None,
                document_type=RequirementDocumentType.GOVERNMENT_ID,
                tax_year=2025,
            ).exists()
        )

        # W-2
        self.assertTrue(
            Requirement.objects.filter(
                tax_case=self.tax_case,
                person=gaurav,
                employment=gaurav_employment,
                document_type=RequirementDocumentType.W2,
                tax_year=2025,
            ).exists()
        )

    # Test 6

    def test_different_tax_cases_have_independent_requirements(self):
        """
        Requirements from one tax case must not interfere
        with requirements from another tax case.
        """

        generate_requirements(self.tax_case)

        # Another client
        second_client = Client.objects.create(
            name="Second Client",
        )

        second_tax_case = TaxCase.objects.create(
            client=second_client,
            tax_year=2026,
            filing_status=TaxCase.FilingStatus.SINGLE,
        )

        second_person = Person.objects.create(
            tax_case=second_tax_case,
            name="Rahul",
            role=Person.Role.TAXPAYER,
        )

        second_employment = Employment.objects.create(
            person=second_person,
            employer_name="Company A",
            start_date=date(2026, 1, 1),
        )

        second_requirements = generate_requirements(
            second_tax_case
        )

        self.assertEqual(
            len(second_requirements),
            3,
        )

        # First tax case remains unchanged
        self.assertEqual(
            Requirement.objects.filter(
                tax_case=self.tax_case,
            ).count(),
            6,
        )

        # Second tax case has its own requirements
        self.assertEqual(
            Requirement.objects.filter(
                tax_case=second_tax_case,
            ).count(),
            3,
        )

        self.assertTrue(
            Requirement.objects.filter(
                tax_case=second_tax_case,
                person=second_person,
                employment=second_employment,
                document_type=RequirementDocumentType.W2,
                tax_year=2026,
            ).exists()
        )