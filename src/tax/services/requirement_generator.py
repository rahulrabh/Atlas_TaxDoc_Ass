from tax.models import Requirement, RequirementDocumentType

def generate_requirements(tax_case):
    """
    Derive the document requirements for a tax case
    """
    requirements = []
    previous_tax_year = tax_case.tax_year - 1

    # 1 Previous year Form 1040
    req_1040, _ = Requirement.objects.get_or_create(
        person=None,
        employment=None,
        tax_case=tax_case,
        document_type=RequirementDocumentType.FORM_1040,
        tax_year=previous_tax_year,
    )
    requirements.append(req_1040)

    # 2. Government ID for every person

    for person in tax_case.people.all():
        #Create government ID for the person
        req_gov_id, _ = Requirement.objects.get_or_create(
            person=person,
            employment=None,
            tax_case=tax_case,
            tax_year=tax_case.tax_year,
            document_type=RequirementDocumentType.GOVERNMENT_ID,
        )
        requirements.append(req_gov_id)

    # 3. W-2 for every employment
        for employment in person.employments.all():
        # Create W-2 requirement tied to this specific employment
            req_w2, _ = Requirement.objects.get_or_create(
                person=person,
                tax_case=tax_case,
                employment=employment,
                document_type=RequirementDocumentType.W2,
                tax_year=tax_case.tax_year,
            )
            requirements.append(req_w2)

    return requirements