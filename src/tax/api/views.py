from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from tax.models import TaxCase
from tax.services.collection_status import get_collection_status

from .serializers import CollectionStatusSerializer

class TaxCaseStatusAPIView(APIView):

    def get(self, request, tax_case_id):
        tax_case = get_object_or_404(
            TaxCase,
            id=tax_case_id,
        )

        collection_status = get_collection_status(
            tax_case
        )

        response_data = {
            "tax_case_id": tax_case.id,
            "tax_year": tax_case.tax_year,
            "summary": collection_status["summary"],
            "requirements": collection_status["requirements"],
        }

        serializer = CollectionStatusSerializer(
            response_data
        )

        return Response(serializer.data)