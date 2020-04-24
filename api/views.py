import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Recipe, Comment
from .serializers import CategorySerializer, RecipeSerializer, CommentSerializer, MyUserSerializer


@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        serializer = MyUserSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status.HTTP_400_BAD_REQUEST)

    return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST'])
def category_list(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def category_detail(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = CategorySerializer(instance=category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.update(serializer.instance, request.data)
            return Response(serializer.data)
        return Response({'error': serializer.errors})
    elif request.method == 'DELETE':
        category.delete()
        return Response({'deleted': True})


class RecipeListAPIView(APIView):
    def get(self, request):
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecipeDetailAPIView(APIView):
    def get_object(self, recipe_id):
        try:
            return Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist as e:
            return Response({'error': str(e)})

    def get(self, request, recipe_id):
        # recipe = self.get_object(recipe_id)
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    def put(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        serializer = RecipeSerializer(instance=recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'errors': serializer.errors})

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        recipe.delete()

        return Response({'deleted': True})


class RecipeByCategoryAPIView(APIView):
    def get(self, request, category_id):
        recipes = Recipe.objects.filter(category=category_id)
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)


class TopTenRecipesAPIView(APIView):
    def get(self, request):
        top_ten = Recipe.objects.order_by('likes')[:10]
        serializer = RecipeSerializer(top_ten, many=True)
        return Response(serializer.data)


class CommentsByRecipeAPIView(generics.ListAPIView):
    def get_queryset(self):
        return Comment.objects.filter(recipe=self.kwargs.get('pk'))

    serializer_class = CommentSerializer


class FollowRecipeAPIView(APIView):
    def put(self, request, recipe_id):
        recipe = Recipe.objects.get(id=recipe_id)
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized user'}, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        recipe.followers.add(user)
        user.recipe_set.add(recipe)
        recipe.save()
        user.save()
        return Response({'message': 'User {} successfully followed recipe {}'.format(user.id, recipe_id)},
                        status=status.HTTP_200_OK)


class LikeRecipeAPIView(APIView):
    def put(self, request, recipe_id):
        recipe = Recipe.objects.get(id=recipe_id)
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized user'}, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        recipe.likes += 1
        recipe.save()
        return Response({'message': 'Recipe {} successfully liked'.format(recipe_id)})