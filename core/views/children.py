from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from core.models import Children
from core.serializers import ChildrenSerializer,ChildrenListSerializer

# ================== Create a child entry
class ChildrenCreateView(generics.CreateAPIView):
    queryset = Children.objects.all()
    serializer_class = ChildrenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            child = serializer.save()
            return Response({
                "message": "data has been successfully registered", "crated_data": serializer.data
               
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ====================== Update a child entry==================


class ChildrenUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Children.objects.all()
    serializer_class = ChildrenSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            child = serializer.save()
        
            return Response({
                    "message": "data has been successfully updated", "updated_data": serializer.data
                
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#===========Delete record====================

class ChildrenDeleteView(generics.DestroyAPIView):
    queryset = Children.objects.all()
    serializer_class = ChildrenSerializer
    lookup_field = 'pk'  

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
      

        self.perform_destroy(instance)  # Delete the record

        return Response({
            "message": "Data has been successfully deleted",
           
        }, status=status.HTTP_200_OK)

# ==================== List children by parent_id =========================


class ChildrenListByParentView(generics.ListAPIView):
    serializer_class = ChildrenListSerializer

    def get_queryset(self):
        parent_id = self.kwargs['parent_id']  
        return Children.objects.filter(parent_id=parent_id)  

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():  
            return Response({
                "message": "No record found in the table for this ID",
                "sms": f"No children records found for parent ID {self.kwargs['parent_id']}."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
