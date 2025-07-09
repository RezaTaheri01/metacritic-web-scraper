from django.db import models
from django.utils import timezone


class Game(models.Model):
    # tba: To be announced state
    title = models.CharField(max_length=64, verbose_name="Product Title")
    link = models.CharField(max_length=128, verbose_name="Product Link")
    slug = models.SlugField(verbose_name="Slug", unique=True)

    meta_score = models.FloatField(verbose_name="Metacritic Score", null=True)
    meta_score_count = models.CharField(
        max_length=16, verbose_name="Meta Reviews Count", null=True)
    user_score = models.FloatField(verbose_name="User Score", null=True)
    user_score_count = models.CharField(
        max_length=16, verbose_name="User Reviews Count", null=True)

    platforms = models.CharField(
        max_length=128, verbose_name="Platforms", null=True, blank=True)
    release_date = models.DateField(
        verbose_name="Release Date", null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    developer = models.CharField(
        max_length=64, verbose_name="Developer", null=True)
    publisher = models.CharField(
        max_length=64, verbose_name="Publisher", null=True)

    updated_date = models.DateField(null=True, blank=True)

    image = models.ImageField(upload_to='images/games',
                              null=True, verbose_name='Games Image')
    bg_image = models.ImageField(
        upload_to='images/games/bg', null=True, verbose_name='Games BG Image')
    yt_link = models.CharField(
        max_length=256, null=True, verbose_name="Youtube Trailer Link")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.updated_date = timezone.now()  # at each save!
        return super(Game, self).save(*args, **kwargs)


class Page(models.Model):
    page_number = models.IntegerField(default=1)
    
    def __str__(self):
        return str(self.page_number)
