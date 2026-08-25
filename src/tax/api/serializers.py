from rest_framework import serializers

class RequirementStatusSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="requirement.id")
    document_type = serializers.CharField(
        source="requirement.document_type"
    )
    tax_year = serializers.IntegerField(
        source="requirement.tax_year"
    )
    status = serializers.CharField()

class CollectionSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    received = serializers.IntegerField()
    outstanding = serializers.IntegerField()
    needs_review = serializers.IntegerField()

class CollectionStatusSerializer(serializers.Serializer):
    tax_case_id = serializers.UUIDField()
    tax_year = serializers.IntegerField()
    summary = CollectionSummarySerializer()
    requirements = RequirementStatusSerializer(
        many=True
    )