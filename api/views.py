import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics, filters
from rest_framework.decorators import api_view
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
    def get(self, request, recipe_id):
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


class CommentsByRecipeAPIView(APIView):
    def get(self, request, **kwargs):
        comments = Comment.objects.filter(recipe=kwargs.get('recipe_id'))
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, **kwargs):
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized user'}, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        request.data["author"] = user.id
        request.data["recipe"] = kwargs.get('recipe_id')
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentByRecipeAPIView(APIView):
    def put(self, request, recipe_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        user = request.user
        if comment.author.id != user.id:
            return Response({'message': 'You can not edit this comment'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(instance=comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'errors': serializer.errors})

    def delete(self, request, recipe_id, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        user = request.user
        if comment.author.id != user.id:
            return Response({'message': 'You can not edit this comment'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response({'deleted': True})


class FollowRecipeAPIView(APIView):
    def put(self, request, recipe_id):
        recipe = Recipe.objects.get(id=recipe_id)
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized user'}, status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        recipes = Recipe.objects.filter(followers__in=[user])
        if recipe in recipes:
            recipe.followers.remove(user)
            user.followed_recipes.remove(recipe)
            recipe.save()
            user.save()
            return Response({'message': 'User {} successfully unfollowed recipe {}'.format(user.id, recipe_id)},
                            status=status.HTTP_200_OK)
        else:
            recipe.followers.add(user)
            user.followed_recipes.add(recipe)
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


class FollowedRecipesByUserAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'message': 'Unauthorized user'}, status=status.HTTP_401_UNAUTHORIZED)
        recipes = Recipe.objects.filter(followers__in=[request.user])
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)


class RecipeSearchAPIView(generics.ListCreateAPIView):
    search_fields = ['title']
    filter_backends = (filters.SearchFilter,)
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
