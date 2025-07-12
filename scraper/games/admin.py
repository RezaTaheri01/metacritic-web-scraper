from django.contrib import admin
from .models import Game, Page

# Register your models here.

@admin.register(Game)
class GamesAdmin(admin.ModelAdmin):
    search_fields = ["title", "slug"] # Fields to search within
    
    
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    ...
    
    
