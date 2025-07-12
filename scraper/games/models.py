from django.db import models
from django.utils import timezone


class Game(models.Model):
    title = models.CharField(
        max_length=64, verbose_name="Game Title", null=True, blank=True)
    link = models.URLField(max_length=200, verbose_name="Game Link")
    slug = models.SlugField(verbose_name="Slug", unique=True, blank=True)

    meta_score = models.CharField(
        max_length=4, verbose_name="Metacritic Score", null=True, blank=True)
    meta_score_count = models.CharField(
        max_length=16, verbose_name="Meta Reviews Count", null=True, blank=True)
    user_score = models.CharField(
        max_length=4, verbose_name="User Score", null=True, blank=True)
    user_score_count = models.CharField(
        max_length=16, verbose_name="User Reviews Count", null=True, blank=True)

    platforms = models.CharField(
        max_length=128, verbose_name="Platforms", null=True, blank=True)
    release_date = models.DateField(
        verbose_name="Release Date", null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    developer = models.CharField(
        max_length=64, verbose_name="Developer", null=True, blank=True)
    publisher = models.CharField(
        max_length=64, verbose_name="Publisher", null=True, blank=True)

    updated_date = models.DateField(auto_now=True, null=True, blank=True)

    image = models.ImageField(upload_to='images/games',
                              verbose_name='Games Image', null=True, blank=True)
    image_failed = models.BooleanField(default=False)
    bg_image = models.ImageField(
        upload_to='images/games/bg', verbose_name='Games BG Image', null=True, blank=True)

    def __str__(self):
        return self.slug


class Page(models.Model):
    page_number = models.IntegerField(default=1)

    def __str__(self):
        return str(self.page_number)
