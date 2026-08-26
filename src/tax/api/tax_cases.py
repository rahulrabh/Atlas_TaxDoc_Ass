from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from tax.models import TaxCase


class TaxCaseListAPIView(APIView):

    def get(self, request):
        tax_cases = (
            TaxCase.objects
            .select_related("client")
            .order_by("-tax_year", "created_at")
        )

        cases = []

        for tax_case in tax_cases:
            cases.append({
                "id": str(tax_case.id),
                "client_name": tax_case.client.name,
                "tax_year": tax_case.tax_year,
                "filing_status": tax_case.filing_status,
            })

        return Response(
            {
                "tax_cases": cases,
            },
            status=status.HTTP_200_OK,
        )