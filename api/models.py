from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Recipe(models.Model):
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=1000)
    ingredients = models.CharField(max_length=1000)
    steps = models.CharField(max_length=1000)
    likes = models.IntegerField()
    front_image = models.CharField(max_length=1000)
    first_image = models.CharField(max_length=1000, default='')
    second_image = models.CharField(max_length=1000, default='')
    third_image = models.CharField(max_length=1000, default='')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="recipes")
    author = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name="recipes", default=1)
    followers = models.ManyToManyField(MyUser)

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'


class Comment(models.Model):
    title = models.CharField(max_length=100, default='default title')
    text = models.CharField(max_length=1000, default='default text')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='comments')

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
